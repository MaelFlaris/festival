from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

from apps.common.drf import enforce_readonly_for_anonymous 

from .models import FestivalEdition, Venue, Stage, Contact
from .serializers import (
    FestivalEditionSerializer, VenueSerializer,
    StageSerializer, ContactSerializer
)
from .services import activate_edition, get_edition_summary

@enforce_readonly_for_anonymous
class FestivalEditionViewSet(viewsets.ModelViewSet):
    queryset = FestivalEdition.objects.all()
    serializer_class = FestivalEditionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['year', 'is_active']
    search_fields = ['name', 'tagline']
    ordering_fields = ['year', 'start_date', 'created_at']
    ordering = ['-year']

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        edition = self.get_object()
        activate_edition(edition)
        serializer = self.get_serializer(edition, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="summary")
    def summary(self, request, pk=None):
        edition = self.get_object()
        data = get_edition_summary(edition)
        return Response(data, status=status.HTTP_200_OK)


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
