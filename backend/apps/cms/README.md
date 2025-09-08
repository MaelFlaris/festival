# Festival — apps/cms (README)

## Rôle & Vision
Gestion éditoriale multi-édition : **Pages** Markdown, **FAQ**, **News** taguées, avec publication planifiée et outils de preview/SEO.

## Fonctionnalités
- **Publication** avec fenêtres `publish_at` / `unpublish_at` (hérite de `PublishableModel`).
- **Rendu sécurisé**: `body_md` → `body_html` (Markdown → HTML **sanitizé**).
- **Versioning** : si `django-simple-history` présent, historique/diff/rollback.
- **Preview sécurisée** : génération d’URL pré-signée (token HMAC, TTL configurable).
- **Endpoints publics**: lecture uniquement des contenus **publiés** et dans fenêtre.
- **Sitemap** par édition (pages + news publiées).
- **Webhooks**: `cms.page.published`, `cms.news.published` (via common).
- **Métriques**: `cms_published_entities_total{type}`, `cms_preview_requests_total`.

## API (DRF)
- Admin/éditorial:
  - `GET/POST /api/cms/pages/`, `GET/PUT/PATCH/DELETE /api/cms/pages/{id}/`
  - `GET/POST /api/cms/news/`, `GET/PUT/PATCH/DELETE /api/cms/news/{id}/`
  - `GET/POST /api/cms/faqs/`, `GET/PUT/PATCH/DELETE /api/cms/faqs/{id}/`
- Public:
  - `GET /api/cms/public/pages/` (query: `edition`, `slug`)
  - `GET /api/cms/public/news/` (query: `edition`, `tag`, `limit`)
- Preview:
  - `POST /api/cms/preview` → `{"url":".../api/cms/preview/resolve?token=..."}`  
  - `GET /api/cms/preview/resolve?token=...` → contenu JSON si token valide.
- Sitemap:
  - `GET /api/cms/sitemap/<int:edition_id>.xml`

## Sécurité / Cache
- Contenus non publiés **jamais** exposés via endpoints publics.
- TTL recommandé: `CMS_PUBLIC_CACHE_TTL = 300` (sec).

## Dépendances
- `markdown` et `bleach` conseillés (fallback minimal si absents).
