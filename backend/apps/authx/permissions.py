# apps/authx/permissions.py
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrAdmin(BasePermission):
    """
    - Admin/staff: accès total
    - Sinon: peut lire sa propre ressource; modification seulement sur sa ressource
    """

    def has_permission(self, request, view):
        # GET list: autorisé, mais queryset sera filtré dans la view
        return bool(getattr(request, "user", None) and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user and (request.user.is_staff or request.user.is_superuser):
            return True
        if request.method in SAFE_METHODS:
            return obj.user_id == getattr(request.user, "id", None)
        # Écriture/DELETE limitées au propriétaire
        return obj.user_id == getattr(request.user, "id", None)
