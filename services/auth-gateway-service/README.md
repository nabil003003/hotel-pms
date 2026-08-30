# auth-gateway-service

Proxy Keycloak : provisioning utilisateurs, synchronisation des rôles,
multi-tenant (`user_establishments`). Sprint 1.

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| GET | `/api/v1/auth/me` | authentifié |
| POST | `/api/v1/auth/users` | `admin` |
| GET | `/api/v1/auth/establishments/{id}/users` | `admin`, `manager` |
| POST | `/api/v1/auth/elevate` | `manager`, `admin` |
| POST | `/api/v1/auth/elevate/consume` | authentifié (compte de service — consommé par reservation-service, D8) |

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec auth-gateway-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec auth-gateway-service pytest
```

Voir `docs/decisions/` pour les choix D1/D2 (réplication d'événements,
claims JWT multi-établissement) qui affectent ce service.
