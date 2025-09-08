  # Festival — apps/authx (README)

  ## Rôle & Vision
  Étendre l’authentification Django par un **profil utilisateur** riche et exploitable pour la personnalisation.

  **Objectifs (avec roadmap transverse V2+)**
  - **Self‑service** : chaque utilisateur modifie uniquement **son** profil.
  - **Consentements RGPD** (V2+) : `consents` horodatés.
  - **SSO/OIDC** (V2+) : hydratation automatique (`email`, `name`, `picture`, `locale`). 
  - **Webhooks** : `authx.profile.updated` pour CRM/marketing.

  ## Modèle
  - `UserProfile(user:OneToOne, display_name, avatar, preferences:JSON)`
    - `preferences` (schéma recommandé) : 
      - `default_filters`: `{edition, stages:[], genres:[], only_published:true}`
      - `ui`: `{theme:"dark"|"light"}`

  ## API (DRF)
  - `GET/POST /api/authx/profiles/` ; `GET/PUT/PATCH/DELETE /api/authx/profiles/{id}/`
    - Recherche : `user__username,user__email,display_name`; tri : `user__username,created_at`.

  ## Sécurité & Permissions
  - **Object‑level** : propriétaire requis pour modifier ; admins peuvent tout lister/éditer.
  - Limite taille `preferences` ≤ 32 Ko.

  ## Observabilité
  - Metric : `authx_profile_updates_total` ; logs diff clés modifiées (sans données sensibles).

  ## Tests
  - Accès propriétaire (`200`) vs autre utilisateur (`403`). Sérialisation RO de `username`/`email`.

  ## Exemples `curl`
  ```bash
  curl -X PATCH -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \
-d '{"display_name":"Maël","preferences":{"ui":{"theme":"dark"}}}' \
/api/authx/profiles/123/
  ```

  ## Roadmap dédiée
  - OIDC/SSO ; avatars upload (S3) ; Audit Trail des préférences ; webhooks de synchro.
