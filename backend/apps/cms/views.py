from __future__ import annotations

from typing import Optional

from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django.utils import timezone
from django.utils.feedgenerator import rfc2822_date
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend

from .metrics import PREVIEW_REQUESTS_TOTAL
from .models import Page, FAQItem, News
from .serializers import PageSerializer, FAQItemSerializer, NewsSerializer
from .services import (
    build_preview_url,
    create_preview_token,
    current_public_cache_version,
    is_within_publish_window,
    markdown_to_html_safe,
    verify_preview_token,
)


# -------------------------
# ViewSets “éditoriaux” (admin/editeurs)
# -------------------------

from apps.common.rbac import ObjectPermissionsMixin, AssignCreatorObjectPermsMixin


class PageViewSet(AssignCreatorObjectPermsMixin, ObjectPermissionsMixin, viewsets.ModelViewSet):
    queryset = Page.objects.select_related("edition").all()
    serializer_class = PageSerializer
    # ObjectPermissionsMixin enforces IsAuthenticated + object perms
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["edition", "status"]
    search_fields = ["slug", "title", "body_md"]
    ordering_fields = ["slug", "publish_at", "created_at"]
    ordering = ["edition", "slug"]

    @action(methods=["POST"], detail=True, url_path="publish")
    def publish(self, request, pk=None):
        obj = self.get_object()
        if not request.user.has_perm("cms.publish_page", obj):
            return Response({"detail": "Forbidden"}, status=403)
        try:
            from apps.common.models import PublishStatus
            obj.status = PublishStatus.PUBLISHED
            obj.save(update_fields=["status", "updated_at"])
        except Exception:
            return Response({"detail": "Unable to publish"}, status=400)
        return Response(PageSerializer(obj, context=self.get_serializer_context()).data)


class FAQItemViewSet(AssignCreatorObjectPermsMixin, ObjectPermissionsMixin, viewsets.ModelViewSet):
    queryset = FAQItem.objects.select_related("edition").all()
    serializer_class = FAQItemSerializer
    # ObjectPermissionsMixin enforces IsAuthenticated + object perms
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["edition"]
    search_fields = ["question", "answer_md"]
    ordering_fields = ["order", "created_at"]
    ordering = ["edition", "order", "id"]


class NewsViewSet(AssignCreatorObjectPermsMixin, ObjectPermissionsMixin, viewsets.ModelViewSet):
    queryset = News.objects.select_related("edition").all()
    serializer_class = NewsSerializer
    # ObjectPermissionsMixin enforces IsAuthenticated + object perms
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    # Note: django-filter doesn't auto-handle JSONField; keep custom ?tag= filter below
    filterset_fields = ["edition", "status"]
    search_fields = ["title", "summary", "body_md"]
    ordering_fields = ["publish_at", "created_at"]
    ordering = ["-publish_at", "-created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        # Filtre pratique: ?tag=foo (PostgreSQL JSON contains)
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__contains=[tag])
        return qs

    @action(methods=["POST"], detail=True, url_path="publish")
    def publish(self, request, pk=None):
        obj = self.get_object()
        if not request.user.has_perm("cms.publish_news", obj):
            return Response({"detail": "Forbidden"}, status=403)
        # Minimal publish: set status to published
        try:
            from apps.common.models import PublishStatus
            obj.status = PublishStatus.PUBLISHED
            obj.save(update_fields=["status", "updated_at"])
        except Exception:
            return Response({"detail": "Unable to publish"}, status=400)
        return Response(NewsSerializer(obj, context=self.get_serializer_context()).data)


# -------------------------
# Endpoints publics (lecture-only, contenus publiés)
# -------------------------

class PublicPageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = []
    search_fields = ["slug", "title", "body_md"]
    ordering_fields = ["slug", "publish_at", "created_at"]
    ordering = ["slug"]

    def get_queryset(self):
        now = timezone.now()
        return (
            Page.objects.select_related("edition")
            .filter(status="published")
            .filter(models.Q(publish_at__lte=now) | models.Q(publish_at__isnull=True))
            .filter(models.Q(unpublish_at__gt=now) | models.Q(unpublish_at__isnull=True))
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ttl = int(getattr(settings, "CMS_PUBLIC_CACHE_TTL", 300))
        v = current_public_cache_version()
        key = f"cms:pages:v{v}:{hash(frozenset(request.query_params.items()))}"
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        serializer = self.get_serializer(queryset, many=True)
        cache.set(key, serializer.data, ttl)
        return Response(serializer.data)


class PublicNewsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NewsSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    # Avoid auto-filter on JSONField; use ?tag= convenience param in get_queryset
    filterset_fields = []
    search_fields = ["title", "summary", "body_md"]
    ordering_fields = ["publish_at", "created_at"]
    ordering = ["-publish_at", "-created_at"]

    def get_queryset(self):
        now = timezone.now()
        qs = (
            News.objects.select_related("edition")
            .filter(status="published")
            .filter(models.Q(publish_at__lte=now) | models.Q(publish_at__isnull=True))
            .filter(models.Q(unpublish_at__gt=now) | models.Q(unpublish_at__isnull=True))
        )
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__contains=[tag])
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        ttl = int(getattr(settings, "CMS_PUBLIC_CACHE_TTL", 300))
        v = current_public_cache_version()
        key = f"cms:news:v{v}:{hash(frozenset(request.query_params.items()))}"
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)
        serializer = self.get_serializer(queryset, many=True)
        cache.set(key, serializer.data, ttl)
        return Response(serializer.data)


# -------------------------
# Preview sécurisé
# -------------------------

@api_view(["POST"])
def preview_create(request):
    """
    Body attendu:
    {
      "type": "page" | "news",
      "id": 123,
      "redirect_base": "optional absolute URL to resolve endpoint"
    }
    """
    PREVIEW_REQUESTS_TOTAL.labels(action="create").inc()
    data = request.data or {}
    kind = (data.get("type") or "").lower()
    pk = data.get("id")
    if kind not in {"page", "news"} or not pk:
        return Response({"detail": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    token = create_preview_token(kind, int(pk))
    base = data.get("redirect_base") or request.build_absolute_uri(request.path.replace("preview", "preview/resolve"))
    url = build_preview_url(base, token)
    return Response({"url": url}, status=status.HTTP_200_OK)


@api_view(["GET"])
def preview_resolve(request):
    token = request.query_params.get("token")
    if not token:
        PREVIEW_REQUESTS_TOTAL.labels(action="invalid").inc()
        return Response({"detail": "token required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        payload = verify_preview_token(token)
    except Exception as exc:
        PREVIEW_REQUESTS_TOTAL.labels(action="invalid").inc()
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    PREVIEW_REQUESTS_TOTAL.labels(action="resolve").inc()
    kind = payload.get("k")
    pk = payload.get("id")

    if kind == "page":
        try:
            obj = Page.objects.select_related("edition").get(pk=pk)
        except Page.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = PageSerializer(obj)
        return Response({"type": "page", "data": ser.data})
    elif kind == "news":
        try:
            obj = News.objects.select_related("edition").get(pk=pk)
        except News.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        ser = NewsSerializer(obj)
        return Response({"type": "news", "data": ser.data})
    return Response({"detail": "Invalid token payload"}, status=status.HTTP_400_BAD_REQUEST)


# -------------------------
# Sitemap par édition
# -------------------------

def _abs(request, path: str) -> str:
    base = getattr(settings, "SITE_BASE_URL", None)
    if base:
        return base.rstrip("/") + "/" + path.lstrip("/")
    return request.build_absolute_uri("/" + path.lstrip("/"))

@api_view(["GET"])
def sitemap_edition(request, edition_id: int):
    """
    Sitemap très simple (pages + news publiées) pour une édition.
    """
    pages = [p for p in Page.objects.filter(edition_id=edition_id).all()
             if is_within_publish_window(p.status, p.publish_at, p.unpublish_at)]
    news = [n for n in News.objects.filter(edition_id=edition_id).all()
            if is_within_publish_window(n.status, n.publish_at, n.unpublish_at)]

    def _url(loc: str, lastmod: Optional[str] = None) -> str:
        lm = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        return f"<url><loc>{loc}</loc>{lm}</url>"

    items = []
    for p in pages:
        # suppose un schéma de route front de type /{year}/{slug}
        loc = _abs(request, f"{p.edition.year}/{p.slug}/")
        items.append(_url(loc, p.updated_at.date().isoformat()))
    for n in news:
        loc = _abs(request, f"{n.edition.year}/news/{n.id}/")
        items.append(_url(loc, n.updated_at.date().isoformat()))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' \
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' \
          + "\n".join(items) + "\n</urlset>"
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")
