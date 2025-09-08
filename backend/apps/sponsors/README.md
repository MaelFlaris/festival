# Festival — apps/sponsors (README)

## Rôle & Vision
Gérer les **partenaires** par **tier** avec visibilité contrôlée, contrats et statistiques.

**Objectifs (avec roadmap transverse V2+)**
- **Contrats S3** : upload/stockage sécurisé + métadonnées.
- **Statistiques** : montants par tier/édition, taux de visibilité.
- **Webhooks** : sur création/modification de partenariat.

## Modèles
- `SponsorTier(name, slug, rank:int, display_name)` (ordering `rank`, 1 = plus haut).
- `Sponsor(name, slug, website, logo, description)`.
- `Sponsorship(edition, sponsor, tier, amount_eur, contract_url, visible, order)`
  - Unicité `(edition, sponsor)` ; ordering `tier__rank, order, sponsor__name`.

## API (DRF)
- CRUD `/api/sponsors/tiers|sponsors|sponsorships/`
  - Filtres `sponsorships` : `edition,tier,visible` ; recherche : `sponsor__name,tier__name` ; tri : `order,created_at` (def `edition,tier__rank,order,sponsor__name`).

## Règles & validations
- `logo` et `website` : URLs `https` valides (V2+ : contrôle mimetype/logo à l’upload).

## Observabilité
- Metrics : `sponsors_visible_total{tier}`, `sponsorship_amount_sum_eur{edition}`.

## Tests
- Unicité `(edition,sponsor)` ; tri multi‑clés ; validation d’URLs.

## Exemples `curl`
```bash
curl -s '/api/sponsors/sponsorships/?edition=2025&visible=true&ordering=tier__rank,order'
```

## Roadmap dédiée
- Contrats S3 ; analytics partenaires ; webhooks d’intégration (site vitrine, CRM).
