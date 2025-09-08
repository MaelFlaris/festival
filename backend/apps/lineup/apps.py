from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import post_save


class LineupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.lineup"

    def ready(self):
        # Brancher les webhooks/metrics sur la création/màj d'artistes
        from .models import Artist
        from .signals import on_artist_saved  # noqa: F401

        post_save.connect(on_artist_saved, sender=Artist, dispatch_uid="lineup_artist_saved")
