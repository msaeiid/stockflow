from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand, CommandError

from inventory import demo


class Command(BaseCommand):
    help = (
        "Wipe all inventory data and visitor accounts, then reload the demo data. "
        "Needs DEMO_MODE=True; meant for a nightly cron job."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            "--noinput",
            action="store_false",
            dest="interactive",
            help="Do not ask for confirmation.",
        )

    def handle(self, *args, interactive=True, **options):
        try:
            demo.ensure_demo_mode()
        except ImproperlyConfigured as exc:
            raise CommandError(str(exc)) from exc
        if interactive:
            answer = input("This deletes all StockFlow data in this database. Type 'yes': ")
            if answer.strip().lower() != "yes":
                raise CommandError("Reset cancelled.")
        try:
            counts = demo.reset()
        except ImproperlyConfigured as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Demo reset done: {counts}"))
