import pytest
from django.urls import reverse

from trips.models import Bag, PackingItem, TripShare

pytestmark = pytest.mark.django_db


def test_packing_mode_loads(auth_client, trip):
    PackingItem.objects.create(trip=trip, name='Socks')
    resp = auth_client.get(reverse('packing_mode', args=[trip.pk]))
    assert resp.status_code == 200
    assert b'Socks' in resp.content


def test_toggle_packs_and_unpacks(auth_client, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    auth_client.post(reverse('pack_toggle', args=[trip.pk, item.pk]))
    item.refresh_from_db()
    assert item.packed is True
    auth_client.post(reverse('pack_toggle', args=[trip.pk, item.pk]))
    item.refresh_from_db()
    assert item.packed is False


def test_toggle_updates_progress_count(auth_client, trip):
    a = PackingItem.objects.create(trip=trip, name='A')
    PackingItem.objects.create(trip=trip, name='B')
    resp = auth_client.post(reverse('pack_toggle', args=[trip.pk, a.pk]))
    assert b'1/2 packed' in resp.content


def test_all_packed_message(auth_client, trip):
    item = PackingItem.objects.create(trip=trip, name='Only')
    resp = auth_client.post(reverse('pack_toggle', args=[trip.pk, item.pk]))
    assert b'All packed' in resp.content


def test_pack_bag_mark_packs_all(auth_client, trip):
    bag = Bag.objects.create(trip=trip, name='Duffel')
    PackingItem.objects.create(trip=trip, name='A', bag=bag)
    PackingItem.objects.create(trip=trip, name='B', bag=bag)
    auth_client.post(reverse('pack_bag_mark', args=[trip.pk, bag.pk]), {'packed': 'true'})
    assert bag.items.filter(packed=True).count() == 2


def test_pack_group_switches_lens(auth_client, trip):
    resp = auth_client.get(reverse('pack_group', args=[trip.pk]), {'mode': 'bag'})
    assert resp.status_code == 200
    assert auth_client.session[f'group_mode_{trip.pk}'] == 'bag'


# --- access control ---

def test_view_only_sees_packing_mode_readonly(client, other_user, trip):
    PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.get(reverse('packing_mode', args=[trip.pk]))
    assert resp.status_code == 200
    assert b'Socks' in resp.content
    # no toggle button rendered for a view-only user
    assert b'pack-check readonly' in resp.content
    assert reverse('pack_toggle', args=[trip.pk, 0])[:-2] not in resp.content.decode()


def test_view_only_cannot_toggle(client, other_user, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(reverse('pack_toggle', args=[trip.pk, item.pk]))
    assert resp.status_code == 404
    item.refresh_from_db()
    assert item.packed is False


def test_no_access_toggle_404(client, other_user, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    client.force_login(other_user)  # no share at all
    assert client.post(reverse('pack_toggle', args=[trip.pk, item.pk])).status_code == 404
