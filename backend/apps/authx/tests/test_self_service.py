from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient

from apps.authx.models import UserProfile


User = get_user_model()


class AuthxSelfServiceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(username="alice", email="a@example.com", password="pwd")
        self.user_b = User.objects.create_user(username="bob", email="b@example.com", password="pwd")
        self.staff = User.objects.create_user(username="staff", email="s@example.com", password="pwd", is_staff=True)

    def test_signal_auto_profile_creation(self):
        u = User.objects.create_user(username="charlie", email="c@example.com", password="pwd")
        assert UserProfile.objects.filter(user=u).exists()

    def test_me_get_and_patch(self):
        self.client.login(username="alice", password="pwd")
        url = reverse("authx-profiles-me")
        # GET
        r1 = self.client.get(url)
        assert r1.status_code == 200
        assert r1.data.get("user") == self.user_a.id
        assert r1.data.get("username") == "alice"
        assert r1.data.get("email") == "a@example.com"
        # PATCH
        r2 = self.client.patch(url, {"display_name": "Alice L."}, format="json")
        assert r2.status_code == 200
        assert r2.data.get("display_name") == "Alice L."
        # user should remain unchanged and read-only
        assert r2.data.get("user") == self.user_a.id

    def test_owner_only_permissions(self):
        # Ensure both users have profiles
        pa, _ = UserProfile.objects.get_or_create(user=self.user_a)
        pb, _ = UserProfile.objects.get_or_create(user=self.user_b)

        self.client.login(username="alice", password="pwd")
        # Detail GET on Bob's profile -> forbidden (403)
        detail_b = reverse("authx-profiles-detail", args=[pb.id])
        r1 = self.client.get(detail_b)
        assert r1.status_code == 403
        # Update on Bob's profile -> forbidden (403)
        r2 = self.client.patch(detail_b, {"display_name": "H4x"}, format="json")
        assert r2.status_code == 403

    def test_list_filtered_for_standard_user(self):
        # Auto-create Alice profile via /me
        self.client.login(username="alice", password="pwd")
        self.client.get(reverse("authx-profiles-me"))
        list_url = reverse("authx-profiles-list")
        r = self.client.get(list_url)
        assert r.status_code == 200
        # Pagination-aware assertions
        if isinstance(r.data, dict) and "results" in r.data:
            assert r.data.get("count") == 1
            assert len(r.data.get("results") or []) == 1
            assert r.data["results"][0]["username"] == "alice"
        else:
            # Fallback if pagination disabled
            assert len(r.data) == 1
            assert r.data[0]["username"] == "alice"

    def test_staff_can_list_all(self):
        # Ensure two profiles exist
        UserProfile.objects.get_or_create(user=self.user_a)
        UserProfile.objects.get_or_create(user=self.user_b)
        self.client.login(username="staff", password="pwd")
        r = self.client.get(reverse("authx-profiles-list"))
        assert r.status_code == 200
        if isinstance(r.data, dict) and "results" in r.data:
            assert r.data.get("count", 0) >= 2
        else:
            assert len(r.data) >= 2

