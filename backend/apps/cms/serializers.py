from __future__ import annotations

from rest_framework import serializers

from .models import Page, FAQItem, News
from .services import markdown_to_html_safe


class PageSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    body_html = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Page
        fields = (
            "id", "edition", "edition_year", "slug", "title", "body_md", "body_html",
            "meta", "status", "publish_at", "unpublish_at",
            "created_at", "updated_at"
        )

    def get_body_html(self, obj: Page) -> str:
        return markdown_to_html_safe(obj.body_md or "")


class FAQItemSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    answer_html = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FAQItem
        fields = (
            "id", "edition", "edition_year", "order", "question",
            "answer_md", "answer_html", "created_at", "updated_at"
        )

    def get_answer_html(self, obj: FAQItem) -> str:
        return markdown_to_html_safe(obj.answer_md or "")


class NewsSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    body_html = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = News
        fields = (
            "id", "edition", "edition_year", "title", "summary",
            "body_md", "body_html", "cover", "tags", "status",
            "publish_at", "unpublish_at", "created_at", "updated_at"
        )

    def get_body_html(self, obj: News) -> str:
        return markdown_to_html_safe(obj.body_md or "")
