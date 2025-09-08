# Festival — apps/common (README)

## Rôle & Vision
Fournir des **fondations transverses** (mixins et conventions) pour homogénéiser toutes les apps : horodatage, slugs, publication, adresses.

**Objectifs (avec roadmap transverse V2+)**
- Abstractions solides et testées pour `TimeStampedModel`, `SluggedModel`, `PublishableModel`, `AddressMixin`.
- Prévoir **SoftDelete** et **Versioning / Audit Trail** (Django‑Simple‑History) pour historiser et restaurer.
- Exposer des **webhooks transverses** sur événements structurants (ex. suppression logique, changement de statut de publication).
- **i18n** des adresses (normalisation, geohash) et validation stricte des pays ISO‑3166‑1 alpha‑2.

## Modèles fournis
- `TimeStampedModel` : `created_at`, `updated_at` (indexés).
- `SluggedModel` : `name`, `slug` unique (auto‑généré via `slugify`, troncature 220 car.) avec stratégie anti‑collision (suffixe court).
- `PublishStatus` (`draft|review|published|archivé`), `PublishableModel` : `status`, `publish_at`, `unpublish_at`.
- `AddressMixin` : `address`, `city`, `postal_code`, `country`, `latitude`, `longitude`.

## Exigences & règles
- `SluggedModel.save()` renseigne le slug si absent ; garantit l’unicité (DB) et la stabilité.
- `PublishableModel` : validation (V2+) → si `publish_at` et `unpublish_at` présents : `publish_at < unpublish_at`.

## Sécurité & Permissions
- Pas d’API directe exposée ; utilisé par composition dans les autres apps.
- (V2+) Décorateurs utilitaires DRF pour imposer `IsAuthenticatedOrReadOnly` sur les modèles publiables.

## Observabilité
- (V2+) Signaux `post_save` sur modèles publiables → **invalidation cache** + **webhooks**.

## Tests attendus
- Génération de slug multi‑langue (y compris accents) ; max 220 caractères ; anti‑collision.
- Sérialisation d’adresses avec caractères non‑ASCII ; validation `country` ISO2.

## Roadmap dédiée
- `GeoMixin` (geohash, SRID, distance).
- `SoftDeleteModel` (champ `deleted_at`, scopes actifs/supprimés).
- `VersionedModel` (audit minimal) et intégration Django‑Simple‑History.
- Webhooks transverses (suppression logique, publication).
