# Runbook Ops

Procédures de dépannage pour les alertes du spec §6.7. Livrable §8.3
point 3, rédigé Sprint 8 (D15).

**Périmètre réel** : sur les 5 alertes spec, 2 sont réellement câblées
dans Prometheus (`infra/prometheus/alerts.yml`) à partir des métriques
`pms_api_*` exposées par les 11 services
(`prometheus-fastapi-instrumentator`, voir `app/main.py` de chaque
service). Les 3 autres n'ont pas de métrique source ce sprint (pas
d'exporter Postgres, pas de compteur métier Night Audit/Channel Manager)
— leur procédure ci-dessous reste manuelle (`docker logs` / requêtes SQL
directes) en attendant l'instrumentation métier dédiée (dette Sprint 8+,
voir D15).

Accès : Grafana `http://localhost:3300` (admin/`amh_dev_password`,
lecture anonyme activée) · Prometheus `http://localhost:9090` · doc API
agrégée `http://localhost:8090`.

## ERROR rate > 1% pendant 5 min

**Câblée** (`HighErrorRate`, `infra/prometheus/alerts.yml`) :
`sum(rate(pms_api_requests_total{status=~"5.."}[5m])) by (job) /
sum(rate(pms_api_requests_total[5m])) by (job) > 0.01`.

1. Identifier le(s) service(s) concerné(s) : l'alerte porte le label
   `job` (nom du service, ex. `reservation-service`).
2. `docker logs infra-<service>-1 --tail 200` — chercher les tracebacks
   autour de l'horodatage de déclenchement.
3. Différencier une panne locale (bug de code, DB injoignable) d'une
   panne en cascade (le service amont qu'il appelle est down — vérifier
   l'alerte `ServiceDown` en parallèle).
4. Vérifier dans Grafana (datasource Prometheus déjà provisionnée) le
   graphe `pms_api_requests_total{status=~"5.."}` par `handler` pour
   isoler l'endpoint fautif plutôt que tout le service.

## Night Audit échec 3 jours consécutifs → Email direction

**Non câblée automatiquement** (pas de compteur
`pms_night_audit_duration_seconds`/succès-échec instrumenté ce sprint —
le nom de métrique existe dans le spec §6.7 mais n'a pas été ajouté à
`night-audit-service`, dette D15).

Procédure manuelle :
1. `docker exec infra-postgres-1 psql -U amh -d audit_db -c "SELECT
   establishment_id, business_date, status FROM audit_runs ORDER BY
   business_date DESC LIMIT 5;"` — un `status` autre que `closed` sur les
   3 dernières dates indique un blocage.
2. La cause la plus fréquente vérifiée pendant ce projet : un écart
   débits/crédits non résolu (`DISCREPANCY_DETECTED`, voir
   [`docs/workflows/workflow-i-nightaudit.md`](./workflows/workflow-i-nightaudit.md))
   — `GET /api/v1/night-audit/discrepancy-report` pour le détail par
   poste comptable.
3. Vérifier que `notification-service` a bien reçu et journalisé
   l'alerte de discrepancy (`GET /api/v1/notifications?event_type=audit.discrepancy_detected`)
   — en Sprint 8 la livraison reste un stub dev (D11, aucun email/SMS
   réel envoyé), donc "email direction" de l'alerte spec est encore un
   log, pas un vrai email.

## Redis indisponible > 30s → Slack #ops

**Non câblée automatiquement** (pas de `redis_exporter` installé —
`up{job="redis"}` n'existe pas car Redis n'est pas scrapé par
Prometheus, seuls les 11 services FastAPI le sont).

Procédure manuelle :
1. `docker compose -f infra/docker-compose.yml ps redis` — vérifier
   `unhealthy`/`Restarting`.
2. Impact en cascade attendu : verrous de réservation
   (`booking_lock:*`), idempotence, cache business-date deviennent
   indisponibles — `reservation-service` échouera ses créations de
   réservation avec des erreurs de connexion Redis (`docker logs
   infra-reservation-service-1`).
3. `docker compose -f infra/docker-compose.yml restart redis`, puis
   vérifier `docker compose ... exec redis redis-cli ping` → `PONG`.
4. Le routage Slack #ops réel n'existe pas (pas de webhook Slack
   configuré, D15) — à brancher manuellement en prod.

## PostgreSQL connections > 80% → Auto-scale (si cloud)

**Non câblée automatiquement** (pas de `postgres_exporter` installé).

Procédure manuelle :
1. `docker exec infra-postgres-1 psql -U amh -c "SELECT count(*), max_conn
   FROM pg_stat_activity, (SELECT setting::int AS max_conn FROM
   pg_settings WHERE name='max_connections') s GROUP BY max_conn;"`
2. Onze services partagent la même instance Postgres (une base par
   service, `POSTGRES_DB: postgres` + `init-databases.sh`) — un pic vient
   généralement d'une fuite de connexions côté SQLAlchemy (pool mal
   dimensionné) plutôt que d'un vrai pic de trafic sur cette échelle de
   déploiement. Vérifier `pg_stat_activity.query` pour des connexions
   `idle in transaction` anormalement nombreuses.
3. "Auto-scale si cloud" (texte du spec) ne s'applique pas à ce
   déploiement dev/single-host — sur cette machine, la seule option
   réelle est d'augmenter `max_connections` ou de réduire la taille du
   pool par service.

## Channel Manager sync échec > 5 min → Alert admin

**Non câblée automatiquement** (pas de compteur
`pms_channel_sync_latency_seconds`/échec instrumenté ce sprint).

Procédure manuelle : voir la section Troubleshooting de
[`CHANNEL_MANAGER.md`](../CHANNEL_MANAGER.md) — mêmes vérifications
(signature HMAC, mapping OTA manquant, latence des services amont
establishment/pricing dans le chemin critique synchrone du webhook).

## Service down (bonus, câblée)

**Câblée** (`ServiceDown`, `infra/prometheus/alerts.yml`) : `up{job=~".*-service"}
== 0` pendant 1 min — n'est pas une des 5 alertes nommées du spec mais
couvre un cas plus basique (crash/OOM) qu'elles supposent implicitement.

1. `docker compose -f infra/docker-compose.yml ps <service>` — statut du
   conteneur.
2. `docker logs infra-<service>-1 --tail 100` — souvent une erreur de
   connexion DB au démarrage (dépendance `postgres`/`redis`/`rabbitmq`
   pas encore `healthy` au moment du `depends_on`) ou un crash applicatif.
3. `docker compose -f infra/docker-compose.yml restart <service>`.
