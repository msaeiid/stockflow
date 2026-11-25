import pytest

from inventory.models import Category, Product

from .factories import CategoryFactory, ProductFactory

pytestmark = pytest.mark.django_db


def test_staff_can_read_but_not_write_products(staff_client):
    product = ProductFactory()
    assert staff_client.get("/api/products/").status_code == 200
    assert staff_client.get(f"/api/products/{product.pk}/").status_code == 200
    response = staff_client.patch(f"/api/products/{product.pk}/", {"name": "x"}, format="json")
    assert response.status_code == 403
    assert staff_client.delete(f"/api/products/{product.pk}/").status_code == 403


def test_manager_can_create_and_update_product(manager_client):
    category = CategoryFactory()
    response = manager_client.post(
        "/api/products/",
        {"name": "Desk Lamp", "sku": "LAMP-1", "category": category.pk, "sale_price": "19.90"},
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["category_name"] == category.name
    pk = response.data["id"]
    response = manager_client.patch(f"/api/products/{pk}/", {"sale_price": "21.00"}, format="json")
    assert response.status_code == 200
    assert str(Product.objects.get(pk=pk).sale_price) == "21.00"


def test_negative_prices_are_rejected(manager_client):
    category = CategoryFactory()
    response = manager_client.post(
        "/api/products/",
        {"name": "Bad", "sku": "BAD-1", "category": category.pk, "cost_price": "-1"},
        format="json",
    )
    assert response.status_code == 400
    assert "cost_price" in response.data


def test_duplicate_sku_is_rejected(manager_client):
    product = ProductFactory()
    response = manager_client.post(
        "/api/products/",
        {"name": "Copy", "sku": product.sku, "category": product.category_id},
        format="json",
    )
    assert response.status_code == 400
    assert "sku" in response.data


def test_deleting_a_category_in_use_returns_409(manager_client):
    product = ProductFactory()
    response = manager_client.delete(f"/api/categories/{product.category_id}/")
    assert response.status_code == 409
    assert Category.objects.filter(pk=product.category_id).exists()


def test_deleting_an_unused_category_works(manager_client):
    category = CategoryFactory()
    assert manager_client.delete(f"/api/categories/{category.pk}/").status_code == 204


def test_product_search_and_filter(staff_client):
    ProductFactory(name="Blue Widget", sku="BW-1")
    ProductFactory(name="Red Gadget", sku="RG-1", is_active=False)
    response = staff_client.get("/api/products/", {"search": "widget"})
    assert [p["sku"] for p in response.data["results"]] == ["BW-1"]
    response = staff_client.get("/api/products/", {"is_active": "false"})
    assert [p["sku"] for p in response.data["results"]] == ["RG-1"]


def test_superuser_can_write_without_group(db):
    from django.contrib.auth.models import User
    from rest_framework.test import APIClient

    admin = User.objects.create_superuser("root", "root@example.com", "pass12345")
    client = APIClient()
    client.force_authenticate(admin)
    assert client.post("/api/categories/", {"name": "Spare"}).status_code == 201
