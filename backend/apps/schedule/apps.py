from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save


class ScheduleConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.schedule"

    def ready(self):
        # Brancher les signaux (webhooks + métriques + détection d'annulation)
        from .models import Slot
        from .signals import slot_pre_save_cache, slot_post_save_emit  # noqa: F401

        pre_save.connect(slot_pre_save_cache, sender=Slot, dispatch_uid="schedule_slot_pre_save")
        post_save.connect(slot_post_save_emit, sender=Slot, dispatch_uid="schedule_slot_post_save")
