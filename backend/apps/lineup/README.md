# Festival — apps/lineup (README)

## Rôle & Vision
Catalogue **Artistes & Genres** + gestion des **disponibilités** pour le booking et la programmation.

## Fonctionnalités
- **Import/enrichissement** depuis Spotify / MusicBrainz (best-effort) → médias, popularité, IDs externes.
- **Score de compatibilité** artiste ↔ cible (liste de genres) : jaccard + boost popularité.
- **Webhooks** : `lineup.artist.created` | `lineup.artist.updated`.
- **Permissions** : rôles `booker` (ou staff) autorisés à créer/éditer.
- **Endpoints** additionnels:
  - `GET /api/lineup/artists/top?limit=20` (cacheable)
  - `POST /api/lineup/artists/{id}/enrich` (body: `{"source":"spotify","spotify_id":"..."}` ou `{"source":"musicbrainz","mbid":"..."}`)
  - `GET /api/lineup/artists/{id}/compatibility?genres=1,2,3`
  - `GET /api/lineup/availabilities/?for_date=YYYY-MM-DD` (ou `artists/?available_on=YYYY-MM-DD`)
- **Métriques** : `lineup_artists_total`, `lineup_import_jobs_total{source}`.

## Paramètres
```python
LINEUP_TOP_CACHE_TTL = 300
SPOTIFY_TOKEN = ""        # token 'Bearer ...' si enrichissement Spotify
MUSICBRAINZ_APP = "Festival/1.0 (contact@example.com)"
COMMON_WEBHOOK_URLS = [...]         # (via common)
COMMON_WEBHOOK_SECRET = "..."       # optionnel
