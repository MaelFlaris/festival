from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete


class TicketsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tickets"

    def ready(self):
        from .models import TicketType
        from .signals import (
            cache_version_bump,
            remember_old_sale_state,
            emit_sale_window_webhooks_and_recompute_metrics,
        )

        pre_save.connect(remember_old_sale_state, sender=TicketType, dispatch_uid="tickets_pre_save_remember")
        post_save.connect(emit_sale_window_webhooks_and_recompute_metrics, sender=TicketType,
                          dispatch_uid="tickets_post_save_emit")
        post_save.connect(cache_version_bump, sender=TicketType, dispatch_uid="tickets_post_save_cache_bump")
        post_delete.connect(cache_version_bump, sender=TicketType, dispatch_uid="tickets_post_delete_cache_bump")
