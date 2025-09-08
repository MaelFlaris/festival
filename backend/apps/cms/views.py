from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Page, FAQItem, News
from .serializers import PageSerializer, FAQItemSerializer, NewsSerializer


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'status']
    search_fields = ['slug', 'title', 'body_md']
    ordering_fields = ['slug', 'publish_at', 'created_at']
    ordering = ['edition', 'slug']


class FAQItemViewSet(viewsets.ModelViewSet):
    queryset = FAQItem.objects.all()
    serializer_class = FAQItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition']
    search_fields = ['question', 'answer_md']
    ordering_fields = ['order', 'created_at']
    ordering = ['edition', 'order', 'id']


class NewsViewSet(viewsets.ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'status', 'tags']
    search_fields = ['title', 'summary', 'body_md']
    ordering_fields = ['publish_at', 'created_at']
    ordering = ['-publish_at', '-created_at']
