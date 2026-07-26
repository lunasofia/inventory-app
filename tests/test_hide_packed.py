"""Tests for the Hide packed filter toggle on the trip board."""
import re
import pytest
from django.urls import reverse

from trips.models import Bag, PackingItem
from trips.views import _grouped_items

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Unit tests: _grouped_items with hide_packed kwarg
# ---------------------------------------------------------------------------

def test_hide_packed_excludes_packed_items(trip):
    """hide_packed=True filters out packed items from grouped output."""
    PackingItem.objects.create(trip=trip, name='Socks', packed=False)
    PackingItem.objects.create(trip=trip, name='Hat', packed=True)

    groups = _grouped_items(trip, mode='bag', hide_packed=True)
    all_items = [item for _, _, items in groups for item in items]
    names = [i.name for i in all_items]
    assert 'Socks' in names
    assert 'Hat' not in names


def test_hide_packed_false_restores_all(trip):
    """hide_packed=False (default) returns both packed and unpacked items."""
    PackingItem.objects.create(trip=trip, name='Socks', packed=False)
    PackingItem.objects.create(trip=trip, name='Hat', packed=True)

    groups = _grouped_items(trip, mode='bag', hide_packed=False)
    all_items = [item for _, _, items in groups for item in items]
    names = [i.name for i in all_items]
    assert 'Socks' in names
    assert 'Hat' in names


def test_default_hide_packed_is_false(trip):
    """Calling _grouped_items without hide_packed kwarg returns all items
    (backwards-compatible default)."""
    PackingItem.objects.create(trip=trip, name='Socks', packed=True)
    groups = _grouped_items(trip, mode='bag')
    all_items = [item for _, _, items in groups for item in items]
    assert any(i.name == 'Socks' for i in all_items)


def test_fully_packed_group_disappears(trip):
    """When every item in a bag is packed, the bag group is omitted entirely."""
    bag = Bag.objects.create(trip=trip, name='Main bag')
    PackingItem.objects.create(trip=trip, name='Socks', bag=bag, packed=True)
    PackingItem.objects.create(trip=trip, name='Shirt', bag=bag, packed=True)

    groups = _grouped_items(trip, mode='bag', hide_packed=True)
    headings = [heading for heading, _, _ in groups]
    assert 'Main bag' not in headings


def test_partially_packed_bag_stays(trip):
    """Bag groups that still have unpacked items remain visible."""
    bag = Bag.objects.create(trip=trip, name='Main bag')
    PackingItem.objects.create(trip=trip, name='Socks', bag=bag, packed=True)
    PackingItem.objects.create(trip=trip, name='Shirt', bag=bag, packed=False)

    groups = _grouped_items(trip, mode='bag', hide_packed=True)
    headings = [heading for heading, _, _ in groups]
    assert 'Main bag' in headings


def test_hide_packed_in_all_mode(trip):
    """In all mode with hide_packed=True, the Packed group is suppressed."""
    PackingItem.objects.create(trip=trip, name='Socks', packed=False)
    PackingItem.objects.create(trip=trip, name='Hat', packed=True)

    groups = _grouped_items(trip, mode='all', hide_packed=True)
    headings = [heading for heading, _, _ in groups]
    assert not any('Packed' in h for h in headings)
    all_items = [item for _, _, items in groups for item in items]
    names = [i.name for i in all_items]
    assert 'Hat' not in names


def test_hide_packed_category_mode(trip):
    """hide_packed works in category mode too."""
    from catalog.models import Category
    # seed_user_defaults already creates Clothing; get_or_create avoids unique violation
    cat, _ = Category.objects.get_or_create(owner=trip.owner, name='Clothing')
    PackingItem.objects.create(trip=trip, name='Socks', category=cat, packed=True)
    PackingItem.objects.create(trip=trip, name='Shirt', category=cat, packed=False)

    groups = _grouped_items(trip, mode='category', hide_packed=True)
    all_items = [item for _, _, items in groups for item in items]
    names = [i.name for i in all_items]
    assert 'Socks' not in names
    assert 'Shirt' in names


# ---------------------------------------------------------------------------
# Session / endpoint tests
# ---------------------------------------------------------------------------

def test_set_hide_packed_flips_session_on(auth_client, trip):
    """GET set_hide_packed?on=1 sets hide_packed to True in session."""
    resp = auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '1'})
    assert resp.status_code == 200
    session = auth_client.session
    assert session[f'hide_packed_{trip.pk}'] is True


def test_set_hide_packed_flips_session_off(auth_client, trip):
    """GET set_hide_packed?on=0 sets hide_packed to False in session."""
    auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '1'})
    auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '0'})
    session = auth_client.session
    assert session[f'hide_packed_{trip.pk}'] is False


def test_set_hide_packed_rerenders_planning(auth_client, trip):
    """set_hide_packed returns the #planning fragment."""
    resp = auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '1'})
    assert resp.status_code == 200
    assert b'id="planning"' in resp.content


def test_trip_detail_resets_hide_packed(auth_client, trip):
    """Full page load of trip_detail resets the hide_packed session key to False."""
    session = auth_client.session
    session[f'hide_packed_{trip.pk}'] = True
    session.save()

    auth_client.get(reverse('trip_detail', args=[trip.pk]))

    session = auth_client.session
    assert session[f'hide_packed_{trip.pk}'] is False


def test_hide_packed_filter_hides_items_in_response(auth_client, trip):
    """When filter is on, packed item name does not appear in rendered planning."""
    PackingItem.objects.create(trip=trip, name='Toothbrush', packed=True)
    PackingItem.objects.create(trip=trip, name='Passport', packed=False)

    resp = auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '1'})
    assert b'Passport' in resp.content
    assert b'Toothbrush' not in resp.content


def test_hide_packed_off_shows_all_items_in_response(auth_client, trip):
    """When filter is off, both packed and unpacked items appear."""
    PackingItem.objects.create(trip=trip, name='Toothbrush', packed=True)
    PackingItem.objects.create(trip=trip, name='Passport', packed=False)

    resp = auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '0'})
    assert b'Passport' in resp.content
    assert b'Toothbrush' in resp.content


def test_check_off_still_works_with_filter_on(auth_client, trip):
    """item_toggle still works when hide_packed is active in session."""
    item = PackingItem.objects.create(trip=trip, name='Sunscreen', packed=False)

    # Enable the filter
    auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '1'})

    # Toggle the item packed -- it should disappear from the response
    resp = auth_client.post(reverse('item_toggle', args=[trip.pk, item.pk]))
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.packed is True
    # The item is now packed and filter is on -- it should not be in the response
    assert b'Sunscreen' not in resp.content


# ---------------------------------------------------------------------------
# Render / smoke test: HTMX attributes and ASCII quotes
# ---------------------------------------------------------------------------

def test_hide_packed_toggle_renders_htmx_attributes(auth_client, trip):
    """The hide-packed button in the rendered #planning has valid HTMX attrs
    with ASCII quotes (no smart/curly quotes used as attribute delimiters)."""
    resp = auth_client.get(reverse('trip_detail', args=[trip.pk]))
    assert resp.status_code == 200
    content = resp.content.decode('utf-8')

    # hx-target must point to #planning with ASCII quotes
    assert 'hx-target="#planning"' in content

    # The hide-packed toggle must exist in the output (styled as a view-toggle
    # segment to match the grouping lens); assert on stable label + endpoint.
    assert 'Hide packed' in content
    assert reverse('set_hide_packed', args=[trip.pk]) in content

    # No smart/curly quotes used as attribute value delimiters (=<smart-quote>)
    # Prose text like the empty-state message is acceptable; attribute values must use ASCII
    for char in ('“', '”', '‘', '’'):
        assert ('=' + char) not in content, (
            f'Found smart-quote attribute delimiter =U+{ord(char):04X} in rendered HTML'
        )


def test_hide_packed_endpoint_renders_htmx_attributes(auth_client, trip):
    """The planning fragment returned by set_hide_packed has valid HTMX attrs
    with ASCII quotes (no smart/curly quotes used as attribute delimiters)."""
    resp = auth_client.get(reverse('set_hide_packed', args=[trip.pk]), {'on': '1'})
    assert resp.status_code == 200
    content = resp.content.decode('utf-8')

    assert 'hx-target="#planning"' in content

    for char in ('“', '”', '‘', '’'):
        assert ('=' + char) not in content, (
            f'Found smart-quote attribute delimiter =U+{ord(char):04X} in rendered HTML'
        )
