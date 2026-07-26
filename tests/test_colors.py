import pytest
from django.urls import reverse

from catalog.models import Category, SWATCH_SLUGS, DEFAULT_CATEGORY_COLORS, random_swatch
from trips.models import Bag, PackingItem, Template, TemplateShare, TripShare

pytestmark = pytest.mark.django_db


# --- model defaults ---

def test_category_color_defaults_to_valid_swatch(user):
    cat = Category.objects.create(owner=user, name='New stuff')
    assert cat.color in SWATCH_SLUGS


def test_bag_color_defaults_to_valid_swatch(trip):
    bag = Bag.objects.create(trip=trip, name='Blue roller')
    assert bag.color in SWATCH_SLUGS


def test_random_swatch_returns_valid_swatch():
    for _ in range(20):
        assert random_swatch() in SWATCH_SLUGS


def test_seeded_defaults_use_mapped_colors(user):
    for name, expected_color in DEFAULT_CATEGORY_COLORS.items():
        cat = user.categories.get(name=name)
        assert cat.color == expected_color, f"{name} should be {expected_color}, got {cat.color}"


# --- category set_color endpoint ---

def test_category_set_color_get_renders_picker(auth_client, user):
    cat = user.categories.get(name='Clothing')
    resp = auth_client.get(reverse('category_set_color', args=[cat.pk]))
    assert resp.status_code == 200
    # Smoke-check: ASCII hx-post attribute is present
    assert b'hx-post="' in resp.content


def test_category_set_color_post_saves_color(auth_client, user):
    cat = user.categories.get(name='Clothing')
    resp = auth_client.post(reverse('category_set_color', args=[cat.pk]), {'color': 'sky'})
    assert resp.status_code == 200
    cat.refresh_from_db()
    assert cat.color == 'sky'


def test_category_set_color_rejects_bogus_color(auth_client, user):
    cat = user.categories.get(name='Clothing')
    original_color = cat.color
    resp = auth_client.post(reverse('category_set_color', args=[cat.pk]), {'color': 'bogus-color'})
    assert resp.status_code == 200
    cat.refresh_from_db()
    assert cat.color == original_color  # unchanged


def test_category_set_color_wrong_owner_404(client, other_user, user):
    cat = user.categories.get(name='Clothing')
    client.force_login(other_user)
    resp = client.get(reverse('category_set_color', args=[cat.pk]))
    assert resp.status_code == 404


# --- bag set_color endpoint ---

def test_bag_set_color_get_renders_picker(auth_client, trip):
    bag = Bag.objects.create(trip=trip, name='Roller')
    resp = auth_client.get(reverse('bag_set_color', args=[trip.pk, bag.pk]))
    assert resp.status_code == 200
    assert b'hx-post="' in resp.content


def test_bag_set_color_post_saves_color(auth_client, trip):
    bag = Bag.objects.create(trip=trip, name='Roller')
    resp = auth_client.post(reverse('bag_set_color', args=[trip.pk, bag.pk]), {'color': 'teal'})
    assert resp.status_code == 200
    bag.refresh_from_db()
    assert bag.color == 'teal'


def test_bag_set_color_rejects_bogus_color(auth_client, trip):
    bag = Bag.objects.create(trip=trip, name='Roller')
    original_color = bag.color
    resp = auth_client.post(reverse('bag_set_color', args=[trip.pk, bag.pk]), {'color': 'x'})
    assert resp.status_code == 200
    bag.refresh_from_db()
    assert bag.color == original_color


def test_bag_set_color_view_only_gets_404(client, other_user, trip):
    bag = Bag.objects.create(trip=trip, name='Roller')
    TripShare.objects.create(trip=trip, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.get(reverse('bag_set_color', args=[trip.pk, bag.pk]))
    assert resp.status_code == 404


# --- item chip renders swatch class ---

def test_item_chip_renders_swatch_class(auth_client, user, trip):
    cat = user.categories.get(name='Clothing')
    cat.color = 'sage'
    cat.save(update_fields=['color'])
    PackingItem.objects.create(trip=trip, name='Shirt', category=cat)
    resp = auth_client.get(reverse('trip_detail', args=[trip.pk]))
    assert resp.status_code == 200
    assert b'swatch-sage' in resp.content
    assert b'cat-clothing' not in resp.content


# --- template-page category add ---

def test_template_page_category_add_creates_category(auth_client, user):
    tpl = Template.objects.create(owner=user, name='Beach')
    resp = auth_client.post(reverse('category_add'), {'name': 'Surf gear', 'template': tpl.pk})
    assert resp.status_code == 200
    assert Category.objects.filter(owner=user, name='Surf gear').exists()


def test_template_page_category_add_rerenders_categories_region(auth_client, user):
    tpl = Template.objects.create(owner=user, name='Beach')
    resp = auth_client.post(reverse('category_add'), {'name': 'Surf gear', 'template': tpl.pk})
    assert resp.status_code == 200
    assert b'id="template-categories"' in resp.content


def test_template_page_view_only_cannot_add_category_via_template_param(client, other_user, user):
    tpl = Template.objects.create(owner=user, name='Beach')
    TemplateShare.objects.create(template=tpl, shared_with=other_user, permission='view')
    client.force_login(other_user)
    resp = client.post(reverse('category_add'), {'name': 'Sneaky', 'template': tpl.pk})
    assert resp.status_code == 404


# --- render-level smoke tests (HTMX attributes, no smart quotes) ---

def test_categories_page_has_ascii_hx_post(auth_client):
    resp = auth_client.get(reverse('category_manage'))
    assert resp.status_code == 200
    assert b'hx-post="' in resp.content
    # Confirm no smart quotes in hx attributes
    content = resp.content.decode('utf-8')
    assert '“' not in content  # left double quote
    assert '”' not in content  # right double quote


def test_category_color_picker_has_ascii_hx_post(auth_client, user):
    cat = user.categories.get(name='Clothing')
    resp = auth_client.get(reverse('category_set_color', args=[cat.pk]))
    assert resp.status_code == 200
    assert b'hx-post="' in resp.content
    content = resp.content.decode('utf-8')
    assert '“' not in content
    assert '”' not in content
