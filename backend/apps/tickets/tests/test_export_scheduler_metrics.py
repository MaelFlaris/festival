from __future__ import annotations

import csv
from io import StringIO
from datetime import datetime, timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition
from apps.tickets.models import TicketType, PricePhase


class TicketsExportSchedulerMetricsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _make_base(self):
        ed = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", is_active=True, name="ed2025")
        # Early on sale since 20 days ago, should advance
        sale_start = timezone.now() - timedelta(days=20)
        t1 = TicketType.objects.create(
            edition=ed, code="EARLY1", name="Early Bird", price=50, phase=PricePhase.EARLY,
            quota_total=100, quota_reserved=0, sale_start=sale_start
        )
        # Regular with low remaining quota, should advance to late
        t2 = TicketType.objects.create(
            edition=ed, code="REG1", name="Regular", price=70, phase=PricePhase.REGULAR,
            quota_total=100, quota_reserved=95, sale_start=timezone.now() - timedelta(days=5)
        )
        return ed, [t1, t2]

    def test_export_csv_ok(self):
        ed, items = self._make_base()
        url = f"/api/v1/tickets/types/export.csv?edition={ed.id}"
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"].startswith("text/csv")
        rows = list(csv.reader(StringIO(resp.content.decode("utf-8"))))
        assert rows[0][:5] == ["id", "edition", "code", "name", "phase"]
        assert len(rows) >= 3

    def test_recompute_metrics_ok(self):
        self._make_base()
        call_command("tickets_recompute_metrics")

    def test_phase_scheduler_ok(self):
        ed, items = self._make_base()
        call_command("tickets_advance_phases", edition=ed.id, date_from=(timezone.now().date()).isoformat())
        t1 = TicketType.objects.get(code="EARLY1")
        t2 = TicketType.objects.get(code="REG1")
        assert t1.phase == PricePhase.REGULAR
        assert t2.phase == PricePhase.LATE

