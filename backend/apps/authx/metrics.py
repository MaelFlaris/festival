# apps/authx/metrics.py
from __future__ import annotations

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None

if Counter:
    PROFILE_UPDATES_TOTAL = Counter(
        "authx_profile_updates_total",
        "Total des mises à jour de profils utilisateur",
        ["field"],
    )
else:  # Fallback no-op
    class _Noop:
        def labels(self, *args, **kwargs):
            return self
        def inc(self, *args, **kwargs):
            return None
    PROFILE_UPDATES_TOTAL = _Noop()
