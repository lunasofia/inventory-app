import pytest
from django.urls import reverse

from tests.conftest import category_id
from trips.models import Bag, PackingItem, TripShare

pytestmark = pytest.mark.django_db


def move_url(trip, item):
    return reverse('item_move', args=[trip.pk, item.pk])


def set_lens(client, trip, mode):
    client.get(reverse('set_group', args=[trip.pk]), {'mode': mode})


# --- bag lens ---

def test_move_reassigns_bag(auth_client, trip):
    src = Bag.objects.create(trip=trip, name='Blue duffel')
    dst = Bag.objects.create(trip=trip, name='Black roller')
    item = PackingItem.objects.create(trip=trip, name='Socks', bag=src)
    set_lens(auth_client, trip, 'bag')
    resp = auth_client.post(move_url(trip, item), {'bag': dst.pk})
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bag_id == dst.pk


def test_move_to_unbagged(auth_client, trip):
    src = Bag.objects.create(trip=trip, name='Blue duffel')
    item = PackingItem.objects.create(trip=trip, name='Socks', bag=src)
    set_lens(auth_client, trip, 'bag')
    resp = auth_client.post(move_url(trip, item), {'bag': ''})
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.bag is None


# --- category lens ---

def test_move_reassigns_category(auth_client, user, trip):
    item = PackingItem.objects.create(
        trip=trip, name='Socks', category_id=category_id(user, 'Clothing'))
    set_lens(auth_client, trip, 'category')
    dst = category_id(user, 'Toiletries')
    resp = auth_client.post(move_url(trip, item), {'category': dst})
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.category_id == dst


def test_move_to_uncategorized(auth_client, user, trip):
    item = PackingItem.objects.create(
        trip=trip, name='Socks', category_id=category_id(user, 'Clothing'))
    set_lens(auth_client, trip, 'category')
    resp = auth_client.post(move_url(trip, item), {'category': ''})
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.category is None


def test_move_preserves_other_fields(auth_client, trip):
    src = Bag.objects.create(trip=trip, name='Blue duffel')
    dst = Bag.objects.create(trip=trip, name='Black roller')
    item = PackingItem.objects.create(
        trip=trip, name='Socks', bag=src, quantity=4, packed=True, notes='wool')
    set_lens(auth_client, trip, 'bag')
    auth_client.post(move_url(trip, item), {'bag': dst.pk})
    item.refresh_from_db()
    assert (item.quantity, item.packed, item.notes) == (4, True, 'wool')


# --- render-level smoke checks (guard against render-only bugs) ---

def test_move_row_renders_htmx_attrs(auth_client, trip):
    dst = Bag.objects.create(trip=trip, name='Black roller')
    item = PackingItem.objects.create(trip=trip, name='Socks')
    set_lens(auth_client, trip, 'bag')
    resp = auth_client.get(move_url(trip, item))
    assert resp.status_code == 200
    html = resp.content.decode()
    # real, ASCII-quoted HTMX attributes present
    assert 'hx-trigger="change"' in html
    assert 'hx-target="#planning"' in html
    assert '<select name="bag"' in html
    assert 'Black roller' in html
    # no smart-quote attribute delimiters slipped in
    for bad in ('=”', '=“'):
        assert bad not in html


def test_move_button_shown_per_lens_and_hidden_in_all(auth_client, trip):
    PackingItem.objects.create(trip=trip, name='Socks')
    lens = reverse('set_group', args=[trip.pk])
    # set_group re-renders the #planning region with the chosen lens.
    assert '/move/' in auth_client.get(lens, {'mode': 'bag'}).content.decode()
    assert '/move/' in auth_client.get(lens, {'mode': 'category'}).content.decode()
    assert '/move/' not in auth_client.get(lens, {'mode': 'all'}).content.decode()


# --- access control ---

def test_view_only_cannot_move(client, other_user, trip):
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    bag = Bag.objects.create(trip=trip, name='Blue duffel')
    item = PackingItem.objects.create(trip=trip, name='Socks')
    client.force_login(other_user)
    assert client.post(move_url(trip, item), {'bag': bag.pk}).status_code == 404
