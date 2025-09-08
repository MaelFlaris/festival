from rest_framework import serializers
from .models import FestivalEdition, Venue, Stage, Contact


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = (
            "id", "name", "description", "address", "city", 
            "postal_code", "country", "latitude", "longitude", 
            "map_url", "created_at", "updated_at"
        )


class StageSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source="venue.name", read_only=True)
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    
    class Meta:
        model = Stage
        fields = (
            "id", "name", "edition", "edition_year", "venue", 
            "venue_name", "covered", "capacity", "created_at", "updated_at"
        )


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id", "edition", "type", "label", "email", 
            "phone", "notes", "created_at", "updated_at"
        )


class FestivalEditionSerializer(serializers.ModelSerializer):
    stages = StageSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    
    class Meta:
        model = FestivalEdition
        fields = (
            "id", "name", "slug", "year", "start_date", "end_date", 
            "tagline", "hero_image", "is_active", "stages", "contacts",
            "created_at", "updated_at"
        )
