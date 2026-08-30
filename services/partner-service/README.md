# partner-service

Fiches agences/TO/sociétés/OTA, contrats tarifaires (référence
`partner_id` consommée par pricing-service `partner_rates` et
channel-manager-service pour les OTA). Sprint 2. Schéma transcrit verbatim
du spec §5.8.

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| POST | `/api/v1/partners/{establishment_id}` | `admin`/`manager` |
| GET | `/api/v1/partners/{establishment_id}` | authentifié |
| GET | `/api/v1/partners/{establishment_id}/{partner_id}` | authentifié |
| PATCH/DELETE | `/api/v1/partners/{establishment_id}/{partner_id}` | `admin`/`manager` |

Lecture ouverte à tout utilisateur authentifié (y compris `receptionniste`) :
Workflow B exige un `partner_id` valide pour toute réservation B2B, la
réception doit pouvoir le résoudre.

`ota_credentials_encrypted` : chiffré (Fernet, `app/infrastructure/crypto.py`)
à l'écriture, jamais renvoyé par l'API même chiffré. Le spec définit aussi
`ota_mappings.credentials_encrypted` côté establishment-service pour le même
usage OTA — duplication non résolue par le spec, documentée mais non
corrigée en Sprint 2 (voir plan Sprint 2, non-goals).

Ne publie aucun événement RabbitMQ (vérifié contre l'Appendix C du spec).

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec partner-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec partner-service pytest
```
