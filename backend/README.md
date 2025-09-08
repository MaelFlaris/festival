# Festival – Pack de READMEs par app (spécifications détaillées & ambitieuses)

> **Objet** : Spécifier **les attentes détaillées** (fonctionnelles & non‑fonctionnelles) pour chaque app du backend. Chaque section intègre la **Roadmap transverse V2+** directement dans les objectifs, avec critères d’acceptation, API, sécurité, validation, observabilité, webhooks, i18n, cache, tests et performance.
>
> **Convention d’API** : préfixe `/api/` (ex. `/api/cms/pages/`). Réponses JSON UTF‑8. Dates/Heures en ISO‑8601. Fuseau par défaut **Europe/Paris**.

---

## 🔭 Architecture & conventions communes

### API & formats

* **Pagination** : DRF limit/offset (`?limit=50&offset=0`) + `page_size` max 200 ; exposer `count`, `next`, `previous`, `results`.
* **Recherche** : `?search=` plein‑texte sur champs déclarés ; **exactitude** non garantie, tri secondaire déterministe (clé primaire croissante).
* **Tri** : `?ordering=field` ou `?ordering=-field` ; multiples autorisés `?ordering=-publish_at,slug`.
* **Filtres** : exclusivement sur `filterset_fields` ; plusieurs valeurs via répétition `?tags=annonce&tags=lineup`.
* **Schéma d’erreur** (uniforme) :

```json
{
  "request_id": "uuid",
  "detail": "Human readable error",
  "code": "ERROR_CODE",
  "field_errors": {"field": ["message1", "message2"]}
}
```

* **Idempotence** : POST non idempotent ; PUT/PATCH idempotent par `id`.
* **Version d’API** (Roadmap) : header `X-API-Version: 1`. Dépréciations via `Sunset` + `Link: rel="deprecation"`.

### Sécurité

* **Auth** : Token (SimpleJWT) ou session ; endpoints publics en lecture pour contenu publié.
* **RBAC transverse** (permissions DRF) :

  * `viewer` : lecture publique (contenu publié, line‑up, slots confirmés, sponsors visibles, tickets en vente).
  * `editor` : CRUD CMS & contenu non publié ; scope d’édition par **édition**.
  * `booker` : CRUD lineup/schedule.
  * `sponsor_manager` : CRUD sponsors/sponsorships.
  * `ticket_manager` : CRUD ticket types.
  * `admin` : super‑permissions.
* **OWASP** : escape/sanitize de toutes rendus HTML (CMS Markdown) ; anti‑CSRF pour sessions ; rate‑limit (voir plus bas).
* **Audits** (Roadmap) : audit trail (Django‑Simple‑History) activé sur entités clés ; export CSV.

### Performance & SLO

* **SLO API** (lectures) : P95 ≤ 300 ms (cache) / P95 ≤ 600 ms (non‑cache) ; P99 ≤ 1 s.
* **SLO API** (écritures) : P95 ≤ 800 ms, P99 ≤ 2 s.
* **Capacité** cible : 150 req/s en lecture, 20 req/s en écriture sur infra standard (1 app + 1 DB + Redis cache).
* **Payload** : 1 Mo max par réponse (`413` sinon). Pagination obligatoire au‑delà.

### Cache & invalidation

* **Layer** : Redis + CDN (Roadmap). TTL par ressource :

  * CMS public (pages/news publiées) : TTL 300s ; purge sur `post_save`/`post_delete`.
  * Schedule `?day=...` : TTL 120s ; purge sur modification de slot du jour.
  * Lineup `artists?ordering=-popularity` : TTL 300s.
* **Cache headers** : `ETag`, `Last‑Modified` ; 304 si inchangé.

### Observabilité

* **Logs structurés** (JSON) avec `request_id`, `user_id`, `role`, `latency_ms`, `status_code`.
* **Metrics Prometheus** (exemples) :

  * `http_requests_total{route,method,status}`
  * `http_request_duration_seconds_bucket{route}`
  * `cms_published_entities_total{type}`
  * `schedule_slots_status_total{status}`
  * `tickets_on_sale_total`
* **Tracing** (Roadmap) : OpenTelemetry (OTLP) avec spans DB/Redis.

### Webhooks (transverse)

* **Signature** : `X-Signature-SHA256` = HMAC(body, secret). Retry avec backoff jusqu’à 24h.
* **Événements** (noms canoniques) :

  * `cms.page.published`, `cms.news.published`, `cms.page.unpublished`
  * `schedule.slot.created|updated|canceled`
  * `lineup.artist.created|updated`
  * `tickets.type.sale_opened|sale_closed`
  * `core.edition.activated`
* **Payload** :

```json
{
  "id": "uuid",
  "type": "schedule.slot.updated",
  "occurred_at": "2025-09-08T08:20:00+02:00",
  "version": "1.0",
  "data": { "slot_id": 123, "changes": {"status": ["tentative","confirmed"]} }
}
```

### i18n & accessibilité

* **Phase 1** : FR ; **Phase 2** : FR/EN (Roadmap) via champs localisés dans CMS.
* **A11y** : textes alternatifs obligatoires pour images (cover, logos) côté CMS.

### Qualité & tests

* **Couverture** : ≥ 85% par app.
* **Pyramide** : unitaires (modèles/validators) > intégration (viewsets/permissions) > E2E (scénarios clés).
* **Fixtures** nommées : `core.editions.json`, `cms.pages.json`, etc.
* **CI** : `migrations --check`, `flake8`, `isort`, `mypy` (Roadmap), `pytest -q`.

---

## 📦 apps/common

### 1) Objectifs (incl. Roadmap)

* Offrir des **abstractions solides** (time, slug, publish, address) réutilisables.
* **SoftDelete** & **Versioning** (Roadmap) pour historiser et restaurer.
* **Webhooks transverses** sur événements structurants (suppression logique, changements de statut de publication).
* **Internationalisation** des adresses (normalisation, geohash – Roadmap).

### 2) Exigences fonctionnelles

* `SluggedModel` génère automatiquement le slug si absent ; collisions → suffixe court unique.
* `PublishableModel` tolère `publish_at/unpublish_at` vides ; validation (Roadmap) : `publish_at < unpublish_at` si les deux définis.

### 3) Exigences non‑fonctionnelles

* Aucun endpoint direct exposé ; code 100% abstrait ; documentation par docstrings.

### 4) Tests attendus

* Génération de slug multi‑langue ; longueur max 220.
* Sérialisation d’adresses avec caractères spéciaux.

---

## 🧱 apps/core

### 1) Objectifs (incl. Roadmap)

* Être la **source de vérité** des Éditions, Lieux, Scènes, Contacts.
* **Activation unique** d’une édition à la fois (Roadmap : contrainte applicative + migration data).
* **Endpoint résumé** `/editions/{id}/summary` (Roadmap) pour KPIs : nb stages, nb slots par status, nb news publiées, nb sponsors visibles, types de tickets en vente.
* **Webhooks** : `core.edition.activated`.

### 2) Exigences fonctionnelles

* `FestivalEdition`

  * `year` unique ; `start_date ≤ end_date` (validator).
  * `is_active` : passer à `true` doit **désactiver** les autres éditions (Roadmap : transaction + signal).
* `Stage` : `(edition, name)` unique.
* `Contact` : `(edition, type, label)` unique.

### 3) API

* `GET /api/core/editions/?year=&is_active=` ; `search=name,tagline` ; `ordering=year,start_date,created_at` (def `-year`).
* `GET /api/core/stages/?edition=&venue=&covered=` ; `search=name,venue__name`.
* **Summary (Roadmap)** : `GET /api/core/editions/{id}/summary` →

```json
{
  "edition": {"id": 1, "year": 2025},
  "stages": 5,
  "slots": {"total": 42, "confirmed": 30, "canceled": 2},
  "news_published": 10,
  "sponsors_visible": 14,
  "tickets_on_sale": 6
}
```

### 4) Permissions

* `viewer` lecture ; `editor` CRUD scindé par édition ; `admin` total.

### 5) Observabilité & Cache

* Invalidation sur `is_active` ; métrique `core_active_edition{year}`.

### 6) Tests

* Activation unique ; intégrité `(edition,name)` ; validation dates.

---

## 👤 apps/authx

### 1) Objectifs (incl. Roadmap)

* Centraliser les **profils** (display\_name, avatar, preferences).
* **Consentements RGPD** (Roadmap) : structure `consents` horodatée.
* **SSO/OIDC** (Roadmap) : hydratation `UserProfile` via claims (email, name, picture, locale).
* **Webhooks** : `authx.profile.updated` pour CRM/marketing.

### 2) Exigences fonctionnelles

* Champ `preferences` JSON schémé (doc JSONSchema – Roadmap) :

  * `default_filters`: `{edition, stages:[], genres:[], only_published:true}`
  * `ui`: `{theme:"dark"|"light"}`
* **Self‑service** : un utilisateur ne modifie **que son** profil.

### 3) API

* `GET /api/authx/profiles/?search=` (admin) ; `PATCH /api/authx/profiles/{id}/` (owner/admin).

### 4) Permissions & Sécurité

* Contrôle ownership object‑level ; tests systématiques.
* Taille `preferences` ≤ 32 Ko.

### 5) Observabilité

* Metric `authx_profile_updates_total` ; log anonymisé des clés modifiées.

### 6) Tests

* Lecture/écriture par propriétaire ; refus si autre user (`403`).

---

## 📰 apps/cms

### 1) Objectifs (incl. Roadmap)

* Gérer Pages/FAQ/News par édition avec publication.
* **Prévisualisation sécurisée** (`/preview`) via token temporel (15 min) – sans indexation.
* **Versioning & diff** des Markdown (Roadmap) ; rollback.
* **SEO** : sitemap par édition, balises `og:*`/`twitter:*` alimentées par `meta`.
* **Webhooks** : `cms.page.published`, `cms.news.published`.

### 2) Exigences fonctionnelles

* Un contenu **non publié** n’est **jamais** exposé aux endpoints publics (filtre automatique côté ViewSet public – Roadmap : ViewSet Public distinct).
* Rendu Markdown → HTML **sanitizé** (bleach) ; **liste blanche** de balises (`p, h1..h3, a, ul, ol, li, em, strong, img(alt,src), blockquote, code, pre`).
* `Page` : `(edition, slug)` unique ; `slug` kebab‑case.
* `News.tags` : tableau de chaînes ; filtre multiple.

### 3) API

* `GET /api/cms/pages/?edition=&status=&search=&ordering=`.
* `GET /api/cms/news/?edition=&status=&tags=&search=&ordering=-publish_at`.
* **Preview** : `POST /api/cms/preview/` → body `{type:"page|news", id:123}` ⇒ URL pré‑signée (Roadmap).

### 4) Cache & Performance

* TTL 300s ; purge ciblée par `edition` & `slug`/`id`.

### 5) Observabilité

* `cms_published_entities_total{type}` ; `cms_preview_requests_total`.

### 6) Tests

* Interdiction d’exposition des brouillons ; sanitization ; unicité `(edition,slug)`.

---

## 🎤 apps/lineup

### 1) Objectifs (incl. Roadmap)

* Être le **catalogue artistique** ; import/enrichissement depuis **Spotify/MusicBrainz** ;
* Calculer un **score de compatibilité** artiste ↔ scène/genre (heuristique) ;
* Déclencher des **webhooks** lors d’ajouts/mises à jour significatives.

### 2) Exigences fonctionnelles

* `Artist.popularity` ∈ \[0,100] ; indexée.
* `external_ids` JSON : schéma minimal (`spotify`, `musicbrainz`) ; validé.
* `ArtistAvailability` : `(artist,date)` unique ; `available` bool.

### 3) API

* Lecture‑seule actuel (GET) ; Roadmap : POST/PUT réservés `booker`.
* Filtres : `country` ISO2 ; `genres` (M2M) ; `popularity` (exacte, ou plage Roadmap `min_pop`/`max_pop`).

### 4) Cache & Performance

* TTL 300s pour tops popularité.

### 5) Observabilité

* `lineup_artists_total` ; `lineup_import_jobs_total{source}` (Roadmap).

### 6) Tests

* Contraintes `(artist,date)` ; validateurs `popularity` ; recherche et tri déterministes.

---

## 📅 apps/schedule

### 1) Objectifs (incl. Roadmap)

* Construire un **planning sans conflits** ;
* **Génération automatique** par templates (copie d’une édition N‑1) ;
* **Webhooks** sur modifications (`created|updated|canceled`) ;
* Export **ICS** standard.

### 2) Exigences fonctionnelles

* `Slot` : `end_time > start_time` ; `day` ∈ \[edition.start\_date, edition.end\_date].
* **Anti‑chevauchement** (Roadmap) : sur `(stage,day)` pas de recouvrement d’horaires ; renvoi `409 CONFLICT` avec `conflicts=[{slot_id, start, end}]`.
* `is_headliner` pour mise en avant.
* `setlist_urls` : tableau d’URL ; validation.

### 3) API

* `GET/POST /api/schedule/slots/` ; filtres `edition,stage,artist,day,status,is_headliner` ; tri `day,start_time`.
* **ICS** : `GET /api/schedule/ics/?day=&artist=&stage=` ; timezone Europe/Paris ; each event : `SUMMARY="{artist} @ {stage}"`.

### 4) Cache & Performance

* TTL 120s pour vues `?day=`.

### 5) Observabilité

* `schedule_slots_status_total{status}` ; `schedule_conflicts_detected_total` (Roadmap).

### 6) Tests

* Validation horaire ; génération ICS ; détection chevauchements (unit + intégration).

---

## 🤝 apps/sponsors

### 1) Objectifs (incl. Roadmap)

* Gérer sponsors par **tier** ;
* **Contrats S3** (upload + métadonnées) ;
* **Statistiques** (montants par tier, visibilité) ;
* **Webhooks** lors de nouveaux partenariats.

### 2) Exigences fonctionnelles

* `SponsorTier.rank` : entier, 1 = plus haut ; ordering par `rank`.
* `Sponsorship` : `(edition,sponsor)` unique ; `visible` bool ; `order` pour tri intra‑tier.
* `logo` : URL https ; validation mimetype à l’upload (Roadmap).

### 3) API

* CRUD sur `tiers`, `sponsors`, `sponsorships` ; filtres `edition,tier,visible` ; recherche `sponsor__name`.

### 4) Observabilité

* `sponsors_visible_total{tier}` ; `sponsorship_amount_sum_eur{edition}`.

### 5) Tests

* Unicité `(edition,sponsor)` ; tri par `tier.rank, order` ; validations URL.

---

## 🎟️ apps/tickets

### 1) Objectifs (incl. Roadmap)

* Définir l’offre de billets ;
* **Paliers dynamiques** (EARLY/REGULAR/LATE – Roadmap : champ `phase`) ;
* **Quotas segmentés** par canal (`quota_by_channel` JSON – Roadmap) ;
* **Anti‑fraude** : rate‑limit (création de réservations si module vente) ;
* **Webhooks** : `tickets.type.sale_opened|sale_closed`.

### 2) Exigences fonctionnelles

* `quota_reserved ≤ quota_total` ; `sale_end > sale_start` si définis ; `day` dans la plage de l’édition s’il existe.
* `is_on_sale()` : actif ET maintenant dans `[sale_start, sale_end]` si présents.
* `currency` figée `EUR` (Roadmap multi‑devises si besoin).

### 3) API

* CRUD `/api/tickets/types/` ; filtres `edition,currency,is_active,day` ; tri `code,price`.

### 4) Cache & Performance

* TTL 120s pour listes publiques « en vente ». Invalidation sur update.

### 5) Observabilité

* `tickets_on_sale_total` ; `tickets_quota_remaining_sum` ; `tickets_sale_window_open_total`.

### 6) Tests

* Bornes `is_on_sale()` ; validations quotas/dates ; unicité `(edition,code)`.

---

## 🚦 Rate‑limit & anti‑abus

* **Public GET** : 120 req/min/IP.
* **Authenticated GET** : 240 req/min/token.
* **Writes (POST/PUT/PATCH/DELETE)** : 60 req/min/token.
* **Webhooks** : 10 req/s endpoint avec burst 50 ; retry exponentiel (cap 24h).

## 🗃️ Migration & données

* **Politique migrations** : une migration par PR ; nom explicite ; `RunPython` pour backfill si ajout de contraintes.
* **Rétention** : logs 30j (prod) ; audit 365j ; RGPD : suppression sur demande utilisateur (authx – Roadmap SoftDelete + purge planifiée).

## 🧩 Dépendances inter‑apps (résumé)

* `core` ⇢ référencé par `cms`, `schedule`, `sponsors`, `tickets`.
* `lineup` ⇢ référencé par `schedule`.
* `common` ⇢ mixins utilisés partout.
* `authx` ⇢ aucune FK sortante, mais consommé transversalement pour préférences et ownership.

## ✅ Critères d’acceptation transverses

* 100% des endpoints respectent pagination/tri/recherche documentés.
* Schéma d’erreur uniforme partout ; `request_id` systématique.
* Rôles DRF vérifiés par tests d’autorisation.
* Cache actif sur endpoints listés ; invalidations testées.
* Couverture tests ≥ 85%.
* Metrics Prometheus exposées au moins pour CMS/Schedule/Tickets/Core.

---

### Annexes (exemples requêtes)

**Lister les news publiées de l’édition active triées par date**

```bash
curl -s \
  "/api/cms/news/?edition=2025&status=published&ordering=-publish_at&limit=10" | jq
```

**Exporter l’ICS du J2 scène Main Stage**

```bash
curl -s "/api/schedule/ics/?day=2025-07-19&stage=3" -o festival-day2.ics
```

**Créer un ticket PASS1J pour J3**

```bash
curl -X POST \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "edition": 1,
    "code": "PASS1J-J3",
    "name": "Pass 1 jour – J3",
    "day": "2025-07-20",
    "price": "69.00",
    "currency": "EUR",
    "vat_rate": "20.0",
    "quota_total": 1500,
    "quota_reserved": 0,
    "is_active": true
  }' \
  /api/tickets/types/
```
