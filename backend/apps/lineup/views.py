from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Genre, Artist, ArtistAvailability
from .serializers import GenreSerializer, ArtistSerializer, ArtistAvailabilitySerializer
from rest_framework.viewsets import ReadOnlyModelViewSet


class GenreViewSet(ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ArtistViewSet(ReadOnlyModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'genres', 'popularity']
    search_fields = ['name', 'short_bio']
    ordering_fields = ['name', 'popularity', 'created_at']
    ordering = ['-popularity', 'name']


class ArtistAvailabilityViewSet(ReadOnlyModelViewSet):
    queryset = ArtistAvailability.objects.all()
    serializer_class = ArtistAvailabilitySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['artist', 'available', 'date']
    search_fields = ['artist__name', 'notes']
    ordering_fields = ['date', 'created_at']
    ordering = ['date', 'artist__name']
