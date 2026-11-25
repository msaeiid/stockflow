from django.conf import settings
from django.core.management.base import BaseCommand

from inventory import demo


class Command(BaseCommand):
    help = (
        "Load the sample catalogue, stock and orders for local development "
        "(the same fictional data set as the public demo; idempotent). "
        "Creates the demo login too when DEMO_PASSWORD is set."
    )

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")
        counts = demo.seed(with_demo_user=len(settings.DEMO_PASSWORD) >= 8)
        self.stdout.write(self.style.SUCCESS(f"Done: {counts}"))
