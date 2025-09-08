from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.tickets.services import recompute_metrics


class Command(BaseCommand):
    help = "Recompute tickets Prometheus gauges (on sale total, quota remaining sum)."

    def handle(self, *args, **options):
        try:
            recompute_metrics()
        except Exception as exc:
            self.stderr.write(self.style.WARNING(f"metrics recompute encountered an error: {exc}"))
        self.stdout.write(self.style.SUCCESS("Tickets metrics recomputed."))

