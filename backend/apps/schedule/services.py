# apps/schedule/services.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from django.core.cache import cache
from django.db.models import Q

from apps.core.models import FestivalEdition, Stage
from .models import Slot, SlotStatus


# ---------------------------------------------------------------------------
# Conflits
# ---------------------------------------------------------------------------

@dataclass
class Conflict:
    slot_id: int
    start: str
    end: str
    artist: str

    def to_dict(self) -> Dict:
        return asdict(self)


def _overlap(a_start, a_end, b_start, b_end) -> bool:
    # chevauchement strict (frontières ouvertes)
    return a_start < b_end and a_end > b_start


def find_conflicts(
    *,
    edition_id: int,
    stage_id: int,
    day,
    start_time,
    end_time,
    exclude_id: Optional[int] = None,
) -> List[Conflict]:
    qs = Slot.objects.select_related("artist").filter(
        edition_id=edition_id,
        stage_id=stage_id,
        day=day,
    ).exclude(status=SlotStatus.CANCELED)
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)

    conflicts: List[Conflict] = []
    for s in qs:
        if _overlap(start_time, end_time, s.start_time, s.end_time):
            conflicts.append(Conflict(slot_id=s.id, start=str(s.start_time), end=str(s.end_time), artist=s.artist.name))
    return conflicts


def find_conflicts_for_slot_queryset(slot: Slot) -> List[Conflict]:
    return find_conflicts(
        edition_id=slot.edition_id,
        stage_id=slot.stage_id,
        day=slot.day,
        start_time=slot.start_time,
        end_time=slot.end_time,
        exclude_id=slot.id,
    )


# ---------------------------------------------------------------------------
# Copie par template (édition N-1 -> N)
# ---------------------------------------------------------------------------

@dataclass
class TemplateCopyResult:
    created: int
    skipped_out_of_range: int
    skipped_conflicts: int
    total_source: int

    def to_dict(self): return asdict(self)


def copy_template(
    *,
    from_edition_id: int,
    to_edition_id: int,
    stage_map: Optional[Dict[str, str]] = None,
    status: str = SlotStatus.TENTATIVE,
    dry_run: bool = False,
) -> TemplateCopyResult:
    src = FestivalEdition.objects.get(pk=from_edition_id)
    dst = FestivalEdition.objects.get(pk=to_edition_id)
    offset_days = (dst.start_date - src.start_date).days

    stage_map = stage_map or {}
    created = skipped_out = skipped_conf = 0

    source_slots = Slot.objects.filter(edition_id=src.id).order_by("day", "stage_id", "start_time")
    for s in source_slots:
        new_day = s.day + timedelta(days=offset_days)
        if not (dst.start_date <= new_day <= dst.end_date):
            skipped_out += 1
            continue

        new_stage_id = int(stage_map.get(str(s.stage_id), s.stage_id))
        conflicts = find_conflicts(
            edition_id=dst.id,
            stage_id=new_stage_id,
            day=new_day,
            start_time=s.start_time,
            end_time=s.end_time,
            exclude_id=None,
        )
        if conflicts:
            skipped_conf += 1
            continue

        if not dry_run:
            Slot.objects.create(
                edition_id=dst.id,
                stage_id=new_stage_id,
                artist_id=s.artist_id,
                day=new_day,
                start_time=s.start_time,
                end_time=s.end_time,
                status=status,
                is_headliner=s.is_headliner,
                setlist_urls=s.setlist_urls,
                tech_rider=s.tech_rider,
                notes=f"[copied from {src.year}] {s.notes or ''}".strip(),
            )
        created += 1

    return TemplateCopyResult(
        created=created,
        skipped_out_of_range=skipped_out,
        skipped_conflicts=skipped_conf,
        total_source=source_slots.count(),
    )
