# backend/apps/cms/models.py
from __future__ import annotations

from django.db import models
from apps.common.models import TimeStampedModel, PublishableModel
from apps.common.versioning import VersionedModel
from apps.core.models import FestivalEdition


class Page(VersionedModel, TimeStampedModel, PublishableModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="pages")
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=200)
    body_md = models.TextField(help_text="Markdown")
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("edition", "slug")]
        ordering = ["slug"]
        permissions = [
            ("publish_page", "Peut publier la page"),
        ]

    def __str__(self):
        return f"{self.edition.year} / {self.slug}"


class FAQItem(VersionedModel, TimeStampedModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="faqs")
    order = models.PositiveIntegerField(default=0)
    question = models.CharField(max_length=240)
    answer_md = models.TextField()

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.edition.year} / #{self.order} {self.question[:40]}"


class News(VersionedModel, TimeStampedModel, PublishableModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="news")
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=280, blank=True)
    body_md = models.TextField()
    cover = models.URLField(blank=True)
    tags = models.JSONField(default=list, blank=True)  # ["annonce","lineup"]

    class Meta:
        ordering = ["-publish_at", "-created_at"]
        permissions = [
            ("publish_news", "Peut publier l'actualité"),
        ]

    def __str__(self):
        return f"{self.edition.year} / {self.title[:40]}"
