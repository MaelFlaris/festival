# apps/common/admin.py
from __future__ import annotations

from django.contrib import admin
from django.utils import timezone
from typing import Optional

# Mixins d'admin réutilisables pour les apps concrètes

class SoftDeleteStateFilter(admin.SimpleListFilter):
    title = "État (soft delete)"
    parameter_name = "soft_state"

    def lookups(self, request, model_admin):
        return (
            ("alive", "Actifs"),
            ("deleted", "Supprimés"),
            ("all", "Tous"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "alive":
            return getattr(queryset, "alive", lambda: queryset.filter(deleted_at__isnull=True))()
        if value == "deleted":
            return getattr(queryset, "dead", lambda: queryset.filter(deleted_at__isnull=False))()
        return queryset


class PublishStatusListFilter(admin.SimpleListFilter):
    title = "Statut de publication"
    parameter_name = "pub_status"

    def lookups(self, request, model_admin):
        from .models import PublishStatus
        return [(c.value, c.label) for c in PublishStatus]

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(status=value)
        return queryset


class SoftDeleteAdminMixin:
    """Ajoute actions et affichage pour les modèles SoftDeleteModel."""
    actions = ("admin_undelete", "admin_hard_delete")

    def admin_undelete(self, request, queryset):
        for obj in queryset:
            undelete = getattr(obj, "undelete", None)
            if callable(undelete):
                undelete()
    admin_undelete.short_description = "Restaurer (undelete)"

    def admin_hard_delete(self, request, queryset):
        for obj in queryset:
            hard_delete = getattr(obj, "hard_delete", None)
            if callable(hard_delete):
                hard_delete()
    admin_hard_delete.short_description = "Supprimer définitivement"


# Intégration facultative simple_history
try:
    from simple_history.admin import SimpleHistoryAdmin
    class HistoryAdminBase(SimpleHistoryAdmin):
        """Base admin si simple_history installé."""
        pass
except Exception:  # pragma: no cover
    class HistoryAdminBase(admin.ModelAdmin):
        """Fallback sans historique."""
        pass

# Remarque : pas de registres ici car common ne déclare pas de modèles concrets.
