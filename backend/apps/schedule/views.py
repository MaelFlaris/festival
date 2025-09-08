from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.dateparse import parse_date, parse_time
from django.utils.timezone import now
from icalendar import Calendar, Event
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .metrics import CONFLICTS_TOTAL
from .models import Slot, SlotStatus
from .serializers import SlotSerializer
from .services import copy_template, find_conflicts
from collections import defaultdict


# ---------------------------------------------------------------------------
# ViewSet CRUD + 409 conflits
# ---------------------------------------------------------------------------

class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.select_related("edition", "stage", "artist").all()
    serializer_class = SlotSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["edition", "stage", "artist", "day", "status", "is_headliner"]
    search_fields = ["artist__name", "stage__name", "notes"]
    ordering_fields = ["day", "start_time", "created_at"]
    ordering = ["day", "stage__name", "start_time"]

    def list(self, request, *args, **kwargs):
        # cache appliquer lorsque ?day= est fourni
        day = request.query_params.get("day")
        ttl = int(getattr(settings, "SCHEDULE_LIST_DAY_CACHE_TTL", 120))
        if day:
            key = f"schedule:list:{day}:{hash(frozenset(request.GET.items()))}"
            cached = cache.get(key)
            if cached is not None:
                return Response(cached)
            resp = super().list(request, *args, **kwargs)
            cache.set(key, resp.data, ttl)
            return resp
        return super().list(request, *args, **kwargs)

    def _check_and_block_conflicts(self, data, exclude_id=None):
        conflicts = find_conflicts(
            edition_id=data["edition"],
            stage_id=data["stage"],
            day=data["day"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            exclude_id=exclude_id,
        )
        if conflicts:
            CONFLICTS_TOTAL.inc()
            return Response(
                {"detail": "Slot conflict", "conflicts": [c.to_dict() for c in conflicts]},
                status=409,
            )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        block = self._check_and_block_conflicts(ser.validated_data, exclude_id=None)
        if block:
            return block
        self.perform_create(ser)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ser = self.get_serializer(instance, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        # s'il manque certains champs (partial), on complète pour l'analyse
        payload = {
            "edition": ser.validated_data.get("edition", instance.edition).id if isinstance(ser.validated_data.get("edition"), type(instance.edition)) else (ser.validated_data.get("edition") or instance.edition_id),
            "stage": ser.validated_data.get("stage", instance.stage).id if isinstance(ser.validated_data.get("stage"), type(instance.stage)) else (ser.validated_data.get("stage") or instance.stage_id),
            "day": ser.validated_data.get("day", instance.day),
            "start_time": ser.validated_data.get("start_time", instance.start_time),
            "end_time": ser.validated_data.get("end_time", instance.end_time),
        }
        block = self._check_and_block_conflicts(payload, exclude_id=instance.id)
        if block:
            return block
        self.perform_update(ser)
        return Response(ser.data)

    @action(methods=["GET"], detail=False, url_path="conflicts")
    def conflicts(self, request):
        try:
            edition = int(request.query_params.get("edition"))
            stage = int(request.query_params.get("stage"))
            day = parse_date(request.query_params.get("day"))
            start_time = parse_time(request.query_params.get("start_time"))
            end_time = parse_time(request.query_params.get("end_time"))
        except Exception:
            return Response({"detail": "Missing or invalid parameters"}, status=400)
        conflicts = find_conflicts(
            edition_id=edition, stage_id=stage, day=day, start_time=start_time, end_time=end_time
        )
        if conflicts:
            CONFLICTS_TOTAL.inc()
        return Response({"conflicts": [c.to_dict() for c in conflicts]})

    @action(methods=["GET"], detail=False, url_path="validate")
    def validate(self, request):
        try:
            edition = int(request.query_params.get("edition"))
        except Exception:
            return Response({"detail": "edition is required"}, status=400)
        qs = Slot.objects.select_related("stage").filter(edition_id=edition).order_by("day", "stage_id", "start_time")
        groups = defaultdict(list)
        for s in qs:
            groups[(s.stage_id, s.day)].append(s)

        results = []
        for (stage_id, day), slots in groups.items():
            # sorted by start_time already
            n = len(slots)
            for i in range(n):
                s1 = slots[i]
                overlaps = []
                for j in range(i + 1, n):
                    s2 = slots[j]
                    if s2.start_time >= s1.end_time:
                        break
                    if s1.start_time < s2.end_time and s1.end_time > s2.start_time:
                        overlaps.append(s2.id)
                if overlaps:
                    results.append({
                        "slot_id": s1.id,
                        "stage": s1.stage.name,
                        "day": str(s1.day),
                        "range": [str(s1.start_time), str(s1.end_time)],
                        "overlaps_with": overlaps,
                    })
        return Response({"edition": edition, "conflicts": results})

    @action(methods=["POST"], detail=False, url_path="template/copy")
    def template_copy(self, request):
        """
        Body:
        {
          "from_edition": 2024, "to_edition": 2025,
          "stage_map": {"1":"3"}, "status": "tentative", "dry_run": true
        }
        """
        data = request.data or {}
        try:
            from_edition = int(data["from_edition"])
            to_edition = int(data["to_edition"])
            status_val = data.get("status") or SlotStatus.TENTATIVE
            if status_val not in dict(SlotStatus.choices):
                return Response({"detail": "Invalid status"}, status=400)
            res = copy_template(
                from_edition_id=from_edition,
                to_edition_id=to_edition,
                stage_map=data.get("stage_map"),
                status=status_val,
                dry_run=bool(data.get("dry_run", False)),
            )
            return Response(res.to_dict())
        except KeyError:
            return Response({"detail": "from_edition and to_edition are required"}, status=400)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=400)


# ---------------------------------------------------------------------------
# ICS export (cache)
# ---------------------------------------------------------------------------

def ics_export(request):
    qs = Slot.objects.select_related("edition", "stage", "artist").all()

    edition = request.GET.get("edition")
    day = request.GET.get("day")
    artist = request.GET.get("artist")
    stage = request.GET.get("stage")
    status_param = request.GET.get("status")

    if edition:
        qs = qs.filter(edition_id=edition)
    if day:
        qs = qs.filter(day=day)
    if artist:
        qs = qs.filter(artist_id=artist)
    if stage:
        qs = qs.filter(stage_id=stage)
    if status_param:
        qs = qs.filter(status=status_param)

    # cache ICS uniquement pour filtres (sinon flux énorme)
    cacheable = any([edition, day, artist, stage, status_param])
    cache_ttl = int(getattr(settings, "SCHEDULE_ICS_CACHE_TTL", 120))
    cache_key = None
    if cacheable:
        cache_key = f"schedule:ics:{hash(frozenset(request.GET.items()))}"
        cached = cache.get(cache_key)
        if cached is not None:
            return HttpResponse(cached, content_type="text/calendar")

    tz = ZoneInfo("Europe/Paris")
    cal = Calendar()
    cal.add("prodid", "-//Festival//FR")
    cal.add("version", "2.0")

    for s in qs:
        ev = Event()
        ev.add("uid", f"slot-{s.id}@festival")
        ev.add("summary", f"{s.artist.name} @ {s.stage.name}")
        ev.add("dtstart", datetime.combine(s.day, s.start_time, tz))
        ev.add("dtend", datetime.combine(s.day, s.end_time, tz))
        ev.add("location", s.stage.name)
        ev.add("categories", ["Headliner"] if s.is_headliner else [])
        ev.add("description", (s.notes or "")[:1024])
        cal.add_component(ev)

    data = cal.to_ical()
    if cacheable:
        cache.set(cache_key, data, cache_ttl)
    return HttpResponse(data, content_type="text/calendar")
