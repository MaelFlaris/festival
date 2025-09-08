from __future__ import annotations

import csv
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition, Venue, Stage
from apps.sponsors.models import Sponsor, SponsorTier, Sponsorship


class SponsorsExportMetricsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _make_base(self):
        ed = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", is_active=True, name="ed2025")
        tier = SponsorTier.objects.create(name="gold", slug="gold", display_name="Gold", rank=1)
        s1 = Sponsor.objects.create(name="Acme", slug="acme")
        s2 = Sponsor.objects.create(name="Globex", slug="globex")
        sp1 = Sponsorship.objects.create(edition=ed, sponsor=s1, tier=tier, amount_eur=1000, visible=True, order=1)
        sp2 = Sponsorship.objects.create(edition=ed, sponsor=s2, tier=tier, amount_eur=2000, visible=False, order=2)
        return ed, tier, [sp1, sp2]

    def test_export_csv_ok(self):
        ed, tier, items = self._make_base()
        url = f"/api/v1/sponsors/sponsorships/export.csv?edition={ed.id}"
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"].startswith("text/csv")
        sio = StringIO(resp.content.decode("utf-8"))
        rows = list(csv.reader(sio))
        assert rows[0] == [
            "edition_id", "edition_year", "tier_rank", "tier_name",
            "sponsor_id", "sponsor_name", "amount_eur", "visible", "order",
            "logo_url", "contract_url", "created_at"
        ]
        assert len(rows) == 3  # header + 2 rows

    def test_metrics_command_ok(self):
        self._make_base()
        # Should not raise
        call_command("sponsors_recompute_metrics")

