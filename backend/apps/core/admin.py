from django.contrib import admin
from .models import FestivalEdition, Venue, Stage, Contact


@admin.register(FestivalEdition)
class FestivalEditionAdmin(admin.ModelAdmin):
    list_display = ("year", "name", "start_date", "end_date", "is_active", "created_at")
    list_filter = ("is_active", "year", "start_date")
    search_fields = ("name", "tagline")
    ordering = ("-year",)


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "country", "created_at")
    list_filter = ("country", "city")
    search_fields = ("name", "address", "city")
    ordering = ("name",)


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("name", "edition", "venue", "covered", "capacity", "created_at")
    list_filter = ("edition", "venue", "covered")
    search_fields = ("name", "venue__name")
    ordering = ("edition", "name")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("edition", "type", "label", "email", "phone", "created_at")
    list_filter = ("edition", "type")
    search_fields = ("label", "email", "phone")
    ordering = ("edition", "type", "label")
