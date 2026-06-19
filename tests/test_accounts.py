import pytest
from django.urls import reverse

from accounts.models import User

pytestmark = pytest.mark.django_db


def test_register_creates_user_and_seeds_defaults(client):
    resp = client.post(reverse('register'), {
        'email': 'new@example.com',
        'display_name': 'New Person',
        'password1': 'pw-test-12345',
        'password2': 'pw-test-12345',
    })
    assert resp.status_code == 302
    user = User.objects.get(email='new@example.com')
    # signup seeds 6 categories and 4 conditions, with exactly one default
    assert user.categories.count() == 6
    assert user.conditions.count() == 4
    assert user.conditions.filter(is_default=True).count() == 1


def test_register_rejects_duplicate_email(client, user):
    resp = client.post(reverse('register'), {
        'email': user.email,
        'display_name': 'Dup',
        'password1': 'pw-test-12345',
        'password2': 'pw-test-12345',
    })
    assert resp.status_code == 200  # re-rendered with error
    assert User.objects.filter(email=user.email).count() == 1


def test_protected_page_redirects_anonymous(client):
    resp = client.get(reverse('dashboard'))
    assert resp.status_code == 302
    assert reverse('login') in resp.url


def test_profile_update(auth_client, user):
    resp = auth_client.post(reverse('profile'), {'display_name': 'Renamed'})
    assert resp.status_code == 302
    user.refresh_from_db()
    assert user.display_name == 'Renamed'
