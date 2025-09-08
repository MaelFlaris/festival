from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient

from apps.lineup.models import Artist


User = get_user_model()


class LineupAdminRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="u", password="pwd")
        self.artist = Artist.objects.create(name="Band", slug="band")

    def test_admin_viewset_list_filtered(self):
        self.client.login(username="u", password="pwd")
        r = self.client.get(reverse("lineup-admin-artists-list"))
        assert (r.data.get("count") == 0) if isinstance(r.data, dict) else (len(r.data) == 0)
        assign_perm("lineup.view_artist", self.user, self.artist)
        r = self.client.get(reverse("lineup-admin-artists-list"))
        count = r.data.get("count") if isinstance(r.data, dict) else len(r.data)
        assert count == 1

