import pytest
from django.urls import reverse

from trips.models import PackingItem, TripShare

pytestmark = pytest.mark.django_db


# Check-off now happens inline on the unified trip board (item_toggle), not a
# separate packing page.

def test_toggle_packs_and_unpacks(auth_client, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    auth_client.post(reverse('item_toggle', args=[trip.pk, item.pk]))
    item.refresh_from_db()
    assert item.packed is True
    auth_client.post(reverse('item_toggle', args=[trip.pk, item.pk]))
    item.refresh_from_db()
    assert item.packed is False


def test_toggle_updates_progress_count(auth_client, trip):
    a = PackingItem.objects.create(trip=trip, name='A')
    PackingItem.objects.create(trip=trip, name='B')
    resp = auth_client.post(reverse('item_toggle', args=[trip.pk, a.pk]))
    assert b'1/2' in resp.content


def test_all_packed_message(auth_client, trip):
    item = PackingItem.objects.create(trip=trip, name='Only')
    resp = auth_client.post(reverse('item_toggle', args=[trip.pk, item.pk]))
    assert b'All packed' in resp.content


def test_view_only_sees_board_readonly(client, other_user, trip):
    PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.get(reverse('trip_detail', args=[trip.pk]))
    assert resp.status_code == 200
    assert b'Socks' in resp.content
    assert b'item-toggle readonly' in resp.content  # no interactive toggle


def test_view_only_cannot_toggle(client, other_user, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(reverse('item_toggle', args=[trip.pk, item.pk]))
    assert resp.status_code == 404
    item.refresh_from_db()
    assert item.packed is False


def test_no_access_toggle_404(client, other_user, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    client.force_login(other_user)  # no share at all
    assert client.post(reverse('item_toggle', args=[trip.pk, item.pk])).status_code == 404
