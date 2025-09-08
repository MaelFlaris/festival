from datetime import datetime
from zoneinfo import ZoneInfo

from django.http import HttpResponse
from icalendar import Calendar, Event
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Slot
from .serializers import SlotSerializer


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all()
    serializer_class = SlotSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'stage', 'artist', 'day', 'status', 'is_headliner']
    search_fields = ['artist__name', 'stage__name', 'notes']
    ordering_fields = ['day', 'start_time', 'created_at']
    ordering = ['day', 'stage__name', 'start_time']

def ics_export(request):
    qs = Slot.objects.select_related("edition","stage","artist").all()
    day = request.GET.get("day"); artist = request.GET.get("artist"); stage = request.GET.get("stage")
    if day: qs = qs.filter(day=day)
    if artist: qs = qs.filter(artist_id=artist)
    if stage: qs = qs.filter(stage_id=stage)

    tz = ZoneInfo("Europe/Paris")
    cal = Calendar(); cal.add("prodid","-//Festival//FR"); cal.add("version","2.0")
    for s in qs:
        ev = Event()
        ev.add("summary", f"{s.artist.name} @ {s.stage.name}")
        ev.add("dtstart", datetime.combine(s.day, s.start_time, tz))
        ev.add("dtend",   datetime.combine(s.day, s.end_time, tz))
        ev.add("location", s.stage.name)
        cal.add_component(ev)
    return HttpResponse(cal.to_ical(), content_type="text/calendar")