# apps/lineup/signals.py
from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from .metrics import ARTISTS_TOTAL
from .models import Artist
from .services import emit_artist_webhook


@receiver(post_save, sender=Artist)
def on_artist_saved(sender, instance: Artist, created: bool, **kwargs):
    if created:
        ARTISTS_TOTAL.labels(event="created").inc()
        emit_artist_webhook("lineup.artist.created", instance)
    else:
        ARTISTS_TOTAL.labels(event="updated").inc()
        emit_artist_webhook("lineup.artist.updated", instance)
