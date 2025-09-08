from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandParser

from apps.lineup.models import Artist, Genre


class Command(BaseCommand):
    help = "Importe/enrichit des artistes depuis un fichier JSON (liste d'objets)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("path", type=str, help="Chemin du JSON (liste)")
        parser.add_argument("--update-by", choices=["id", "slug", "name"], default="slug")
        parser.add_argument("--create-missing", action="store_true", default=False)

    def handle(self, *args, **options):
        path = Path(options["path"])
        data = json.loads(path.read_text(encoding="utf-8"))
        upby = options["update_by"]
        created, updated, skipped = 0, 0, 0
        for item in data:
            key = str(item.get(upby) or "")
            if not key:
                skipped += 1
                continue
            qs = Artist.objects
            if upby == "id":
                qs = qs.filter(id=int(key))
            elif upby == "slug":
                qs = qs.filter(slug=key)
            else:
                qs = qs.filter(name=key)
            obj = qs.first()
            if not obj:
                if not options["create_missing"]:
                    skipped += 1
                    continue
                obj = Artist(name=item.get("name") or key)
                created += 1
            else:
                updated += 1

            for f in ("country", "short_bio", "long_bio", "picture", "banner", "website", "socials", "external_ids", "popularity"):
                if f in item and item[f] is not None:
                    setattr(obj, f, item[f])
            obj.full_clean()
            obj.save()

            # genres: liste de noms
            gnames = item.get("genres") or []
            if gnames:
                gids = []
                for gn in gnames:
                    g, _ = Genre.objects.get_or_create(name=str(gn))
                    gids.append(g.id)
                obj.genres.set(gids)

        self.stdout.write(self.style.SUCCESS(f"created={created} updated={updated} skipped={skipped}"))
