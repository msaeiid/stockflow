from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_low_stock_alert(stock_id):
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
