from decimal import Decimal

import pytest

from inventory.models import Order, Stock

pytestmark = pytest.mark.django_db


def _order(warehouse, *lines, customer="Test Customer"):
    return {
        "warehouse": warehouse.pk,
        "customer_name": customer,
        "items": [{"product": p.pk, "quantity": q} for p, q in lines],
    }


def test_staff_can_place_an_order(staff_client, stocked):
    warehouse, p1, p2 = stocked
    response = staff_client.post("/api/orders/", _order(warehouse, (p1, 3), (p2, 2)), format="json")
    assert response.status_code == 201, response.data
    assert response.data["status"] == "CONFIRMED"
    assert response.data["reference"].startswith("ORD-")
    assert Decimal(response.data["total"]) == Decimal("80.00")
    assert {i["product_name"] for i in response.data["items"]} == {p1.name, p2.name}
    assert Stock.objects.get(product=p1).quantity == 7
    assert Stock.objects.get(product=p2).quantity == 3


def test_order_is_rejected_atomically_when_one_line_is_short(staff_client, stocked):
    warehouse, p1, p2 = stocked
    response = staff_client.post("/api/orders/", _order(warehouse, (p1, 3), (p2, 6)), format="json")
    assert response.status_code == 400
    assert Order.objects.count() == 0
    assert Stock.objects.get(product=p1).quantity == 10


def test_inactive_products_cannot_be_ordered(staff_client, stocked):
    warehouse, p1, _ = stocked
    p1.is_active = False
    p1.save()
    response = staff_client.post("/api/orders/", _order(warehouse, (p1, 1)), format="json")
    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_order_needs_items_and_customer(staff_client, stocked):
    warehouse, p1, _ = stocked
    assert staff_client.post("/api/orders/", _order(warehouse), format="json").status_code == 400
    payload = _order(warehouse, (p1, 1), customer="")
    assert staff_client.post("/api/orders/", payload, format="json").status_code == 400


def test_order_price_is_a_snapshot(staff_client, stocked):
    warehouse, p1, _ = stocked
    staff_client.post("/api/orders/", _order(warehouse, (p1, 1)), format="json")
    p1.sale_price = Decimal("99.00")
    p1.save()
    order = staff_client.get("/api/orders/").data["results"][0]
    assert Decimal(order["items"][0]["unit_price"]) == Decimal("10.00")


def test_orders_cannot_be_changed_or_deleted(manager_client, stocked):
    warehouse, p1, _ = stocked
    pk = manager_client.post("/api/orders/", _order(warehouse, (p1, 1)), format="json").data["id"]
    assert (
        manager_client.patch(f"/api/orders/{pk}/", {"note": "x"}, format="json").status_code == 405
    )
    assert manager_client.delete(f"/api/orders/{pk}/").status_code == 405


def test_anonymous_cannot_order(anon_client, stocked):
    warehouse, p1, _ = stocked
    assert (
        anon_client.post("/api/orders/", _order(warehouse, (p1, 1)), format="json").status_code
        == 401
    )
