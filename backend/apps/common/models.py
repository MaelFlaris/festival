# backend/apps/common/models.py
from django.db import models
from django.core.exceptions import ValidationError 
from django.utils import timezone 
from .services import unique_slugify
from .validators import validate_country_iso2
from .signals import publish_status_changed, soft_deleted

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    class Meta:
        abstract = True

class SluggedModel(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    class Meta:
        abstract = True
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, slug_field_name="slug", max_length=220)
        super().save(*args, **kwargs)

class PublishStatus(models.TextChoices):
    DRAFT = "draft", "Brouillon"
    REVIEW = "review", "Relecture"
    PUBLISHED = "published", "Publié"
    ARCHIVED = "archivé", "Archivé"


class PublishableModel(models.Model):
    status = models.CharField(max_length=12, choices=PublishStatus.choices, default=PublishStatus.DRAFT, db_index=True)
    publish_at = models.DateTimeField(null=True, blank=True)
    unpublish_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.publish_at and self.unpublish_at and self.publish_at >= self.unpublish_at:
            raise ValidationError({"unpublish_at": "Doit être postérieure à publish_at."})

    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            old_status = type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first()
        super().save(*args, **kwargs)
        if old_status is not None and old_status != self.status:
            publish_status_changed.send(
                sender=type(self),
                instance=self,
                old_status=old_status,
                new_status=self.status,
            )
            
            
class AddressMixin(models.Model):
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(
        max_length=2,
        blank=True,
        validators=[validate_country_iso2],
        help_text="Code ISO-3166-1 alpha-2 (FR, BE, …)",
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        abstract = True

    def clean(self):
        from .services import normalize_iso2
        if self.country:
            self.country = normalize_iso2(self.country)
        return super().clean()

class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):  # bulk soft delete
        now = timezone.now()
        return super().update(deleted_at=now)

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        return bool(self.deleted_at)

    def delete(self, using=None, keep_parents=False):
        if self.deleted_at:
            return  # idempotent
        self.deleted_at = timezone.now()
        super().save(update_fields=["deleted_at"])
        soft_deleted.send(sender=type(self), instance=self)

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def undelete(self):
        if not self.deleted_at:
            return
        self.deleted_at = None
        super().save(update_fields=["deleted_at"])
        
        
class GeoMixin(models.Model):
    """
    Ajoute un geohash et un SRID. Suppose l'existence de champs latitude/longitude
    (ex: combiné avec AddressMixin).
    """
    geohash = models.CharField(max_length=12, blank=True, db_index=True)
    srid = models.IntegerField(default=4326, help_text="Système de référence (4326=WGS84)")

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Calcule un geohash 9 (≈ 2.4m) si lat/lon présents
        lat = getattr(self, "latitude", None)
        lon = getattr(self, "longitude", None)
        if lat is not None and lon is not None:
            self.geohash = geohash_encode(float(lat), float(lon), precision=9)
        super().save(*args, **kwargs)

    def distance_km_to(self, other_lat: float, other_lon: float) -> float:
        lat = getattr(self, "latitude", None)
        lon = getattr(self, "longitude", None)
        if lat is None or lon is None:
            raise ValueError("latitude/longitude manquants sur l'instance")
        return haversine_km(float(lat), float(lon), float(other_lat), float(other_lon))