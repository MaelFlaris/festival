# Festival

Plateforme de gestion d'un festival combinant une API Django et une interface React.

## Prérequis

- [Python](https://www.python.org/) 3.12+
- [Node.js](https://nodejs.org/) 18+
- [npm](https://www.npmjs.com/)
- [Docker](https://www.docker.com/) et Docker Compose

## Configuration

1. Copier les variables d'environnement :
   ```bash
   cp .env.example .env
   ```
2. Installer les dépendances :
   ```bash
   pip install -r backend/requirements.txt
   npm install --prefix frontend
   ```
3. Démarrer l'infrastructure :
   ```bash
   docker compose up -d
   ```

## Lancement

### Backend

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

L'API est exposée sur `http://localhost:8000/`.

### Frontend

```bash
cd frontend
npm run dev
```

L'application est disponible sur `http://localhost:5173/`.

## Architecture

| Composant | Description | Point d'entrée |
|-----------|-------------|----------------|
| Backend   | API REST Django (Django REST Framework) | `backend/manage.py` |
| Frontend  | Interface React propulsée par Vite | `frontend/src/main.tsx` |
| Base de données | PostgreSQL 16 (Docker) | `compose.yaml` |

Le backend expose les endpoints sous `/api/…` (configuration dans `backend/festival_backend/urls.py`).
Le frontend consomme cette API via l'URL définie par `VITE_API_BASE_URL`.
