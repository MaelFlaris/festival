# backend/apps/authx/models.py
from __future__ import annotations

import json
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.common.versioning import VersionedModel


def _max_pref_bytes_default() -> int:
    # Paramétrable via settings.AUTHX_PREFERENCES_MAX_BYTES (par défaut 32 KiB)
    return getattr(settings, "AUTHX_PREFERENCES_MAX_BYTES", 32 * 1024)


class UserProfile(VersionedModel, TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=120, blank=True)
    avatar = models.URLField(blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    # Consents RGPD horodatés : dict[str, list[events]]
    # event: {"granted": bool, "at": iso8601, "source": str}
    consents = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user"], name="uniq_authx_profile_user"),
        ]

    def __str__(self):
        return self.display_name or self.user.get_username()

    # ---- Validation & helpers ------------------------------------------------

    def clean(self):
        super().clean()
        # Taille max préférences (approx en bytes sur JSON UTF-8)
        try:
            raw = json.dumps(self.preferences, ensure_ascii=False).encode("utf-8")
        except Exception as exc:  # JSON pas sérialisable
            raise ValidationError({"preferences": f"Invalid JSON: {exc}"})
        max_bytes = _max_pref_bytes_default()
        if len(raw) > max_bytes:
            raise ValidationError({"preferences": f"Size exceeds {max_bytes} bytes"})

    def set_consent(self, key: str, granted: bool, source: str = "api") -> None:
        """Ajoute un événement de consentement horodaté."""
        now = timezone.now().isoformat()
        data = {"granted": bool(granted), "at": now, "source": source}
        cons = dict(self.consents or {})
        history = list(cons.get(key, []))
        history.append(data)
        cons[key] = history
        self.consents = cons

    def get_last_consent(self, key: str) -> Optional[Dict[str, Any]]:
        history = (self.consents or {}).get(key) or []
        return history[-1] if history else None

    def last_consents_snapshot(self) -> Dict[str, Any]:
        """Résumé compact (clé -> {granted, at})."""
        out: Dict[str, Any] = {}
        for k, lst in (self.consents or {}).items():
            if lst:
                out[k] = {"granted": bool(lst[-1].get("granted")), "at": lst[-1].get("at")}
        return out
