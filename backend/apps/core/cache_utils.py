from typing import Iterable, Optional
from django.core.cache import cache

def purge_public_cache(keys: Optional[Iterable[str]] = None) -> None:
    """
    Purge ciblée si possible. À défaut, clear().
    On tente delete_pattern si backend le supporte (ex: django-redis).
    """
    try:
        if keys:
            for k in keys:
                try:
                    cache.delete(k)
                except Exception:
                    pass
        # Si backend supporte delete_pattern, purger le namespace public
        try:
            cache.delete_pattern('public:*')  # type: ignore[attr-defined]
        except Exception:
            pass
    except Exception:
        # Fallback bourrin (facultatif)
        try:
            cache.clear()
        except Exception:
            pass
