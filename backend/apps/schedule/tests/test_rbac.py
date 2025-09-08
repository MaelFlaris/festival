from __future__ import annotations

from datetime import time

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition, Venue, Stage
from apps.lineup.models import Artist
from apps.schedule.models import Slot, SlotStatus


User = get_user_model()


class ScheduleRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pwd")
        self.staff = User.objects.create_user(username="staff", password="pwd", is_staff=True)
        self.ed = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", name="ed2025")
        self.v = Venue.objects.create(name="Hall", address="a", city="c", country="FR")
        self.stage = Stage.objects.create(edition=self.ed, venue=self.v, name="Main")
        self.artist = Artist.objects.create(name="Band", slug="band")
        self.slot = Slot.objects.create(edition=self.ed, stage=self.stage, artist=self.artist, day=self.ed.start_date, start_time=time(18,0), end_time=time(19,0))

    def test_list_and_manage_slot(self):
        self.client.login(username="u", password="pwd")
        r = self.client.get(reverse("schedule-slots-list"))
        assert (r.data.get("count") == 0) if isinstance(r.data, dict) else (len(r.data) == 0)
        assign_perm("schedule.view_slot", self.user, self.slot)
        r = self.client.get(reverse("schedule-slots-detail", args=[self.slot.id]))
        assert r.status_code == 200
        # Try to change status: requires manage_slot and change_slot
        r = self.client.patch(reverse("schedule-slots-detail", args=[self.slot.id]), {"status": SlotStatus.CONFIRMED}, format="json")
        assert r.status_code == 403
        assign_perm("schedule.change_slot", self.user, self.slot)
        assign_perm("schedule.manage_slot", self.user, self.slot)
        r = self.client.patch(reverse("schedule-slots-detail", args=[self.slot.id]), {"status": SlotStatus.CONFIRMED}, format="json")
        assert r.status_code == 200

