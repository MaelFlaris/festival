# apps/common/versioning.py
from __future__ import annotations

from django.db import models

try:
    from simple_history.models import HistoricalRecords
except Exception:  # pragma: no cover
    HistoricalRecords = None


class VersionedModel(models.Model):
    """
    Intègre django-simple-history si disponible.
    Héritez de cette classe dans vos modèles concrets.
    """
    if HistoricalRecords:
        history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True
