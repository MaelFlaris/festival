from __future__ import annotations

import json
import os
from datetime import datetime, date
from typing import Optional

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tickets.models import TicketType, PricePhase
from apps.tickets.services import dispatch_webhook


class Command(BaseCommand):
    help = "Advance ticket phases early→regular→late based on rules (age or remaining quota)."

    def add_arguments(self, parser):
        parser.add_argument("--edition", type=int, help="Filter by edition id", default=None)
        parser.add_argument("--date-from", dest="date_from", type=str, default=None,
                            help="Reference date YYYY-MM-DD (defaults to today)")
        parser.add_argument("--rules", type=str, default=None,
                            help='JSON: {"days_since_start": 14, "remaining_pct": 0.1}')

    def handle(self, *args, **opts):
        edition: Optional[int] = opts.get("edition")
        date_from_s: Optional[str] = opts.get("date_from")
        rules_s: Optional[str] = opts.get("rules")

        # Parse reference date
        if date_from_s:
            ref_date = datetime.strptime(date_from_s, "%Y-%m-%d").date()
        else:
            ref_date = timezone.now().date()

        # Load rules from args or ENV
        days_since_start = int(os.getenv("TICKETS_PHASE_DAYS", "14"))
        remaining_pct = float(os.getenv("TICKETS_PHASE_REMAINING_PCT", "0.1"))
        if rules_s:
            try:
                r = json.loads(rules_s)
                days_since_start = int(r.get("days_since_start", days_since_start))
                remaining_pct = float(r.get("remaining_pct", remaining_pct))
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f"Invalid --rules JSON, using defaults: {exc}"))

        qs = TicketType.objects.all()
        if edition:
            qs = qs.filter(edition_id=edition)

        changed = 0
        for tt in qs:
            new_phase = None
            if tt.phase == PricePhase.EARLY:
                if self._should_advance(tt, ref_date, days_since_start, remaining_pct):
                    new_phase = PricePhase.REGULAR
            elif tt.phase == PricePhase.REGULAR:
                if self._should_advance(tt, ref_date, days_since_start, remaining_pct):
                    new_phase = PricePhase.LATE

            if new_phase and new_phase != tt.phase:
                old = tt.phase
                tt.phase = new_phase
                tt.save(update_fields=["phase", "updated_at"])
                changed += 1
                self.stdout.write(f"TicketType {tt.id} phase {old} -> {new_phase}")
                try:
                    dispatch_webhook("tickets.type.phase_changed", {
                        "id": tt.id,
                        "edition": tt.edition_id,
                        "code": tt.code,
                        "from": old,
                        "to": new_phase,
                    })
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS(f"Advanced phases for {changed} ticket types."))

    def _should_advance(self, tt: TicketType, ref_date: date, days_limit: int, remaining_pct: float) -> bool:
        # Time-based rule
        if tt.sale_start:
            try:
                days = (ref_date - tt.sale_start.date()).days
                if days >= days_limit:
                    return True
            except Exception:
                pass
        # Quota-based rule
        try:
            total = int(tt.quota_total or 0)
            if total > 0:
                remaining_ratio = int(tt.quota_remaining) / float(total)
                if remaining_ratio <= remaining_pct:
                    return True
        except Exception:
            pass
        return False

