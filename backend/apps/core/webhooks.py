import json
from typing import Any, Dict, Optional
from django.conf import settings

def post_webhook(event: str, payload: Dict[str, Any]) -> None:
    """
    Envoi best-effort d’un webhook si configuré dans settings.WEBHOOKS[event].
    """
    url = getattr(settings, 'WEBHOOKS', {}).get(event)
    if not url:
        return
    try:
        import requests
        headers = {'Content-Type': 'application/json', 'X-Event': event}
        requests.post(url, data=json.dumps(payload), headers=headers, timeout=3.0)
    except Exception:
        # no-op: on ne casse pas la requête métier
        pass
