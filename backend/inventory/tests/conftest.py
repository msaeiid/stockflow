import pytest
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from rest_framework.test import APIClient

from inventory.models import StockMovement

from .factories import ProductFactory, WarehouseFactory


@pytest.fixture(autouse=True)
def _plain_static_storage(settings):
    # The manifest storage needs collectstatic; tests do not run it.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture(autouse=True)
def _clear_cache():
    # Dashboard stats and DRF throttle counters live in the cache.
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def manager(db):
    user = User.objects.create_user(username="mgr", password="pass12345")
    user.groups.add(Group.objects.get_or_create(name="Manager")[0])
    return user


@pytest.fixture
def staff(db):
    user = User.objects.create_user(username="staff", password="pass12345")
    user.groups.add(Group.objects.get_or_create(name="Staff")[0])
    return user


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


@pytest.fixture
def anon_client():
    return _client()


@pytest.fixture
def manager_client(manager):
    return _client(manager)


@pytest.fixture
def staff_client(staff):
    return _client(staff)


@pytest.fixture
def stocked(db):
    """One warehouse with two products: 10 and 5 units in stock."""
    warehouse = WarehouseFactory()
    p1 = ProductFactory(sale_price=10, cost_price=4, reorder_threshold=3)
    p2 = ProductFactory(sale_price=25, cost_price=12, reorder_threshold=3)
    for product, qty in ((p1, 10), (p2, 5)):
        StockMovement.objects.create(
            product=product,
            warehouse=warehouse,
            movement_type=StockMovement.MovementType.IN,
            quantity=qty,
        )
    return warehouse, p1, p2
