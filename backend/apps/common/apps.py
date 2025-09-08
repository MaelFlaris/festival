# apps/common/apps.py
from __future__ import annotations

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"

    def ready(self):
        # Enregistrer les receivers pour webhooks/observabilité
        from django.dispatch import receiver  # noqa
        from .signals import publish_status_changed, soft_deleted  # noqa
        from .services import dispatch_webhook  # noqa

        @receiver(publish_status_changed)
        def _on_publish_status_changed(sender, instance, old_status, new_status, **kwargs):
            try:
                payload = {
                    "event": "publish_status_changed",
                    "model": f"{sender._meta.app_label}.{sender.__name__}",
                    "pk": instance.pk,
                    "old_status": old_status,
                    "new_status": new_status,
                }
                dispatch_webhook("publish_status_changed", payload)
            except Exception:
                # Ne bloque pas la transaction applicative
                pass

        @receiver(soft_deleted)
        def _on_soft_deleted(sender, instance, **kwargs):
            try:
                payload = {
                    "event": "soft_deleted",
                    "model": f"{sender._meta.app_label}.{sender.__name__}",
                    "pk": instance.pk,
                    "deleted_at": getattr(instance, "deleted_at", None).isoformat() if getattr(instance, "deleted_at", None) else None,
                }
                dispatch_webhook("soft_deleted", payload)
            except Exception:
                pass

        # Autorise des modules utilitaires dans d'autres apps (ex: admin_mixins.py)
        try:
            autodiscover_modules("admin_mixins")
        except Exception:
            pass