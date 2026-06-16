import pytest
from django.core.exceptions import ValidationError
from inventory.models import Stock, StockMovement
from .factories import ProductFactory, WarehouseFactory

pytestmark = pytest.mark.django_db


def test_stock_in_increases_quantity():
    product = ProductFactory()
    warehouse = WarehouseFactory()
    StockMovement.objects.create(
        product=product, warehouse=warehouse,
        movement_type=StockMovement.MovementType.IN, quantity=50,
    )
    stock = Stock.objects.get(product=product, warehouse=warehouse)
    assert stock.quantity == 50


def test_stock_out_decreases_quantity():
    product = ProductFactory()
    warehouse = WarehouseFactory()
    StockMovement.objects.create(
        product=product, warehouse=warehouse,
        movement_type=StockMovement.MovementType.IN, quantity=50,
    )
    StockMovement.objects.create(
        product=product, warehouse=warehouse,
        movement_type=StockMovement.MovementType.OUT, quantity=20,
    )
    stock = Stock.objects.get(product=product, warehouse=warehouse)
    assert stock.quantity == 30


def test_cannot_remove_more_than_available():
    product = ProductFactory()
    warehouse = WarehouseFactory()
    StockMovement.objects.create(
        product=product, warehouse=warehouse,
        movement_type=StockMovement.MovementType.IN, quantity=10,
    )
    with pytest.raises(ValidationError):
        StockMovement.objects.create(
            product=product, warehouse=warehouse,
            movement_type=StockMovement.MovementType.OUT, quantity=100,
        )


def test_is_low_flag():
    product = ProductFactory(reorder_threshold=10)
    warehouse = WarehouseFactory()
    StockMovement.objects.create(
        product=product, warehouse=warehouse,
        movement_type=StockMovement.MovementType.IN, quantity=5,
    )
    stock = Stock.objects.get(product=product, warehouse=warehouse)
    assert stock.is_low is True