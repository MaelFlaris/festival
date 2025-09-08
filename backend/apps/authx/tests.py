"""Authx tests (self-service profile)."""
from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import UserProfile

User = get_user_model()


class AuthxApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="user", email="u@example.com", password="pwd")
        self.other = User.objects.create_user(username="other", email="o@example.com", password="pwd")
        self.admin = User.objects.create_superuser(username="admin", email="a@example.com", password="pwd")

    def test_me_autocreate_and_get(self):
        self.client.login(username="user", password="pwd")
        url = reverse("authx-profiles-me")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["username"], "user")
        # le profil doit exister en base
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_me_patch_self(self):
        self.client.login(username="user", password="pwd")
        url = reverse("authx-profiles-me")
        resp = self.client.patch(url, {"display_name": "Maël"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["display_name"], "Maël")

    def test_cannot_edit_others_profile(self):
        # crée profil 'other'
        UserProfile.objects.get_or_create(user=self.other)
        self.client.login(username="user", password="pwd")
        # liste filtrée à soi-même
        list_url = reverse("authx-profiles-list")
        resp = self.client.get(list_url)
        self.assertEqual(resp.status_code, 200)
        # ne doit contenir que son profil (créé à la volée ou non)
        # force création propre profil
        self.client.get(reverse("authx-profiles-me"))
        resp = self.client.get(list_url)
        self.assertTrue(all(item["username"] == "user" for item in resp.data))

        # tentative de patch du profil "other"
        other_profile = UserProfile.objects.get(user=self.other)
        detail_url = reverse("authx-profiles-detail", args=[other_profile.id])
        resp = self.client.patch(detail_url, {"display_name": "H4x"}, format="json")
        self.assertEqual(resp.status_code, 404)  # non visible pour user standard

    def test_admin_can_list_all(self):
        self.client.login(username="admin", password="pwd")
        # crée des profils
        UserProfile.objects.get_or_create(user=self.user)
        UserProfile.objects.get_or_create(user=self.other)
        url = reverse("authx-profiles-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_preferences_size_limit(self):
        self.client.login(username="user", password="pwd")
        url = reverse("authx-profiles-me")
        big = {"blob": "x" * (33 * 1024)}  # > 32 KiB
        resp = self.client.patch(url, {"preferences": big}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("preferences", resp.data)

    def test_consent_updates(self):
        self.client.login(username="user", password="pwd")
        url = reverse("authx-profiles-me")
        payload = {
            "consent_updates": [
                {"key": "newsletter", "granted": True, "source": "ui"},
                {"key": "tracking", "granted": False},
            ]
        }
        resp = self.client.patch(url, payload, format="json")
        self.assertEqual(resp.status_code, 200)
        # snapshot compact doit refléter les décisions
        snap = resp.data.get("consents_snapshot") or {}
        self.assertIn("newsletter", snap)
        self.assertEqual(snap["newsletter"]["granted"], True)
        self.assertIn("tracking", snap)
        self.assertEqual(snap["tracking"]["granted"], False)
