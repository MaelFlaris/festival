from __future__ import annotations

from django.db.models import QuerySet
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from .models import UserProfile
from .permissions import IsOwnerOrAdmin
from .serializers import UserProfileSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    Règles self-service:
    - Admin/Staff: CRUD complet sur tous les profils.
    - User standard: visibilité et modification limitées à SON profil.
    - Endpoint utilitaire: /api/authx/profiles/me (GET/PATCH/PUT)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__username", "user__email", "display_name"]
    ordering_fields = ["user__username", "created_at", "updated_at"]
    ordering = ["user__username"]

    def get_queryset(self) -> QuerySet[UserProfile]:
        qs = UserProfile.objects.select_related("user").all()
        u = self.request.user
        if u.is_staff or u.is_superuser:
            return qs
        # For list views, restrict to own profile; for detail, rely on object perms (403)
        if getattr(self, "action", None) == "list":
            return qs.filter(user=u)
        return qs

    def perform_create(self, serializer: UserProfileSerializer):
        # Forcer l'association au user courant
        serializer.save(user=self.request.user)

    @action(methods=["GET", "PATCH", "PUT"], detail=False, url_path="me", permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """
        GET: retourne ou crée le profil du user courant
        PATCH/PUT: met à jour le profil du user courant
        """
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if request.method == "GET":
            ser = self.get_serializer(profile)
            return Response(ser.data)
        # PATCH/PUT
        partial = request.method == "PATCH"
        ser = self.get_serializer(profile, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        self.perform_update(ser)
        return Response(ser.data)
