# D7 — Statut de réservation sans front-office-service

**Statut** : Adopté, Sprint 3.

## Contexte

Le spec (Workflow A, §4.1) fait dépendre `status_confirmed` d'un appel
synchrone à front-office-service pour encaisser un acompte. Ce service
n'existe pas avant le Sprint 4. Le spec définit aussi `status_no_show` dans
l'enum `bookings.status` (§5.2, ligne 839) sans jamais décrire ni
déclencheur, ni endpoint, ni job pour l'atteindre.

## Décision

`POST /api/v1/bookings` accepte un flag `deposit_paid: bool` (attestation
manuelle du réceptionniste — aucun vrai traitement de paiement). Logique de
statut :

- `source` OTA (`ota_booking`/`ota_expedia`/`ota_airbnb`) → toujours
  `status_confirmed` (les OTA ne créent jamais d'option, spec Workflow C).
- Segment `PARTENAIRES` ou `source: b2b_agency` → toujours `status_voucher`.
- Sinon → `status_confirmed` si `deposit_paid=true`, sinon `status_option`
  avec `option_expiry_date = now + 48h` (`OPTION_EXPIRY_HOURS`, configurable).

`status_no_show` reste une transition manuelle uniquement (via `PATCH
/api/v1/bookings/{id}/status`) — aucun job automatique inventé pour un
comportement que le spec ne décrit nulle part.

Purge des options expirées : boucle asyncio en tâche de fond
(`main.py` lifespan, `expire_stale_options`), pas de Celery introduit —
même stratégie que les consumers RabbitMQ déjà en place depuis Sprint 1.

## Conséquences

- Quand front-office-service existera (Sprint 4), le flux réel
  encaissement→confirmation devra remplacer `deposit_paid` par un vrai
  appel synchrone — `deposit_paid` reste utilisable comme flag de
  compatibilité ou peut être retiré à ce moment-là.
- `deposit_amount` (colonne existante) n'est pas alimenté par ce flag —
  reste à 0 tant qu'aucun vrai paiement n'est tracé.
