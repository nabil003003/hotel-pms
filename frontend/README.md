# frontend — AMH Hospitality PMS

Next.js 14 (App Router), "Frontend + BFF" (spec §2) : un proxy HTTP par
microservice (`app/api/proxy/{service}/[...path]/route.ts`) relaie les
appels du navigateur vers les backends FastAPI en injectant le Bearer token
lu depuis le cookie httpOnly (`lib/proxy.ts`) — le token n'est jamais exposé
au JS client.

## État (Sprint 6 + passe de couverture complète)

Toutes les pages front-office-facing des 11 services sont implémentées et
branchées sur les vraies API (aucun mock), avec une couverture étendue à
(quasi) tous les endpoints exposés par chaque service, pas seulement le
workflow principal :

| Route | Service | Rôles | Contenu |
|---|---|---|---|
| `/reservations` | reservation-service | receptionniste, manager, admin | Planning + création (Workflow A), Disponibilité, Segments (CRUD), Clients (CRM), changement de chambre/upsell (Workflow F, jeton manager via auth-gateway), changement de statut générique |
| `/front-office` | front-office-service | receptionniste, manager, admin | Opérations (check-in/out, folios, charges — manuelles ou catalogue, paiements) + Rapports (débits/crédits/CA détaillé/encaissements/débiteurs/départs/écarts) |
| `/housekeeping` | housekeeping-service | tous (Sprint 1) | Statuts chambres, incidents, historique par chambre |
| `/analytics` | analytics-service | comptable, manager, admin | KPI jour/mois, segments (répartition/CA/tendance), YTD, performance canal, consolidé (super-admin) |
| `/night-audit` | night-audit-service | manager, admin | Verify → close, rapport d'écarts |
| `/notifications` | notification-service | tous | Journal filtrable par événement + détail |
| `/admin/establishments` | establishment-service | admin | Établissement (paramètres), chambres (CRUD complet), services, mappings OTA |
| `/admin/users` | auth-gateway-service | admin | Création utilisateur + liste par établissement |
| `/admin/pricing` | pricing-service | manager, admin | Saisons, grille tarifaire, taxes, extras (CRUD+activation), tarifs négociés, forfaits, calculateur |
| `/admin/partners` | partner-service | manager, admin | CRUD complet (création/édition/désactivation) |
| `/admin/channels` | channel-manager-service | manager, admin | Connexions OTA + performance de synchronisation |

Endpoints volontairement sans UI humaine (machine-à-machine) : webhook OTA
entrant, `elevate/consume`, `internal/resync`, `notifications/send` direct —
ce sont des points d'intégration service-à-service, pas des actions qu'un
utilisateur déclenche depuis l'écran.

Gating par rôle dans `components/app-shell/sidebar.tsx` (nav) et
`middleware.ts` (redirection `/login` si non authentifié — le matcher doit
lister explicitement chaque route protégée, Next.js n'a pas de wildcard
implicite).

**Mobile Housekeeping** : PWA installable (`public/manifest.json`,
`start_url: /housekeeping`), pas une app Expo/React Native séparée — voir
`docs/decisions/D13-mobile-housekeeping-pwa.md`. Pas de service worker /
mode hors-ligne dans ce sprint.

## Démarrage

```bash
cp .env.example .env.local   # ajuster les URLs si les services ne tournent pas sur localhost
npm install
npm run dev
```

Nécessite l'infra + les 11 microservices backend up (`docker compose
--profile core up`, voir le README racine) et Keycloak provisionné
(`scripts/keycloak_setup.py`).

## Architecture

- `app/(app)/{module}/page.tsx` — une page par module, client component,
  React Query pour le fetch/cache, mutations avec invalidation ciblée.
- `lib/api-clients/{service}.ts` — wrappers `fetch` typés vers
  `/api/proxy/{service}/...` (jamais d'appel direct cross-origin au
  backend depuis le navigateur).
- `store/session-store.ts` — Zustand, établissement actif + claims JWT
  décodés côté client (non sensibles, cookie `amh_session` lisible par JS).
- Vérifié Sprint 6 : build de production propre (`npm run build`), toutes
  les nouvelles routes protégées par le middleware, tous les nouveaux
  endpoints proxy testés bout en bout (lecture ET écriture) contre les
  backends réels avec un vrai token Keycloak.
- Vérifié passe de couverture complète (après Sprint 6) : build de
  production propre à nouveau, tous les nouveaux endpoints de lecture
  testés bout en bout contre les backends réels (mêmes cookies qu'un vrai
  navigateur). Les nouveaux chemins d'écriture (PATCH établissement/chambres,
  POST services/mappings OTA/saisons/tarifs négociés/forfaits/segments/
  clients, `check-availability`, `elevate`) réutilisent le même mécanisme
  BFF déjà prouvé en écriture au Sprint 6 (POST/PATCH/DELETE partenaire) —
  non re-testés un par un à la demande de l'utilisateur, à valider en usage
  réel ou lors d'un futur passage avec `claude-in-chrome` connecté.
