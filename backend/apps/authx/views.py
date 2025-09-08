from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserProfile
from .serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email', 'display_name']
    ordering_fields = ['user__username', 'created_at']
    ordering = ['user__username']
