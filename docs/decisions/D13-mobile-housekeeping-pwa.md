# D13 — Mobile Housekeeping : PWA installable, pas d'app Expo/React Native séparée

**Statut** : Adopté, Sprint 6.

## Contexte

Le spec (ligne 69) prescrit "React Native / PWA" pour l'interface mobile
gouvernante/femme de chambre, avec Expo SDK 50+ comme référence technique.
Construire une seconde application (dépôt/toolchain Expo distinct) est un
projet à part entière — hors de portée d'un sprint qui doit livrer une
"UI complète avec mocks remplacés" pour l'ensemble des 11 services.

## Décision

- La page `/housekeeping` existante (React Query + WebSocket temps réel,
  déjà construite Sprint 1) sert de socle : son responsive Tailwind
  existant couvre déjà l'essentiel du besoin mobile (table + boutons
  d'action tactiles).
- Ajout d'un **Web App Manifest** (`public/manifest.json` + `public/icon.svg`)
  avec `start_url: "/housekeeping"` — l'app s'installe directement sur
  l'écran d'accueil (Android/iOS "Ajouter à l'écran d'accueil") en visant
  cet écran spécifiquement, pas le dashboard générique.
- **Pas de service worker / cache offline** dans ce sprint — l'app reste
  réseau-dépendante. Un vrai mode déconnecté (queue d'actions à rejouer)
  serait un chantier séparé nécessitant une vraie stratégie de
  synchronisation (conflits statut chambre concurrents), pas ajouté sans
  cas d'usage validé.
- Aucune app React Native/Expo créée. Si un jour un vrai besoin natif
  émerge (accès caméra pour les photos d'incident par ex., notifications
  push natives), ce sera un projet séparé, pas une extension de ce sprint.

## Conséquences

- L'app est installable et utilisable sur mobile, mais nécessite une
  connexion réseau active en permanence (pas de tolérance de panne).
- `public/manifest.json`/`icon.svg` sont volontairement minimalistes (une
  seule icône SVG `any`/`maskable`) — pas de jeu d'icônes PNG multi-résolutions
  généré, non nécessaire pour la démonstration.
