import pytest
from django.core.exceptions import ValidationError

from inventory.models import Order, Stock, StockMovement
from inventory.services import create_order

from .factories import ProductFactory, WarehouseFactory

pytestmark = pytest.mark.django_db


def _add_stock(product, warehouse, qty):
    StockMovement.objects.create(
        product=product,
        warehouse=warehouse,
        movement_type=StockMovement.MovementType.IN,
        quantity=qty,
    )


def test_create_order_deducts_stock():
    w = WarehouseFactory()
    p1, p2 = ProductFactory(), ProductFactory()
    _add_stock(p1, w, 10)
    _add_stock(p2, w, 5)

    order = create_order(
        warehouse=w,
        customer_name="Alice",
        items=[{"product": p1, "quantity": 3}, {"product": p2, "quantity": 2}],
    )

    assert order.items.count() == 2
    assert Stock.objects.get(product=p1, warehouse=w).quantity == 7
    assert Stock.objects.get(product=p2, warehouse=w).quantity == 3


def test_order_rolls_back_if_any_item_short():
    w = WarehouseFactory()
    p1, p2 = ProductFactory(), ProductFactory()
    _add_stock(p1, w, 10)
    _add_stock(p2, w, 1)  # not enough for the order below

    with pytest.raises(ValidationError):
        create_order(
            warehouse=w,
            customer_name="Bob",
            items=[{"product": p1, "quantity": 3}, {"product": p2, "quantity": 5}],
        )

    # The crucial assertions: NOTHING was committed.
    assert Order.objects.count() == 0
    assert Stock.objects.get(product=p1, warehouse=w).quantity == 10  # untouched
