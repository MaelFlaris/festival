from __future__ import annotations

from datetime import time
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition, Stage
from apps.lineup.models import Artist
from .models import Slot, SlotStatus


class ScheduleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        today = timezone.now().date()
        self.ed = FestivalEdition.objects.create(
            name="Test",
            year=today.year,
            start_date=today,
            end_date=today,
            tagline="",
            hero_image="",
            is_active=True,
        )
        self.stage = Stage.objects.create(name="Main")
        self.a1 = Artist.objects.create(name="Alpha", country="FR")
        self.a2 = Artist.objects.create(name="Beta", country="FR")

    def test_model_validation(self):
        # end_time <= start_time
        url = reverse("schedule-slots-list")
        payload = {
            "edition": self.ed.id,
            "stage": self.stage.id,
            "artist": self.a1.id,
            "day": str(self.ed.start_date),
            "start_time": "20:00",
            "end_time": "20:00",
            "status": "tentative",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 400)

    def test_conflict_409(self):
        d = self.ed.start_date
        Slot.objects.create(
            edition=self.ed, stage=self.stage, artist=self.a1,
            day=d, start_time=time(20,0), end_time=time(21,0), status=SlotStatus.CONFIRMED
        )
        url = reverse("schedule-slots-list")
        payload = {
            "edition": self.ed.id,
            "stage": self.stage.id,
            "artist": self.a2.id,
            "day": str(d),
            "start_time": "20:30",
            "end_time": "21:10",
            "status": "tentative",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 409)
        self.assertIn("conflicts", res.data)

    def test_ics_export(self):
        d = self.ed.start_date
        Slot.objects.create(
            edition=self.ed, stage=self.stage, artist=self.a1,
            day=d, start_time=time(18,0), end_time=time(19,0), status=SlotStatus.CONFIRMED
        )
        url = reverse("schedule-ics")
        res = self.client.get(url, {"edition": self.ed.id})
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"BEGIN:VCALENDAR", res.content)

    def test_template_copy_dry_run(self):
        # crée un slot source
        d = self.ed.start_date
        Slot.objects.create(
            edition=self.ed, stage=self.stage, artist=self.a1,
            day=d, start_time=time(18,0), end_time=time(19,0), status=SlotStatus.CONFIRMED
        )
        # crée destination au lendemain
        ed2 = FestivalEdition.objects.create(
            name="Test2", year=self.ed.year, start_date=d, end_date=d, tagline="", hero_image="", is_active=False
        )
        url = reverse("schedule-slots-template-copy")
        res = self.client.post(url, {"from_edition": self.ed.id, "to_edition": ed2.id, "dry_run": True}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("created", res.data)
