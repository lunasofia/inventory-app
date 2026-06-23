import pytest
from django.urls import reverse

from trips.models import (
    DEFAULT_REMINDERS, PackingItem, Reminder, Template, TemplateReminder,
    Trip, TripReminder, TripShare,
)

pytestmark = pytest.mark.django_db


# --- seeding ---

def test_exit_page_seeds_reminders_from_defaults(auth_client, user, trip):
    assert trip.reminders.count() == 0
    resp = auth_client.get(reverse('exit_page', args=[trip.pk]))
    assert resp.status_code == 200
    trip.refresh_from_db()
    assert trip.reminders_seeded is True
    assert trip.reminders.count() == len(DEFAULT_REMINDERS)


def test_exit_page_seeds_from_template(auth_client, user):
    tpl = Template.objects.create(owner=user, name='Beach')
    TemplateReminder.objects.create(template=tpl, text='Check the safe')
    trip = Trip.objects.create(owner=user, name='T', origin_template=tpl)
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    assert [r.text for r in trip.reminders.all()] == ['Check the safe']


def test_reopen_does_not_reseed(auth_client, trip):
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    n = trip.reminders.count()
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    assert trip.reminders.count() == n


# --- unpacked list ---

def test_exit_lists_only_unpacked(auth_client, trip):
    PackingItem.objects.create(trip=trip, name='Socks', packed=False)
    PackingItem.objects.create(trip=trip, name='Hat', packed=True)
    resp = auth_client.get(reverse('exit_page', args=[trip.pk]))
    names = [i.name for i in resp.context['unpacked']]
    assert names == ['Socks']


def test_exit_toggle_packs_item(auth_client, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    resp = auth_client.post(reverse('exit_item_toggle', args=[trip.pk, item.pk]))
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.packed is True
    assert b'Everything' in resp.content  # all-packed state (was the only item)


# --- trip reminders ---

def test_tick_reminder_persists(auth_client, trip):
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    r = trip.reminders.first()
    auth_client.post(reverse('trip_reminder_toggle', args=[trip.pk, r.pk]))
    r.refresh_from_db()
    assert r.checked is True
    auth_client.post(reverse('trip_reminder_toggle', args=[trip.pk, r.pk]))
    r.refresh_from_db()
    assert r.checked is False


def test_add_and_remove_trip_reminder(auth_client, trip):
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    auth_client.post(reverse('trip_reminder_add', args=[trip.pk]), {'text': 'Grab the dress'})
    r = trip.reminders.get(text='Grab the dress')
    auth_client.post(reverse('trip_reminder_delete', args=[trip.pk, r.pk]))
    assert not trip.reminders.filter(text='Grab the dress').exists()


def test_reset_reseeds(auth_client, trip):
    auth_client.get(reverse('exit_page', args=[trip.pk]))
    trip.reminders.all().delete()
    auth_client.post(reverse('reminders_reset', args=[trip.pk]))
    assert trip.reminders.count() == len(DEFAULT_REMINDERS)


# --- default reminders (settings) ---

def test_reminder_manage_add_delete(auth_client, user):
    before = Reminder.objects.filter(owner=user).count()
    auth_client.post(reverse('reminder_add'), {'text': 'Lock the door'})
    assert Reminder.objects.filter(owner=user, text='Lock the door').exists()
    r = Reminder.objects.get(owner=user, text='Lock the door')
    auth_client.post(reverse('reminder_delete', args=[r.pk]))
    assert Reminder.objects.filter(owner=user).count() == before


# --- template reminders ---

def test_template_reminder_add_delete(auth_client, user):
    tpl = Template.objects.create(owner=user, name='Tpl')
    auth_client.post(reverse('template_reminder_add', args=[tpl.pk]), {'text': 'Check the safe'})
    r = tpl.reminders.get(text='Check the safe')
    auth_client.post(reverse('template_reminder_delete', args=[tpl.pk, r.pk]))
    assert not tpl.reminders.exists()


# --- access control ---

def test_view_only_can_see_but_not_mutate(client, other_user, trip):
    item = PackingItem.objects.create(trip=trip, name='Socks')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    assert client.get(reverse('exit_page', args=[trip.pk])).status_code == 200
    assert client.post(reverse('exit_item_toggle', args=[trip.pk, item.pk])).status_code == 404
    assert client.post(reverse('trip_reminder_add', args=[trip.pk]), {'text': 'x'}).status_code == 404
