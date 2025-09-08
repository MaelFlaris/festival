# backend/apps/sponsors/models.py
from django.db import models
from apps.common.models import TimeStampedModel, SluggedModel
from apps.core.models import FestivalEdition

class SponsorTier(TimeStampedModel, SluggedModel):
    rank = models.PositiveIntegerField(default=100, db_index=True)  # 1=plus haut
    display_name = models.CharField(max_length=120)
    class Meta:
        ordering = ["rank"]

class Sponsor(TimeStampedModel, SluggedModel):
    website = models.URLField(blank=True)
    logo = models.URLField(blank=True)
    description = models.TextField(blank=True)

class Sponsorship(TimeStampedModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="sponsorships")
    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name="sponsorships")
    tier = models.ForeignKey(SponsorTier, on_delete=models.PROTECT, related_name="sponsorships")
    amount_eur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    contract_url = models.URLField(blank=True)
    visible = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("edition", "sponsor")]
        ordering = ["tier__rank", "order", "sponsor__name"]
