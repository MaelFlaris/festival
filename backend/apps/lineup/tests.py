from __future__ import annotations

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Artist, ArtistAvailability, Genre


class LineupBasicTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.g1 = Genre.objects.create(name="Rock")
        self.g2 = Genre.objects.create(name="Electro")
        self.a1 = Artist.objects.create(name="Alpha", country="fr", popularity=80)
        self.a1.genres.add(self.g1)
        self.a2 = Artist.objects.create(name="Beta", country="us", popularity=20)
        self.a2.genres.add(self.g2)

    def test_unique_availability(self):
        d = timezone.now().date()
        ArtistAvailability.objects.create(artist=self.a1, date=d, available=True)
        with self.assertRaises(Exception):
            ArtistAvailability.objects.create(artist=self.a1, date=d, available=False)

    def test_top_endpoint(self):
        url = reverse("lineup-artists-top")
        res = self.client.get(url, {"limit": 1})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "Alpha")

    def test_available_on_filter(self):
        d = timezone.now().date()
        ArtistAvailability.objects.create(artist=self.a2, date=d, available=True)
        url = reverse("lineup-artists-list")
        res = self.client.get(url, {"available_on": str(d)})
        self.assertEqual(res.status_code, 200)
        items = res.data["results"] if isinstance(res.data, dict) else res.data
        names = [x["name"] for x in items]
        self.assertIn("Beta", names)
        self.assertNotIn("Alpha", names)

    def test_compatibility(self):
        url = reverse("lineup-artists-compatibility", args=[self.a1.id])
        res = self.client.get(url, {"genres": f"{self.g1.id},{self.g2.id}"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("score", res.data)
        self.assertTrue(0 <= res.data["score"] <= 100)

    def test_enrich_payload(self):
        url = reverse("lineup-artists-enrich", args=[self.a2.id])
        payload = {
            "source": "spotify",
            "payload": {"name": "Beta+", "images": [{"url": "https://ex/img.jpg"}], "popularity": 55},
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, 200)
        self.a2.refresh_from_db()
        self.assertEqual(self.a2.name, "Beta+")
        self.assertEqual(self.a2.popularity, 55)
