# Festival — apps/tickets (README)

## Rôle & Vision
Définir l’**offre de billets** par édition : types, prix, quotas, fenêtres de vente.

**Objectifs (avec roadmap transverse V2+)**
- **Paliers dynamiques** (`EARLY/REGULAR/LATE`) via champ `phase` et règles de bascule.
- **Quotas segmentés** par canal (`quota_by_channel` JSON) et agrégations.
- **Anti‑fraude** : rate‑limit sur réservations (si module vente ajouté) ; webhooks `tickets.type.sale_opened|sale_closed`.

## Modèle `TicketType`
- Champs : `edition, code, name, description, day?, price, currency(EUR), vat_rate, quota_total, quota_reserved, sale_start, sale_end, is_active`.
- Propriétés : `quota_remaining = max(0, quota_total - quota_reserved)` ; `is_on_sale()` selon fenêtre et `is_active`.
- Contraintes : `(edition, code)` unique ; `quota_reserved ≤ quota_total` ; si `sale_start` et `sale_end` ⇒ `sale_end > sale_start` ; si `day` présent ⇒ dans la plage de l’édition.

## API (DRF)
- CRUD `/api/tickets/types/` ; filtres `edition,currency,is_active,day` ; recherche `code,name,description` ; tri `code,price,created_at` (def `edition,code`).

## Cache & Observabilité
- TTL 120 s pour listings « en vente ». Invalidation à l’update.
- Metrics : `tickets_on_sale_total`, `tickets_quota_remaining_sum`, `tickets_sale_window_open_total`.

## Tests
- Bornes `is_on_sale()` ; validations quotas/dates ; unicité `(edition,code)`.

## Exemples `curl`
```bash
curl -X POST -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \
  -d '{"edition":1,"code":"PASS1J-J3","name":"Pass 1 jour – J3","day":"2025-07-20","price":"69.00","currency":"EUR","vat_rate":"20.0","quota_total":1500,"quota_reserved":0,"is_active":true}' \
  /api/tickets/types/
```

## Roadmap dédiée
- Phases tarifaires ; quotas par canal ; webhooks d’ouverture/fermeture ; multi‑devises (optionnel).
