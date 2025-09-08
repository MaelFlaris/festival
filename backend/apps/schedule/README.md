# Festival — apps/schedule (README)

## Rôle & Vision
Construire et publier le **planning** (slots) par jour/scène/artiste, avec statuts et export **ICS**.

## Fonctionnalités
- **Zéro conflit** (V2) : détection et refus (HTTP `409`) des chevauchements horaires **sur la même scène et le même jour** (hors slots `canceled`).
- **Export ICS** (`GET /api/schedule/ics/`) — fuseau `Europe/Paris`, `SUMMARY="{artist} @ {stage}"`, `UID=slot-{id}@festival`.
- **Copie par template** (V2) : copier les slots d’une édition N-1 vers N (avec décalage de dates), endpoint `/api/schedule/template/copy`.
- **Webhooks** : `schedule.slot.created|updated|canceled`.
- **Métriques** : `schedule_slots_status_total{status}`, `schedule_conflicts_detected_total`.
- **Cache** :
  - Listes `GET /slots/?day=YYYY-MM-DD` → TTL configurable.
  - ICS (requêtes filtrées) → TTL configurable.

## API (DRF)
- CRUD : `/api/schedule/slots/` (+ `{id}/`) ; filtres : `edition,stage,artist,day,status,is_headliner` ; recherche : `artist__name,stage__name,notes` ; tri : `day,start_time,created_at` (def `day,stage__name,start_time`).
- **Conflicts** : `GET /api/schedule/conflicts?edition=&stage=&day=&start_time=&end_time=&exclude_id=`  
  → `{"conflicts":[{"slot_id":42,"start":"20:00","end":"21:00","artist":"..."}]}`
- **Template** : `POST /api/schedule/template/copy` avec body:
  ```json
  {
    "from_edition": 2024, "to_edition": 2025,
    "stage_map": {"1":"3"}, "status":"tentative", "dry_run": false
  }
