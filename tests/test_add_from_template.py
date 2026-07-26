"""Tests for the "add from template" feature (multi-select at creation + add to existing trip)."""
import pytest
from django.urls import reverse

from catalog.models import Condition, Item
from trips.models import PackingItem, Template, TemplateItem, TemplateShare, Trip, TripShare
from trips.views import _clone_template_into_trip

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_template(user, name='Baseline'):
    return Template.objects.create(owner=user, name=name)


def add_template_item(template, name, quantity=1, category=None, sort_order=0):
    return TemplateItem.objects.create(
        template=template, name=name, quantity=quantity,
        category=category, sort_order=sort_order,
    )


def make_trip(user, name='Test Trip'):
    return Trip.objects.create(owner=user, name=name, status=Trip.Status.PLANNING)


# ---------------------------------------------------------------------------
# Refactored helper — parity + dedup + intra-batch
# ---------------------------------------------------------------------------

def test_clone_into_empty_trip_adds_all_skipped_zero(user):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen', quantity=2, sort_order=1)
    add_template_item(tpl, 'Towel', quantity=1, sort_order=2)
    trip = make_trip(user)

    added, skipped = _clone_template_into_trip(tpl, trip)

    assert added == 2
    assert skipped == 0
    assert trip.items.count() == 2


def test_clone_catalog_linked_usage_not_bumped(user):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen', quantity=2)
    trip = make_trip(user)

    _clone_template_into_trip(tpl, trip)

    item = trip.items.get(name='Sunscreen')
    cat_item = Item.objects.get(owner=user, name='Sunscreen')
    assert item.catalog_item_id == cat_item.pk
    assert cat_item.times_used == 0


def test_clone_default_condition_set(user):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')
    trip = make_trip(user)
    default_cond = Condition.objects.filter(owner=user, is_default=True).first()

    _clone_template_into_trip(tpl, trip)

    item = trip.items.get(name='Sunscreen')
    assert item.condition_id == (default_cond.pk if default_cond else None)


def test_clone_category_resolved_to_trip_owner(user, other_user):
    # other_user already has a 'Clothing' category from seed_user_defaults
    other_cat = other_user.categories.get(name='Clothing')
    tpl = Template.objects.create(owner=other_user, name='Shared')
    TemplateShare.objects.create(template=tpl, shared_with=user, permission='view')
    add_template_item(tpl, 'Shirt', category=other_cat)
    trip = make_trip(user)

    _clone_template_into_trip(tpl, trip)

    item = trip.items.get(name='Shirt')
    assert item.category is not None
    assert item.category.owner_id == user.pk
    assert item.category.name == 'Clothing'


def test_clone_sort_order_sequential(user):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'A', sort_order=1)
    add_template_item(tpl, 'B', sort_order=2)
    add_template_item(tpl, 'C', sort_order=3)
    trip = make_trip(user)
    # Pre-seed an item with sort_order 5 to test continuation
    PackingItem.objects.create(trip=trip, name='Pre', sort_order=5)

    _clone_template_into_trip(tpl, trip)

    orders = list(trip.items.exclude(name='Pre').values_list('sort_order', flat=True).order_by('sort_order'))
    assert orders == sorted(orders)
    assert all(o > 5 for o in orders)


def test_clone_skips_existing_name_case_insensitive(user):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')
    add_template_item(tpl, 'Towel')
    trip = make_trip(user)
    PackingItem.objects.create(trip=trip, name='sunscreen', sort_order=1)

    added, skipped = _clone_template_into_trip(tpl, trip)

    assert added == 1
    assert skipped == 1
    assert trip.items.filter(name='Towel').exists()
    assert trip.items.filter(name__iexact='sunscreen').count() == 1  # not duplicated


def test_clone_intra_batch_dedup(user):
    """Two templates sharing an item name: second occurrence should be skipped."""
    tpl1 = make_template(user, 'T1')
    add_template_item(tpl1, 'Passport', sort_order=1)
    tpl2 = make_template(user, 'T2')
    add_template_item(tpl2, 'Passport', sort_order=1)  # duplicate
    add_template_item(tpl2, 'Towel', sort_order=2)
    trip = make_trip(user)

    added1, skipped1 = _clone_template_into_trip(tpl1, trip)
    added2, skipped2 = _clone_template_into_trip(tpl2, trip)

    assert added1 == 1 and skipped1 == 0
    assert added2 == 1 and skipped2 == 1  # Passport skipped, Towel added
    assert trip.items.filter(name='Passport').count() == 1


# ---------------------------------------------------------------------------
# Trip creation — multi-select
# ---------------------------------------------------------------------------

def test_create_trip_from_two_templates_union_deduped(auth_client, user):
    tpl1 = make_template(user, 'T1')
    add_template_item(tpl1, 'Passport', sort_order=1)
    add_template_item(tpl1, 'Sunscreen', sort_order=2)
    tpl2 = make_template(user, 'T2')
    add_template_item(tpl2, 'Sunscreen', sort_order=1)  # duplicate
    add_template_item(tpl2, 'Towel', sort_order=2)

    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Beach Trip',
        'status': 'planning',
        'start_from_template': [tpl1.pk, tpl2.pk],
    })
    assert resp.status_code == 302
    trip = Trip.objects.get(name='Beach Trip')
    names = set(trip.items.values_list('name', flat=True))
    assert names == {'Passport', 'Sunscreen', 'Towel'}


def test_origin_template_set_for_single_selection(auth_client, user):
    tpl = make_template(user, 'Solo')
    add_template_item(tpl, 'Passport')
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Solo Trip',
        'status': 'planning',
        'start_from_template': [tpl.pk],
    })
    assert resp.status_code == 302
    trip = Trip.objects.get(name='Solo Trip')
    assert trip.origin_template_id == tpl.pk


def test_origin_template_null_for_two_selections(auth_client, user):
    tpl1 = make_template(user, 'T1')
    tpl2 = make_template(user, 'T2')
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Multi Trip',
        'status': 'planning',
        'start_from_template': [tpl1.pk, tpl2.pk],
    })
    assert resp.status_code == 302
    trip = Trip.objects.get(name='Multi Trip')
    assert trip.origin_template_id is None


def test_origin_template_null_for_zero_selections(auth_client):
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Blank Trip',
        'status': 'planning',
    })
    assert resp.status_code == 302
    trip = Trip.objects.get(name='Blank Trip')
    assert trip.origin_template_id is None


def test_create_trip_success_message_single_template(auth_client, user):
    tpl = make_template(user, 'T1')
    add_template_item(tpl, 'Passport')
    add_template_item(tpl, 'Sunscreen')
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Trip1',
        'status': 'planning',
        'start_from_template': [tpl.pk],
    }, follow=True)
    messages_list = list(resp.context['messages'])
    assert any('2 items from 1 template' in str(m) for m in messages_list)


def test_create_trip_success_message_two_templates(auth_client, user):
    tpl1 = make_template(user, 'T1')
    add_template_item(tpl1, 'Passport')
    tpl2 = make_template(user, 'T2')
    add_template_item(tpl2, 'Towel')
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Trip2',
        'status': 'planning',
        'start_from_template': [tpl1.pk, tpl2.pk],
    }, follow=True)
    messages_list = list(resp.context['messages'])
    assert any('2 items from 2 templates' in str(m) for m in messages_list)


def test_create_trip_no_template_no_count_in_message(auth_client):
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'BlankTrip',
        'status': 'planning',
    }, follow=True)
    messages_list = list(resp.context['messages'])
    assert any('Created "BlankTrip"' in str(m) for m in messages_list)
    assert all('items from' not in str(m) for m in messages_list)


# ---------------------------------------------------------------------------
# Add from template on existing trip
# ---------------------------------------------------------------------------

def test_add_template_appends_after_max_sort_order(auth_client, user, trip):
    PackingItem.objects.create(trip=trip, name='Pre', sort_order=10)
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen', sort_order=1)

    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': tpl.pk})
    assert resp.status_code == 200

    # Pre item untouched
    assert trip.items.get(name='Pre').sort_order == 10
    # New item appended after
    new_item = trip.items.get(name='Sunscreen')
    assert new_item.sort_order > 10


def test_add_template_existing_items_untouched(auth_client, user, trip):
    existing = PackingItem.objects.create(trip=trip, name='Pre', sort_order=5, quantity=3)
    tpl = make_template(user, 'T')
    add_template_item(tpl, 'Sunscreen')

    auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                     {'template': tpl.pk})

    existing.refresh_from_db()
    assert existing.quantity == 3
    assert existing.sort_order == 5


def test_add_template_duplicate_names_skipped(auth_client, user, trip):
    PackingItem.objects.create(trip=trip, name='Sunscreen', sort_order=1)
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')  # duplicate
    add_template_item(tpl, 'Towel')

    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': tpl.pk}, follow=True)
    assert resp.status_code == 200

    assert trip.items.filter(name__iexact='sunscreen').count() == 1
    assert trip.items.filter(name='Towel').exists()
    messages_list = list(resp.context['messages'])
    assert any('1 skipped' in str(m) for m in messages_list)


def test_add_template_same_template_twice_second_all_skipped(auth_client, user, trip):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')
    add_template_item(tpl, 'Towel')

    auth_client.post(reverse('trip_add_template', args=[trip.pk]), {'template': tpl.pk})
    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': tpl.pk}, follow=True)

    assert trip.items.filter(name='Sunscreen').count() == 1
    assert trip.items.filter(name='Towel').count() == 1
    messages_list = list(resp.context['messages'])
    assert any('skipped' in str(m) for m in messages_list)


def test_add_template_editor_succeeds(client, user, other_user):
    trip = make_trip(user)
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    tpl = make_template(other_user, 'SharedTpl')
    add_template_item(tpl, 'Passport')

    client.force_login(other_user)
    resp = client.post(reverse('trip_add_template', args=[trip.pk]),
                       {'template': tpl.pk})
    assert resp.status_code == 200
    assert trip.items.filter(name='Passport').exists()


def test_add_template_viewer_gets_404(client, user, other_user):
    trip = make_trip(user)
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    tpl = make_template(user, 'T')
    add_template_item(tpl, 'Passport')

    client.force_login(other_user)
    resp = client.post(reverse('trip_add_template', args=[trip.pk]),
                       {'template': tpl.pk})
    assert resp.status_code == 404


def test_add_inaccessible_template_returns_404(auth_client, user, other_user, trip):
    other_tpl = make_template(other_user, 'Private')
    add_template_item(other_tpl, 'Secret Item')

    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': other_tpl.pk})
    assert resp.status_code == 404
    assert not trip.items.filter(name='Secret Item').exists()


def test_add_empty_template_friendly_message(auth_client, user, trip):
    tpl = make_template(user, 'Empty')
    # No items added

    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': tpl.pk}, follow=True)
    assert resp.status_code == 200
    messages_list = list(resp.context['messages'])
    assert any('no items to add' in str(m) for m in messages_list)
    assert trip.items.count() == 0


def test_add_template_catalog_no_bump_default_condition(auth_client, user, trip):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')
    default_cond = Condition.objects.filter(owner=user, is_default=True).first()

    auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                     {'template': tpl.pk})

    item = trip.items.get(name='Sunscreen')
    cat_item = Item.objects.get(owner=user, name='Sunscreen')
    assert item.catalog_item_id == cat_item.pk
    assert cat_item.times_used == 0
    assert item.condition_id == (default_cond.pk if default_cond else None)


def test_add_template_origin_template_unchanged(auth_client, user):
    """Adding a template to an existing trip should never change origin_template."""
    tpl_origin = make_template(user, 'Origin')
    add_template_item(tpl_origin, 'Passport')
    trip = Trip.objects.create(owner=user, name='TripWithOrigin',
                               status=Trip.Status.PLANNING, origin_template=tpl_origin)

    tpl2 = make_template(user, 'Extra')
    add_template_item(tpl2, 'Towel')

    auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                     {'template': tpl2.pk})

    trip.refresh_from_db()
    assert trip.origin_template_id == tpl_origin.pk


def test_add_template_success_message_no_skipped_clause(auth_client, user, trip):
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')
    add_template_item(tpl, 'Towel')

    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': tpl.pk}, follow=True)
    messages_list = list(resp.context['messages'])
    assert any('Added 2 items from' in str(m) for m in messages_list)
    assert all('skipped' not in str(m) for m in messages_list)


def test_add_template_success_message_with_skipped_clause(auth_client, user, trip):
    PackingItem.objects.create(trip=trip, name='Sunscreen', sort_order=1)
    tpl = make_template(user, 'Beach')
    add_template_item(tpl, 'Sunscreen')
    add_template_item(tpl, 'Towel')

    resp = auth_client.post(reverse('trip_add_template', args=[trip.pk]),
                            {'template': tpl.pk}, follow=True)
    messages_list = list(resp.context['messages'])
    assert any('1 skipped' in str(m) for m in messages_list)


# ---------------------------------------------------------------------------
# trip_detail context includes add_template_options
# ---------------------------------------------------------------------------

def test_trip_detail_passes_add_template_options(auth_client, user, trip):
    tpl = make_template(user, 'MyTemplate')
    resp = auth_client.get(reverse('trip_detail', args=[trip.pk]))
    assert resp.status_code == 200
    assert tpl in resp.context['add_template_options']
