# Festival — apps/schedule (README)

## Rôle & Vision
Construire et publier le **planning** (slots) par jour/scène/artiste, avec statuts et export **ICS**.

**Objectifs (avec roadmap transverse V2+)**
- **Zéro conflit** : détecter et interdire les chevauchements horaires sur une même scène/jour (409 CONFLICT + détails).
- **Génération automatique** : copier un template (édition N‑1) pour initialiser une édition.
- **Webhooks** : `schedule.slot.created|updated|canceled`.

## Modèle `Slot`
- Champs : `edition`, `stage`, `artist`, `day(date)`, `start_time`, `end_time`, `status(tentative|confirmed|canceled)`, `is_headliner`, `setlist_urls:list`, `tech_rider:url`, `notes`.
- Indexes : `(edition, day, stage, start_time)` ; ordering `day, stage__name, start_time`.
- Validation : `end_time > start_time` ; `day` ∈ plage de l’édition.

## API (DRF)
- CRUD : `/api/schedule/slots/` (+ `{id}/`) ; filtres : `edition,stage,artist,day,status,is_headliner` ; recherche : `artist__name,stage__name,notes` ; tri : `day,start_time,created_at` (def `day,stage__name,start_time`).
- Export ICS : `GET /api/schedule/ics/?day=&artist=&stage=` ; fuseau **Europe/Paris** ; `SUMMARY="{artist} @ {stage}"`.

## Anti‑conflit (V2+)
- Sur `(stage, day)` : si `start_time < existing.end_time` ET `end_time > existing.start_time` ⇒ conflit.
- Réponse `409` JSON :
```json
{"detail":"Slot conflict","conflicts":[{"slot_id":42,"start":"20:00","end":"21:00"}]}
```

## Cache & Observabilité
- TTL 120 s pour listes `?day=`.
- Metrics : `schedule_slots_status_total{status}`, (V2+) `schedule_conflicts_detected_total`.

## Tests
- Validation temporelle ; génération ICS ; détection de chevauchements (unitaires + intégration).

## Exemples `curl`
```bash
curl -s '/api/schedule/ics/?day=2025-07-19&stage=3' -o day2.ics
```

## Roadmap dédiée
- Génération par template ; notifications webhooks ; outil de détection/explication des conflits.
