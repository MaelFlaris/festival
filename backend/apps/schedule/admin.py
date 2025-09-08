# backend/apps/schedule/admin.py
from django.contrib import admin
from .models import Slot

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("edition","day","stage","artist","start_time","end_time","status","is_headliner")
    list_filter = ("edition","day","stage","status","is_headliner")
    search_fields = ("artist__name","stage__name")
    ordering = ("edition","day","stage__name","start_time")
