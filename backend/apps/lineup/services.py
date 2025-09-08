# apps/lineup/services.py
from __future__ import annotations

import requests
from typing import Dict, Iterable, List, Optional, Tuple

from django.conf import settings

from apps.common.services import dispatch_webhook
from .metrics import ARTISTS_TOTAL, IMPORT_JOBS_TOTAL
from .models import Artist, Genre


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

def emit_artist_webhook(event: str, artist: Artist) -> None:
    payload = {
        "event": event,
        "artist": {
            "id": artist.id,
            "name": artist.name,
            "slug": artist.slug,
            "country": artist.country,
            "popularity": artist.popularity,
        },
    }
    dispatch_webhook(event, payload)


# ---------------------------------------------------------------------------
# Compatibilité (simple, explicable)
# ---------------------------------------------------------------------------

def compute_compatibility(artist: Artist, target_genre_ids: Iterable[int]) -> int:
    """
    Score [0..100] = 70% Jaccard(artist.genres, target_genres) + 30% Popularité/100
    """
    artist_gids = set(artist.genres.values_list("id", flat=True))
    target = set(int(g) for g in target_genre_ids if g)
    if not target:
        base = 0.0
    else:
        inter = len(artist_gids & target)
        uni = len(artist_gids | target) or 1
        base = inter / uni
    pop = (artist.popularity or 0) / 100.0
    score = 0.7 * base + 0.3 * pop
    return int(round(score * 100))


# ---------------------------------------------------------------------------
# Imports externes (best-effort)
# ---------------------------------------------------------------------------

def enrich_from_spotify(artist: Artist, spotify_id: str, token: Optional[str] = None) -> Dict:
    """
    Met à jour l'artiste depuis Spotify API: name, images[0], popularity.
    Requiert un token Bearer; si absent → no-op.
    """
    token = token or getattr(settings, "SPOTIFY_TOKEN", None)
    if not token or not spotify_id:
        return {"updated": False, "reason": "missing_token_or_id"}

    url = f"https://api.spotify.com/v1/artists/{spotify_id}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers, timeout=6)
    r.raise_for_status()
    data = r.json()

    changed = False
    if data.get("name") and data["name"] != artist.name:
        artist.name = data["name"]; changed = True
    if data.get("images"):
        pic = data["images"][0].get("url")
        if pic and pic != artist.picture:
            artist.picture = pic; changed = True
    if "popularity" in data:
        p = int(data["popularity"]) if data["popularity"] is not None else artist.popularity
        p = max(0, min(100, p))
        if p != artist.popularity:
            artist.popularity = p; changed = True

    ext = dict(artist.external_ids or {})
    if spotify_id and ext.get("spotify") != spotify_id:
        ext["spotify"] = spotify_id; changed = True
    artist.external_ids = ext

    if changed:
        artist.full_clean()
        artist.save()
    IMPORT_JOBS_TOTAL.labels(source="spotify").inc()
    return {"updated": changed, "source": "spotify"}


def enrich_from_musicbrainz(artist: Artist, mbid: str) -> Dict:
    """
    Met à jour l'artiste depuis MusicBrainz ws/2 (name).
    """
    if not mbid:
        return {"updated": False, "reason": "missing_mbid"}

    headers = {"User-Agent": getattr(settings, "MUSICBRAINZ_APP", "Festival/1.0")}
    url = f"https://musicbrainz.org/ws/2/artist/{mbid}?fmt=json"
    r = requests.get(url, headers=headers, timeout=6)
    r.raise_for_status()
    data = r.json()

    changed = False
    if data.get("name") and data["name"] != artist.name:
        artist.name = data["name"]; changed = True

    ext = dict(artist.external_ids or {})
    if ext.get("musicbrainz") != mbid:
        ext["musicbrainz"] = mbid; changed = True
    artist.external_ids = ext

    if changed:
        artist.full_clean()
        artist.save()
    IMPORT_JOBS_TOTAL.labels(source="musicbrainz").inc()
    return {"updated": changed, "source": "musicbrainz"}
