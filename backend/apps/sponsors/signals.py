# apps/sponsors/signals.py
from __future__ import annotations

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Sponsorship
from .services import _dispatch_webhook, recompute_metrics


@receiver(post_save, sender=Sponsorship)
def sponsorship_changed_recompute(sender, instance: Sponsorship, **kwargs):
    # Recompute gauges on change
    try:
        recompute_metrics()
    except Exception:
        pass


@receiver(post_save, sender=Sponsorship)
def sponsorship_emit_webhook(sender, instance: Sponsorship, created: bool, **kwargs):
    event = "sponsors.sponsorship.created" if created else "sponsors.sponsorship.updated"
    payload = {
        "event": event,
        "sponsorship": {
            "id": instance.id,
            "edition": instance.edition_id,
            "sponsor": instance.sponsor_id,
            "tier": instance.tier_id,
            "visible": instance.visible,
            "amount_eur": float(instance.amount_eur or 0),
        }
    }
    _dispatch_webhook(event, payload)
