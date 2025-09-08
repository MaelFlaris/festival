# apps/tickets/services.py
from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional

from django.core.cache import cache
from django.db.models import F, Sum

from .metrics import ON_SALE_TOTAL_GAUGE, QUOTA_REMAINING_SUM_GAUGE
from .models import TicketType


# --- Webhook dispatch (fallback no-op) --------------------------------------

def dispatch_webhook(event: str, payload: dict) -> None:
    try:
        from apps.common.services import dispatch_webhook as _dw  # type: ignore
    except Exception:
        _dw = None
    if _dw:
        try:
            _dw(event, payload)
        except Exception:
            pass


# --- Cache versioning -------------------------------------------------------

CACHE_VERSION_KEY = "tickets:on_sale:version"

def bump_cache_version():
    try:
        v = cache.get(CACHE_VERSION_KEY, 0)
        cache.set(CACHE_VERSION_KEY, int(v) + 1, None)
    except Exception:
        pass

def current_cache_version() -> int:
    try:
        return int(cache.get(CACHE_VERSION_KEY, 0))
    except Exception:
        return 0


# --- Metrics recompute ------------------------------------------------------

def recompute_metrics():
    qs = TicketType.objects.all()
    on_sale = [t for t in qs if t.is_on_sale()]
    ON_SALE_TOTAL_GAUGE.set(len(on_sale))
    QUOTA_REMAINING_SUM_GAUGE.set(sum(int(t.quota_remaining) for t in on_sale))
