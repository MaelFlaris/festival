from __future__ import annotations

from rest_framework import serializers
from .models import TicketType


class TicketTypeSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    quota_remaining = serializers.ReadOnlyField()
    is_on_sale = serializers.SerializerMethodField()
    price_net = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    price_vat_amount = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = TicketType
        fields = (
            "id", "edition", "edition_year", "code", "name", "description",
            "day", "phase", "price", "price_net", "price_vat_amount",
            "currency", "vat_rate", "quota_total", "quota_reserved",
            "quota_by_channel", "reserved_by_channel", "quota_remaining",
            "sale_start", "sale_end", "is_active", "is_on_sale",
            "created_at", "updated_at"
        )

    def get_is_on_sale(self, obj: TicketType) -> bool:
        return obj.is_on_sale()
