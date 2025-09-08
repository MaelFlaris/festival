from django.contrib import admin
from .models import Genre, Artist, ArtistAvailability


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "color", "created_at")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "country", "popularity", "created_at")
    list_filter = ("country", "popularity", "genres")
    search_fields = ("name", "short_bio")
    filter_horizontal = ("genres",)
    ordering = ("-popularity", "name")


@admin.register(ArtistAvailability)
class ArtistAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("artist", "date", "available", "notes", "created_at")
    list_filter = ("available", "date", "artist")
    search_fields = ("artist__name", "notes")
    ordering = ("date", "artist__name")
