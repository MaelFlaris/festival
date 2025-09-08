from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.sponsors.services import recompute_metrics


class Command(BaseCommand):
    help = "Recompute sponsors Prometheus gauges (visible per tier, amount per edition)."

    def handle(self, *args, **options):
        try:
            recompute_metrics()
        except Exception as exc:
            # Do not fail hard if prometheus client is missing; services handles no-op
            self.stderr.write(self.style.WARNING(f"metrics recompute encountered an error: {exc}"))
        self.stdout.write(self.style.SUCCESS("Sponsors metrics recomputed."))

