import uuid

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Order, OrderItem, StockMovement


@transaction.atomic
def create_order(*, warehouse, customer_name, items, note=""):
    """
    items: list of dicts like {"product": <Product>, "quantity": <int>}
    Deducts stock for all items atomically. If any item lacks stock,
    the entire order is rolled back.
    """
    if not items:
        raise ValidationError("An order must contain at least one item.")

    order = Order.objects.create(
        reference=f"ORD-{uuid.uuid4().hex[:8].upper()}",
        warehouse=warehouse,
        customer_name=customer_name,
        note=note,
        status=Order.Status.CONFIRMED,
    )

    for entry in items:
        product = entry["product"]
        quantity = entry["quantity"]

        # This raises ValidationError if stock is insufficient,
        # which rolls back the whole transaction.
        StockMovement.objects.create(
            product=product,
            warehouse=warehouse,
            movement_type=StockMovement.MovementType.OUT,
            quantity=quantity,
            note=f"Order {order.reference}",
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.sale_price,
        )

    return order
