# apps/common/services.py
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import logging
from typing import Iterable, Optional
from urllib import request as _urlreq, error as _urlerr
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Model
from django.utils.text import slugify


# ---------------------------------------------------------------------------
# Slug util
# ---------------------------------------------------------------------------

def unique_slugify(
    instance: Model,
    value: str,
    slug_field_name: str = "slug",
    max_length: int = 220,
) -> str:
    """
    Génère un slug unique pour le modèle de l'instance :
    - slugify(value)
    - troncature <= max_length
    - suffixes -2, -3, ... en cas de collision
    """
    base = slugify(value or "")
    base = base[:max_length] if base else ""

    if not base:
        base = "item"

    model_cls = instance.__class__
    slug_field = slug_field_name

    def exists(candidate: str) -> bool:
        qs = model_cls.objects.filter(**{slug_field: candidate})
        if instance.pk:
            qs = qs.exclude(pk=instance.pk)
        return qs.exists()

    candidate = base
    if not exists(candidate):
        return candidate

    i = 2
    while True:
        suffix = f"-{i}"
        cut = max_length - len(suffix)
        trimmed = base[:cut]
        candidate = f"{trimmed}{suffix}"
        if not exists(candidate):
            return candidate
        i += 1


# ---------------------------------------------------------------------------
# ISO-3166-1 alpha-2 utils
# ---------------------------------------------------------------------------

ISO2_COUNTRIES = {
    # Europe
    "FR","BE","DE","ES","IT","NL","PT","CH","AT","LU","IE","GB","SE","NO","FI","DK","PL","CZ","SK","HU","RO","BG","GR","HR","SI","EE","LV","LT","IS","MT","CY","UA","RU","BA","RS","ME","MK","AL","XK","LI","MC","AD","SM","VA",
    # Americas
    "US","CA","MX","AR","BR","CL","CO","PE","VE","UY","BO","PY","EC","CR","PA","GT","SV","HN","NI","CU","DO","HT","BS","BB","JM","TT",
    # Africa
    "ZA","MA","DZ","TN","EG","NG","GH","CI","SN","CM","KE","ET","TZ","UG","RW","BJ","BF","ML","NE","TD","SD","SS","ZM","ZW","MZ","AO",
    # Middle East / Asia
    "TR","IL","PS","SA","AE","QA","KW","BH","OM","IR","IQ","JO","LB","SY","YE","AM","AZ","GE","KZ","KG","TJ","TM","AF","PK","IN","BD","LK","NP","BT","MV",
    # East / South-East Asia & Oceania
    "CN","JP","KR","TW","HK","MO","MN","SG","MY","TH","VN","LA","KH","PH","ID","BN","AU","NZ","PG","FJ",
}

def normalize_iso2(country: Optional[str]) -> Optional[str]:
    if not country:
        return country
    return country.upper()

def is_valid_iso2(country: Optional[str]) -> bool:
    if not country:
        return True
    up = country.upper()
    if len(up) != 2:
        return False
    return up in ISO2_COUNTRIES


# ---------------------------------------------------------------------------
# Geo utils (geohash, haversine)
# ---------------------------------------------------------------------------

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

def geohash_encode(lat: float, lon: float, precision: int = 9) -> str:
    """
    Encode lat/lon en geohash base32.
    Implémentation légère, suffisante pour indexation simple.
    """
    # Bornes initiales
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    hash_str = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    even = True

    while len(hash_str) < precision:
        if even:
            mid = sum(lon_interval) / 2
            if lon > mid:
                ch |= bits[bit]
                lon_interval[0] = mid
            else:
                lon_interval[1] = mid
        else:
            mid = sum(lat_interval) / 2
            if lat > mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid
        even = not even
        if bit < 4:
            bit += 1
        else:
            hash_str.append(_BASE32[ch])
            bit = 0
            ch = 0

    return "".join(hash_str)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance grand-cercle en kilomètres."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlbd = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlbd / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


# ---------------------------------------------------------------------------
# Webhooks (optionnels)
# ---------------------------------------------------------------------------

def _build_signature(secret: str, body: bytes) -> str:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return "sha256=" + base64.b16encode(mac).decode("ascii").lower()

def dispatch_webhook(event: str, payload: dict) -> None:
    """
    Envoie le payload vers chaque URL de `settings.COMMON_WEBHOOK_URLS`.
    - Ajoute en-têtes: Content-Type, X-Common-Event, X-Common-Signature (si secret).
    - Best-effort, exceptions capturées.
    """
    logger = logging.getLogger(__name__)
    urls: Iterable[str] = getattr(settings, "COMMON_WEBHOOK_URLS", []) or []
    if not urls:
        return

    data = json.dumps(payload).encode("utf-8")
    secret = getattr(settings, "COMMON_WEBHOOK_SECRET", None)
    signature = _build_signature(secret, data) if secret else None
    timeout = int(getattr(settings, "COMMON_WEBHOOK_TIMEOUT", 5) or 5)

    for url in urls:
        # Validate scheme http/https
        try:
            scheme = (urlparse(url).scheme or "").lower()
        except Exception:
            scheme = ""
        if scheme not in {"http", "https"}:
            logger.warning("dispatch_webhook: ignored URL with invalid scheme: %s", url)
            continue

        req = _urlreq.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Common-Event", event)
        if signature:
            req.add_header("X-Common-Signature", signature)
        # One retry on transient failure
        attempts = 2
        for i in range(attempts):
            try:
                _urlreq.urlopen(req, timeout=timeout)
                break
            except Exception as exc:  # pragma: no cover (errors are environment dependent)
                if i == attempts - 1:
                    logger.warning("dispatch_webhook failed for %s: %s", url, exc)
                # Never raise to caller
                continue
