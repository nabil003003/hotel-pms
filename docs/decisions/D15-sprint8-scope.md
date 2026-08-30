# D15 — Sprint 8 : périmètre réaliste (optimisation, documentation, handover)

**Statut** : Adopté, Sprint 8.

## Contexte

Le spec §8 + §9 attend un livrable "production-ready" complet : infra
`docker-compose.prod.yml` avec réplicas et réseaux isolés, stack
d'observabilité complète (OpenTelemetry, Prometheus avec des métriques
nommées, ELK avec rétention 30j/1an/3ans, alertes Grafana routées vers
PagerDuty/Slack), documentation exhaustive (OpenAPI agrégé via Kong,
diagrammes Mermaid pour les 11 workflows A-K, runbook ops, guides de
déploiement/channel-manager/mobile). Cette machine est un poste de dev
Windows unique (Docker Desktop alloué à 7.5 GiB, ~16 conteneurs déjà actifs
pour le profil `core`), sans comptes PagerDuty/Slack réels, sans cluster
multi-hôte pour vérifier des réplicas en conditions réelles, et sans volume
de logs de production justifiant une politique de rétention sur 3 ans.
Même logique que D14 pour Sprint 7 : exécuter ce qui est réellement
vérifiable sur cette stack, documenter explicitement le reste comme dette
plutôt que de prétendre une couverture non vérifiable.

## Décisions

**Optimisation (§6.6)** : le p95 mesuré par le load test Sprint 7
(`scripts/load_test_sprint7.py`, 30 réservations à concurrence 15) était de
2338ms contre un objectif spec de 200ms. Deux corrections réelles apportées
et re-mesurées :
1. `reservation-service.create_booking` chaînait en série l'appel
   establishment-service (résolution de chambre) puis, après acquisition du
   verrou Redis, l'appel pricing-service (calcul tarif) — aucun des deux
   n'a de dépendance sur l'autre une fois le segment de marché résolu.
   Parallélisés via `asyncio.create_task`/`gather` implicite (tâches
   lancées tôt, `await`-ées seulement quand le résultat devient nécessaire).
2. `establishment_client.py` et `pricing_client.py` ouvraient un
   `httpx.AsyncClient` neuf (donc une connexion TCP neuve, sans keep-alive)
   à **chaque** appel — remplacé par un client HTTP module-level partagé,
   réutilisé entre requêtes (pattern explicitement recommandé par httpx pour
   un usage concurrent).

Résultat mesuré : p95 2338ms → 732ms (fix 1 seul) → **604ms** (fix 1+2),
soit une réduction réelle de ~74%, toujours au-dessus des 200ms cible. La
piste restante la plus probable (non creusée ce sprint, faute de temps face
au reste du périmètre §8) : la validation JWT côté establishment-service et
pricing-service eux-mêmes est dans le chemin critique de chaque appel — pas
investigué si leur vérification de signature Keycloak est mise en cache
localement ou refaite à chaque requête. Piste secondaire : taille du pool
de connexions asyncpg de reservation-service sous concurrence. Les deux
restent dette documentée plutôt qu'une optimisation non vérifiée.

**Le même anti-pattern `async with httpx.AsyncClient(...)` par appel existe
probablement dans d'autres clients inter-services du monorepo** (pas audité
service par service ce sprint — corrigé uniquement sur le chemin
effectivement mesuré par le load test Sprint 7). À reprendre au cas par cas
si un futur load test isole un autre service comme goulot.

**Observabilité — Prometheus + Grafana (§6.7)** : mis en place pour de vrai,
profil Compose `observability`, métriques réellement scrapées (pas une
config vide) — voir la section Résultats une fois exécuté.

**Observabilité — OpenTelemetry (traces distribuées, §6.7)** : **hors
périmètre, non simulé.** Nécessite un collecteur (Jaeger/Tempo) + instrumenter
les 11 services + propager `correlation_id` à travers les appels HTTP et
RabbitMQ — un chantier à part entière, pas un ajout ponctuel de fin de
sprint. Dette documentée pour un Sprint 9 dédié si le projet continue.

**Observabilité — ELK (logs, §6.7)** : **hors périmètre, non simulé.**
Trois raisons concrètes, pas juste "manque de temps" :
1. Contrainte mémoire réelle : Elasticsearch seul recommande ≥2GB de heap,
   Logstash et Kibana ajoutent chacun several centaines de Mo — sur les
   7.5GiB alloués à Docker Desktop avec déjà ~16 conteneurs du profil
   `core` actifs, empiler ELK risque de déstabiliser une stack qui
   fonctionne et est entièrement vérifiée (Sprints 1-7).
2. Prérequis manquant : aucun service n'émet de logs JSON structurés
   aujourd'hui (`logging` standard Python, non configuré) — le format
   `{timestamp, level, service, correlation_id, user_id, establishment_id,
   message, context}` exigé par le spec n'existe nulle part. Brancher une
   stack ELK sur des logs texte libres ne produirait rien d'exploitable ;
   le vrai travail est le passage à des logs structurés service par
   service, pas l'installation d'Elasticsearch.
3. La politique de rétention du spec (30j chaud / 1 an tiède / 3 ans
   froid) présuppose un volume de logs de production que cette machine de
   dev ne générera jamais — comme k6/Locust en Sprint 7, ce serait de
   l'outillage pour un usage qui n'existe pas encore.

`docker logs <container>` reste la voie d'inspection réelle sur cette
stack. Si le projet passe un jour en environnement partagé/cloud, l'ordre
de travail réaliste est : (a) logs JSON structurés par service, (b) ELK ou
équivalent managé (le spec lui-même laisse la porte ouverte "Auto-scale si
cloud" en §6.7).

**Alertes Grafana → PagerDuty/Slack (§6.7)** : **hors périmètre.** Pas de
comptes PagerDuty/Slack réels disponibles pour cette machine de dev — un
webhook vers un compte inexistant ne serait pas une vérification, juste une
URL qui échouerait silencieusement. Les règles d'alerte elles-mêmes
(seuils Prometheus) sont configurées et vérifiables ; le routage externe
est documenté dans le runbook comme étape manuelle à brancher en prod.

**`docker-compose.prod.yml` (§8.1 point 2)** : écrit avec réplicas
(reservation/front-office/channel-manager), health checks, restart
policies, réseaux isolés (frontend/backend/database/monitoring) — validé
via `docker compose -f docker-compose.prod.yml config` (parsing/résolution
de variables correct) mais **pas démarré en conditions réelles** : un vrai
test de réplicas (load balancing entre instances, failover) demande soit
un orchestrateur (Swarm/K8s) soit plusieurs hôtes, aucun des deux
disponible ici. Honnêtement marqué comme "config vérifiée, comportement de
prod non testé" plutôt que revendiqué comme équivalent au profil `core`
Sprint 1-7 (celui-là testé en vrai à chaque sprint).

**Documentation (§8.3)** : les 6 livrables (OpenAPI agrégé Kong,
diagrammes Mermaid A-K, runbook ops, `DEPLOYMENT.md`, `CHANNEL_MANAGER.md`,
`MOBILE.md`) sont tous réalisables sans infra supplémentaire — traités
comme le cœur vérifiable de ce sprint, au même niveau de rigueur que le
code (reflètent ce qui est réellement implémenté et vérifié dans les
Sprints 1-7, pas l'aspiration initiale du spec — ex. Workflow F documenté
comme un dialogue de formulaire, pas un drag & drop, comme déjà tranché
côté E2E Sprint 7).

## Conséquences

- Ce qui est livré dans ce sprint est réellement vérifié : le gain de perf
  est un avant/après mesuré (pas une estimation), Prometheus/Grafana
  scrapent de vraies métriques, la documentation décrit le système tel
  qu'il existe et a été testé.
- Dette explicitement documentée pour la suite : OpenTelemetry, ELK (+
  logs structurés comme prérequis), routage d'alertes PagerDuty/Slack, test
  de `docker-compose.prod.yml` en conditions réelles multi-hôtes, audit du
  pattern `AsyncClient`-par-appel dans les autres clients inter-services,
  et l'écart p95 restant (604ms vs 200ms cible).

## Résultats (exécution réelle, même sprint)

- **Kong OpenAPI (§8.3 point 1)** : `infra/kong/kong.yml` route les 11
  `/openapi.json` réels à travers Kong (`/openapi/{service}.json`, gotcha
  réel corrigé : `kong:3.5-alpine` référencé depuis Sprint 1 n'existe plus
  sur Docker Hub, remplacé par `kong:3.5`). Un conteneur `swagger-ui`
  séparé (port 8090, pas routé via Kong — son mécanisme `BASE_URL`
  produisait une config nginx cassée avec cette image, contourné en le
  servant à sa propre racine) les agrège dans un sélecteur unique. Vérifié
  : les 11 routes retournent 200 avec le vrai schéma FastAPI de chaque
  service, `swagger-initializer.js` liste bien les 11 URLs.
- **`docker-compose.prod.yml`** : `docker compose ... config` résout sans
  erreur (réseaux isolés correctement fusionnés par service, restart
  policy partout, `deploy.replicas: 2` sur les 3 services critiques).
  `frontend/Dockerfile` (nouveau — le frontend n'était jamais conteneurisé
  avant ce sprint) **construit et démarre réellement** : `docker build` +
  `docker run` + `GET /login` → 200 vérifié avant d'être intégré au
  compose file.
- **Prometheus + Grafana** : les 11 services exposent `/metrics`
  (`prometheus-fastapi-instrumentator`, ajouté à chacun) — reconstruits et
  redéployés, `up{job=...}==1` confirmé pour les 11 cibles via l'API
  Prometheus, et une vraie requête de test (`GET /api/v1/bookings` sur
  reservation-service) a été observée apparaître dans
  `pms_api_http_requests_total` après un cycle de scrape (15s), preuve que
  la chaîne complète fonctionne, pas juste que le conteneur répond.
  Grafana a sa datasource Prometheus provisionnée automatiquement (vérifié
  via `GET /api/v1/datasources`). 2 des 5 alertes spec sont câblées pour
  de vrai (`HighErrorRate`, `ServiceDown` — les 3 autres demanderaient des
  exporters/métriques métier non ajoutés ce sprint, voir `docs/runbook.md`
  pour la procédure manuelle). Gotcha réel rencontré : le nom de métrique
  généré par l'instrumentator n'est pas `pms_api_requests_total` mais
  `pms_api_http_requests_total` (le nom de base `http_requests_total` est
  conservé, namespace/subsystem ne font que préfixer) — la règle d'alerte
  et toute requête PromQL future doivent utiliser ce nom réel, pas celui
  du spec.
- **Documentation** : les 11 diagrammes Mermaid (`docs/workflows/`),
  `docs/runbook.md`, `DEPLOYMENT.md`, `CHANNEL_MANAGER.md`, `MOBILE.md`
  sont tous rédigés à partir du comportement réel du code (pas de
  l'aspiration du spec).
- **Non-régression** : après tous les changements ci-dessus (11 services
  reconstruits avec l'instrumentation, `reservation-service` modifié pour
  la perf), re-vérifié en une seule passe : les 11 suites de tests
  unitaires passent, les 5 scénarios d'intégration bord-de-cas Sprint 7
  passent, les 3 scénarios E2E Playwright passent — rien cassé par ce
  sprint.
