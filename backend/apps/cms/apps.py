from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.common.signals import publish_status_changed
from .services import (
    bump_public_cache_version,
    dispatch_publish_webhook,
)


class CmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cms"

    def ready(self):
        # Enregistrement des receivers pour webhooks de publication
        from .models import Page, News
        from apps.common.models import PublishStatus

        @receiver(publish_status_changed, sender=Page)
        def _on_page_status(sender, instance: Page, old_status, new_status, **kwargs):
            dispatch_publish_webhook(instance, old_status, new_status)
            bump_public_cache_version()

        @receiver(publish_status_changed, sender=News)
        def _on_news_status(sender, instance: News, old_status, new_status, **kwargs):
            dispatch_publish_webhook(instance, old_status, new_status)
            bump_public_cache_version()

        @receiver(post_save, sender=Page)
        def _on_page_saved(sender, instance: Page, **kwargs):
            if instance.status == PublishStatus.PUBLISHED:
                bump_public_cache_version()

        @receiver(post_delete, sender=Page)
        def _on_page_deleted(sender, instance: Page, **kwargs):
            bump_public_cache_version()

        @receiver(post_save, sender=News)
        def _on_news_saved(sender, instance: News, **kwargs):
            if instance.status == PublishStatus.PUBLISHED:
                bump_public_cache_version()

        @receiver(post_delete, sender=News)
        def _on_news_deleted(sender, instance: News, **kwargs):
            bump_public_cache_version()
