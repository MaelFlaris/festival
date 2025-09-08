# backend/apps/tickets/models.py
from __future__ import annotations

from decimal import Decimal
from typing import Dict

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.core.models import FestivalEdition


class Currency(models.TextChoices):
    EUR = "EUR", "Euro"


class PricePhase(models.TextChoices):
    EARLY = "early", "Early"
    REGULAR = "regular", "Regular"
    LATE = "late", "Late"


PHASE_ORDER = ["early", "regular", "late"]


class TicketType(TimeStampedModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="ticket_types")
    code = models.CharField(max_length=32, db_index=True)  # ex: PASS1J, PASS3J, EARLY
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    day = models.DateField(null=True, blank=True, help_text="Si billet 1 jour, renseigner la date")

    # Prix TTC par défaut ; calculs net/TVA exposés en lecture
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EUR)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("20.0"), help_text="TVA %")

    # Phases tarifaires (V2)
    phase = models.CharField(max_length=10, choices=PricePhase.choices, default=PricePhase.REGULAR, db_index=True)

    # Quotas
    quota_total = models.PositiveIntegerField(default=0)
    quota_reserved = models.PositiveIntegerField(default=0)
    quota_by_channel = models.JSONField(default=dict, blank=True, help_text='{"online": 0, "partner": 0} (≤ quota_total)')
    reserved_by_channel = models.JSONField(default=dict, blank=True, help_text='{"online": 0, "partner": 0} (≤ quota_by_channel)')

    # Fenêtres de vente
    sale_start = models.DateTimeField(null=True, blank=True)
    sale_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = [("edition", "code")]
        ordering = ["code"]
        indexes = [
            models.Index(fields=["edition", "phase", "is_active"]),
            models.Index(fields=["edition", "day", "is_active"]),
        ]
        permissions = [
            ("manage_pricing", "Peut gérer phases/prix"),
        ]

    # ---- Validations -------------------------------------------------------

    def clean(self):
        if self.quota_reserved > self.quota_total:
            raise ValidationError("quota_reserved > quota_total")
        if self.sale_start and self.sale_end and self.sale_end <= self.sale_start:
            raise ValidationError("sale_end doit être > sale_start")
        if self.day and not (self.edition.start_date <= self.day <= self.edition.end_date):
            raise ValidationError("day du billet 1J doit être dans l’édition")

        # quotas par canal: somme ≤ quota_total
        if self.quota_by_channel:
            s = int(sum(int(v or 0) for v in self.quota_by_channel.values()))
            if s > int(self.quota_total):
                raise ValidationError({"quota_by_channel": "Somme des quotas par canal > quota_total"})

        # réservations par canal: somme ≤ quota_reserved et ≤ quota_by_channel/canal
        if self.reserved_by_channel:
            s = int(sum(int(v or 0) for v in self.reserved_by_channel.values()))
            if s > int(self.quota_reserved):
                raise ValidationError({"reserved_by_channel": "Somme réservée par canal > quota_reserved"})
            for ch, cnt in self.reserved_by_channel.items():
                ch_quota = int((self.quota_by_channel or {}).get(ch, self.quota_total))
                if int(cnt or 0) > ch_quota:
                    raise ValidationError({"reserved_by_channel": f"Canal '{ch}' dépasse son quota ({cnt}>{ch_quota})"})

    # ---- Propriétés/Helpers ------------------------------------------------

    @property
    def quota_remaining(self) -> int:
        return max(0, int(self.quota_total) - int(self.quota_reserved))

    def is_on_sale(self) -> bool:
        now = timezone.now()
        if not self.is_active:
            return False
        if self.sale_start and now < self.sale_start:
            return False
        if self.sale_end and now > self.sale_end:
            return False
        return self.quota_remaining > 0

    @property
    def price_vat_amount(self) -> Decimal:
        # price TTC -> VAT amount
        rate = (self.vat_rate or Decimal("0")) / Decimal("100")
        # VAT part from gross: price * rate / (1 + rate)
        return (self.price * rate / (Decimal("1") + rate)).quantize(Decimal("0.01"))

    @property
    def price_net(self) -> Decimal:
        return (self.price - self.price_vat_amount).quantize(Decimal("0.01"))

    # Phase helpers
    def next_phase(self) -> str | None:
        try:
            i = PHASE_ORDER.index(self.phase)
            return PHASE_ORDER[i + 1]
        except Exception:
            return None
