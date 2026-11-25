import pytest
from django.core.exceptions import ValidationError

from inventory.models import Stock, StockMovement

pytestmark = pytest.mark.django_db


def test_record_in_and_out_movements(staff_client, stocked):
    warehouse, p1, _ = stocked
    payload = {"product": p1.pk, "warehouse": warehouse.pk, "movement_type": "IN", "quantity": 7}
    assert staff_client.post("/api/movements/", payload, format="json").status_code == 201
    payload.update(movement_type="OUT", quantity=4)
    assert staff_client.post("/api/movements/", payload, format="json").status_code == 201
    assert Stock.objects.get(product=p1, warehouse=warehouse).quantity == 13


def test_out_movement_beyond_stock_is_rejected(staff_client, stocked):
    warehouse, p1, _ = stocked
    payload = {"product": p1.pk, "warehouse": warehouse.pk, "movement_type": "OUT", "quantity": 11}
    response = staff_client.post("/api/movements/", payload, format="json")
    assert response.status_code == 400
    assert "Not enough stock" in str(response.data)
    assert Stock.objects.get(product=p1, warehouse=warehouse).quantity == 10


@pytest.mark.parametrize("quantity", [0, -3, 10_000_000])
def test_movement_quantity_bounds(staff_client, stocked, quantity):
    warehouse, p1, _ = stocked
    payload = {
        "product": p1.pk,
        "warehouse": warehouse.pk,
        "movement_type": "IN",
        "quantity": quantity,
    }
    assert staff_client.post("/api/movements/", payload, format="json").status_code == 400


def test_movements_cannot_be_edited_or_deleted_through_the_api(manager_client, stocked):
    movement = StockMovement.objects.first()
    url = f"/api/movements/{movement.pk}/"
    assert manager_client.put(url, {}, format="json").status_code == 405
    assert manager_client.patch(url, {"quantity": 1}, format="json").status_code == 405
    assert manager_client.delete(url).status_code == 405


def test_saving_an_existing_movement_does_not_double_count(stocked):
    warehouse, p1, _ = stocked
    movement = StockMovement.objects.get(product=p1)
    with pytest.raises(ValidationError):
        movement.save()
    with pytest.raises(ValidationError):
        movement.delete()
    assert Stock.objects.get(product=p1, warehouse=warehouse).quantity == 10


def test_out_check_is_repeated_under_the_lock(stocked):
    """save() must refuse even when clean() was skipped (e.g. a stale check)."""
    warehouse, p1, _ = stocked
    movement = StockMovement(product=p1, warehouse=warehouse, movement_type="OUT", quantity=50)
    with pytest.raises(ValidationError):
        movement.save()
    assert Stock.objects.get(product=p1, warehouse=warehouse).quantity == 10


def test_stock_list_and_filter(staff_client, stocked):
    warehouse, p1, _ = stocked
    response = staff_client.get("/api/stocks/", {"product": p1.pk})
    assert response.status_code == 200
    (row,) = response.data["results"]
    assert row["quantity"] == 10
    assert row["warehouse_name"] == warehouse.name
    assert row["is_low"] is False


def test_anonymous_cannot_read_stock(anon_client):
    assert anon_client.get("/api/stocks/").status_code == 401
    assert anon_client.get("/api/movements/").status_code == 401
