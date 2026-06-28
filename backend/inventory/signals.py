from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Stock
from .tasks import send_low_stock_alert


@receiver(post_save, sender=Stock)
def alert_on_low_stock(sender, instance, **kwargs):
    if instance.quantity <= instance.product.reorder_threshold:
        stock_id = instance.id
        transaction.on_commit(lambda: send_low_stock_alert.delay(stock_id))
