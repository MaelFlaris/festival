from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import TicketType
from .serializers import TicketTypeSerializer


class TicketTypeViewSet(viewsets.ModelViewSet):
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['edition', 'currency', 'is_active', 'day']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'price', 'created_at']
    ordering = ['edition', 'code']
