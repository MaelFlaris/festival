from __future__ import annotations

from django.contrib import admin
from .models import TicketType


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = (
        "edition", "code", "name", "phase", "day", "price", "currency",
        "quota_total", "quota_reserved", "quota_remaining", "is_active",
        "is_on_sale_admin", "sale_start", "sale_end", "created_at"
    )
    list_filter = ("edition", "currency", "is_active", "phase", "day")
    search_fields = ("code", "name", "description")
    ordering = ("edition", "code")
    readonly_fields = ("created_at", "updated_at")

    def is_on_sale_admin(self, obj: TicketType) -> bool:
        return obj.is_on_sale()
    is_on_sale_admin.boolean = True
    is_on_sale_admin.short_description = "On sale?"
