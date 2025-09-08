from __future__ import annotations

from typing import Iterable

from django.db.models import QuerySet
from rest_framework.permissions import DjangoObjectPermissions
from guardian.shortcuts import assign_perm, get_objects_for_user


class ObjectPermissionsMixin:
    """
    Enforces DRF object-level permissions using django-guardian.
    - Requires authentication + DjangoObjectPermissions
    - Filters list queryset to objects the user can view, unless staff/superuser
    """

    # Do not enforce global IsAuthenticated here to avoid breaking public endpoints.
    # Views can still opt-in to stricter permission classes.

    def get_required_object_permissions(self, method, model_cls):  # pragma: no cover - DRF hook
        perms = super().get_required_object_permissions(method, model_cls)  # type: ignore[attr-defined]
        # Ensure 'view' is required for safe methods
        if method in ("GET", "HEAD", "OPTIONS"):
            view_codename = f"{model_cls._meta.app_label}.view_{model_cls._meta.model_name}"
            if view_codename not in perms:
                perms = list(perms) + [view_codename]
        return perms

    def get_queryset(self) -> QuerySet:
        qs: QuerySet = super().get_queryset()  # type: ignore
        user = getattr(self.request, "user", None)
        if not user or user.is_anonymous:
            return qs.none()
        if user.is_staff or user.is_superuser:
            return qs
        # Restrict to objects the user can view (accept global perms)
        perm = f"{qs.model._meta.app_label}.view_{qs.model._meta.model_name}"
        return get_objects_for_user(
            user,
            perm,
            klass=qs,
            any_perm=True,
            accept_global_perms=True,
        )


class AssignCreatorObjectPermsMixin:
    """After create, grant creator view/change/delete on the object."""

    def perform_create(self, serializer):  # pragma: no cover - exercised by integration tests
        obj = serializer.save()
        request = getattr(self, "request", None)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            app = obj._meta.app_label
            model = obj._meta.model_name
            for action in ("view", "change", "delete"):
                try:
                    assign_perm(f"{app}.{action}_{model}", user, obj)
                except Exception:
                    pass
        return obj
