# reservation-service

Cœur métier réservations (manuel + OTA) : réservations, segments, CRM
client, cycle de vie, room shifting. Sprint 3. Schéma transcrit verbatim du
spec §5.2.

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| POST/GET | `/api/v1/market-segments/{establishment_id}` | `admin` / authentifié |
| PATCH | `/api/v1/market-segments/{establishment_id}/{id}` | `admin` |
| POST/GET | `/api/v1/customers/{establishment_id}` | authentifié |
| GET/PATCH | `/api/v1/customers/{establishment_id}/{id}` | authentifié |
| POST | `/api/v1/bookings/check-availability` | `receptionniste`/`manager`/`admin` |
| POST | `/api/v1/bookings` | `receptionniste`/`manager`/`admin` (+ comptes de service `is_super_admin`, ex. `svc-channel-manager`) |
| GET | `/api/v1/bookings`, `/api/v1/bookings/{id}` | authentifié (lecture seule incl. `gouvernante`/`femme_de_chambre`) |
| PATCH | `/api/v1/bookings/{id}/status` | `receptionniste`/`manager`/`admin` |
| PATCH | `/api/v1/bookings/{id}/room` | `receptionniste`/`manager`/`admin` (upsell nécessite un token d'élévation, D8) |
| GET | `/api/v1/planning?from&to&establishment_id` | authentifié |

Publie `booking.created`, `booking.cancelled`, `booking.room_changed` sur
`amh.booking`. Consomme `room.status_changed` (`amh.room`, queue
`reservation.room_events`) — journalisation seulement, aucune logique
métier décrite par le spec pour ce consumer à ce stade.

## Décisions Sprint 3

- **D7** — `POST /api/v1/bookings` accepte un flag `deposit_paid` (attestation
  manuelle, pas de vrai paiement — front-office-service n'existe pas encore) :
  OTA → toujours `status_confirmed` ; segment `PARTENAIRES`/`b2b_agency` →
  `status_voucher` ; sinon `status_confirmed` si `deposit_paid` sinon
  `status_option` (expire après `OPTION_EXPIRY_HOURS`, 48h par défaut,
  purgé par une boucle asyncio — pas de Celery). `status_no_show` reste une
  transition manuelle uniquement (gap du spec, aucun déclencheur décrit).
- **D8** — Room shifting (`PATCH .../room`) : `same_category` est fourni
  par l'appelant (pas de nouvel appel establishment-service pour
  résoudre les catégories) ; `ROOM_BLOCKED` non implémenté (housekeeping
  n'a pas ce statut) ; `force=true` sur un conflit ne cascade pas la
  réservation existante (limitation documentée). Élévation
  (`POST /api/v1/auth/elevate` sur auth-gateway-service, consommée via
  `POST /api/v1/auth/elevate/consume`) obligatoire pour tout upsell ou
  `force=true`.
- **D6 (mise à jour)** — `POST /api/v1/bookings` accepte un `room_category`
  (résolu en `room_id` disponible via establishment-service) et un objet
  `customer` inline (résolu/créé par email) — c'est ce qui permet à
  channel-manager-service d'appeler ce endpoint de façon synchrone pour le
  chemin OTA (voir `channel-manager-service/README.md`).
- Idempotence (`X-Idempotency-Key`) : pas de colonne dédiée (schéma figé) —
  implémentée via Redis (`idempotency:{key}` → `booking_id`, TTL 24h).

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec reservation-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec reservation-service pytest
```
