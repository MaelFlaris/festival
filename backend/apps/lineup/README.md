# Festival — apps/lineup (README)

## Rôle & Vision
Catalogue **Artistes & Genres** + gestion des **disponibilités** pour le booking et la programmation.

**Objectifs (avec roadmap transverse V2+)**
- **Import/enrichissement** depuis Spotify/MusicBrainz (external_ids, médias, popularité).
- Calcul d’un **score de compatibilité** artiste ↔ scène/genre (heuristique explicable).
- **Webhooks** : `lineup.artist.created|updated`.

## Modèles
- `Genre(name, slug, color #RRGGBB)` (ordering `name`).
- `Artist(name, slug, country ISO2, bios, picture, banner, website, socials:JSON, external_ids:JSON, popularity[0..100], genres M2M)`
  - Index sur `popularity` ; validateurs bornes.
- `ArtistAvailability(artist, date, available, notes)` : unicité `(artist,date)` ; ordering `date`.

## API (DRF)
- Lecture‑seule actuelle : `GET /api/lineup/genres/`, `artists/`, `availabilities/`.
  - Filtres `artists`: `country,genres,popularity` ; recherche `name,short_bio` ; tri `name,popularity,created_at` (def `-popularity,name`).
  - Filtres `availabilities`: `artist,available,date` ; recherche `artist__name,notes` ; tri `date,created_at`.
- (V2+) Autoriser POST/PUT aux rôles `booker`.

## Validation & règles
- `popularity ∈ [0,100]` ; `external_ids` JSON : clés validées (`spotify`, `musicbrainz`).
- Disponibilités : interdiction de doublons `(artist,date)`.

## Cache & Observabilité
- TTL 300 s pour tops popularité.
- Metrics : `lineup_artists_total`, (V2+) `lineup_import_jobs_total{source}`.

## Tests
- Contraintes `(artist,date)` ; validateurs `popularity` ; recherche/tri déterministes.

## Exemples `curl`
```bash
curl -s '/api/lineup/artists/?ordering=-popularity&limit=20'
```

## Roadmap dédiée
- Imports externes (jobs planifiés), scoring compatibilité, publication de webhooks.
