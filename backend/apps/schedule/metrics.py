# apps/schedule/metrics.py
from __future__ import annotations

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None

if Counter:
    SLOTS_STATUS_TOTAL = Counter(
        "schedule_slots_status_total",
        "Total de slots par statut (créations/màj)",
        ["status"],  # tentative | confirmed | canceled
    )
    CONFLICTS_TOTAL = Counter(
        "schedule_conflicts_detected_total",
        "Total des conflits détectés (API create/update ou endpoint conflicts)",
    )
else:
    class _Noop:
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): return None
    SLOTS_STATUS_TOTAL = _Noop()
    CONFLICTS_TOTAL = _Noop()
