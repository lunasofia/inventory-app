import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User
from catalog.models import seed_user_defaults
from trips.models import PackingItem, Trip, TripShare

pytestmark = pytest.mark.django_db


def make_user(email):
    u = User.objects.create_user(email=email, password='pw-test-12345')
    seed_user_defaults(u)
    return u


# --- add ---

def test_owner_shares_by_email(auth_client, user, trip, other_user):
    resp = auth_client.post(reverse('share_add', args=[trip.pk]),
                            {'email': other_user.email, 'permission': 'edit'})
    assert resp.status_code == 200
    share = TripShare.objects.get(trip=trip, shared_with=other_user)
    assert share.permission == 'edit'


def test_share_unknown_email_rejected(auth_client, trip):
    resp = auth_client.post(reverse('share_add', args=[trip.pk]),
                            {'email': 'nobody@nowhere.com', 'permission': 'edit'})
    assert b'No Packwell account' in resp.content
    assert trip.shares.count() == 0


def test_cannot_share_with_self(auth_client, user, trip):
    resp = auth_client.post(reverse('share_add', args=[trip.pk]),
                            {'email': user.email, 'permission': 'edit'})
    assert b'already own this trip' in resp.content
    assert trip.shares.count() == 0


def test_re_adding_updates_permission(auth_client, trip, other_user):
    auth_client.post(reverse('share_add', args=[trip.pk]),
                     {'email': other_user.email, 'permission': 'view'})
    auth_client.post(reverse('share_add', args=[trip.pk]),
                     {'email': other_user.email, 'permission': 'edit'})
    assert trip.shares.count() == 1
    assert trip.shares.get(shared_with=other_user).permission == 'edit'


# --- update / revoke ---

def test_update_permission(auth_client, trip, other_user):
    share = TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    auth_client.post(reverse('share_update', args=[trip.pk, share.pk]), {'permission': 'edit'})
    share.refresh_from_db()
    assert share.permission == 'edit'


def test_revoke_cuts_access(auth_client, trip, other_user):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    share = TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    collab = Client()  # separate client so the owner's session stays intact
    collab.force_login(other_user)
    assert collab.get(reverse('trip_detail', args=[trip.pk])).status_code == 200
    # owner revokes
    auth_client.post(reverse('share_revoke', args=[trip.pk, share.pk]))
    assert not TripShare.objects.filter(pk=share.pk).exists()
    # access is gone immediately
    assert collab.get(reverse('trip_detail', args=[trip.pk])).status_code == 404
    assert collab.post(reverse('item_toggle', args=[trip.pk, item.pk])).status_code == 404


# --- recipient experience ---

def test_edit_collaborator_can_toggle(client, trip, other_user):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    client.force_login(other_user)
    assert client.post(reverse('item_toggle', args=[trip.pk, item.pk])).status_code == 200
    item.refresh_from_db()
    assert item.packed is True


def test_view_collaborator_cannot_toggle(client, trip, other_user):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    assert client.post(reverse('item_toggle', args=[trip.pk, item.pk])).status_code == 404


# --- owner-only management ---

def test_non_owner_cannot_manage_sharing(client, trip, other_user):
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    client.force_login(other_user)  # an edit collaborator
    assert client.post(reverse('share_add', args=[trip.pk]),
                       {'email': 'x@y.com', 'permission': 'edit'}).status_code == 404


# --- recent collaborators ---

def test_recent_collaborators_suggested_and_scoped(auth_client, user, trip, other_user):
    # user has shared a (different) trip with other_user before
    past = Trip.objects.create(owner=user, name='Past trip')
    TripShare.objects.create(trip=past, shared_with=other_user, permission='edit')
    stranger = make_user('stranger@example.com')
    resp = auth_client.get(reverse('collaborator_suggest', args=[trip.pk]), {'email': ''})
    assert other_user.email.encode() in resp.content       # prior collaborator suggested
    assert stranger.email.encode() not in resp.content      # never collaborated → not suggested


def test_suggest_excludes_existing_collaborators(auth_client, user, trip, other_user):
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='edit')
    resp = auth_client.get(reverse('collaborator_suggest', args=[trip.pk]))
    assert other_user.email.encode() not in resp.content  # already on this trip
