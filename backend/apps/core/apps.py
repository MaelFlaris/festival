from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        from .services import edition_activated
        from .metrics import set_active_edition_metric
        from .cache_utils import purge_public_cache
        from .webhooks import post_webhook

        def _on_edition_activated(sender, instance, payload, **kwargs):
            # Webhook
            post_webhook('core.edition.activated', payload)
            # Cache purge ciblée
            purge_public_cache(keys=[f"edition:{instance.id}", "homepage", "menu"])
            # Metric
            try:
                set_active_edition_metric(instance.year)
            except Exception:
                pass

        edition_activated.connect(_on_edition_activated, dispatch_uid="core_on_edition_activated")
