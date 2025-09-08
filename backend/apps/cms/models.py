# backend/apps/cms/models.py
from django.db import models
from apps.common.models import TimeStampedModel, PublishableModel
from apps.core.models import FestivalEdition

class Page(TimeStampedModel, PublishableModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="pages")
    slug = models.SlugField(max_length=100)
    title = models.CharField(max_length=200)
    body_md = models.TextField(help_text="Markdown")
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [("edition", "slug")]
        ordering = ["slug"]

class FAQItem(TimeStampedModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="faqs")
    order = models.PositiveIntegerField(default=0)
    question = models.CharField(max_length=240)
    answer_md = models.TextField()

    class Meta:
        ordering = ["order", "id"]

class News(TimeStampedModel, PublishableModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="news")
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=280, blank=True)
    body_md = models.TextField()
    cover = models.URLField(blank=True)
    tags = models.JSONField(default=list, blank=True)  # ["annonce","lineup"]

    class Meta:
        ordering = ["-publish_at", "-created_at"]
