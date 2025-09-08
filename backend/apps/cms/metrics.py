# apps/cms/metrics.py
from __future__ import annotations

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None

if Counter:
    PUBLISHED_TOTAL = Counter(
        "cms_published_entities_total",
        "Total publications CMS",
        ["type"],
    )
    PREVIEW_REQUESTS_TOTAL = Counter(
        "cms_preview_requests_total",
        "Total de requêtes de prévisualisation CMS",
        ["action"],  # "create" | "resolve" | "invalid"
    )
else:
    class _Noop:
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): return None
    PUBLISHED_TOTAL = _Noop()
    PREVIEW_REQUESTS_TOTAL = _Noop()
