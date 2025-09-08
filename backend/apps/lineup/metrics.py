# apps/lineup/metrics.py
from __future__ import annotations

try:
    from prometheus_client import Counter
except Exception:  # pragma: no cover
    Counter = None

if Counter:
    ARTISTS_TOTAL = Counter(
        "lineup_artists_total",
        "Total artistes (créations/mises à jour)",
        ["event"],  # created | updated
    )
    IMPORT_JOBS_TOTAL = Counter(
        "lineup_import_jobs_total",
        "Total des jobs d'import lineup",
        ["source"],  # spotify | musicbrainz | other
    )
else:
    class _Noop:
        def labels(self, *args, **kwargs): return self
        def inc(self, *args, **kwargs): return None
    ARTISTS_TOTAL = _Noop()
    IMPORT_JOBS_TOTAL = _Noop()
