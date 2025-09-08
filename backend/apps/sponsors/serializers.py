from __future__ import annotations

from rest_framework import serializers
from .models import SponsorTier, Sponsor, Sponsorship


class SponsorTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorTier
        fields = ("id", "name", "slug", "display_name", "rank", "created_at", "updated_at")


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = ("id", "name", "slug", "website", "logo", "description", "created_at", "updated_at")


class SponsorshipSerializer(serializers.ModelSerializer):
    sponsor_name = serializers.CharField(source="sponsor.name", read_only=True)
    tier_name = serializers.CharField(source="tier.display_name", read_only=True)
    tier_rank = serializers.IntegerField(source="tier.rank", read_only=True)
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)

    class Meta:
        model = Sponsorship
        fields = (
            "id", "edition", "edition_year", "sponsor", "sponsor_name",
            "tier", "tier_name", "tier_rank", "amount_eur", "contract_url",
            "visible", "order", "created_at", "updated_at"
        )