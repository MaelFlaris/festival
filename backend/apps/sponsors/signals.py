# apps/sponsors/signals.py
from __future__ import annotations

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

import logging
from urllib import request as _urlreq
from urllib.error import URLError, HTTPError
from .models import Sponsorship, Sponsor
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


@receiver(post_save, sender=Sponsor)
def sponsor_logo_check(sender, instance: Sponsor, **kwargs):
    """Quick HEAD/GET to validate sponsor.logo content-type.
    Logs a warning if not image/* or on failure. Non-blocking.
    """
    logger = logging.getLogger(__name__)
    url = instance.logo
    if not url:
        return
    try:
        req = _urlreq.Request(url, method="HEAD")
        resp = _urlreq.urlopen(req, timeout=2)
        ctype = resp.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            logger.warning("Sponsor %s logo URL not image content-type: %s (%s)", instance.id, url, ctype)
    except Exception:
        # Fallback to GET small check
        try:
            req = _urlreq.Request(url, method="GET")
            resp = _urlreq.urlopen(req, timeout=3)
            ctype = resp.headers.get("Content-Type", "")
            if not ctype.startswith("image/"):
                logger.warning("Sponsor %s logo URL not image content-type: %s (%s)", instance.id, url, ctype)
        except Exception as exc:
            logger.warning("Sponsor %s logo check failed for %s: %s", instance.id, url, exc)
