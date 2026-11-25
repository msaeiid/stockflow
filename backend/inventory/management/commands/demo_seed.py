from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from inventory import demo


class Command(BaseCommand):
    help = "Load the fictional demo data and the demo login (idempotent). Needs DEMO_MODE=True."

    def handle(self, *args, **options):
        try:
            demo.ensure_demo_mode()
            counts = demo.seed()
        except ImproperlyConfigured as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Demo data ready: {counts}"))
