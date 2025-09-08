# apps/common/serializers.py
from __future__ import annotations

from rest_framework import serializers
from .services import is_valid_iso2, normalize_iso2


class AddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=120, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=2, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)

    def validate_country(self, value: str):
        if value == "":
            return value
        value = normalize_iso2(value)
        if not is_valid_iso2(value):
            raise serializers.ValidationError("Invalid ISO-3166-1 alpha-2 country code")
        return value
