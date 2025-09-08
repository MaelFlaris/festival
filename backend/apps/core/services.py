from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Optional, Dict, Any

from django.db import transaction
from django.dispatch import Signal
from django.apps import apps

from .models import FestivalEdition

edition_activated: Signal = Signal()  # provides: instance, payload

@dataclass
class EditionActivatedPayload:
    id: int
    year: int
    is_active: bool

@transaction.atomic
def activate_edition(edition: FestivalEdition) -> FestivalEdition:
    FestivalEdition.objects.exclude(pk=edition.pk).filter(is_active=True).update(is_active=False)
    if not edition.is_active:
        edition.is_active = True
        edition.save(update_fields=["is_active"])
    payload = EditionActivatedPayload(id=edition.id, year=edition.year, is_active=edition.is_active)
    edition_activated.send(sender=FestivalEdition, instance=edition, payload=asdict(payload))
    return edition

def _safe_count(model_label: str, **filters) -> int:
    """Compte si l'app/modèle existe, sinon 0."""
    try:
        Model = apps.get_model(model_label)
        return Model.objects.filter(**filters).count()
    except Exception:
        return 0

def get_edition_summary(edition: FestivalEdition) -> Dict[str, Any]:
    """Agrégats cross-apps. Fallback = 0 si l’app n’est pas installée."""
    # core
    nb_stages = edition.stages.count()

    # schedule/slots par statut (exemple: apps.schedule.Slot(status, edition FK))
    slots_total = _safe_count('schedule.Slot', edition=edition)
    slots_published = _safe_count('schedule.Slot', edition=edition, status='published')
    slots_draft = _safe_count('schedule.Slot', edition=edition, status='draft')
    slots_cancelled = _safe_count('schedule.Slot', edition=edition, status='cancelled')

    # news publiées (apps.news.News visible/publication liée à edition)
    news_published = _safe_count('news.News', edition=edition, is_published=True)

    # sponsors visibles (apps.sponsors.Sponsor visible/edition)
    sponsors_visible = _safe_count('sponsors.Sponsor', edition=edition, visible=True)

    # tickets en vente (apps.tickets.TicketType active/edition)
    tickets_on_sale = _safe_count('tickets.TicketType', edition=edition, on_sale=True)

    return {
        "edition": {"id": edition.id, "year": edition.year, "name": edition.name},
        "stages": {"count": nb_stages},
        "slots": {
            "total": slots_total,
            "published": slots_published,
            "draft": slots_draft,
            "cancelled": slots_cancelled,
        },
        "news": {"published": news_published},
        "sponsors": {"visible": sponsors_visible},
        "tickets": {"on_sale": tickets_on_sale},
    }
