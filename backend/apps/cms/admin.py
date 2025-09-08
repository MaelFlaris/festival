from django.contrib import admin
from .models import Page, FAQItem, News

# Filtres/mixins réutilisables depuis common
try:
    from apps.common.admin import HistoryAdminBase, PublishStatusListFilter
except Exception:  # pragma: no cover
    from django.contrib import admin as _admin
    class HistoryAdminBase(_admin.ModelAdmin):
        pass
    class PublishStatusListFilter(admin.SimpleListFilter):
        title = "Statut"
        parameter_name = "status"
        def lookups(self, request, model_admin):
            return (("draft","Brouillon"),("review","Relecture"),("published","Publié"),("archivé","Archivé"))
        def queryset(self, request, queryset):
            return queryset.filter(status=self.value()) if self.value() else queryset


@admin.register(Page)
class PageAdmin(HistoryAdminBase):
    list_display = ("edition", "slug", "title", "status", "publish_at", "created_at")
    list_filter = ("edition", PublishStatusListFilter, "publish_at")
    search_fields = ("slug", "title", "body_md")
    ordering = ("edition", "slug")
    list_select_related = ("edition",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(FAQItem)
class FAQItemAdmin(HistoryAdminBase):
    list_display = ("edition", "order", "question", "created_at")
    list_filter = ("edition",)
    search_fields = ("question", "answer_md")
    ordering = ("edition", "order", "id")
    list_select_related = ("edition",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(News)
class NewsAdmin(HistoryAdminBase):
    list_display = ("edition", "title", "status", "publish_at", "created_at")
    list_filter = ("edition", PublishStatusListFilter, "publish_at", "tags")
    search_fields = ("title", "summary", "body_md")
    ordering = ("-publish_at", "-created_at")
    list_select_related = ("edition",)
    readonly_fields = ("created_at", "updated_at")
