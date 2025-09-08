from rest_framework import serializers
from .models import FestivalEdition, Venue, Stage, Contact
from .services import activate_edition, get_edition_summary


# -------------------------------------------------------------------
# Helpers i18n
# -------------------------------------------------------------------
def _pick_lang(mapping, request):
    if not isinstance(mapping, dict):
        return None
    # 1) ?lang=xx  2) Accept-Language  3) 'fr'  4) première valeur non vide
    lang = (request and request.query_params.get('lang')) or None
    if not lang and request:
        al = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if al:
            lang = al.split(',')[0].split('-')[0].strip() or None
    for key in filter(None, [lang, 'fr']):
        if key in mapping and mapping[key]:
            return mapping[key]
    return next((v for v in mapping.values() if v), None)

# -------------------------------------------------------------------
# Serializers élémentaires (définis AVANT FestivalEditionSerializer)
# -------------------------------------------------------------------
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

    # Champs i18n (CRUD brut)
    name_i18n = serializers.JSONField(required=False)
    tagline_i18n = serializers.JSONField(required=False)

    # Lecture pratique localisée
    name_localized = serializers.SerializerMethodField()
    tagline_localized = serializers.SerializerMethodField()

    class Meta:
        model = FestivalEdition
        fields = (
            "id", "name", "name_i18n", "name_localized",
            "slug", "year", "start_date", "end_date",
            "tagline", "tagline_i18n", "tagline_localized",
            "hero_image", "is_active", "stages", "contacts",
            "created_at", "updated_at"
        )

    def get_name_localized(self, obj):
        req = self.context.get('request')
        return _pick_lang(getattr(obj, 'name_i18n', {}) or {}, req) or obj.name

    def get_tagline_localized(self, obj):
        req = self.context.get('request')
        return _pick_lang(getattr(obj, 'tagline_i18n', {}) or {}, req) or obj.tagline

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date < start_date"})
        return attrs

    def create(self, validated_data):
        instance = super().create(validated_data)
        if instance.is_active:
            instance = activate_edition(instance)
        return instance

    def update(self, instance, validated_data):
        new_active = validated_data.pop("is_active", None) if "is_active" in validated_data else None
        instance = super().update(instance, validated_data)
        if new_active is True:
            instance = activate_edition(instance)
        elif new_active is False and instance.is_active:
            instance.is_active = False
            instance.save(update_fields=["is_active"])
        return instance
