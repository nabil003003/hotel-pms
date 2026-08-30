
# PMS AMH Hospitality

Système de gestion hôtelière multi-établissements (chaîne de Riads à
Marrakech) — architecture microservices Next.js / FastAPI / Keycloak /
PostgreSQL. Spec complète : [`PMS_PROMPT_TECHNIQUE_V3_ENHANCED.md`](./PMS_PROMPT_TECHNIQUE_V3_ENHANCED.md).

## État du projet

**Sprint 1** (fondations), **Sprint 2** (tarification + partenaires +
intégration OTA), **Sprint 3** (cœur métier réservations), **Sprint 4**
(check-in/out + dashboards), **Sprint 5** (clôture comptable + alertes) et
**Sprint 6** (intégration frontend) sont implémentés : les 11 microservices
backend (`auth-gateway-service`, `establishment-service`,
`housekeeping-service`, `pricing-service`, `partner-service`,
`channel-manager-service`, `reservation-service`, `front-office-service`,
`analytics-service`, `night-audit-service`, `notification-service`) + infra
Docker Compose (profil `core`, qui grandit à chaque sprint plutôt que
d'introduire un profil par sprint — MinIO y est entré au Sprint 5, D12) +
un frontend Next.js qui couvre désormais les 9 services front-office-facing
(réservations, front-office, housekeeping, analytics, night-audit,
notifications, tarification, partenaires, canaux OTA — voir
`frontend/README.md`). Mobile Housekeeping = PWA installable dans ce même
frontend, pas une app Expo/React Native séparée (D13).

**Sprint 7** (tests E2E/charge/sécurité, D14) est également fait — résultats
réels et mesurés, périmètre volontairement réduit vs le §7 du spec (détail
dans `docs/decisions/D14-sprint7-test-strategy-scope.md`) :
- Tests unitaires renforcés (night-audit, notification, analytics, partner)
  + tests d'intégration : tous verts (`docker exec <service> pytest`).
- 5 scénarios d'intégration bord-de-cas jamais exercés jusqu'ici
  (`scripts/test_integration_sprint7.py`) : tous verts. A révélé et corrigé
  un bug réel dans `reservation-service.check_availability` — un séjour déjà
  `status_checked_out` bloquait indéfiniment sa chambre pour les mêmes dates
  (statut terminal absent de l'exclusion `notin_`), rendant une chambre
  invendable à vie sur une plage de dates dès qu'un premier séjour s'y
  termine.
- 3 scénarios E2E Playwright (`frontend/e2e/`) réellement exécutés contre
  `next dev` + Docker : tous verts (le premier run a échoué sur le bug
  ci-dessus, découvert par ce test avant d'être corrigé côté backend).
- Test de charge pragmatique (`scripts/load_test_sprint7.py`, asyncio+httpx
  — ni k6 ni Locust installés) : 30 réservations à concurrence 15 (scénario
  spec "15 réceptionnistes × 30 résa/min"), 30/30 réussies, mais **p95 mesuré
  ≈ 2.3s contre un objectif spec de < 200ms** — dette de perf réelle et
  mesurée à traiter en Sprint 8, pas un nombre inventé pour faire joli.
- Tests de sécurité (`scripts/security_test_sprint7.sh`) : JWT falsifié,
  RBAC, idempotence (X-Idempotency-Key), isolation multi-tenant, **et JWT
  réellement expiré** (le script attend la vraie durée de vie du token,
  300s, plutôt que de forger un `exp` invérifiable sans la clé privée
  Keycloak) — 5/5 verts.
- Hors-scope documenté (pas simulé) : scan OWASP ZAP, tests WebAuthn,
  mesure de couverture pytest-cov instrumentée, 3 des 4 scénarios de charge
  du spec (Night Audit 50 chambres, WebSocket 30 clients, 50 webhooks/min).

**Sprint 8** (optimisation, documentation, handover, D15) est également
fait — périmètre réaliste vs le §8 du spec (détail complet dans
`docs/decisions/D15-sprint8-scope.md`) :
- **Perf** : p95 du load test Sprint 7 mesuré à nouveau après deux
  correctifs réels dans `reservation-service.create_booking`
  (parallélisation des appels establishment-service/pricing-service +
  client HTTP partagé au lieu d'un `AsyncClient` neuf par appel) — **2338ms
  → 604ms** (~74% de réduction, mesuré, toujours au-dessus des 200ms
  cible ; piste restante documentée comme dette).
- **Documentation** : diagrammes Mermaid pour les 11 workflows A-K
  (`docs/workflows/`), `docs/runbook.md` (5 alertes spec, 2 réellement
  câblées dans Prometheus), `DEPLOYMENT.md`, `CHANNEL_MANAGER.md`,
  `MOBILE.md` — tous décrivent le système tel qu'il existe et a été
  vérifié, pas l'aspiration initiale du spec.
- **Kong** : `/openapi.json` des 11 services agrégé à travers Kong
  (`infra/kong/kong.yml`) + un sélecteur `swagger-ui` (port 8090) — vérifié
  en vrai, 11/11 routes retournent le vrai schéma FastAPI de chaque
  service.
- **`docker-compose.prod.yml`** : réplicas (reservation/front-office/
  channel-manager), restart policies, réseaux isolés
  frontend/backend/database/monitoring — config validée
  (`docker compose config`), plus un nouveau `frontend/Dockerfile`
  (le frontend n'était jamais conteneurisé avant ce sprint) construit et
  démarré avec succès. Comportement de prod réel (réplicas, failover)
  **non testé** — pas d'orchestrateur/cluster multi-hôte disponible sur
  cette machine, marqué honnêtement comme tel plutôt que revendiqué.
- **Prometheus + Grafana** : réellement câblés — les 11 services exposent
  `/metrics`, tous scrapés (`up==1` confirmé), une vraie requête de test
  observée dans les métriques après un cycle de scrape, datasource
  Grafana provisionnée automatiquement.
- **Hors-scope documenté** (pas simulé, mêmes raisons que les impasses
  Sprint 7) : OpenTelemetry (traçage distribué), ELK (logs structurés pas
  encore en place comme prérequis + contrainte mémoire de cette machine),
  routage d'alertes vers PagerDuty/Slack (pas de comptes réels), 3 des 5
  alertes spec sans exporter/métrique métier dédiée.
- **Non-régression** : après tous ces changements (11 services
  reconstruits, reservation-service modifié), les 11 suites de tests
  unitaires + les 5 scénarios d'intégration bord-de-cas Sprint 7 + les 3
  scénarios E2E Playwright repassent tous verts.

Feuille de route : voir `docs/decisions/` et les notes de décision D1-D15
qui cadrent les zones grises du spec. Dette restante consolidée dans D15 —
prochaine étape naturelle si le projet continue : OpenTelemetry/ELK,
couverture pytest-cov instrumentée, scan OWASP ZAP, test de
`docker-compose.prod.yml` en conditions réelles multi-hôtes.

## Démarrage rapide

```bash
# 1. Lancer l'infra (incl. MinIO, D12) + les 11 services Sprint 1-5
docker compose -f infra/docker-compose.yml --profile core up -d --build

# 2. Provisionner le realm Keycloak (API Admin — voir docs/decisions/D4)
python scripts/keycloak_setup.py

# 3. Appliquer les migrations
docker compose -f infra/docker-compose.yml exec auth-gateway-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec establishment-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec housekeeping-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec pricing-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec partner-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec channel-manager-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec reservation-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec front-office-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec analytics-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec night-audit-service alembic upgrade head
docker compose -f infra/docker-compose.yml exec notification-service alembic upgrade head

# 4. Peupler les données de référence (Riad Yasmine, cf. fixtures/)
./scripts/seed_sprint1.sh
export RIAD_YASMINE_ID=<uuid affiché par le script>
./scripts/seed_sprint2.sh
./scripts/seed_sprint3.sh
./scripts/seed_sprint4.sh
./scripts/seed_sprint5.sh

# 5. Vérifier bout en bout
./scripts/smoke_test_sprint1.sh
./scripts/smoke_test_sprint2.sh
./scripts/smoke_test_sprint3.sh
./scripts/smoke_test_sprint4.sh
./scripts/smoke_test_sprint5.sh

# 6. Frontend (dans un autre terminal)
cd frontend && cp .env.example .env.local && npm run dev
```

Comptes de test (mot de passe `ChangeMe123!`) : `sidi.omar` (super-admin),
`test.receptionniste`, `test.gouvernante`, `test.femmedechambre`.

## Structure du monorepo

```
services/{service-name}/   # 1 microservice = 1 dossier = 1 déploiement
infra/                      # docker-compose, Keycloak, Kong, RabbitMQ
frontend/                   # Next.js (BFF + UI, Sprint 1 puis intégration complète Sprint 6)
fixtures/                   # jeu de données de référence partagé
docs/decisions/             # notes D1-D10+ sur les arbitrages du spec
Design/                     # maquettes HTML d'origine (référence UX)
```

Voir le `README.md` de chaque service pour ses endpoints et son statut.
