# apps/cms/services.py
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone

from apps.common.services import dispatch_webhook

# ---------------------------------------------------------------------------
# Markdown -> HTML (sanitizé)
# ---------------------------------------------------------------------------

def markdown_to_html_safe(md_text: str) -> str:
    try:
        import markdown as _md
        html = _md.markdown(md_text or "", extensions=["extra", "sane_lists", "toc"])
    except Exception:
        # Fallback ultra-simple
        html = "<p>{}</p>".format((md_text or "").replace("\n", "<br/>"))

    # Sanitization
    try:
        import bleach
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS.union({"p", "pre", "span", "h1","h2","h3","h4","h5","h6","img","hr","br","ul","ol","li","code","blockquote"})
        allowed_attrs = {"a": ["href", "title", "rel"], "img": ["src", "alt", "title"], "*": ["id", "class"]}
        clean = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        # Lien safe
        clean = bleach.linkify(clean)
        return clean
    except Exception:
        return html


# ---------------------------------------------------------------------------
# Publication window helper
# ---------------------------------------------------------------------------

def is_within_publish_window(status: str, publish_at, unpublish_at) -> bool:
    if status != "published":
        return False
    now = timezone.now()
    if publish_at and publish_at > now:
        return False
    if unpublish_at and unpublish_at <= now:
        return False
    return True


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

def dispatch_publish_webhook(instance, old_status: Optional[str], new_status: Optional[str]) -> None:
    """
    Émet un webhook quand on passe en 'published'.
    """
    if new_status != "published":
        return
    evt = None
    from .models import Page, News
    if isinstance(instance, Page):
        evt = "cms.page.published"
        identity = {"edition": instance.edition_id, "slug": instance.slug}
    elif isinstance(instance, News):
        evt = "cms.news.published"
        identity = {"edition": instance.edition_id, "id": instance.id}
    else:
        return
    payload = {
        "event": evt,
        "entity": identity,
        "timestamp": timezone.now().isoformat(),
    }
    dispatch_webhook(evt, payload)

# ---------------------------------------------------------------------------
# Preview tokens (HMAC)
# ---------------------------------------------------------------------------

def _preview_secret() -> str:
    return getattr(settings, "CMS_PREVIEW_SECRET", settings.SECRET_KEY)

def _preview_ttl() -> int:
    return int(getattr(settings, "CMS_PREVIEW_TTL_SECONDS", 900))

def create_preview_token(kind: str, pk: int, extra: Optional[Dict[str, Any]] = None) -> str:
    """
    Génère un token compact: base64url(header).base64url(payload).base64url(sig)
    header: {"alg":"HS256","typ":"PRV"}
    payload: {"k":kind,"id":pk,"exp":timestamp, **extra}
    """
    header = {"alg": "HS256", "typ": "PRV"}
    payload = {"k": kind, "id": int(pk), "exp": int(time.time()) + _preview_ttl()}
    if extra:
        payload.update(extra)

    def b64u(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

    h = b64u(json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    p = b64u(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    signing_input = f"{h}.{p}".encode("ascii")
    sig = hmac.new(_preview_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
    s = b64u(sig)
    return f"{h}.{p}.{s}"

def verify_preview_token(token: str) -> Dict[str, Any]:
    def b64u_decode(s: str) -> bytes:
        pad = "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode(s + pad)

    try:
        h, p, s = token.split(".")
        signing_input = f"{h}.{p}".encode("ascii")
        sig = b64u_decode(s)
        expected = hmac.new(_preview_secret().encode("utf-8"), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            raise ValueError("Invalid signature")
        payload = json.loads(b64u_decode(p).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("Expired token")
        return payload
    except Exception as exc:
        raise ValueError(f"Invalid token: {exc}")

def build_preview_url(base_url: str, token: str) -> str:
    return f"{base_url}?{urlencode({'token': token})}"
