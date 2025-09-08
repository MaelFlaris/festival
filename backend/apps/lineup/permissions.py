# apps/lineup/permissions.py
from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsBookerOrReadOnly(BasePermission):
    """
    - Lecture: ouverte
    - Écriture: user staff/superuser ou membre du groupe 'booker'
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser or u.is_staff:
            return True
        return u.groups.filter(name="booker").exists()
