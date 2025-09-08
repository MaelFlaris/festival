# apps/authx/services.py
from __future__ import annotations

from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model

from apps.common.services import dispatch_webhook
from .models import UserProfile

User = get_user_model()


def get_or_create_profile(user: User) -> UserProfile:
    prof, _ = UserProfile.objects.get_or_create(user=user)
    return prof


def hydrate_profile_from_claims(user: User, claims: Dict[str, Any]) -> None:
    """
    Hydrate le profil à partir de claims OIDC/OAuth.
    Clés reconnues (si présentes): name, picture, locale, given_name, family_name.
    """
    if not claims:
        return
    profile = get_or_create_profile(user)
    # Hydratation douce (n’écrase pas si vide/absent)
    name = claims.get("name") or " ".join(filter(None, [claims.get("given_name"), claims.get("family_name")])).strip()
    if name and not profile.display_name:
        profile.display_name = name[:120]
    if claims.get("picture") and not profile.avatar:
        profile.avatar = str(claims["picture"])[:2000]
    # On peut conserver la locale en préférence
    loc = claims.get("locale")
    if loc:
        prefs = dict(profile.preferences or {})
        prefs.setdefault("i18n", {})["locale"] = str(loc)
        profile.preferences = prefs
    profile.full_clean()
    profile.save()


def hydrate_profile_from_request(user: User, request) -> None:
    """
    Tentatives non-intrusives:
    - En-têtes HTTP injectés par un proxy/IdP (X-Authx-*)
    - Session OIDC si présente (clé 'oidc_id_token' / 'oidc_userinfo'…)
    """
    claims: Dict[str, Any] = {}

    # 1) En-têtes HTTP (reverse proxy / IdP)
    meta = getattr(request, "META", {}) or {}
    hdr = lambda k: meta.get(k) or meta.get(k.replace("-", "_"))
    if hdr("HTTP_X_AUTHX_NAME"):
        claims["name"] = hdr("HTTP_X_AUTHX_NAME")
    if hdr("HTTP_X_AUTHX_PICTURE"):
        claims["picture"] = hdr("HTTP_X_AUTHX_PICTURE")
    if hdr("HTTP_X_AUTHX_LOCALE"):
        claims["locale"] = hdr("HTTP_X_AUTHX_LOCALE")

    # 2) Session OIDC opportuniste
    sess = getattr(request, "session", None)
    if sess:
        for k in ("oidc_id_token", "oidc_userinfo", "social_auth_user_details"):
            if k in sess and isinstance(sess[k], dict):
                claims.update(sess[k] or {})

    if claims:
        hydrate_profile_from_claims(user, claims)


def emit_profile_updated_webhook(profile: UserProfile, changed_fields: Optional[list[str]] = None) -> None:
    payload = {
        "event": "authx.profile.updated",
        "user_id": profile.user_id,
        "profile_id": profile.id,
        "changed_fields": changed_fields or [],
    }
    dispatch_webhook("authx.profile.updated", payload)
