# backend/apps/core/models.py
from django.db import models
from apps.common.models import TimeStampedModel, SluggedModel, AddressMixin

class FestivalEdition(TimeStampedModel, SluggedModel):
    year = models.PositiveIntegerField(db_index=True, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    tagline = models.CharField(max_length=200, blank=True)
    # Champs i18n (JSON mapping {"fr": "Nom", "en": "Name"})
    name_i18n = models.JSONField(default=dict, blank=True, help_text="Traductions du nom")
    tagline_i18n = models.JSONField(default=dict, blank=True, help_text="Traductions de l'accroche")
    hero_image = models.URLField(blank=True)
    is_active = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-year"]
        indexes = [models.Index(fields=["start_date", "end_date"])]

    def __str__(self):
        return f"Edition {self.year}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date < self.start_date:
            raise ValidationError("end_date < start_date")

class Venue(TimeStampedModel, AddressMixin):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    map_url = models.URLField(blank=True)
    def __str__(self):
        return self.name

class Stage(TimeStampedModel):
    # edition/venue peuvent être omis lors de la création (tests); l'édition active est utilisée par défaut.
    edition = models.ForeignKey(
        FestivalEdition,
        on_delete=models.CASCADE,
        related_name="stages",
        null=True,
        blank=True,
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="stages",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    covered = models.BooleanField(default=False)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [("edition", "name")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.edition.year})"

    def save(self, *args, **kwargs):
        # Utilise l'édition active par défaut si non fournie
        if self.edition_id is None:
            active = FestivalEdition.objects.filter(is_active=True).first()
            if active:
                self.edition = active
        super().save(*args, **kwargs)

class Contact(TimeStampedModel):
    class ContactType(models.TextChoices):
        PRESS = "press", "Presse"
        ARTIST_REL = "artist_rel", "Relations artistes"
        PUBLIC = "public", "Public"
        TECH = "tech", "Technique"
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="contacts")
    type = models.CharField(max_length=20, choices=ContactType.choices)
    label = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    notes = models.TextField(blank=True)
    class Meta:
        unique_together = [("edition", "type", "label")]
