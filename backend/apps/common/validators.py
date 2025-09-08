# apps/common/validators.py
from __future__ import annotations

from django.core.exceptions import ValidationError
from .services import is_valid_iso2, normalize_iso2


def validate_country_iso2(value):
    if value:
        code = normalize_iso2(value)
        if not is_valid_iso2(code):
            raise ValidationError("Invalid ISO-3166-1 alpha-2 country code")
