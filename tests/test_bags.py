import pytest
from django.urls import reverse

from trips.models import Bag, PackingItem
from trips.views import _grouped_items

pytestmark = pytest.mark.django_db


def make_bag(trip, name):
    return Bag.objects.create(trip=trip, name=name)


# --- create / manage ---

def test_create_bag(auth_client, trip):
    resp = auth_client.post(reverse('bag_create', args=[trip.pk]), {'name': 'Blue duffel'})
    assert resp.status_code == 200
    assert trip.bags.filter(name='Blue duffel').exists()


def test_duplicate_bag_name_rejected_case_insensitive(auth_client, trip):
    make_bag(trip, 'Blue duffel')
    resp = auth_client.post(reverse('bag_create', args=[trip.pk]), {'name': 'blue duffel'})
    assert resp.status_code == 200
    assert b'already have a bag with that name' in resp.content
    assert trip.bags.count() == 1


def test_empty_bag_name_rejected(auth_client, trip):
    resp = auth_client.post(reverse('bag_create', args=[trip.pk]), {'name': '   '})
    assert trip.bags.count() == 0
    assert b'required' in resp.content  # Django's "This field is required." fires first


def test_rename_bag_keeps_items(auth_client, trip):
    bag = make_bag(trip, 'Blue duffel')
    item = PackingItem.objects.create(trip=trip, name='Socks', bag=bag)
    resp = auth_client.post(reverse('bag_edit', args=[trip.pk, bag.pk]), {'name': 'Black roller'})
    assert resp.status_code == 200
    bag.refresh_from_db()
    item.refresh_from_db()
    assert bag.name == 'Black roller'
    assert item.bag_id == bag.pk  # contents untouched


def test_delete_bag_unbags_items(auth_client, trip):
    bag = make_bag(trip, 'Blue duffel')
    item = PackingItem.objects.create(trip=trip, name='Socks', bag=bag)
    auth_client.post(reverse('bag_delete', args=[trip.pk, bag.pk]))
    item.refresh_from_db()
    assert not Bag.objects.filter(pk=bag.pk).exists()
    assert item.bag is None  # item survives, now Unbagged


# --- assignment ---

def test_add_item_assigned_to_bag(auth_client, trip):
    bag = make_bag(trip, 'Blue duffel')
    auth_client.post(reverse('item_add', args=[trip.pk]),
                     {'name': 'Socks', 'quantity': 1, 'category': '', 'bag': bag.pk})
    assert trip.items.get(name='Socks').bag_id == bag.pk


def test_move_item_between_bags(auth_client, trip):
    a = make_bag(trip, 'Bag A')
    b = make_bag(trip, 'Bag B')
    item = PackingItem.objects.create(trip=trip, name='Socks', bag=a)
    auth_client.post(reverse('item_edit', args=[trip.pk, item.pk]),
                     {'name': 'Socks', 'quantity': 1, 'category': '', 'bag': b.pk})
    item.refresh_from_db()
    assert item.bag_id == b.pk


# --- grouping ---

def test_grouping_by_bag_alphabetical_unbagged_last(user, trip):
    blue = make_bag(trip, 'Blue duffel')
    apack = make_bag(trip, 'Aux pack')
    PackingItem.objects.create(trip=trip, name='Socks', bag=blue)
    PackingItem.objects.create(trip=trip, name='Charger', bag=apack)
    PackingItem.objects.create(trip=trip, name='Loose thing')  # no bag
    headings = [h for h, _bag, _items in _grouped_items(trip, 'bag')]
    assert headings == ['Aux pack', 'Blue duffel', 'Unbagged']


def test_empty_bag_has_no_heading(user, trip):
    make_bag(trip, 'Empty bag')
    PackingItem.objects.create(trip=trip, name='Socks')  # unbagged only
    headings = [h for h, _b, _i in _grouped_items(trip, 'bag')]
    assert 'Empty bag' not in headings


# --- bag-level status ---

def test_mark_bag_packed_packs_all_items(auth_client, trip):
    bag = make_bag(trip, 'Blue duffel')
    PackingItem.objects.create(trip=trip, name='Socks', bag=bag)
    PackingItem.objects.create(trip=trip, name='Shirt', bag=bag, packed=True)
    auth_client.post(reverse('bag_mark', args=[trip.pk, bag.pk]), {'packed': 'true'})
    assert bag.items.filter(packed=True).count() == 2
    assert bag.is_packed is True


def test_mark_bag_unpacked_clears_all_items(auth_client, trip):
    bag = make_bag(trip, 'Blue duffel')
    PackingItem.objects.create(trip=trip, name='Socks', bag=bag, packed=True)
    PackingItem.objects.create(trip=trip, name='Shirt', bag=bag, packed=True)
    auth_client.post(reverse('bag_mark', args=[trip.pk, bag.pk]), {'packed': 'false'})
    assert bag.items.filter(packed=True).count() == 0
    assert bag.is_packed is False


def test_is_packed_false_for_empty_bag(trip):
    bag = make_bag(trip, 'Empty')
    assert bag.is_packed is False


# --- grouping lens toggle ---

def test_set_group_switches_lens(auth_client, trip):
    resp = auth_client.get(reverse('set_group', args=[trip.pk]), {'mode': 'bag'})
    assert resp.status_code == 200
    assert auth_client.session[f'group_mode_{trip.pk}'] == 'bag'


# --- access control ---

def test_view_only_cannot_create_bag(client, other_user, trip):
    from trips.models import TripShare
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(reverse('bag_create', args=[trip.pk]), {'name': 'Sneaky'})
    assert resp.status_code == 404
    assert not trip.bags.exists()


def test_view_only_cannot_mark_bag(client, other_user, trip):
    from trips.models import TripShare
    bag = make_bag(trip, 'Blue duffel')
    PackingItem.objects.create(trip=trip, name='Socks', bag=bag)
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(reverse('bag_mark', args=[trip.pk, bag.pk]), {'packed': 'true'})
    assert resp.status_code == 404
    assert bag.items.filter(packed=True).count() == 0


def test_edit_share_can_create_bag(client, other_user, trip):
    from trips.models import TripShare
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    client.force_login(other_user)
    resp = client.post(reverse('bag_create', args=[trip.pk]), {'name': 'Allowed'})
    assert resp.status_code == 200
    assert trip.bags.filter(name='Allowed').exists()
