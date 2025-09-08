from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import SponsorTier, Sponsor, Sponsorship
from .serializers import SponsorTierSerializer, SponsorSerializer, SponsorshipSerializer


class SponsorTierViewSet(viewsets.ModelViewSet):
    queryset = SponsorTier.objects.all()
    serializer_class = SponsorTierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'display_name']
    ordering_fields = ['rank', 'name', 'created_at']
    ordering = ['rank', 'name']


class SponsorViewSet(viewsets.ModelViewSet):
    queryset = Sponsor.objects.all()
    serializer_class = SponsorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class SponsorshipViewSet(viewsets.ModelViewSet):
    queryset = Sponsorship.objects.all()
    serializer_class = SponsorshipSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'tier', 'visible']
    search_fields = ['sponsor__name', 'tier__name']
    ordering_fields = ['order', 'created_at']
    ordering = ['edition', 'tier__rank', 'order', 'sponsor__name']
