from django.contrib import admin
from .models import Genre, Artist, ArtistAvailability

# Historisation si dispo (via common)
try:
    from apps.common.admin import HistoryAdminBase
except Exception:  # pragma: no cover
    from django.contrib import admin as _admin
    class HistoryAdminBase(_admin.ModelAdmin):
        pass


@admin.register(Genre)
class GenreAdmin(HistoryAdminBase):
    list_display = ("name", "slug", "color", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Artist)
class ArtistAdmin(HistoryAdminBase):
    list_display = ("name", "slug", "country", "popularity", "created_at")
    list_filter = ("country", "popularity", "genres")
    search_fields = ("name", "short_bio")
    filter_horizontal = ("genres",)
    ordering = ("-popularity", "name")
    list_select_related = ()
    readonly_fields = ("created_at", "updated_at")


@admin.register(ArtistAvailability)
class ArtistAvailabilityAdmin(HistoryAdminBase):
    list_display = ("artist", "date", "available", "notes", "created_at")
    list_filter = ("available", "date", "artist")
    search_fields = ("artist__name", "notes")
    ordering = ("date", "artist__name")
    list_select_related = ("artist",)
    readonly_fields = ("created_at", "updated_at")
