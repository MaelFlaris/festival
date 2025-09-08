from django.contrib import admin
from .models import UserProfile

# Intégration de l'historique si disponible via common
try:
    from apps.common.admin import HistoryAdminBase
except Exception:  # pragma: no cover
    from django.contrib import admin as _admin
    class HistoryAdminBase(_admin.ModelAdmin):
        pass


@admin.register(UserProfile)
class UserProfileAdmin(HistoryAdminBase):
    list_display = ("user", "display_name", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "display_name")
    ordering = ("user__username",)
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
