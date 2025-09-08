from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SponsorTier, Sponsor, Sponsorship
from .permissions import IsSponsorManagerOrReadOnly
from .serializers import SponsorTierSerializer, SponsorSerializer, SponsorshipSerializer
from .services import presign_contract_put, public_grouped_by_edition, stats_summary


class SponsorTierViewSet(viewsets.ModelViewSet):
    queryset = SponsorTier.objects.all()
    serializer_class = SponsorTierSerializer
    permission_classes = [IsSponsorManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "display_name"]
    ordering_fields = ["rank", "name", "created_at"]
    ordering = ["rank", "name"]


class SponsorViewSet(viewsets.ModelViewSet):
    queryset = Sponsor.objects.all()
    serializer_class = SponsorSerializer
    permission_classes = [IsSponsorManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class SponsorshipViewSet(viewsets.ModelViewSet):
    queryset = Sponsorship.objects.select_related("edition", "tier", "sponsor").all()
    serializer_class = SponsorshipSerializer
    permission_classes = [IsSponsorManagerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["edition", "tier", "visible"]
    search_fields = ["sponsor__name", "tier__name"]
    ordering_fields = ["order", "created_at"]
    ordering = ["edition", "tier__rank", "order", "sponsor__name"]

    # ------- Public grouped (cached) -------
    @action(methods=["GET"], detail=False, url_path="public/by-edition", permission_classes=[])
    def public_by_edition(self, request):
        try:
            edition_id = int(request.query_params.get("edition"))
        except Exception:
            return Response({"detail": "edition is required"}, status=400)
        ttl = int(getattr(settings, "SPONSORS_PUBLIC_CACHE_TTL", 300))
        key = f"sponsors:public:edition:{edition_id}"
        cached = cache.get(key)
        if cached is None:
            data = public_grouped_by_edition(edition_id)
            cache.set(key, data, ttl)
        else:
            data = cached
        return Response(data)

    # ------- Stats summary -------
    @action(methods=["GET"], detail=False, url_path="stats/summary")
    def stats_summary(self, request):
        edition = request.query_params.get("edition")
        ed = int(edition) if edition else None
        return Response(stats_summary(ed))

    # ------- Contracts: presign PUT to S3 -------
    @action(methods=["POST"], detail=False, url_path="contracts/presign")
    def contracts_presign(self, request):
        """
        Body:
        {
          "filename": "contract-123.pdf",
          "content_type": "application/pdf",
          "edition": 2025,
          "sponsor": 42
        }
        -> returns { supported, url?, object_url?, reason? }
        """
        data = request.data or {}
        filename = data.get("filename")
        content_type = data.get("content_type") or "application/octet-stream"
        if not filename:
            return Response({"detail": "filename required"}, status=400)
        # key suggestion: edition/sponsor/filename
        edition = data.get("edition") or "misc"
        sponsor = data.get("sponsor") or "misc"
        key = f"{edition}/{sponsor}/{filename}"
        res = presign_contract_put(key, content_type)
        status_code = 200 if res.get("supported") else 501
        return Response(res, status=status_code)

    # ------- Contracts: attach uploaded URL -------
    @action(methods=["POST"], detail=True, url_path="contracts/attach")
    def contracts_attach(self, request, pk=None):
        """
        Body: { "contract_url": "https://bucket.s3.region.amazonaws.com/contracts/..." }
        """
        sponsorship = self.get_object()
        url = (request.data or {}).get("contract_url")
        if not url:
            return Response({"detail": "contract_url required"}, status=400)
        sponsorship.contract_url = url
        sponsorship.full_clean()
        sponsorship.save(update_fields=["contract_url"])
        return Response({"ok": True, "id": sponsorship.id, "contract_url": sponsorship.contract_url})
