from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from guardian.shortcuts import assign_perm
from rest_framework.test import APIClient

from apps.core.models import FestivalEdition
from apps.cms.models import Page, News


User = get_user_model()


class CmsRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.alice = User.objects.create_user(username="alice", password="pwd")
        self.bob = User.objects.create_user(username="bob", password="pwd")
        self.staff = User.objects.create_user(username="staff", password="pwd", is_staff=True)
        self.ed = FestivalEdition.objects.create(year=2025, start_date="2025-07-18", end_date="2025-07-20", name="ed2025")

    def test_list_filter_and_object_access(self):
        page = Page.objects.create(edition=self.ed, slug="a", title="A", body_md="# a")
        self.client.login(username="alice", password="pwd")
        # No perms yet -> list empty
        r = self.client.get(reverse("cms-pages-list"))
        assert (r.data.get("count") == 0) if isinstance(r.data, dict) else (len(r.data) == 0)
        # Grant view perms -> appears
        assign_perm("cms.view_page", self.alice, page)
        r = self.client.get(reverse("cms-pages-list"))
        count = r.data.get("count") if isinstance(r.data, dict) else len(r.data)
        assert count == 1
        # Detail without change perm is allowed (view); update requires change
        detail = reverse("cms-pages-detail", args=[page.id])
        r = self.client.get(detail)
        assert r.status_code == 200
        r = self.client.patch(detail, {"title": "B"}, format="json")
        assert r.status_code == 403
        assign_perm("cms.change_page", self.alice, page)
        r = self.client.patch(detail, {"title": "B"}, format="json")
        assert r.status_code == 200

    def test_publish_custom_permission(self):
        n = News.objects.create(edition=self.ed, title="N", body_md="x")
        self.client.login(username="alice", password="pwd")
        # Need view to access detail first
        assign_perm("cms.view_news", self.alice, n)
        url = reverse("cms-news-publish", args=[n.id])
        r = self.client.post(url)
        assert r.status_code == 403
        assign_perm("cms.publish_news", self.alice, n)
        r = self.client.post(url)
        assert r.status_code == 200

    def test_assign_on_create(self):
        self.client.login(username="alice", password="pwd")
        payload = {"edition": self.ed.id, "slug": "c", "title": "C", "body_md": "c"}
        r = self.client.post(reverse("cms-pages-list"), payload, format="json")
        assert r.status_code == 201
        # Should be able to see it immediately (view perm assigned)
        pid = r.data["id"]
        r2 = self.client.get(reverse("cms-pages-detail", args=[pid]))
        assert r2.status_code == 200

