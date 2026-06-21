import pytest
from django.urls import reverse

from catalog.models import Category
from trips.models import PackingItem, Template, TemplateItem, Trip

pytestmark = pytest.mark.django_db


# --- add ---

def test_add_category_standalone(auth_client, user):
    resp = auth_client.post(reverse('category_add'), {'name': 'Beach gear'})
    assert resp.status_code == 200
    assert Category.objects.filter(owner=user, name='Beach gear').exists()


def test_add_category_dedupes_case_insensitive(auth_client, user):
    Category.objects.create(owner=user, name='Beach gear')
    before = Category.objects.filter(owner=user).count()
    auth_client.post(reverse('category_add'), {'name': 'beach gear'})
    assert Category.objects.filter(owner=user).count() == before  # no dup


def test_add_empty_rejected(auth_client, user):
    before = Category.objects.filter(owner=user).count()
    resp = auth_client.post(reverse('category_add'), {'name': '  '})
    assert b'required' in resp.content
    assert Category.objects.filter(owner=user).count() == before


def test_add_from_planning_refreshes_dropdown(auth_client, user, trip):
    resp = auth_client.post(reverse('category_add'), {'name': 'Snorkel', 'trip': trip.pk})
    assert resp.status_code == 200
    assert b'id="planning"' in resp.content       # re-rendered planning region
    assert b'Snorkel' in resp.content             # available in the dropdown


# --- rename ---

def test_rename_preserves_item_association(auth_client, user, trip):
    # Note: the user fixture seeds defaults incl. "Toiletries", so rename to a
    # fresh name to avoid a legitimate duplicate rejection.
    cat = Category.objects.create(owner=user, name='Wsh kit')
    item = PackingItem.objects.create(trip=trip, name='Toothbrush', category=cat)
    resp = auth_client.post(reverse('category_rename', args=[cat.pk]), {'name': 'Wash kit'})
    assert resp.status_code == 200
    cat.refresh_from_db()
    item.refresh_from_db()
    assert cat.name == 'Wash kit'
    assert item.category_id == cat.pk  # still attached


def test_rename_to_duplicate_rejected(auth_client, user):
    Category.objects.create(owner=user, name='Clothes')
    cat = Category.objects.create(owner=user, name='Gear')
    resp = auth_client.post(reverse('category_rename', args=[cat.pk]), {'name': 'clothes'})
    assert b'already have a category with that name' in resp.content
    cat.refresh_from_db()
    assert cat.name == 'Gear'


# --- delete ---

def test_delete_unused_category(auth_client, user):
    cat = Category.objects.create(owner=user, name='Temp')
    auth_client.post(reverse('category_delete', args=[cat.pk]))
    assert not Category.objects.filter(pk=cat.pk).exists()


def test_delete_in_use_unsets_items_everywhere(auth_client, user):
    cat = Category.objects.create(owner=user, name='Doomed')
    trip = Trip.objects.create(owner=user, name='T')
    item = PackingItem.objects.create(trip=trip, name='Thing', category=cat)
    tpl = Template.objects.create(owner=user, name='Tpl')
    titem = TemplateItem.objects.create(template=tpl, name='Thing', category=cat)
    auth_client.post(reverse('category_delete', args=[cat.pk]))
    item.refresh_from_db()
    titem.refresh_from_db()
    assert not Category.objects.filter(pk=cat.pk).exists()
    assert item.category is None and titem.category is None   # Uncategorized
    assert PackingItem.objects.filter(pk=item.pk).exists()    # item not deleted


# --- access control ---

def test_cannot_rename_others_category(client, other_user, user):
    cat = Category.objects.create(owner=user, name='Mine')
    client.force_login(other_user)
    assert client.post(reverse('category_rename', args=[cat.pk]), {'name': 'Hijack'}).status_code == 404
    cat.refresh_from_db()
    assert cat.name == 'Mine'


def test_cannot_delete_others_category(client, other_user, user):
    cat = Category.objects.create(owner=user, name='Mine')
    client.force_login(other_user)
    assert client.post(reverse('category_delete', args=[cat.pk])).status_code == 404
    assert Category.objects.filter(pk=cat.pk).exists()


# --- placement ---

def test_manage_page_loads(auth_client):
    assert auth_client.get(reverse('category_manage')).status_code == 200


def test_planning_view_shows_category_panel(auth_client, trip):
    resp = auth_client.get(reverse('trip_detail', args=[trip.pk]))
    assert b'id="categories"' in resp.content
