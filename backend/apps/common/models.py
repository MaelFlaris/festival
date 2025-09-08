# backend/apps/common/models.py
from django.db import models
from django.utils.text import slugify

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    class Meta:
        abstract = True

class SluggedModel(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    class Meta:
        abstract = True
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:220]
        super().save(*args, **kwargs)

class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    REVIEW = "review", "Relecture"
    PUBLISHED = "published", "Publié"
    ARCHIVED = "archivé", "Archivé"


class PublishableModel(models.Model):
    status = models.CharField(max_length=12, choices=PublishStatus.choices, default=PublishStatus.DRAFT, db_index=True)
    publish_at = models.DateTimeField(null=True, blank=True)
    unpublish_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True

class AddressMixin(models.Model):
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=2, blank=True, help_text="Code ISO-3166-1 alpha-2 (FR, BE, …)")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    class Meta:
        abstract = True
