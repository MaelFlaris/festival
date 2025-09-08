# apps/schedule/signals.py
from __future__ import annotations

from typing import Dict

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from apps.common.services import dispatch_webhook
from .metrics import SLOTS_STATUS_TOTAL
from .models import Slot, SlotStatus

_PRE: Dict[int, str] = {}  # cache old status


@receiver(pre_save, sender=Slot)
def slot_pre_save_cache(sender, instance: Slot, **kwargs):
    if instance.pk:
        try:
            _PRE[instance.pk] = sender.objects.only("status").get(pk=instance.pk).status
        except sender.DoesNotExist:
            _PRE.pop(instance.pk, None)


@receiver(post_save, sender=Slot)
def slot_post_save_emit(sender, instance: Slot, created: bool, **kwargs):
    status = instance.status
    SLOTS_STATUS_TOTAL.labels(status=status).inc()

    event = None
    if created:
        event = "schedule.slot.created"
    else:
        old = _PRE.pop(instance.pk, None)
        if old != status:
            if status == SlotStatus.CANCELED:
                event = "schedule.slot.canceled"
            else:
                event = "schedule.slot.updated"

    if event:
        payload = {
            "event": event,
            "slot": {
                "id": instance.id,
                "edition": instance.edition_id,
                "stage": instance.stage_id,
                "artist": instance.artist_id,
                "day": str(instance.day),
                "start": str(instance.start_time),
                "end": str(instance.end_time),
                "status": instance.status,
            }
        }
        try:
            dispatch_webhook(event, payload)
        except Exception:
            pass
