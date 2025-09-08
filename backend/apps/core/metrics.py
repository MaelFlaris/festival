from typing import Optional

def set_active_edition_metric(year: Optional[int]) -> None:
    """
    Expose gauge core_active_edition=1 avec label year, si prometheus_client dispo.
    Sinon no-op.
    """
    try:
        from prometheus_client import Gauge
        gauge = Gauge('core_active_edition', 'Active edition flag', ['year'])
        # reset: set 0 on previous is not trivial sans registry, on simplifie:
        if year is not None:
            gauge.labels(year=str(year)).set(1)
    except Exception:
        # Optionnel: tenter statsd/datadog
        try:
            from django.conf import settings
            import statsd
            c = statsd.StatsClient(
                host=getattr(settings, 'STATSD_HOST', 'localhost'),
                port=getattr(settings, 'STATSD_PORT', 8125),
                prefix='festival'
            )
            if year is not None:
                c.gauge('core_active_edition', 1, tags=[f"year:{year}"])
        except Exception:
            pass
