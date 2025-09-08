# backend/apps/schedule/models.py
from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import TimeStampedModel
from apps.core.models import FestivalEdition, Stage
from apps.lineup.models import Artist

class SlotStatus(models.TextChoices):
    TENTATIVE = "tentative", "Provisoire"
    CONFIRMED = "confirmed", "Confirmé"
    CANCELED = "canceled", "Annulé"

class Slot(TimeStampedModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="slots")
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name="slots")
    artist = models.ForeignKey(Artist, on_delete=models.PROTECT, related_name="slots")
    day = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=SlotStatus.choices, default=SlotStatus.TENTATIVE, db_index=True)
    is_headliner = models.BooleanField(default=False, db_index=True)
    setlist_urls = models.JSONField(default=list, blank=True)  # ["https://..."]
    tech_rider = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["day", "stage__name", "start_time"]
        indexes = [models.Index(fields=["edition", "day", "stage", "start_time"])]

    def __str__(self):
        return f"{self.artist.name} @ {self.stage.name} {self.day} {self.start_time}-{self.end_time}"

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("end_time doit être > start_time")
        if not (self.edition.start_date <= self.day <= self.edition.end_date):
            raise ValidationError("day doit être compris dans l’édition")
