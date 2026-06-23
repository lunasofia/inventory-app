import pytest
from django.urls import reverse

from trips.models import Trip

pytestmark = pytest.mark.django_db


def test_create_trip(auth_client, user):
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Iceland', 'destination': 'Reykjavik', 'status': 'planning',
    })
    assert resp.status_code == 302
    trip = Trip.objects.get(name='Iceland')
    assert trip.owner == user


def test_create_trip_end_before_start_invalid(auth_client):
    resp = auth_client.post(reverse('trip_create'), {
        'name': 'Bad', 'status': 'planning',
        'start_date': '2026-07-10', 'end_date': '2026-07-01',
    })
    assert resp.status_code == 200  # re-rendered with error
    assert b'End date cannot be before the start date.' in resp.content
    assert not Trip.objects.filter(name='Bad').exists()


def test_edit_trip(auth_client, trip):
    resp = auth_client.post(reverse('trip_edit', args=[trip.pk]), {
        'name': 'Renamed', 'status': 'packing',
    })
    assert resp.status_code == 302
    trip.refresh_from_db()
    assert trip.name == 'Renamed'
    assert trip.status == 'packing'


def test_non_owner_cannot_view_trip(client, other_user, trip):
    client.force_login(other_user)
    assert client.get(reverse('trip_detail', args=[trip.pk])).status_code == 404


def test_only_owner_can_delete(client, other_user, trip):
    client.force_login(other_user)
    assert client.post(reverse('trip_delete', args=[trip.pk])).status_code == 404
    assert Trip.objects.filter(pk=trip.pk).exists()


def test_owner_can_delete(auth_client, trip):
    resp = auth_client.post(reverse('trip_delete', args=[trip.pk]))
    assert resp.status_code == 302
    assert not Trip.objects.filter(pk=trip.pk).exists()


def test_dashboard_redirects_to_a_trip_when_present(auth_client, user):
    active = Trip.objects.create(owner=user, name='Active one', status='planning')
    Trip.objects.create(owner=user, name='Done one', status='complete')
    resp = auth_client.get(reverse('dashboard'))
    # Home jumps to the most relevant (non-complete) trip; list lives in sidebar.
    assert resp.status_code == 302
    assert resp.url == reverse('trip_detail', args=[active.pk])


def test_dashboard_welcome_when_no_trips(auth_client):
    resp = auth_client.get(reverse('dashboard'))
    assert resp.status_code == 200
    assert b'Welcome to Packwell' in resp.content
