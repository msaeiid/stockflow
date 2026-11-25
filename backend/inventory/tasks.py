from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import F


@shared_task
def send_low_stock_alert(stock_id: int) -> str:
    from .models import Stock

    try:
        stock = Stock.objects.select_related("product", "warehouse").get(id=stock_id)
    except Stock.DoesNotExist:
        return "Stock not found"

    send_mail(
        subject=f"Low stock alert: {stock.product.name}",
        message=(
            f"{stock.product.name} at {stock.warehouse.name} is running low.\n"
            f"Current quantity: {stock.quantity} "
            f"(threshold: {stock.product.reorder_threshold})."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.LOW_STOCK_ALERT_EMAIL],
    )
    return f"Alert sent for {stock.product.name}"


@shared_task
def generate_daily_stock_report() -> str:
    from .models import Stock

    low_items = list(
        Stock.objects.select_related("product", "warehouse")
        .filter(quantity__lte=F("product__reorder_threshold"))
        .order_by("product__name", "warehouse__name")
    )

    if not low_items:
        body = "All stock levels are healthy. No items below threshold."
    else:
        lines = [
            f"- {s.product.name} @ {s.warehouse.name}: {s.quantity} "
            f"(threshold: {s.product.reorder_threshold})"
            for s in low_items
        ]
        body = "Items below reorder threshold:\n\n" + "\n".join(lines)

    send_mail(
        subject=f"Daily stock report — {len(low_items)} item(s) low",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.LOW_STOCK_ALERT_EMAIL],
    )
    return f"Report sent: {len(low_items)} low item(s)"
