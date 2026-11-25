"""Concurrent OUT movements must never oversell. Needs real row locks, so it
runs on PostgreSQL only (CI); SQLite skips it."""

import threading

import pytest
from django.core.exceptions import ValidationError
from django.db import connection

from inventory.models import Stock, StockMovement

from .factories import ProductFactory, WarehouseFactory

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "postgresql", reason="needs PostgreSQL row locks"),
]


def test_parallel_out_movements_cannot_oversell():
    product, warehouse = ProductFactory(), WarehouseFactory()
    StockMovement.objects.create(
        product=product, warehouse=warehouse, movement_type="IN", quantity=5
    )
    results: list[str] = []
    barrier = threading.Barrier(8)

    def take_one_pair():
        from django.db import connection as thread_connection

        try:
            barrier.wait()
            StockMovement.objects.create(
                product=product, warehouse=warehouse, movement_type="OUT", quantity=2
            )
            results.append("ok")
        except ValidationError:
            results.append("refused")
        finally:
            thread_connection.close()

    threads = [threading.Thread(target=take_one_pair) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("ok") == 2
    assert Stock.objects.get(product=product, warehouse=warehouse).quantity == 1
