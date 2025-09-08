from __future__ import annotations

from rest_framework import serializers

from .models import Slot


class SlotSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source="artist.name", read_only=True)
    stage_name = serializers.CharField(source="stage.name", read_only=True)
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Slot
        fields = (
            "id", "edition", "edition_year", "stage", "stage_name",
            "artist", "artist_name", "day", "start_time", "end_time",
            "status", "is_headliner", "setlist_urls", "tech_rider",
            "notes", "duration_minutes", "created_at", "updated_at"
        )