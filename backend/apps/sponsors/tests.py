from __future__ import annotations

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition
from .models import Sponsor, SponsorTier, Sponsorship


class SponsorsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ed = FestivalEdition.objects.create(
            name="2025", year=2025,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            tagline="", hero_image="", is_active=True,
        )
        self.tier = SponsorTier.objects.create(name="Gold", display_name="Gold", rank=1)
        self.s = Sponsor.objects.create(name="Acme", website="https://acme.test", logo="https://acme.test/logo.png")

    def test_unique_per_edition(self):
        Sponsorship.objects.create(edition=self.ed, sponsor=self.s, tier=self.tier, amount_eur=1000, visible=True)
        with self.assertRaises(Exception):
            Sponsorship.objects.create(edition=self.ed, sponsor=self.s, tier=self.tier)

    def test_https_validation(self):
        sp = Sponsor(name="Bad", website="http://bad.test", logo="")
        with self.assertRaises(Exception):
            sp.full_clean()

    def test_public_grouped(self):
        Sponsorship.objects.create(edition=self.ed, sponsor=self.s, tier=self.tier, visible=True)
        url = reverse("sponsors-sponsorships-public-by-edition")
        res = self.client.get(url, {"edition": self.ed.id})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["tiers"])

    def test_stats_summary(self):
        Sponsorship.objects.create(edition=self.ed, sponsor=self.s, tier=self.tier, visible=True, amount_eur=1500)
        url = reverse("sponsors-sponsorships-stats-summary")
        res = self.client.get(url, {"edition": self.ed.id})
        self.assertEqual(res.status_code, 200)
        self.assertIn("total_amount_eur", res.data)

    def test_contract_attach(self):
        spx = Sponsorship.objects.create(edition=self.ed, sponsor=self.s, tier=self.tier, visible=True)
        url = reverse("sponsors-sponsorships-contracts-attach", args=[spx.id])
        res = self.client.post(url, {"contract_url": "https://bucket.s3.eu-west-3.amazonaws.com/contracts/x.pdf"}, format="json")
        self.assertEqual(res.status_code, 200)
