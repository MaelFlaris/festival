from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition, Venue, Stage
from apps.sponsors.models import SponsorTier, Sponsor, Sponsorship


User = get_user_model()


class SponsorsRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pwd")
        self.staff = User.objects.create_user(username="staff", password="pwd", is_staff=True)
        self.ed = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", name="ed2025")
        self.tier = SponsorTier.objects.create(name="gold", slug="gold", display_name="Gold", rank=1)
        self.sp = Sponsor.objects.create(name="Acme", slug="acme")
        self.spons = Sponsorship.objects.create(edition=self.ed, sponsor=self.sp, tier=self.tier, amount_eur=1234)

    def test_list_and_financial_visibility(self):
        self.client.login(username="u", password="pwd")
        # No perms -> list empty
        r = self.client.get(reverse("sponsors-sponsorships-list"))
        assert (r.data.get("count") == 0) if isinstance(r.data, dict) else (len(r.data) == 0)
        # Grant view -> appears, but amount hidden
        assign_perm("sponsors.view_sponsorship", self.user, self.spons)
        r = self.client.get(reverse("sponsors-sponsorships-detail", args=[self.spons.id]))
        assert r.status_code == 200
        assert r.data.get("amount_eur") is None
        # Grant financials -> amount visible
        assign_perm("sponsors.view_financials", self.user, self.spons)
        r = self.client.get(reverse("sponsors-sponsorships-detail", args=[self.spons.id]))
        assert r.data.get("amount_eur") in (1234, 1234.0, "1234.00")

