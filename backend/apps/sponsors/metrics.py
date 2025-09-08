# apps/sponsors/metrics.py
from __future__ import annotations

try:
    from prometheus_client import Gauge
except Exception:  # pragma: no cover
    Gauge = None

if Gauge:
    VISIBLE_TOTAL = Gauge(
        "sponsors_visible_total",
        "Nombre de sponsors visibles par tier",
        ["tier_slug"],
    )
    AMOUNT_SUM_EUR = Gauge(
        "sponsorship_amount_sum_eur",
        "Somme des montants par édition (EUR)",
        ["edition"],
    )
else:
    class _Noop:
        def labels(self, *args, **kwargs): return self
        def set(self, *args, **kwargs): return None
    VISIBLE_TOTAL = _Noop()
    AMOUNT_SUM_EUR = _Noop()
