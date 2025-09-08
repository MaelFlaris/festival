# Festival — apps/cms (README)

## Rôle & Vision
Gestion éditoriale multi‑édition : **Pages** Markdown, **FAQ**, **News** taguées, avec publication planifiée.

**Objectifs (avec roadmap transverse V2+)**
- **Prévisualisation sécurisée** (token court) des brouillons (`/preview`) non indexée.
- **Versioning & diff** des contenus Markdown (rollback).
- **SEO** : sitemap par édition, métadonnées `og:*`/`twitter:*` via `meta`.
- **Webhooks** : `cms.page.published`, `cms.news.published`.

    ## Modèles
- `Page(edition, slug, title, body_md, meta:JSON, status, publish_at, unpublish_at)`
  - Unicité `(edition, slug)` ; `body_md` → rendu HTML **sanitizé** (whitelist balises).
- `FAQItem(edition, order, question, answer_md)` (ordering par `order,id`).
- `News(edition, title, summary, body_md, cover, tags:[] + publication)` (ordering `-publish_at,-created_at`).

## API (DRF)
- `GET/POST /api/cms/pages/` ; filtres `edition,status` ; recherche `slug,title,body_md` ; tri `slug,publish_at,created_at`.
- `GET/POST /api/cms/news/` ; filtres `edition,status,tags` ; recherche `title,summary,body_md` ; tri `publish_at,created_at` (def `-publish_at`).
- `GET/POST /api/cms/faqs/` ; filtres `edition` ; tri `order,created_at`.
- (V2+) `POST /api/cms/preview/` → URL pré‑signée.

## Règles & sécurité
- Aucune exposition publique des contenus non publiés (ViewSet public distinct recommandé).
- Sanitization stricte du HTML généré (bleach) avec liste blanche.

## Cache & Observabilité
- TTL 300 s sur pages/news publiées ; purge ciblée par `edition`+`slug/id`.
- Metrics : `cms_published_entities_total{type}`, `cms_preview_requests_total`.

## Tests
- Unicité `(edition,slug)` ; transitions de statut ; sanitization ; filtres `tags`.

## Exemples `curl`
```bash
curl -s '/api/cms/news/?edition=2025&status=published&ordering=-publish_at&limit=10'
```

## Roadmap dédiée
- Preview sécurisée ; Versioning/diff ; Sitemap/SEO ; Shortcodes (liens auto vers artistes/stages).
