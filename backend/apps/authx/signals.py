# apps/authx/signals.py
from __future__ import annotations

from typing import Dict, List

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .metrics import PROFILE_UPDATES_TOTAL
from .models import UserProfile
from .services import emit_profile_updated_webhook


# On mémorise un snapshot minimal avant sauvegarde pour détecter les changements clés
_PRE_SAVE_CACHE: Dict[int, Dict[str, object]] = {}


@receiver(pre_save, sender=UserProfile)
def _profile_pre_save(sender, instance: UserProfile, **kwargs):
    if not instance.pk:
        return
    try:
        prev = sender.objects.only("display_name", "avatar", "preferences", "consents").get(pk=instance.pk)
        _PRE_SAVE_CACHE[instance.pk] = {
            "display_name": prev.display_name,
            "avatar": prev.avatar,
            "preferences": prev.preferences,
            "consents": prev.consents,
        }
    except sender.DoesNotExist:
        pass


@receiver(post_save, sender=UserProfile)
def _profile_post_save(sender, instance: UserProfile, created: bool, **kwargs):
    changed: List[str] = []
    prev = _PRE_SAVE_CACHE.pop(instance.pk, {}) if instance.pk in _PRE_SAVE_CACHE else {}

    def _has_changed(field: str) -> bool:
        return prev.get(field) != getattr(instance, field)

    for f in ("display_name", "avatar", "preferences", "consents"):
        if created or _has_changed(f):
            changed.append(f)

    # métriques par champ
    for f in changed:
        PROFILE_UPDATES_TOTAL.labels(field=f).inc()

    # webhook
    try:
        emit_profile_updated_webhook(instance, changed_fields=changed)
    except Exception:
        # jamais bloquant
        pass
