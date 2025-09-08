from __future__ import annotations

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition
from .models import Page, News
from .services import markdown_to_html_safe


class CmsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.edition = FestivalEdition.objects.create(
            name="Édition Test",
            year=2025,
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            tagline="",
            hero_image="",
            is_active=True,
        )

    def test_markdown_sanitization(self):
        md = "# Titre\n<script>alert(1)</script>\n**bold**"
        html = markdown_to_html_safe(md)
        self.assertIn("<h1>", html)
        self.assertIn("<strong>", html)
        self.assertNotIn("<script>", html)

    def test_public_filters_only_published(self):
        Page.objects.create(
            edition=self.edition, slug="a", title="A", body_md="x",
            status="draft"
        )
        Page.objects.create(
            edition=self.edition, slug="b", title="B", body_md="x",
            status="published", publish_at=timezone.now() - timezone.timedelta(minutes=1)
        )
        url = reverse("cms-public-pages-list")
        resp = self.client.get(url, {"edition": self.edition.id})
        self.assertEqual(resp.status_code, 200)
        slugs = [p["slug"] for p in resp.data]
        self.assertIn("b", slugs)
        self.assertNotIn("a", slugs)

    def test_preview_flow(self):
        news = News.objects.create(
            edition=self.edition,
            title="Hello",
            summary="",
            body_md="MD",
            status="draft",
        )
        create_url = reverse("cms-preview-create")
        res = self.client.post(create_url, {"type": "news", "id": news.id}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("url", res.data)

        # Resolve
        resolve_url = res.data["url"]
        res2 = self.client.get(resolve_url)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.data["type"], "news")
        self.assertEqual(res2.data["data"]["id"], news.id)

    def test_sitemap(self):
        Page.objects.create(
            edition=self.edition, slug="home", title="Home", body_md="x",
            status="published", publish_at=timezone.now() - timezone.timedelta(days=1)
        )
        url = reverse("cms-sitemap-edition", args=[self.edition.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("<urlset", res.content.decode("utf-8"))
