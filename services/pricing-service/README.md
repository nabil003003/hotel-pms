# pricing-service

Grille tarifaire, saisons, taxes, extras, packages, tarifs partenaires.
Sprint 2. Schéma transcrit verbatim du spec §5.5.

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| POST/GET | `/api/v1/pricing/{establishment_id}/seasons` | `admin` / authentifié |
| PATCH | `/api/v1/pricing/{establishment_id}/seasons/{id}` | `admin` |
| POST/GET | `/api/v1/pricing/{establishment_id}/rate-grid` | `admin` / authentifié |
| PATCH | `/api/v1/pricing/{establishment_id}/rate-grid/{id}` | `admin` |
| POST/GET | `/api/v1/pricing/{establishment_id}/taxes` | `admin` / authentifié |
| PATCH | `/api/v1/pricing/{establishment_id}/taxes/{id}` | `admin` |
| POST/GET | `/api/v1/pricing/{establishment_id}/extras` | `admin` / authentifié |
| PATCH | `/api/v1/pricing/{establishment_id}/extras/{id}` | `admin` |
| POST/GET | `/api/v1/pricing/{establishment_id}/partner-rates` | `admin` / authentifié |
| PATCH | `/api/v1/pricing/{establishment_id}/partner-rates/{id}` | `admin` |
| POST/GET | `/api/v1/pricing/{establishment_id}/packages` | `admin` / authentifié |
| PATCH | `/api/v1/pricing/{establishment_id}/packages/{id}` | `admin` |
| GET | `/api/v1/rates/calculate` | authentifié (Workflow A) |
| GET | `/api/v1/rates/partner` | authentifié (Workflow B) |

Ne publie aucun événement RabbitMQ (vérifié contre l'Appendix C du spec —
service purement REST). Si `pricing-service` est indisponible,
reservation-service doit créer la réservation en `status_option` sans tarif
plutôt que bloquer (règle de résilience, spec ligne 1353) — `422` est
renvoyé par `/rates/calculate` quand aucune season/rate_grid ne couvre une
nuit demandée, à charge de l'appelant de gérer cette dégradation.

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec pricing-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec pricing-service pytest
```
