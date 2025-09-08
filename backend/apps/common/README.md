# Festival — apps/common (README)

## Rôle & Vision
Fournir des **fondations transverses** (mixins & conventions) pour homogénéiser toutes les apps : horodatage, slugs, publication, adresses, soft-delete, versioning et géolocalisation légère.

## Modèles fournis
- **TimeStampedModel** : `created_at`, `updated_at` (indexés).
- **SluggedModel** : `name`, `slug` unique (auto-généré via `unique_slugify`, anti-collision).
- **PublishStatus** (`draft|review|published|archivé`) et **PublishableModel** : `status`, `publish_at`, `unpublish_at` + validation de fenêtre + **signal `publish_status_changed`**.
- **SoftDeleteModel** : `deleted_at` (+ managers/scopes `.objects`=vivants, `.all_objects`=tous, `.alive()/.dead()`), méthodes `delete()` (soft), `hard_delete()`, `undelete()`, **signal `soft_deleted`**.
- **AddressMixin** : `address`, `city`, `postal_code`, `country` (validator ISO-3166-1 alpha-2), `latitude`, `longitude` (décimaux).
- **GeoMixin** : `geohash`, `srid=4326` + calcul automatique du geohash à l’enregistrement, helper `distance_km_to()` (haversine).

## Webhooks & Observabilité
- **Signals** : `publish_status_changed`, `soft_deleted`.
- **Webhooks** (optionnels) via `dispatch_webhook(event, payload)` :
  - Configure **`settings.COMMON_WEBHOOK_URLS = ["https://..."]`**.
  - Optionnel : **`settings.COMMON_WEBHOOK_SECRET = "…"``** → signature HMAC SHA-256 en header `X-Common-Signature`.
- Les receivers sont branchés dans `CommonConfig.ready()`.

## Versioning (facultatif)
- **VersionedModel** : intègre `simple_history` si installé (fallback no-op sinon).
- Utilisation : hériter de `VersionedModel` dans les modèles concrets.

## Sécurité & DRF
- `ReadonlyForAnonymousViewSet` et décorateur `enforce_readonly_for_anonymous`.
- Pas d’API exposée par common (seulement des mixins, serializers utilitaires).

## Tests attendus
- Slug anti-collision et troncature.
- Validation ISO2 (serializer + validator modèle).
- Haversine & geohash cohérents.
- Soft-delete scopes : `.objects` vs `.all_objects`, `undelete()`.

## Intégration rapide (exemple)
Dans un modèle concret :
- Hérite de `TimeStampedModel`, `SluggedModel`, `PublishableModel`, `SoftDeleteModel`, `AddressMixin`, `GeoMixin` selon besoin.
- Pour l’historique : ajouter `VersionedModel` si `simple_history` disponible.
