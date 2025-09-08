# backend/apps/lineup/models.py
from __future__ import annotations

from typing import Dict

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel, SluggedModel
from apps.common.validators import validate_country_iso2
from apps.common.versioning import VersionedModel


class Genre(VersionedModel, TimeStampedModel, SluggedModel):
    color = models.CharField(max_length=7, blank=True, help_text="#RRGGBB")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Artist(VersionedModel, TimeStampedModel, SluggedModel):
    country = models.CharField(max_length=2, blank=True, validators=[validate_country_iso2],
                               help_text="ISO-3166-1 alpha-2")
    short_bio = models.TextField(blank=True)
    long_bio = models.TextField(blank=True)
    picture = models.CharField(max_length=500, blank=True)
    banner = models.CharField(max_length=500, blank=True)
    website = models.CharField(max_length=500, blank=True)
    socials = models.JSONField(default=dict, blank=True,
                               help_text='{"instagram":"", "youtube":"", "spotify":""}')
    external_ids = models.JSONField(default=dict, blank=True,
                                    help_text='{"musicbrainz":"", "spotify":"..."}')
    genres = models.ManyToManyField(Genre, related_name="artists", blank=True)
    popularity = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        indexes = [models.Index(fields=["popularity"])]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        # Normalisation ISO2
        if self.country:
            self.country = (self.country or "").upper()

        # Valider les clés JSON autorisées
        allowed_ext = {"spotify", "musicbrainz"}
        if self.external_ids:
            for k in self.external_ids.keys():
                if k not in allowed_ext:
                    raise ValidationError({"external_ids": f"Unsupported key '{k}'"})

        allowed_socials = {"instagram", "youtube", "spotify", "facebook", "x", "tiktok"}
        if self.socials:
            for k in self.socials.keys():
                if k not in allowed_socials:
                    raise ValidationError({"socials": f"Unsupported key '{k}'"})


class ArtistAvailability(VersionedModel, TimeStampedModel):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="availabilities")
    date = models.DateField()
    available = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [("artist", "date")]
        ordering = ["date"]

    def __str__(self):
        return f"{self.artist.name} @ {self.date} ({'OK' if self.available else 'NOK'})"
