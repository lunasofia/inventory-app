import pytest

from accounts.models import User
from catalog.models import seed_user_defaults
from trips.models import Trip


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        email='owner@example.com', password='pw-test-12345', display_name='Owner'
    )
    seed_user_defaults(u)
    return u


@pytest.fixture
def other_user(db):
    u = User.objects.create_user(email='other@example.com', password='pw-test-12345')
    seed_user_defaults(u)
    return u


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def trip(user):
    return Trip.objects.create(owner=user, name='Test Trip', status=Trip.Status.PLANNING)


def category_id(user, name):
    return user.categories.get(name=name).pk
