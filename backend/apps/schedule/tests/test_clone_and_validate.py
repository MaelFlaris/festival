from __future__ import annotations

from datetime import time

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition, Venue, Stage
from apps.lineup.models import Artist
from apps.schedule.models import Slot


class ScheduleCloneValidateTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _make_base(self):
        ed1 = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", is_active=True, name="ed2025")
        ed2 = FestivalEdition.objects.create(year=2026, start_date="2026-07-17", end_date="2026-07-19", is_active=False, name="ed2026")
        v = Venue.objects.create(name="Main Venue", address="x", city="y", country="FR")
        st1 = Stage.objects.create(edition=ed1, venue=v, name="Main")
        st2 = Stage.objects.create(edition=ed2, venue=v, name="Main")
        a = Artist.objects.create(name="Band", slug="band")
        Slot.objects.create(edition=ed1, stage=st1, artist=a, day=ed1.start_date, start_time=time(20, 0), end_time=time(21, 0))
        return ed1, ed2, st1, st2, a

    def test_clone_template_ok(self):
        ed1, ed2, st1, st2, a = self._make_base()
        call_command("schedule_clone_template", **{"from": ed1.id, "to": ed2.id, "shift_days": 0})
        assert Slot.objects.filter(edition=ed2).count() == 1

    def test_validate_conflicts_ok(self):
        ed1, ed2, st1, st2, a = self._make_base()
        # Create overlapping slot in same edition/stage/day
        Slot.objects.create(edition=ed1, stage=st1, artist=a, day=ed1.start_date, start_time=time(20, 30), end_time=time(21, 30))
        resp = self.client.get(f"/api/v1/schedule/slots/validate?edition={ed1.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["edition"] == ed1.id
        assert len(data["conflicts"]) >= 1
