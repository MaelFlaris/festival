# apps/tickets/metrics.py
from __future__ import annotations

try:
    from prometheus_client import Gauge
except Exception:  # pragma: no cover
    Gauge = None

if Gauge:
    ON_SALE_TOTAL_GAUGE = Gauge(
        "tickets_on_sale_total",
        "Nombre de types de billets actuellement en vente",
    )
    QUOTA_REMAINING_SUM_GAUGE = Gauge(
        "tickets_quota_remaining_sum",
        "Somme des quotas restants sur les billets en vente",
    )
else:
    class _Noop:
        def set(self, *args, **kwargs): return None
    ON_SALE_TOTAL_GAUGE = _Noop()
    QUOTA_REMAINING_SUM_GAUGE = _Noop()
