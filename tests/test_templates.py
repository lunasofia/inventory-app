import pytest
from django.urls import reverse

from catalog.models import Item
from tests.conftest import category_id
from trips.models import (
    PackingItem, Template, TemplateItem, TemplateReminder, TemplateShare, Trip,
)

pytestmark = pytest.mark.django_db


def make_template(user, name='Baseline'):
    return Template.objects.create(owner=user, name=name)


# --- save a trip as a template ---

def test_save_as_template_copies_items(auth_client, user, trip):
    PackingItem.objects.create(trip=trip, name='Socks', quantity=3,
                               category=user.categories.get(name='Clothing'))
    PackingItem.objects.create(trip=trip, name='Passport')
    resp = auth_client.post(reverse('save_as_template', args=[trip.pk]),
                            {'name': 'My baseline', 'description': ''})
    assert resp.status_code == 302
    tpl = Template.objects.get(owner=user, name='My baseline')
    items = {ti.name: ti for ti in tpl.items.all()}
    assert set(items) == {'Socks', 'Passport'}
    assert items['Socks'].quantity == 3
    assert items['Socks'].category.name == 'Clothing'


def test_template_name_unique_per_owner(auth_client, user, trip):
    make_template(user, 'Dup')
    resp = auth_client.post(reverse('save_as_template', args=[trip.pk]), {'name': 'dup'})
    assert resp.status_code == 200
    assert b'already have a template with that name' in resp.content
    assert Template.objects.filter(owner=user).count() == 1


def test_template_create_get_renders(auth_client):
    resp = auth_client.get(reverse('template_create'))
    assert resp.status_code == 200
    assert b'Create template' in resp.content


def test_template_create_posts_and_redirects(auth_client, user):
    resp = auth_client.post(reverse('template_create'), {
        'name': 'New baseline',
        'description': 'A new reusable list',
    })
    assert resp.status_code == 302
    tpl = Template.objects.get(owner=user, name='New baseline')
    assert tpl.description == 'A new reusable list'


def test_template_create_duplicate_name_shows_error(auth_client, user):
    make_template(user, 'Dup')
    resp = auth_client.post(reverse('template_create'), {'name': 'dup'})
    assert resp.status_code == 200
    assert b'already have a template with that name' in resp.content
    assert Template.objects.filter(owner=user).count() == 1


# --- create a trip from a template ---

def test_create_trip_from_template_clones_and_links(auth_client, user):
    tpl = make_template(user, 'Beach')
    TemplateItem.objects.create(template=tpl, name='Sunscreen', quantity=2)
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Beach trip', 'status': 'planning', 'start_from_template': tpl.pk,
    })
    assert resp.status_code == 302
    trip = Trip.objects.get(name='Beach trip')
    assert trip.origin_template_id == tpl.pk
    item = trip.items.get(name='Sunscreen')
    assert item.quantity == 2
    # catalog linked, but usage not bumped by the clone
    cat_item = Item.objects.get(owner=user, name='Sunscreen')
    assert item.catalog_item_id == cat_item.pk
    assert cat_item.times_used == 0


def test_create_trip_blank_has_no_origin(auth_client):
    auth_client.post(reverse('trip_create'), {'name': 'Blank', 'status': 'planning'})
    assert Trip.objects.get(name='Blank').origin_template_id is None


# --- manage template items ---

def test_template_item_add_edit_delete(auth_client, user):
    tpl = make_template(user)
    auth_client.post(reverse('template_item_add', args=[tpl.pk]),
                     {'name': 'Towel', 'quantity': 1, 'category': ''})
    item = tpl.items.get(name='Towel')
    auth_client.post(reverse('template_item_edit', args=[tpl.pk, item.pk]),
                     {'name': 'Beach towel', 'quantity': 2, 'category': category_id(user, 'Clothing')})
    item.refresh_from_db()
    assert item.name == 'Beach towel' and item.quantity == 2
    auth_client.post(reverse('template_item_delete', args=[tpl.pk, item.pk]))
    assert not tpl.items.filter(pk=item.pk).exists()


def test_template_share_add_update_revoke(auth_client, user, other_user):
    tpl = make_template(user)
    resp = auth_client.post(reverse('template_share_add', args=[tpl.pk]), {
        'email': other_user.email,
        'permission': 'view',
    })
    assert resp.status_code == 200
    share = TemplateShare.objects.get(template=tpl, shared_with=other_user)
    assert share.permission == 'view'

    resp = auth_client.post(reverse('template_share_update', args=[tpl.pk, share.pk]), {
        'permission': 'edit',
    })
    assert resp.status_code == 200
    share.refresh_from_db()
    assert share.permission == 'edit'

    resp = auth_client.post(reverse('template_share_revoke', args=[tpl.pk, share.pk]))
    assert resp.status_code == 200
    assert not TemplateShare.objects.filter(pk=share.pk).exists()


def test_template_detail_share_dropdown_labels(auth_client, user, other_user):
    tpl = make_template(user)
    TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='view')
    resp = auth_client.get(reverse('template_detail', args=[tpl.pk]))
    assert resp.status_code == 200
    assert b'Can view' in resp.content
    assert b'Can edit' in resp.content


# --- access control ---

def test_cannot_touch_others_template(client, other_user, user):
    tpl = make_template(user)
    client.force_login(other_user)
    assert client.get(reverse('template_detail', args=[tpl.pk])).status_code == 404
    assert client.post(reverse('template_delete', args=[tpl.pk])).status_code == 404


def test_view_only_collaborator_cannot_edit_template_reminders(client, other_user, user):
    tpl = make_template(user)
    rem = TemplateReminder.objects.create(template=tpl, text='Check the safe')
    TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='view')
    client.force_login(other_user)
    assert client.post(reverse('template_reminder_add', args=[tpl.pk]),
                       {'text': 'sneaky'}).status_code == 404
    assert client.post(reverse('template_reminder_delete', args=[tpl.pk, rem.pk])).status_code == 404
    assert tpl.reminders.filter(pk=rem.pk).exists()            # not deleted
    assert not tpl.reminders.filter(text='sneaky').exists()    # not added


def test_edit_collaborator_can_edit_template_reminders(client, other_user, user):
    tpl = make_template(user)
    TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='edit')
    client.force_login(other_user)
    assert client.post(reverse('template_reminder_add', args=[tpl.pk]),
                       {'text': 'Wallet'}).status_code == 200
    assert tpl.reminders.filter(text='Wallet').exists()


def test_view_only_user_can_save_trip_as_own_template(client, other_user, user, trip):
    from trips.models import TripShare
    PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(reverse('save_as_template', args=[trip.pk]), {'name': 'Copied'})
    assert resp.status_code == 302
    assert Template.objects.filter(owner=other_user, name='Copied').exists()


# --- diff view (drift) ---

def _setup_diff(user):
    tpl = make_template(user, 'Base')
    clo = user.categories.get(name='Clothing')
    TemplateItem.objects.create(template=tpl, name='Socks', quantity=2, category=clo)
    TemplateItem.objects.create(template=tpl, name='Hat', quantity=1)
    trip = Trip.objects.create(owner=user, name='T', origin_template=tpl)
    PackingItem.objects.create(trip=trip, name='Socks', quantity=4, category=clo)   # changed qty
    PackingItem.objects.create(trip=trip, name='Charger')                            # added
    # 'Hat' absent on trip -> removed
    return tpl, trip


def test_diff_detects_added_removed_changed(auth_client, user):
    tpl, trip = _setup_diff(user)
    resp = auth_client.get(reverse('template_diff', args=[trip.pk]))
    assert resp.status_code == 200
    diff = resp.context['diff']
    assert [d['name'] for d in diff['added']] == ['Charger']
    assert [d['name'] for d in diff['removed']] == ['Hat']
    assert diff['changed'][0]['name'] == 'Socks'
    assert diff['changed'][0]['to_qty'] == 4


def test_diff_detects_category_change(auth_client, user):
    tpl = make_template(user, 'Base')
    TemplateItem.objects.create(template=tpl, name='Socks', quantity=1)  # no category
    trip = Trip.objects.create(owner=user, name='T', origin_template=tpl)
    PackingItem.objects.create(trip=trip, name='Socks', quantity=1,
                               category=user.categories.get(name='Clothing'))
    diff = auth_client.get(reverse('template_diff', args=[trip.pk])).context['diff']
    assert diff['changed'][0]['to_cat'] == 'Clothing'


def test_diff_apply_selected_changes(auth_client, user):
    tpl, trip = _setup_diff(user)
    resp = auth_client.post(reverse('template_diff', args=[trip.pk]), {
        'template': tpl.pk,
        'apply': ['added:charger', 'changed:socks', 'removed:hat'],
    })
    assert resp.status_code == 302
    names = {ti.name: ti.quantity for ti in tpl.items.all()}
    assert 'Charger' in names           # added
    assert names['Socks'] == 4          # changed
    assert 'Hat' not in names           # removed


def test_diff_apply_only_selected(auth_client, user):
    tpl, trip = _setup_diff(user)
    # apply only the addition; leave the change and removal
    auth_client.post(reverse('template_diff', args=[trip.pk]),
                     {'template': tpl.pk, 'apply': ['added:charger']})
    names = {ti.name: ti.quantity for ti in tpl.items.all()}
    assert 'Charger' in names
    assert names['Socks'] == 2  # unchanged
    assert 'Hat' in names       # not removed


def test_diff_case_insensitive_match(auth_client, user):
    tpl = make_template(user, 'Base')
    TemplateItem.objects.create(template=tpl, name='Wool Socks', quantity=1)
    trip = Trip.objects.create(owner=user, name='T', origin_template=tpl)
    PackingItem.objects.create(trip=trip, name='wool socks', quantity=3)
    diff = auth_client.get(reverse('template_diff', args=[trip.pk])).context['diff']
    assert diff['added'] == [] and diff['removed'] == []
    assert diff['changed'][0]['to_qty'] == 3


def test_diff_no_origin_shows_picker(auth_client, user):
    trip = Trip.objects.create(owner=user, name='Orphan')
    make_template(user, 'SomeTemplate')
    resp = auth_client.get(reverse('template_diff', args=[trip.pk]))
    assert resp.status_code == 200
    assert resp.context['template'] is None
