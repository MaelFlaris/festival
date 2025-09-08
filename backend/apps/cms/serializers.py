from rest_framework import serializers
from .models import Page, FAQItem, News


class PageSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    
    class Meta:
        model = Page
        fields = (
            "id", "edition", "edition_year", "slug", "title", "body_md",
            "meta", "status", "publish_at", "unpublish_at", 
            "created_at", "updated_at"
        )


class FAQItemSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    
    class Meta:
        model = FAQItem
        fields = (
            "id", "edition", "edition_year", "order", "question", 
            "answer_md", "created_at", "updated_at"
        )


class NewsSerializer(serializers.ModelSerializer):
    edition_year = serializers.IntegerField(source="edition.year", read_only=True)
    
    class Meta:
        model = News
        fields = (
            "id", "edition", "edition_year", "title", "summary", 
            "body_md", "cover", "tags", "status", "publish_at", 
            "unpublish_at", "created_at", "updated_at"
        )
