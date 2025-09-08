# apps/tickets/signals.py
from __future__ import annotations

from typing import Dict

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from .models import TicketType
from .services import bump_cache_version, dispatch_webhook, recompute_metrics

_PRE: Dict[int, bool] = {}  # pk -> was_on_sale ?


@receiver(pre_save, sender=TicketType)
def remember_old_sale_state(sender, instance: TicketType, **kwargs):
    if instance.pk:
        try:
            prev = sender.objects.get(pk=instance.pk)
            _PRE[instance.pk] = prev.is_on_sale()
        except sender.DoesNotExist:
            _PRE.pop(instance.pk, None)


@receiver(post_save, sender=TicketType)
def emit_sale_window_webhooks_and_recompute_metrics(sender, instance: TicketType, created: bool, **kwargs):
    try:
        old = _PRE.pop(instance.pk, None)
        new = instance.is_on_sale()
        if old is not None and old != new:
            event = "tickets.type.sale_opened" if new else "tickets.type.sale_closed"
            payload = {
                "event": event,
                "ticket_type": {
                    "id": instance.id,
                    "edition": instance.edition_id,
                    "code": instance.code,
                    "name": instance.name,
                    "phase": instance.phase,
                    "sale_start": instance.sale_start.isoformat() if instance.sale_start else None,
                    "sale_end": instance.sale_end.isoformat() if instance.sale_end else None,
                },
            }
            dispatch_webhook(event, payload)
    finally:
        recompute_metrics()


@receiver(post_save, sender=TicketType)
@receiver(post_delete, sender=TicketType)
def cache_version_bump(sender, **kwargs):
    bump_cache_version()
