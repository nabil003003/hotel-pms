# Guide de déploiement

Spec §8.3 point 4. Voir `README.md` ("Démarrage rapide") pour le
développement local — ce guide couvre la mise en production
(`docker-compose.prod.yml`, Sprint 8/D15).

## Ce qui est vérifié vs ce qui ne l'est pas

**Vérifié en vrai sur cette machine de dev** :
- `frontend/Dockerfile` (build multi-stage, sortie Next.js `standalone`)
  construit et démarre réellement (`docker build` + `docker run` +
  `GET /login` → 200) — le frontend n'était packagé qu'en `npm run dev`
  avant ce sprint.
- `docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml
  --profile core --profile gateway config` résout sans erreur : réseaux
  isolés correctement fusionnés par service, `restart: unless-stopped`
  appliqué partout, `deploy.replicas: 2` présent sur les 3 services
  critiques (spec §8.1 point 2).

**Non vérifié — honnêteté du scope (D15)** :
- `deploy.replicas` n'a d'effet réel que sous Docker Swarm. En
  `docker compose up` simple (ce que cette machine peut exécuter), obtenir
  plusieurs instances demande `docker compose up --scale
  reservation-service=2` explicitement — le champ `replicas` est présent
  pour la conformité déclarative et documente l'intention, ce n'est pas de
  l'auto-scaling en compose nu.
- Aucun test de bascule/répartition de charge entre réplicas réel n'a été
  effectué — nécessiterait un orchestrateur (Swarm/K8s) ou plusieurs hôtes,
  aucun des deux disponible ici.
- Aucun déploiement sur un vrai hôte de production (cloud ou autre) n'a eu
  lieu — tout ce qui suit est vérifié en configuration/`docker compose
  config`, pas en conditions réelles multi-hôtes.

## Prérequis

- Docker + Docker Compose v2.
- Un hôte avec au moins 8 GiB de RAM disponibles pour Docker (16
  conteneurs du profil `core` + gateway consomment significativement plus
  qu'en dev léger — voir la note mémoire de D15 sur pourquoi ELK n'est pas
  inclus).
- Un realm Keycloak provisionné (`scripts/keycloak_setup.py` — nécessite
  l'API Admin Keycloak, pas juste le déclaratif `docker-compose.yml`).

## Secrets à changer avant tout déploiement non-dev

Toutes ces valeurs sont des **secrets de développement codés en dur**,
partagés entre tous les services — vérifiées comme telles dans
`docs/decisions/` (D2 chiffrement OTA, Sprint 2 ; webhook HMAC,
Sprint 3) :

| Secret | Où | Valeur dev actuelle |
|---|---|---|
| `POSTGRES_PASSWORD` | `docker-compose.yml` | `amh_dev_password` |
| `KEYCLOAK_CLIENT_SECRET` (× 11, un par service) | `docker-compose.yml`, `environment:` de chaque service | `dev-secret-<service>` |
| `ENCRYPTION_KEY` (credentials OTA chiffrés) | `config.py` de chaque service | valeur Fernet partagée codée en dur |
| `WEBHOOK_HMAC_SECRET` | `channel-manager-service/config.py` | `dev-webhook-hmac-secret` |
| `MINIO_ROOT_PASSWORD` | `docker-compose.yml` | `amh_dev_password` |
| `RABBITMQ` credentials | `docker-compose.yml` | `amh` / `amh_dev_password` |

Aucun secret manager (Vault, AWS Secrets Manager, etc.) n'est câblé — à
faire avant tout déploiement où ces valeurs seraient exposées au-delà de
cette machine de dev.

## Étapes de déploiement

```bash
# 1. Réseaux + volumes + tous les services, avec l'overlay prod
#    (réplicas, restart policy, réseaux isolés, frontend conteneurisé)
docker compose \
  -f infra/docker-compose.yml -f infra/docker-compose.prod.yml \
  --profile core --profile gateway up -d --build

# 2. Provisionner le realm Keycloak (idempotent — vérifie l'existant avant de créer)
python scripts/keycloak_setup.py

# 3. Migrations (une par service, alembic upgrade head)
for svc in auth-gateway establishment housekeeping pricing partner \
           channel-manager reservation front-office analytics \
           night-audit notification; do
  docker compose -f infra/docker-compose.yml exec "${svc}-service" alembic upgrade head
done

# 4. Données de référence (établissement(s), voir fixtures/)
./scripts/seed_sprint1.sh
export RIAD_YASMINE_ID=<uuid affiché>
./scripts/seed_sprint2.sh && ./scripts/seed_sprint3.sh && \
  ./scripts/seed_sprint4.sh && ./scripts/seed_sprint5.sh

# 5. Vérification bout en bout avant d'ouvrir le trafic
./scripts/smoke_test_sprint1.sh && ./scripts/smoke_test_sprint2.sh && \
  ./scripts/smoke_test_sprint3.sh && ./scripts/smoke_test_sprint4.sh && \
  ./scripts/smoke_test_sprint5.sh
python scripts/test_integration_sprint7.py
bash scripts/security_test_sprint7.sh   # ~5 min (attend un vrai JWT expiré)
```

Le frontend est accessible sur le port `3000` (`docker-compose.prod.yml`),
Kong + la doc OpenAPI agrégée sur `8000`/`8090` (voir `README.md`,
section observabilité pour Prometheus/Grafana).

## Rollback

Aucun mécanisme de rollback automatisé (pas de blue/green, pas de
migration `alembic downgrade` exercée en pratique). En cas de problème
après déploiement : `docker compose ... down`, corriger, redéployer depuis
l'étape 1. Les migrations Alembic supportent `downgrade` en théorie
(générées par `alembic revision --autogenerate`) mais **jamais testées en
sens inverse** dans ce projet — à vérifier avant de s'y fier en
production.

## Observabilité (Sprint 8, D15)

Voir `docs/runbook.md` pour la procédure par alerte. Résumé du périmètre
réel :
- **Prometheus + Grafana** : réellement câblés, profil `observability`.
- **OpenTelemetry (traces)**, **ELK (logs)**, **routage
  PagerDuty/Slack** : hors périmètre, dette documentée (D15) — cette
  machine de dev n'a ni le volume de logs ni les comptes externes qui
  justifieraient de les simuler.
