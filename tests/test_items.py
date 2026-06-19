import pytest
from django.urls import reverse

from catalog.models import Item
from tests.conftest import category_id
from trips.models import PackingItem, Trip, TripShare
from trips.views import _grouped_items

pytestmark = pytest.mark.django_db


def add_url(trip):
    return reverse('item_add', args=[trip.pk])


def test_add_item_creates_packingitem_and_catalog(auth_client, user, trip):
    resp = auth_client.post(add_url(trip), {
        'name': 'Wool socks', 'quantity': 3, 'category': category_id(user, 'Clothing'),
    })
    assert resp.status_code == 200
    item = trip.items.get(name='Wool socks')
    assert item.quantity == 3
    # hybrid catalog: a catalog Item was remembered and linked
    cat_item = Item.objects.get(owner=user, name='Wool socks')
    assert item.catalog_item == cat_item
    assert cat_item.times_used == 1


def test_add_item_defaults_quantity_to_one(auth_client, user, trip):
    auth_client.post(add_url(trip), {'name': 'Hat', 'category': ''})
    assert trip.items.get(name='Hat').quantity == 1


def test_add_item_empty_name_invalid(auth_client, trip):
    resp = auth_client.post(add_url(trip), {'name': '', 'quantity': 1, 'category': ''})
    assert resp.status_code == 200
    assert trip.items.count() == 0


def test_add_item_quantity_zero_invalid(auth_client, trip):
    resp = auth_client.post(add_url(trip), {'name': 'Boots', 'quantity': 0, 'category': ''})
    assert b'Quantity must be at least 1.' in resp.content
    assert not trip.items.filter(name='Boots').exists()


def test_catalog_reuse_is_case_insensitive_and_bumps_usage(auth_client, user, trip):
    auth_client.post(add_url(trip), {'name': 'Passport', 'quantity': 1, 'category': ''})
    auth_client.post(add_url(trip), {'name': 'passport', 'quantity': 1, 'category': ''})
    items = Item.objects.filter(owner=user, name__iexact='passport')
    assert items.count() == 1
    assert items.first().times_used == 2
    # duplicates allowed on the trip (no auto-merge)
    assert trip.items.filter(name__iexact='passport').count() == 2


def test_autocomplete_returns_user_catalog_matches(auth_client, user, trip):
    Item.objects.create(owner=user, name='Wool socks', times_used=5)
    Item.objects.create(owner=user, name='Wallet', times_used=1)
    resp = auth_client.get(reverse('item_suggest', args=[trip.pk]), {'name': 'wo'})
    assert resp.status_code == 200
    assert b'Wool socks' in resp.content
    assert b'Wallet' not in resp.content


def test_autocomplete_is_user_scoped(client, other_user, user, trip):
    Item.objects.create(owner=user, name='Secret gadget', times_used=1)
    # other_user has a view share so they can hit the (edit-gated) suggest endpoint? No —
    # suggest requires edit; give them edit to prove scoping, not leakage.
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    client.force_login(other_user)
    resp = client.get(reverse('item_suggest', args=[trip.pk]), {'name': 'sec'})
    assert b'Secret gadget' not in resp.content  # not in other_user's catalog


def test_grouping_alphabetical_with_uncategorized_last(user, trip):
    PackingItem.objects.create(trip=trip, name='Charger')  # no category
    PackingItem.objects.create(trip=trip, name='Socks', category=user.categories.get(name='Clothing'))
    PackingItem.objects.create(trip=trip, name='Passport', category=user.categories.get(name='Documents'))
    groups = _grouped_items(trip)
    headings = [heading for heading, _bag, _items in groups]
    assert headings == ['Clothing', 'Documents', 'Uncategorized']


def test_edit_item_changes_fields(auth_client, user, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks', quantity=1)
    resp = auth_client.post(reverse('item_edit', args=[trip.pk, item.pk]), {
        'name': 'Wool socks', 'quantity': 4, 'category': category_id(user, 'Clothing'),
    })
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.quantity == 4
    assert item.category.name == 'Clothing'


def test_delete_item_preserves_catalog(auth_client, user, trip):
    auth_client.post(add_url(trip), {'name': 'Toothbrush', 'quantity': 1, 'category': ''})
    item = trip.items.get(name='Toothbrush')
    auth_client.post(reverse('item_delete', args=[trip.pk, item.pk]))
    assert not trip.items.filter(name='Toothbrush').exists()
    assert Item.objects.filter(owner=user, name__iexact='toothbrush').exists()


def test_view_only_user_cannot_add(client, other_user, trip):
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(add_url(trip), {'name': 'Sneaky', 'quantity': 1, 'category': ''})
    assert resp.status_code == 404
    assert not trip.items.filter(name='Sneaky').exists()


def test_edit_share_user_can_add(client, other_user, trip):
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    client.force_login(other_user)
    resp = client.post(add_url(trip), {'name': 'Allowed', 'quantity': 1, 'category': ''})
    assert resp.status_code == 200
    assert trip.items.filter(name='Allowed').exists()
