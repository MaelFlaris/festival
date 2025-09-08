# Festival — apps/sponsors (README)

## Rôle & Vision
Gérer les **partenaires** par **tier** avec visibilité contrôlée, contrats et statistiques.

## Fonctionnalités
- **Validations** strictes : `website`, `logo`, `contract_url` en **https**.
- **Statistiques** (endpoint & métriques Prometheus) :
  - Montants par **tier** et par **édition** ; total visible.
  - Compteur/“gauge” de sponsors visibles par tier.
- **Webhooks** sur création/maj : `sponsors.sponsorship.created|updated` (+ payload minimal).
- **Contrats S3** (V2) :
  - `POST /api/sponsors/sponsorships/contracts/presign` → URL présignée **PUT** (S3) si config dispo.
  - `POST /api/sponsors/sponsorships/{id}/contracts/attach` → enregistre `contract_url` une fois l'upload réalisé.
- **Public** (V2) : `GET /api/sponsors/sponsorships/public/by-edition?edition=ID`
  - Regroupe par **tier** (ordre par `rank`), expose les sponsors visibles (nom, logo, site).

## API (DRF)
- CRUD `/api/sponsors/tiers|sponsors|sponsorships/`
  - Filtres `sponsorships` : `edition,tier,visible` ; recherche : `sponsor__name,tier__name` ; tri : `order,created_at` (def `edition,tier__rank,order,sponsor__name`).
- **Stats** : `GET /api/sponsors/sponsorships/stats/summary?edition=ID`
- **Public groupé** : `GET /api/sponsors/sponsorships/public/by-edition?edition=ID`
- **Contrats** : `POST /api/sponsors/sponsorships/contracts/presign` et `POST /api/sponsors/sponsorships/{id}/contracts/attach`

## Paramètres
```python
SPONSORS_PUBLIC_CACHE_TTL = 300

# S3 (optionnel, pour presign PUT)
SPONSORS_S3_BUCKET = "my-bucket"
SPONSORS_S3_REGION = "eu-west-3"
SPONSORS_S3_PREFIX = "contracts/"
# via envs AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_SESSION_TOKEN
Metrics

sponsors_visible_total{tier_slug} (Gauge)

sponsorship_amount_sum_eur{edition} (Gauge)

Tests

Unicité (edition,sponsor) ; validations https ; regroupement public ; presign (skip si non configuré).