# Festival — apps/core (README)

## Rôle & Vision
Cœur du domaine : **Éditions**, **Lieux**, **Scènes**, **Contacts**. Source de vérité temporelle et structurelle.

**Objectifs (avec roadmap transverse V2+)**
- **Activation unique** d’une édition : lorsqu’une édition passe `is_active=true`, toutes les autres sont désactivées (transaction + signal).
- Endpoint **Résumé KPI** `/api/core/editions/{id}/summary` (V2+) : nb stages, slots par statut, news publiées, sponsors visibles, tickets en vente.
- **Webhooks** : `core.edition.activated` (payload minimal : id, year, timestamps).
- **i18n (V2+)** : champs localisés pour `name`, `tagline`.

## Modèles & contraintes
- `FestivalEdition(year, start_date, end_date, tagline, hero_image, is_active)`
  - Validation : `end_date >= start_date`; `year` unique; index sur `(start_date, end_date)`.
- `Venue` (+ `AddressMixin`) : `name` unique, `description`, `map_url`.
- `Stage(edition, venue, name, covered, capacity)`
  - Unicité `(edition, name)` ; ordering par `name`.
- `Contact(edition, type, label, email, phone, notes)`
  - Unicité `(edition, type, label)` ; `type ∈ {press, artist_rel, public, tech}`.

## API (DRF)
- `GET/POST /api/core/editions/` ; `GET/PUT/PATCH/DELETE /api/core/editions/{id}/`
  - Filtres : `year`, `is_active` ; recherche : `name,tagline` ; tri : `year,start_date,created_at` (def `-year`).
- `.../venues/` : filtres `country,city` ; recherche `name,address,city` ; tri `name,created_at`.
- `.../stages/` : filtres `edition,venue,covered` ; recherche `name,venue__name` ; tri `name,created_at`.
- `.../contacts/` : filtres `edition,type` ; recherche `label,email,phone` ; tri `type,label,created_at`.
- (V2+) `GET /api/core/editions/{id}/summary` (voir format dans doc globale).

## Validation & règles
- `FestivalEdition.is_active` : bascule atomique (désactivation des autres) + webhook.
- `Stage` : interdiction de duplication par (édition,nom).

## Permissions
- `viewer` (lecture), `editor` (CRUD scindé par édition), `admin` (tous droits).

## Cache & Observabilité
- Purge ciblée du cache public à l’activation d’une édition.
- Metric : `core_active_edition{year}` (gauge=1 pour l’active).

## Tests
- Validation dates édition ; unicité `(edition,name)` ; activation unique (tests d’intégration).

## Exemples `curl`
```bash
curl -s '/api/core/editions/?is_active=true'
```

## Roadmap dédiée
- Génération auto de jours d’édition (service utilitaire).
- `/summary` agrégé (joins + counts optimisés).
- Audit Trail sur changements d’édition.
