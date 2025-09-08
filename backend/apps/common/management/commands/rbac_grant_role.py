from __future__ import annotations

from typing import Iterable, List, Tuple

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from guardian.shortcuts import assign_perm


ROLE_MAP = {
    # model label (app_label.ModelName) -> role -> list of permission codenames (without app_label)
    "cms.Page": {
        "viewer": ["view_page"],
        "editor": ["view_page", "change_page", "delete_page", "publish_page"],
    },
    "cms.News": {
        "viewer": ["view_news"],
        "editor": ["view_news", "change_news", "delete_news", "publish_news"],
    },
    "sponsors.Sponsorship": {
        "viewer": ["view_sponsorship"],
        "editor": ["view_sponsorship", "change_sponsorship", "delete_sponsorship", "view_financials"],
    },
    "schedule.Slot": {
        "viewer": ["view_slot"],
        "editor": ["view_slot", "change_slot", "delete_slot", "manage_slot"],
    },
    "tickets.TicketType": {
        "viewer": ["view_tickettype"],
        "editor": ["view_tickettype", "change_tickettype", "delete_tickettype", "manage_pricing"],
    },
    # lineup (example editor role)
    "lineup.Artist": {
        "viewer": ["view_artist"],
        "editor": ["view_artist", "change_artist", "delete_artist"],
    },
    "lineup.Genre": {
        "viewer": ["view_genre"],
        "editor": ["view_genre", "change_genre", "delete_genre"],
    },
    "lineup.ArtistAvailability": {
        "viewer": ["view_artistavailability"],
        "editor": ["view_artistavailability", "change_artistavailability", "delete_artistavailability"],
    },
}


class Command(BaseCommand):
    help = "Grant object-level permissions mapped by a simple role to a user or group.\n\n" \
           "Usage: rbac_grant_role app_label.Model pk user:<username>|group:<name> role"

    def add_arguments(self, parser):
        parser.add_argument("model", help="app_label.ModelName")
        parser.add_argument("pk", type=int)
        parser.add_argument("principal", help="user:<username> or group:<name>")
        parser.add_argument("role", choices=["viewer", "editor"])

    def handle(self, *args, **opts):
        model_label: str = opts["model"]
        pk: int = opts["pk"]
        principal: str = opts["principal"]
        role: str = opts["role"]

        if model_label not in ROLE_MAP:
            raise CommandError(f"Unsupported model label: {model_label}")

        try:
            app_label, model_name = model_label.split(".")
            Model = apps.get_model(app_label, model_name)
        except Exception as exc:
            raise CommandError(f"Invalid model: {exc}")

        try:
            obj = Model.objects.get(pk=pk)
        except Model.DoesNotExist:
            raise CommandError("Object not found")

        target = None
        if principal.startswith("user:"):
            username = principal.split(":", 1)[1]
            User = get_user_model()
            try:
                target = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError("User not found")
        elif principal.startswith("group:"):
            name = principal.split(":", 1)[1]
            try:
                target = Group.objects.get(name=name)
            except Group.DoesNotExist:
                raise CommandError("Group not found")
        else:
            raise CommandError("principal must be user:<username> or group:<name>")

        perms = ROLE_MAP[model_label][role]
        granted = []
        for codename in perms:
            full = f"{obj._meta.app_label}.{codename}"
            assign_perm(full, target, obj)
            granted.append(full)
        self.stdout.write(self.style.SUCCESS(f"Granted {len(granted)} perms: {', '.join(granted)}"))

