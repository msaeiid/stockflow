import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from inventory.models import Category, Order, Product, Stock, StockMovement

pytestmark = pytest.mark.django_db

DEMO = {"DEMO_MODE": True, "DEMO_USERNAME": "demo", "DEMO_PASSWORD": "demo-pass-1234"}


@pytest.fixture
def demo_settings(settings):
    for key, value in DEMO.items():
        setattr(settings, key, value)
    return settings


def _snapshot():
    return {
        "products": Product.objects.count(),
        "movements": StockMovement.objects.count(),
        "orders": Order.objects.count(),
        "stock": sorted(Stock.objects.values_list("product__sku", "warehouse__name", "quantity")),
    }


def test_demo_commands_refuse_without_demo_mode(settings):
    settings.DEMO_MODE = False
    with pytest.raises(CommandError, match="DEMO_MODE"):
        call_command("demo_seed")
    with pytest.raises(CommandError, match="DEMO_MODE"):
        call_command("demo_reset", interactive=False)


def test_demo_seed_needs_a_password(demo_settings):
    demo_settings.DEMO_PASSWORD = ""
    with pytest.raises(CommandError, match="DEMO_PASSWORD"):
        call_command("demo_seed")


def test_demo_seed_is_idempotent(demo_settings):
    call_command("demo_seed")
    first = _snapshot()
    assert first["products"] == 16
    assert first["orders"] == 8
    call_command("demo_seed")
    assert _snapshot() == first


def test_demo_data_is_fictional(demo_settings):
    call_command("demo_seed")
    from inventory.models import Supplier

    for supplier in Supplier.objects.all():
        assert supplier.email.endswith(".example.com")
        assert supplier.phone.startswith("555-01")


def test_demo_user_can_log_in_as_manager_without_admin(demo_settings):
    call_command("demo_seed")
    user = User.objects.get(username="demo")
    assert user.groups.filter(name="Manager").exists()
    assert not user.is_staff and not user.is_superuser
    response = APIClient().post(
        "/api/auth/login/", {"username": "demo", "password": "demo-pass-1234"}, format="json"
    )
    assert response.status_code == 200


def test_demo_reset_restores_the_data_set(demo_settings):
    call_command("demo_seed")
    baseline = _snapshot()
    # A visitor changes things...
    Category.objects.create(name="Visitor category")
    product = Product.objects.get(sku="DEMO-1001")
    product.name = "Renamed by a visitor"
    product.save()
    StockMovement.objects.create(
        product=product,
        warehouse=Stock.objects.filter(product=product).first().warehouse,
        movement_type="IN",
        quantity=500,
    )
    User.objects.create_user("visitor-made", password="x-pass-123")
    admin = User.objects.create_superuser("operator", "op@example.com", "x-pass-123")
    demo_user = User.objects.get(username="demo")
    demo_user.set_password("changed-by-visitor")
    demo_user.save()

    call_command("demo_reset", interactive=False)

    assert _snapshot() == baseline
    assert Product.objects.get(sku="DEMO-1001").name == "Wireless Mouse"
    assert not Category.objects.filter(name="Visitor category").exists()
    assert not User.objects.filter(username="visitor-made").exists()
    assert User.objects.filter(pk=admin.pk).exists()
    assert User.objects.get(username="demo").check_password("demo-pass-1234")


def test_demo_info_endpoint(demo_settings, anon_client):
    demo_settings.DEMO_SHOW_CREDENTIALS = False
    data = anon_client.get("/api/demo/").data
    assert data == {"demo_mode": True, "username": None, "password": None}
    demo_settings.DEMO_SHOW_CREDENTIALS = True
    data = anon_client.get("/api/demo/").data
    assert data == {"demo_mode": True, "username": "demo", "password": "demo-pass-1234"}


def test_demo_info_never_shows_credentials_outside_demo_mode(settings, anon_client):
    settings.DEMO_MODE = False
    settings.DEMO_SHOW_CREDENTIALS = True
    settings.DEMO_PASSWORD = "should-not-leak"
    assert anon_client.get("/api/demo/").data["password"] is None


def test_seed_data_works_without_demo_mode(settings):
    settings.DEMO_MODE = False
    settings.DEMO_PASSWORD = ""
    call_command("seed_data")
    call_command("seed_data")
    assert Product.objects.count() == 16
    assert Order.objects.count() == 8
    assert not User.objects.filter(username="demo").exists()
