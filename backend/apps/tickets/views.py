from __future__ import annotations

from decimal import Decimal
from typing import Dict
import csv
import io
from django.http import HttpResponse

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import TicketType, PricePhase, PHASE_ORDER
from .serializers import TicketTypeSerializer
from .services import current_cache_version
from apps.common.rbac import ObjectPermissionsMixin, AssignCreatorObjectPermsMixin


class TicketTypeViewSet(AssignCreatorObjectPermsMixin, ObjectPermissionsMixin, viewsets.ModelViewSet):
    queryset = TicketType.objects.select_related("edition").all()
    serializer_class = TicketTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["edition", "currency", "is_active", "day", "phase"]
    search_fields = ["code", "name", "description"]
    ordering_fields = ["code", "price", "created_at"]
    ordering = ["edition", "code"]

    # -------- On sale listing (cached) --------
    @action(methods=["GET"], detail=False, url_path="on-sale", permission_classes=[])
    def on_sale(self, request):
        edition = request.query_params.get("edition")
        ttl = int(getattr(settings, "TICKETS_ON_SALE_CACHE_TTL", 120))
        v = current_cache_version()
        key = f"tickets:on_sale:v{v}:ed{edition or 'all'}"
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        qs = TicketType.objects.select_related("edition").all()
        if edition:
            qs = qs.filter(edition_id=edition)
        data = [TicketTypeSerializer(t).data for t in qs if t.is_on_sale()]
        cache.set(key, data, ttl)
        return Response(data)

    # -------- Export CSV --------
    @action(methods=["GET"], detail=False, url_path=r"export\.csv")
    def export_csv(self, request):
        qs = self.get_queryset()
        edition = request.query_params.get("edition")
        on_sale = request.query_params.get("on_sale")
        if edition:
            qs = qs.filter(edition_id=edition)
        if on_sale is not None:
            want = str(on_sale).lower() in {"1", "true", "yes", "on"}
            qs = [t for t in qs if t.is_on_sale()] if want else [t for t in qs if not t.is_on_sale()]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "edition", "code", "name", "phase", "day",
            "price_ttc", "price_net", "price_vat_amount", "currency", "vat_rate",
            "quota_total", "quota_reserved", "quota_remaining", "sale_start", "sale_end",
            "is_active", "is_on_sale"
        ])
        iterable = qs if isinstance(qs, list) else qs.iterator()
        for t in iterable:
            writer.writerow([
                t.id,
                t.edition_id,
                t.code,
                t.name,
                t.phase,
                t.day.isoformat() if t.day else "",
                float(t.price),
                float(t.price_net),
                float(t.price_vat_amount),
                t.currency,
                float(t.vat_rate),
                int(t.quota_total),
                int(t.quota_reserved),
                int(t.quota_remaining),
                t.sale_start.isoformat() if t.sale_start else "",
                t.sale_end.isoformat() if t.sale_end else "",
                1 if t.is_active else 0,
                1 if t.is_on_sale() else 0,
            ])
        data = output.getvalue()
        filename = f"ticket_types_{edition or 'all'}.csv"
        resp = HttpResponse(data, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return resp

    # -------- Reserve (anti-fraud: rate limit) --------
    @action(methods=["POST"], detail=True, url_path="reserve", permission_classes=[])
    def reserve(self, request, pk=None):
        """
        Body:
        {
          "quantity": 2,
          "channel": "online",       # optionnel
          "dry_run": false           # si true: vérifie sans écrire
        }
        """
        q = int((request.data or {}).get("quantity") or 1)
        if q < 1:
            return Response({"detail": "quantity must be >= 1"}, status=400)

        # rate limit per IP
        limit = int(getattr(settings, "TICKETS_RESERVE_RATE_LIMIT_PER_MIN", 30))
        ip = request.META.get("REMOTE_ADDR", "anon")
        rl_key = f"tickets:rl:{ip}"
        count = cache.get(rl_key, 0)
        if count >= limit:
            return Response({"detail": "Too many requests"}, status=429)
        cache.set(rl_key, count + 1, 60)

        channel = (request.data or {}).get("channel")
        dry = bool((request.data or {}).get("dry_run", False))

        with transaction.atomic():
            tt = TicketType.objects.select_for_update().get(pk=pk)
            if not tt.is_on_sale():
                return Response({"detail": "Ticket not on sale"}, status=400)
            if tt.quota_remaining < q:
                return Response({"detail": "Insufficient quota", "remaining": tt.quota_remaining}, status=400)

            # quotas canal (si définis)
            if channel:
                ch_quota = int((tt.quota_by_channel or {}).get(channel, tt.quota_total))
                already = int((tt.reserved_by_channel or {}).get(channel, 0))
                if already + q > ch_quota:
                    return Response({"detail": f"Channel '{channel}' quota exceeded"}, status=400)

            if dry:
                return Response({"ok": True, "dry_run": True, "remaining_if_ok": tt.quota_remaining - q})

            # commit
            tt.quota_reserved = int(tt.quota_reserved) + q
            rbc = dict(tt.reserved_by_channel or {})
            if channel:
                rbc[channel] = int(rbc.get(channel, 0)) + q
            tt.reserved_by_channel = rbc
            tt.full_clean()
            tt.save(update_fields=["quota_reserved", "reserved_by_channel", "updated_at"])
            return Response({
                "ok": True,
                "id": tt.id,
                "reserved": q,
                "quota_remaining": tt.quota_remaining,
                "reserved_by_channel": tt.reserved_by_channel,
            })

    # -------- Phase advance --------
    @action(methods=["POST"], detail=True, url_path="phase/advance")
    def phase_advance(self, request, pk=None):
        tt = TicketType.objects.get(pk=pk)
        # Enforce manage_pricing only for authenticated users to preserve backward-compat
        if request.user and request.user.is_authenticated:
            if not request.user.has_perm("tickets.manage_pricing", tt):
                return Response({"detail": "Forbidden"}, status=403)
        nxt = tt.next_phase()
        if not nxt:
            return Response({"detail": "No next phase"}, status=400)
        tt.phase = nxt
        tt.save(update_fields=["phase", "updated_at"])
        return Response({"ok": True, "id": tt.id, "phase": tt.phase})

    # -------- Stats summary --------
    @action(methods=["GET"], detail=False, url_path="stats/summary", permission_classes=[])
    def stats_summary(self, request):
        edition = request.query_params.get("edition")
        qs = self.get_queryset()
        if edition:
            qs = qs.filter(edition_id=edition)

        res = {
            "edition": int(edition) if edition else None,
            "total_types": qs.count(),
            "on_sale": 0,
            "quota_total": 0,
            "quota_reserved": 0,
            "quota_remaining": 0,
            "by_phase": {p: {"count": 0, "on_sale": 0} for p in ["early", "regular", "late"]},
            "total_revenue_potential_ttc": "0.00",
        }
        total_rev = Decimal("0.00")
        for t in qs:
            res["quota_total"] += int(t.quota_total)
            res["quota_reserved"] += int(t.quota_reserved)
            res["quota_remaining"] += int(t.quota_remaining)
            res["by_phase"][t.phase]["count"] += 1
            if t.is_on_sale():
                res["on_sale"] += 1
                res["by_phase"][t.phase]["on_sale"] += 1
            total_rev += (t.price * Decimal(max(0, int(t.quota_total) - int(t.quota_reserved))))
        res["total_revenue_potential_ttc"] = f"{total_rev:.2f}"
        return Response(res)

    def perform_update(self, serializer):
        instance = self.get_object()
        sensitive = {"price", "vat_rate", "phase"}
        if any(k in serializer.validated_data for k in sensitive):
            user = getattr(self.request, "user", None)
            if user and user.is_authenticated and not user.has_perm("tickets.manage_pricing", instance):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Missing manage_pricing permission")
        return super().perform_update(serializer)
