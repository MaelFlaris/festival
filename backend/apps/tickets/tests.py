from __future__ import annotations

from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition
from .models import TicketType, PricePhase


class TicketsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        today = timezone.now().date()
        self.ed = FestivalEdition.objects.create(
            name="2025", year=2025, start_date=today, end_date=today,
            tagline="", hero_image="", is_active=True,
        )
        now = timezone.now()
        self.tt = TicketType.objects.create(
            edition=self.ed, code="PASS1J", name="Pass 1J",
            day=today, price="69.00", vat_rate="20.0",
            quota_total=10, quota_reserved=0, is_active=True,
            sale_start=now - timedelta(hours=1), sale_end=now + timedelta(hours=1),
            phase=PricePhase.EARLY, quota_by_channel={"online": 8, "partner": 2},
        )

    def test_is_on_sale(self):
        self.assertTrue(self.tt.is_on_sale())
        self.tt.is_active = False
        self.tt.save()
        self.assertFalse(TicketType.objects.get(pk=self.tt.id).is_on_sale())

    def test_on_sale_endpoint(self):
        url = reverse("tickets-types-on-sale")
        res = self.client.get(url, {"edition": self.ed.id})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)

    def test_reserve_ok(self):
        url = reverse("tickets-types-reserve", args=[self.tt.id])
        res = self.client.post(url, {"quantity": 2, "channel": "online"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.tt.refresh_from_db()
        self.assertEqual(self.tt.quota_reserved, 2)
        self.assertEqual(self.tt.reserved_by_channel.get("online"), 2)

    def test_reserve_channel_quota_exceeded(self):
        url = reverse("tickets-types-reserve", args=[self.tt.id])
        res = self.client.post(url, {"quantity": 9, "channel": "online"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_phase_advance(self):
        url = reverse("tickets-types-phase-advance", args=[self.tt.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.tt.refresh_from_db()
        self.assertEqual(self.tt.phase, "regular")
