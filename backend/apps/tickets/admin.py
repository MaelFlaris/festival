from django.contrib import admin
from .models import TicketType


@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = (
        "edition", "code", "name", "day", "price", "currency",
        "quota_total", "quota_reserved", "is_active", "created_at"
    )
    list_filter = ("edition", "currency", "is_active", "day")
    search_fields = ("code", "name", "description")
    ordering = ("edition", "code")
