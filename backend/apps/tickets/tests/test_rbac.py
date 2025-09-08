from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition
from apps.tickets.models import TicketType, PricePhase


User = get_user_model()


class TicketsRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pwd")
        self.ed = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", name="ed2025")
        self.tt = TicketType.objects.create(edition=self.ed, code="T1", name="Ticket 1", price=50, phase=PricePhase.EARLY, quota_total=100)

    def test_list_and_manage_pricing(self):
        self.client.login(username="u", password="pwd")
        r = self.client.get(reverse("tickets-types-list"))
        assert (r.data.get("count") == 0) if isinstance(r.data, dict) else (len(r.data) == 0)
        assign_perm("tickets.view_tickettype", self.user, self.tt)
        r = self.client.get(reverse("tickets-types-detail", args=[self.tt.id]))
        assert r.status_code == 200
        # Update price requires manage_pricing + change
        r = self.client.patch(reverse("tickets-types-detail", args=[self.tt.id]), {"price": 60}, format="json")
        assert r.status_code == 403
        assign_perm("tickets.change_tickettype", self.user, self.tt)
        assign_perm("tickets.manage_pricing", self.user, self.tt)
        r = self.client.patch(reverse("tickets-types-detail", args=[self.tt.id]), {"price": 60}, format="json")
        assert r.status_code == 200

