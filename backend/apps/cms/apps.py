from __future__ import annotations

from django.apps import AppConfig
from django.dispatch import receiver

from apps.common.signals import publish_status_changed
from .services import dispatch_publish_webhook


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cms"

    def ready(self):
        # Enregistrement des receivers pour webhooks de publication
        from .models import Page, News

        @receiver(publish_status_changed, sender=Page)
        def _on_page_status(sender, instance: Page, old_status, new_status, **kwargs):
            dispatch_publish_webhook(instance, old_status, new_status)

        @receiver(publish_status_changed, sender=News)
        def _on_news_status(sender, instance: News, old_status, new_status, **kwargs):
            dispatch_publish_webhook(instance, old_status, new_status)
