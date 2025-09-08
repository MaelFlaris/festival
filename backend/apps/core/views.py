from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import FestivalEdition, Venue, Stage, Contact
from .serializers import (
    FestivalEditionSerializer, VenueSerializer, 
    StageSerializer, ContactSerializer
)


class FestivalEditionViewSet(viewsets.ModelViewSet):
    queryset = FestivalEdition.objects.all()
    serializer_class = FestivalEditionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['year', 'is_active']
    search_fields = ['name', 'tagline']
    ordering_fields = ['year', 'start_date', 'created_at']
    ordering = ['-year']


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['country', 'city']
    search_fields = ['name', 'address', 'city']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class StageViewSet(viewsets.ModelViewSet):
    queryset = Stage.objects.all()
    serializer_class = StageSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'venue', 'covered']
    search_fields = ['name', 'venue__name']
    ordering_fields = ['name', 'created_at']
    ordering = ['edition', 'name']


class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'type']
    search_fields = ['label', 'email', 'phone']
    ordering_fields = ['type', 'label', 'created_at']
    ordering = ['edition', 'type', 'label']
