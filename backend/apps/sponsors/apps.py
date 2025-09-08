from __future__ import annotations

from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class SponsorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sponsors"

    def ready(self):
        from .models import Sponsor, Sponsorship, SponsorTier
        from .signals import sponsorship_changed_recompute, sponsorship_emit_webhook, sponsor_logo_check  # noqa: F401

        # Recalcul métriques + webhooks
        post_save.connect(sponsorship_changed_recompute, sender=Sponsorship, dispatch_uid="sponsorship_save_recompute")
        post_delete.connect(sponsorship_changed_recompute, sender=Sponsorship, dispatch_uid="sponsorship_delete_recompute")
        post_save.connect(sponsorship_emit_webhook, sender=Sponsorship, dispatch_uid="sponsorship_save_webhook")
        # Logo content-type checker (non-blocking)
        post_save.connect(sponsor_logo_check, sender=Sponsor, dispatch_uid="sponsor_logo_check")
