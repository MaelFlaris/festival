# Frontend

Ce dossier contient l'interface web du projet **Festival**. Elle est développée
avec **React 19**, **TypeScript** et **Vite** pour offrir un environnement de
développement rapide.

## Configuration

- `vite.config.ts` active le plugin React de Vite.
- `tsconfig.json`, `tsconfig.app.json` et `tsconfig.node.json` définissent la
  compilation TypeScript.
- ESLint et TailwindCSS sont inclus pour garantir la qualité du code et le
  style de l'interface.

## Consommer l'API backend

Le backend expose ses routes sous le préfixe `/api`. Les appels HTTP peuvent
donc être faits avec des URL relatives. Exemple avec Axios :

```ts
import axios from 'axios'

axios.get('/api/events').then(res => {
  console.log(res.data)
})
```

En développement comme en production, les requêtes vers `/api` sont envoyées
au serveur backend.

## Scripts npm

Les commandes suivantes sont disponibles dans ce dossier :

- `npm run dev` – lance le serveur de développement Vite.
- `npm run build` – génère la version de production dans `dist/`.
- `npm run preview` – prévisualise localement le build de production.
- `npm run lint` – exécute ESLint sur le code du projet.

Installer les dépendances au préalable avec `npm install`.

