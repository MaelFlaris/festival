# apps/common/tests.py
from __future__ import annotations

import math
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from apps.core.models import FestivalEdition
from apps.common.views import AddressValidateView, SlugPreviewView
from apps.common.serializers import AddressSerializer
from apps.common.services import geohash_encode, haversine_km, normalize_iso2, is_valid_iso2


class SluggedModelTests(TestCase):
    def test_unique_slug_generation_with_collision(self):
        e1 = FestivalEdition.objects.create(
            name="Édition été",
            year=2024,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            tagline="",
            hero_image="",
            is_active=True,
        )
        self.assertEqual(e1.slug, "edition-ete")

        e2 = FestivalEdition.objects.create(
            name="Édition été",
            year=2025,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            tagline="",
            hero_image="",
            is_active=False,
        )
        self.assertEqual(e2.slug, "edition-ete-2")

    def test_slug_truncation_respects_max_length(self):
        long_name = "x" * 250
        e = FestivalEdition.objects.create(
            name=long_name,
            year=2030,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            tagline="",
            hero_image="",
            is_active=False,
        )
        self.assertLessEqual(len(e.slug), 220)


class AddressSerializerTests(TestCase):
    def test_valid_country_and_unicode_fields(self):
        data = {
            "address": "10 rue de l'Église",
            "city": "Lège-Cap-Ferret",
            "postal_code": "33950",
            "country": "fr",
            "latitude": None,
            "longitude": None,
        }
        ser = AddressSerializer(data=data)
        self.assertTrue(ser.is_valid(), ser.errors)
        self.assertEqual(ser.validated_data.get("country"), "FR")

    def test_invalid_country_code(self):
        data = {"country": "FFF"}
        ser = AddressSerializer(data=data)
        self.assertFalse(ser.is_valid())
        self.assertIn("country", ser.errors)


class CommonViewsTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_address_validate_view_ok(self):
        view = AddressValidateView.as_view()
        req = self.factory.post(
            "/api/common/address/validate",
            {
                "address": "1 Avenue des Champs-Élysées",
                "city": "Paris",
                "postal_code": "75008",
                "country": "FR",
            },
            format="json",
        )
        resp = view(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.get("valid"), True)

    def test_address_validate_view_error(self):
        view = AddressValidateView.as_view()
        req = self.factory.post(
            "/api/common/address/validate", {"country": "Z"}, format="json"
        )
        resp = view(req)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data.get("valid"), False)

    def test_slug_preview_view(self):
        view = SlugPreviewView.as_view()
        req = self.factory.post("/api/common/slug/preview", {"name": "Été 2025"}, format="json")
        resp = view(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data.get("slug"), "ete-2025")


class GeoUtilsTests(TestCase):
    def test_haversine_paris_lyon(self):
        # Paris (48.8566, 2.3522) -> Lyon (45.7640, 4.8357) ≈ 392 km
        d = haversine_km(48.8566, 2.3522, 45.7640, 4.8357)
        self.assertTrue(360 <= d <= 430, f"distance={d}")

    def test_geohash_precision_monotonic(self):
        lat, lon = 48.8566, 2.3522
        gh5 = geohash_encode(lat, lon, precision=5)
        gh6 = geohash_encode(lat, lon, precision=6)
        self.assertTrue(gh6.startswith(gh5))


class IsoUtilsTests(TestCase):
    def test_normalize_and_validate_iso2(self):
        self.assertEqual(normalize_iso2("fr"), "FR")
        self.assertTrue(is_valid_iso2("FR"))
        self.assertFalse(is_valid_iso2("FFF"))
