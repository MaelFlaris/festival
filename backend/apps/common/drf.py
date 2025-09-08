# apps/common/drf.py
from __future__ import annotations

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.viewsets import GenericViewSet


def enforce_readonly_for_anonymous(view_cls):
    """Décorateur simple pour verrouiller en lecture anonyme."""
    view_cls.permission_classes = [IsAuthenticatedOrReadOnly]
    return view_cls


class ReadonlyForAnonymousViewSet(GenericViewSet):
    """Base ViewSet imposant IsAuthenticatedOrReadOnly."""
    permission_classes = [IsAuthenticatedOrReadOnly]
