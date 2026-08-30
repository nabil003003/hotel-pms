# Guide Mobile — Housekeeping PWA

Procédures de build et déploiement pour l'interface mobile
gouvernante/femme de chambre. Livrable spec §8.3 point 6, rédigé Sprint 8
(D15).

**Ce que c'est** : une PWA (Progressive Web App) installable, pas une
application React Native/Expo native — décision actée en D13 (Sprint 6).
Le spec envisageait initialement React Native/Expo ; ce choix a été
délibérément réduit à une PWA pour rester dans le périmètre d'un seul
sprint d'intégration frontend (voir D13 pour le raisonnement complet).

## Ce qui existe

- Page `/housekeeping` du frontend Next.js existant — même code que la
  version desktop, déjà responsive (Tailwind), pas une interface séparée.
- `frontend/public/manifest.json` : Web App Manifest avec
  `start_url: "/housekeeping"` — l'app s'installe en ciblant directement
  cet écran, pas le dashboard générique de l'app.
- `frontend/public/icon.svg` : une seule icône SVG (`any`/`maskable`), pas
  de jeu d'icônes PNG multi-résolutions.
- Mises à jour temps réel des statuts de chambre via WebSocket (Redis
  pub/sub relayé par housekeeping-service) — vérifié en vrai par le
  scénario E2E Sprint 7 (deux sessions navigateur distinctes, propagation
  observée sans refetch manuel).

## Ce qui n'existe pas (limites connues, D13)

- **Pas de service worker / mode hors-ligne.** L'app requiert une
  connexion réseau active en permanence — aucune queue d'actions à
  rejouer, aucun cache de secours. Une gouvernante sans réseau ne peut pas
  mettre à jour un statut de chambre.
- **Pas d'app native.** Pas d'accès caméra natif (photos d'incident),
  pas de notifications push natives — seulement ce qu'un navigateur mobile
  standard permet à une PWA.

## Installation sur un appareil

1. Ouvrir `https://<domaine>/housekeeping` (ou `http://localhost:3000/housekeeping`
   en dev) dans le navigateur mobile (Chrome/Safari).
2. Se connecter avec un compte `gouvernante`/`femmedechambre` (redirection
   Keycloak standard, D4 — pas de formulaire de login custom).
3. Menu navigateur → "Ajouter à l'écran d'accueil" (Android/Chrome) ou
   "Ajouter à l'écran d'accueil" (iOS/Safari, partage → …).
4. L'icône installée lance directement `/housekeeping` en mode
   `standalone` (barre d'adresse masquée), thème sombre
   (`background_color`/`theme_color: #0b0f19`).

## Build / déploiement

Aucune étape de build séparée pour le mobile : la PWA fait partie du build
Next.js standard (`npm run build`, ou l'image Docker
`frontend/Dockerfile` ajoutée en Sprint 8 — voir `DEPLOYMENT.md`). Rien à
publier sur un store d'applications (pas d'app native).

## Troubleshooting

| Symptôme | Cause probable |
|---|---|
| Pas de prompt d'installation | `manifest.json` non servi correctement (vérifier `GET /manifest.json` retourne 200 + `Content-Type: application/manifest+json` ou `application/json`) ou site pas servi en HTTPS (requis par les navigateurs mobiles hors `localhost`) |
| Icône manquante après installation | `icon.svg` non accessible depuis la racine publique — vérifier `GET /icon.svg` |
| Statuts de chambre ne se mettent pas à jour en temps réel | WebSocket non établi (souvent un proxy/reverse-proxy en prod qui ne relaie pas les upgrades WebSocket) — vérifier la configuration du reverse-proxy prod pour `Upgrade`/`Connection` headers sur le chemin WebSocket de housekeeping-service |
| App se comporte comme un onglet navigateur normal (barre d'adresse visible) | PWA pas réellement installée, juste un raccourci — refaire "Ajouter à l'écran d'accueil" en vérifiant que `display: "standalone"` est bien lu (cache navigateur du manifest à vider si le manifest a changé) |
