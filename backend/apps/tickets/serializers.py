from rest_framework import serializers
from .models import TicketType


class TicketTypeSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    quota_remaining = serializers.ReadOnlyField()
    is_on_sale = serializers.ReadOnlyField()
    
    class Meta:
        model = TicketType
        fields = (
            "id", "edition", "edition_year", "code", "name", "description",
            "day", "price", "currency", "vat_rate", "quota_total", 
            "quota_reserved", "quota_remaining", "sale_start", "sale_end",
            "is_active", "is_on_sale", "created_at", "updated_at"
        )
