# backend/apps/lineup/serializers.py
from rest_framework import serializers
from .models import Artist, Genre, ArtistAvailability

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id","name","slug","color")

class ArtistSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    class Meta:
        model = Artist
        fields = ("id","name","slug","country","short_bio","picture","banner","website","socials","external_ids","popularity","genres")

class ArtistAvailabilitySerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source="artist.name", read_only=True)
    class Meta:
        model = ArtistAvailability
        fields = ("id","artist","artist_name","date","available","notes","created_at","updated_at")
