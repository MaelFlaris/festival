# backend/apps/schedule/admin.py
from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Slot
from .services import find_conflicts_for_slot_queryset


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("edition","day","stage","artist","start_time","end_time","status","is_headliner","_conflicts")
    list_filter = ("edition","day","stage","status","is_headliner")
    search_fields = ("artist__name","stage__name","notes")
    ordering = ("edition","day","stage__name","start_time")
    list_select_related = ("edition","stage","artist")
    readonly_fields = ("created_at","updated_at")
    actions = ("admin_check_conflicts",)

    def _conflicts(self, obj: Slot):
        conflicts = find_conflicts_for_slot_queryset(obj)
        if conflicts:
            return format_html('<span style="color:#b91c1c">⚠ {} conflit(s)</span>', len(conflicts))
        return format_html('<span style="color:#16a34a">OK</span>')
    _conflicts.short_description = "Conflits"

    def admin_check_conflicts(self, request, queryset):
        total = 0
        for slot in queryset:
            total += len(find_conflicts_for_slot_queryset(slot))
        self.message_user(request, f"Conflits détectés (sur sélection) : {total}")
    admin_check_conflicts.short_description = "Analyser les conflits (sélection)"
