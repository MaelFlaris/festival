from __future__ import annotations

from django.apps import AppConfig
from django.contrib.auth.signals import user_logged_in


class AuthxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authx"

    def ready(self):
        # Enregistre les receivers (webhooks, metrics, diff…) définis dans signals.py
        from . import signals  # noqa: F401

        # Hydratation opportuniste du profil à la connexion
        from .services import hydrate_profile_from_request

        def _on_login(sender, request, user, **kwargs):
            try:
                hydrate_profile_from_request(user, request)
            except Exception:
                # Best-effort : ne doit pas bloquer l’auth
                pass

        user_logged_in.connect(_on_login, dispatch_uid="authx_on_login_hydrate")
