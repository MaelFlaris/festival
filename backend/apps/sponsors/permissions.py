# apps/sponsors/permissions.py
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSponsorManagerOrReadOnly(BasePermission):
    """
    - Lecture: ouverte
    - Écriture: superuser/staff ou membre du groupe 'partnerships'
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or u.is_staff:
            return True
        return u.groups.filter(name="partnerships").exists()
