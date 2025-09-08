# backend/apps/lineup/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.models import TimeStampedModel, SluggedModel

class Genre(TimeStampedModel, SluggedModel):
    color = models.CharField(max_length=7, blank=True, help_text="#RRGGBB")
    class Meta:
        ordering = ["name"]

class Artist(TimeStampedModel, SluggedModel):
    country = models.CharField(max_length=2, blank=True, help_text="ISO-3166-1 alpha-2")
    short_bio = models.TextField(blank=True)
    long_bio = models.TextField(blank=True)
    picture = models.URLField(blank=True)
    banner = models.URLField(blank=True)
    website = models.URLField(blank=True)
    socials = models.JSONField(default=dict, blank=True, help_text='{"instagram":"", "youtube":"", "spotify":""}')
    external_ids = models.JSONField(default=dict, blank=True, help_text='{"musicbrainz":"", "spotify":"..."}')
    genres = models.ManyToManyField(Genre, related_name="artists", blank=True)
    popularity = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        indexes = [models.Index(fields=["popularity"])]

    def __str__(self):
        return self.name

class ArtistAvailability(TimeStampedModel):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name="availabilities")
    date = models.DateField()
    available = models.BooleanField(default=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [("artist", "date")]
        ordering = ["date"]
