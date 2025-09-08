from django.contrib import admin
from .models import SponsorTier, Sponsor, Sponsorship


@admin.register(SponsorTier)
class SponsorTierAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "display_name", "rank", "created_at")
    search_fields = ("name", "display_name")
    ordering = ("rank", "name")


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "website", "created_at")
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = (
        "edition", "sponsor", "tier", "amount_eur", 
        "visible", "order", "created_at"
    )
    list_filter = ("edition", "tier", "visible")
    search_fields = ("sponsor__name", "tier__name")
    ordering = ("edition", "tier__rank", "order", "sponsor__name")
