from __future__ import annotations

from datetime import date
from typing import Iterable, List

from django.core.cache import cache
from django.utils.dateparse import parse_date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from django.conf import settings

from .models import Artist, ArtistAvailability, Genre
from .permissions import IsBookerOrReadOnly
from .serializers import ArtistAvailabilitySerializer, ArtistSerializer, GenreSerializer
from .services import compute_compatibility, enrich_from_musicbrainz, enrich_from_spotify


# ---------------------------------------------------------------------------
# Genres
# ---------------------------------------------------------------------------

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsBookerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


# ---------------------------------------------------------------------------
# Artists
# ---------------------------------------------------------------------------

class ArtistViewSet(viewsets.ModelViewSet):
    serializer_class = ArtistSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsBookerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country", "genres", "popularity"]
    search_fields = ["name", "short_bio"]
    ordering_fields = ["name", "popularity", "created_at"]
    ordering = ["-popularity", "name"]

    def get_queryset(self):
        qs = Artist.objects.prefetch_related("genres").all()
        # Filtre pratique: disponibilité sur un jour
        avail_str = self.request.query_params.get("available_on")
        if avail_str:
            try:
                d = parse_date(avail_str)
                if d:
                    qs = qs.filter(availabilities__date=d, availabilities__available=True)
            except Exception:
                pass
        return qs

    @action(methods=["GET"], detail=False, url_path="top")
    def top(self, request):
        limit = int(request.query_params.get("limit", 20))
        limit = max(1, min(100, limit))
        cache_ttl = int(getattr(settings, "LINEUP_TOP_CACHE_TTL", 300))
        key = f"lineup:top:{limit}"
        data = cache.get(key)
        if not data:
            qs = Artist.objects.order_by("-popularity", "name").values(
                "id", "name", "slug", "picture", "popularity"
            )[:limit]
            data = list(qs)
            cache.set(key, data, cache_ttl)
        return Response(data)

    @action(methods=["GET"], detail=True, url_path="compatibility")
    def compatibility(self, request, pk=None):
        artist = self.get_object()
        param = request.query_params.get("genres", "")
        try:
            genre_ids = [int(x) for x in param.split(",") if x.strip()]
        except Exception:
            genre_ids = []
        score = compute_compatibility(artist, genre_ids)
        return Response({"artist": artist.id, "score": score})

    @action(methods=["POST"], detail=True, url_path="enrich")
    def enrich(self, request, pk=None):
        """
        Payload:
        - {"source":"spotify","spotify_id":"..."} ou
        - {"source":"musicbrainz","mbid":"..."}
        - (tests) {"source":"spotify","payload":{...}} -> no-op réseau
        """
        artist = self.get_object()
        source = (request.data or {}).get("source", "").lower()
        payload = (request.data or {}).get("payload")
        if source == "spotify":
            if payload:
                # Test/injection: simule la réponse Spotify
                changed = False
                data = payload
                if data.get("name") and data["name"] != artist.name:
                    artist.name = data["name"]; changed = True
                if data.get("images"):
                    pic = data["images"][0].get("url")
                    if pic and pic != artist.picture:
                        artist.picture = pic; changed = True
                if "popularity" in data and data["popularity"] is not None:
                    p = max(0, min(100, int(data["popularity"])))
                    if p != artist.popularity:
                        artist.popularity = p; changed = True
                artist.full_clean()
                if changed:
                    artist.save()
                return Response({"updated": changed, "source": "spotify(payload)"})
            res = enrich_from_spotify(artist, request.data.get("spotify_id"))
            return Response(res)
        elif source == "musicbrainz":
            if payload:
                changed = False
                data = payload
                if data.get("name") and data["name"] != artist.name:
                    artist.name = data["name"]; changed = True
                artist.full_clean()
                if changed:
                    artist.save()
                return Response({"updated": changed, "source": "musicbrainz(payload)"})
            res = enrich_from_musicbrainz(artist, request.data.get("mbid"))
            return Response(res)
        return Response({"detail": "Unsupported source"}, status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Availabilities
# ---------------------------------------------------------------------------

class ArtistAvailabilityViewSet(viewsets.ModelViewSet):
    queryset = ArtistAvailability.objects.select_related("artist").all()
    serializer_class = ArtistAvailabilitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsBookerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["artist", "available", "date"]
    search_fields = ["artist__name", "notes"]
    ordering_fields = ["date", "created_at"]
    ordering = ["date", "artist__name"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Endpoint pratique ?for_date=YYYY-MM-DD
        d_str = self.request.query_params.get("for_date")
        if d_str:
            try:
                d = parse_date(d_str)
                if d:
                    qs = qs.filter(date=d)
            except Exception:
                pass
        return qs
