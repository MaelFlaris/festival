# Festival — apps/tickets (README)

## Rôle & Vision
Définir l’**offre de billets** par édition : types, prix, quotas, fenêtres de vente.

## Fonctionnalités
- **Phases tarifaires** (`early|regular|late`) avec endpoint d’**avancement**.
- **Quotas par canal** (`quota_by_channel`) + suivi `reserved_by_channel` et validations.
- **Endpoints**:
  - `GET /api/tickets/types/on-sale?edition=` → liste des billets en vente (cache TTL).
  - `POST /api/tickets/types/{id}/reserve` → réservation minimale (vérif quotas/canal, option `dry_run`).
  - `POST /api/tickets/types/{id}/phase/advance` → passe à la phase suivante.
  - `GET /api/tickets/types/stats/summary?edition=` → agrégats (par phase, quotas restants, total TTC).
- **Webhooks**: `tickets.type.sale_opened|sale_closed` lors de changements de fenêtre de vente.
- **Anti-fraude basique**: rate-limit par IP sur `/reserve` (configurable).
- **Métriques** Prometheus: `tickets_on_sale_total`, `tickets_quota_remaining_sum`.
- **Cache**: listing on-sale (clé versionnée, invalidation sur save/delete).

## Paramètres
```python
TICKETS_ON_SALE_CACHE_TTL = 120
TICKETS_RESERVE_RATE_LIMIT_PER_MIN = 30
API (DRF)
CRUD /api/tickets/types/ ; filtres edition,currency,is_active,day,phase.

Recherche code,name,description ; tri code,price,created_at (def edition,code).

Tests
Bornes is_on_sale() ; validations quotas/dates/canaux ; reserve (dry_run + quotas).


