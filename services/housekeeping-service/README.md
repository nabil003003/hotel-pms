# housekeeping-service

Statuts chambres, motifs de blocage, planning ménage, incidents. Sprint 1.
Schéma transcrit verbatim du spec §5.4.

## Machine à états (Workflow H)

`Sale → Nettoyage → Propre → Contrôlée → Bloquée → Propre` — exactement ces 5
transitions ; toute autre paire renvoie `409 INVALID_TRANSITION`. Le
déblocage (`Bloquée → Propre`) est réservé à `gouvernante`/`manager`/`admin`
(`femme_de_chambre` ne peut pas débloquer).

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| GET | `/api/v1/rooms` | authentifié |
| GET | `/api/v1/rooms/{id}` / `.../status` | authentifié |
| PATCH | `/api/v1/rooms/{id}/status` | `femme_de_chambre`, `gouvernante`, `manager`, `admin` |
| POST/GET | `/api/v1/rooms/{id}/incidents` | `femme_de_chambre`, `gouvernante` / authentifié |
| GET | `/api/v1/rooms/{id}/history` | authentifié |
| POST | `/api/v1/internal/resync/{establishment_id}` | super-admin / service à service |
| WS | `/api/v1/ws/rooms?establishment_id=&token=` | JWT en query param |

## Synchronisation avec establishment-service (D1)

Consomme `establishment.created`, `establishment.rooms_imported`,
`establishment.room_updated` (exchange `amh.establishment`, queue
`housekeeping.establishment_events`) pour maintenir sa copie locale de
`rooms`. `POST /internal/resync/{id}` est le filet de sécurité REST en cas
d'événement manqué.

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec housekeeping-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec housekeeping-service pytest
```
