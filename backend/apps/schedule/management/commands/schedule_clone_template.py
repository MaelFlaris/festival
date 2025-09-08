from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError

from apps.core.models import FestivalEdition
from apps.schedule.models import Slot, SlotStatus
from apps.schedule.services import find_conflicts


class Command(BaseCommand):
    help = "Clone all slots from a source edition to a destination edition, with optional day shift."

    def add_arguments(self, parser):
        parser.add_argument("--from", dest="from_ed", type=int, required=True, help="Source edition id")
        parser.add_argument("--to", dest="to_ed", type=int, required=True, help="Destination edition id")
        parser.add_argument("--shift-days", dest="shift_days", type=int, default=None,
                            help="Optional fixed day shift applied to all slots")

    def handle(self, *args, **opts):
        from_ed = opts.get("from_ed")
        to_ed = opts.get("to_ed")
        shift_days = opts.get("shift_days")
        if not from_ed or not to_ed:
            raise CommandError("--from and --to are required")

        src = FestivalEdition.objects.get(pk=from_ed)
        dst = FestivalEdition.objects.get(pk=to_ed)
        offset = shift_days if shift_days is not None else (dst.start_date - src.start_date).days

        created = skipped_out = skipped_dupe = skipped_conf = 0
        source_slots = Slot.objects.filter(edition_id=src.id).order_by("day", "stage_id", "start_time")
        for s in source_slots:
            new_day = s.day + timedelta(days=offset)
            if not (dst.start_date <= new_day <= dst.end_date):
                skipped_out += 1
                continue

            # check dupes: stage+day+start_time+artist
            if Slot.objects.filter(
                edition_id=dst.id, stage_id=s.stage_id, day=new_day,
                start_time=s.start_time, artist_id=s.artist_id
            ).exists():
                skipped_dupe += 1
                continue

            # check overlaps on destination stage/day/time
            conf = find_conflicts(
                edition_id=dst.id, stage_id=s.stage_id, day=new_day,
                start_time=s.start_time, end_time=s.end_time
            )
            if conf:
                skipped_conf += 1
                continue

            Slot.objects.create(
                edition_id=dst.id,
                stage_id=s.stage_id,
                artist_id=s.artist_id,
                day=new_day,
                start_time=s.start_time,
                end_time=s.end_time,
                status=SlotStatus.TENTATIVE,
                is_headliner=s.is_headliner,
                setlist_urls=s.setlist_urls,
                tech_rider=s.tech_rider,
                notes=f"[copied from {src.year}] {s.notes or ''}".strip(),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Cloned {created}/{source_slots.count()} slots (out_of_range={skipped_out}, duplicates={skipped_dupe}, conflicts={skipped_conf})."
        ))

