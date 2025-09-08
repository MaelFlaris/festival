# backend/apps/tickets/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.common.models import TimeStampedModel
from apps.core.models import FestivalEdition

class Currency(models.TextChoices):
    EUR = "EUR", "Euro"

class TicketType(TimeStampedModel):
    edition = models.ForeignKey(FestivalEdition, on_delete=models.CASCADE, related_name="ticket_types")
    code = models.CharField(max_length=32, db_index=True)  # ex: PASS1J, PASS3J, EARLY
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    day = models.DateField(null=True, blank=True, help_text="Si billet 1 jour, renseigner la date")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.EUR)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=20.0, help_text="TVA %")
    quota_total = models.PositiveIntegerField(default=0)
    quota_reserved = models.PositiveIntegerField(default=0)
    sale_start = models.DateTimeField(null=True, blank=True)
    sale_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = [("edition", "code")]
        ordering = ["code"]

    def clean(self):
        if self.quota_reserved > self.quota_total:
            raise ValidationError("quota_reserved > quota_total")
        if self.sale_start and self.sale_end and self.sale_end <= self.sale_start:
            raise ValidationError("sale_end doit être > sale_start")
        if self.day and not (self.edition.start_date <= self.day <= self.edition.end_date):
            raise ValidationError("day du billet 1J doit être dans l’édition")

    @property
    def quota_remaining(self):
        return max(0, self.quota_total - self.quota_reserved)

    def is_on_sale(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.sale_start and now < self.sale_start:
            return False
        if self.sale_end and now > self.sale_end:
            return False
        return True
