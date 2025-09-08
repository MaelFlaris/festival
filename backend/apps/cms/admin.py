from django.contrib import admin
from .models import Page, FAQItem, News


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("edition", "slug", "title", "status", "publish_at", "created_at")
    list_filter = ("edition", "status", "publish_at")
    search_fields = ("slug", "title", "body_md")
    ordering = ("edition", "slug")


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ("edition", "order", "question", "created_at")
    list_filter = ("edition",)
    search_fields = ("question", "answer_md")
    ordering = ("edition", "order", "id")


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("edition", "title", "status", "publish_at", "created_at")
    list_filter = ("edition", "status", "publish_at", "tags")
    search_fields = ("title", "summary", "body_md")
    ordering = ("-publish_at", "-created_at")
