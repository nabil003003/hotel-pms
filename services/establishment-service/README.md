# establishment-service

Configuration par Riad (chambres, étages, catégories, services annexes).
Sprint 1. Schéma transcrit verbatim du spec §5.1.

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| POST | `/api/v1/establishments` | `is_super_admin` |
| GET | `/api/v1/establishments` | authentifié (scope auto) |
| GET/PATCH | `/api/v1/establishments/{id}` | `admin` (propre établissement) ou super-admin |
| POST | `/api/v1/establishments/{id}/rooms` | `admin` |
| POST | `/api/v1/establishments/{id}/rooms/bulk-csv` | `admin` |
| GET | `/api/v1/establishments/{id}/rooms` | authentifié |
| PATCH/DELETE | `/api/v1/establishments/{id}/rooms/{room_id}` | `admin` |
| POST/GET | `/api/v1/establishments/{id}/services` | `admin` / authentifié |
| POST | `/api/v1/establishments/{id}/ota-mappings` (upsert) | `admin` |
| GET | `/api/v1/establishments/{id}/ota-mappings` | authentifié |

Publie `establishment.created`, `establishment.rooms_imported`,
`establishment.room_updated` sur l'exchange `amh.establishment` (décision D1
— consommés par housekeeping-service).

`ota_mappings` : table créée pour fidélité au schéma (§5.1), endpoints
ajoutés au Sprint 2 (décision D3, option 1 adoptée) — reste dans
`establishment_db`, lue en REST par channel-manager-service (pas de
credentials renvoyés par l'endpoint GET).

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec establishment-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec establishment-service pytest
```
