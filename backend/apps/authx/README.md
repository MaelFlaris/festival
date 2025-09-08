# Festival — apps/authx (README)

## Rôle & Vision
Profil utilisateur enrichi pour personnalisation, consents RGPD et intégration SSO/OIDC.

## Modèle
- `UserProfile(user:OneToOne, display_name, avatar, preferences:JSON, consents:JSON)`
  - `preferences` max ~32 KiB (configurable via `AUTHX_PREFERENCES_MAX_BYTES`)
  - `consents`: par clé, historique d’événements `{"granted":bool,"at":iso8601,"source":str}`
- Historisation si `django-simple-history` est installé (via `VersionedModel`).

## API (DRF)
- `GET/POST /api/authx/profiles/` — liste
- `GET/PUT/PATCH/DELETE /api/authx/profiles/{id}/`
- `GET/PATCH/PUT /api/authx/profiles/me` — self-service
- Recherche: `user__username,user__email,display_name`
- Tri: `user__username,created_at,updated_at`

### Écriture de consents
Envoyer dans la payload `consent_updates`:
```json
{"consent_updates":[{"key":"newsletter","granted":true,"source":"ui"}]}

Sécurité & Permissions

Self-service via IsOwnerOrAdmin: un utilisateur modifie uniquement son profil.

Admin/Staff: visibilité et édition globales.

Liste filtrée par défaut à l’utilisateur courant.

Observabilité & Webhooks

Compteur Prometheus (si dispo): authx_profile_updates_total{field=...}

Webhook authx.profile.updated (via COMMON_WEBHOOK_URLS / COMMON_WEBHOOK_SECRET)

payload: {"event":"authx.profile.updated","user_id":...,"profile_id":...,"changed_fields":[...]}

SSO / OIDC (V2)

Hydratation opportuniste à la connexion (signal user_logged_in):

En-têtes proxy: X-Authx-Name, X-Authx-Picture, X-Authx-Locale

Session OIDC si disponible (oidc_id_token, oidc_userinfo, …)
