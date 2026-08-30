# channel-manager-service

Synchronisation OTA (Booking.com, Expedia, Airbnb) — connexions,
webhooks entrants, journal de synchronisation. Sprint 2, webhook rewiré en
Sprint 3 pour appeler reservation-service en synchrone (D6).

Le spec ne définit aucune table SQL pour ce service (`domain/models.py` n'est
donc pas une transcription §5.x) ; `ota_mappings` reste dans
`establishment_db` (décision D3, option 1) et est lue en REST via
`app/infrastructure/establishment_client.py`.

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| POST | `/api/v1/channel/connections/{establishment_id}` (upsert) | `manager`/`admin` |
| GET | `/api/v1/channel/connections/{establishment_id}` | authentifié |
| POST | `/api/v1/channel/webhook/{ota_name}?establishment_id=` | signature HMAC (`X-OTA-Signature`), pas de JWT |
| GET | `/api/v1/channel/performance?establishment_id=&period=YYYY-MM` | `manager`/`admin` |

Le manager (pas seulement l'admin) peut gérer le Channel Manager — accordé
explicitement par le spec (§3.3), contrairement à la config tarifs/taxes.

`GET /api/v1/channel/performance` ici = **santé de synchronisation OTA**
(agrégat de `sync_logs` : combien de webhooks ok/error/buffered). Depuis
Sprint 4, `analytics-service` expose un endpoint de même chemin mais de
sens différent — **revenu par canal** (table `channel_performance`,
alimentée par `channel.booking_received`). Deux services, deux ports, même
forme d'URL par coïncidence de nommage spec — pas un doublon à fusionner.

### Webhook — résolu Sprint 3 (décision D6)

Le Workflow C du spec termine par `POST /api/v1/bookings`. Depuis que
`reservation-service` existe (Sprint 3), le webhook l'appelle réellement en
synchrone après avoir vérifié la signature, résolu le mapping chambre via
establishment-service et détecté les doublons : réponse `200
{internal_booking_id, status}`, conforme au contrat d'origine du spec.
`409 OTA_CONFLICT` si `ota_reference` déjà traité avec succès,
`422 MAPPING_ERROR` si `ota_mappings` ne connaît pas le `room_type_id` OU si
reservation-service refuse la réservation (aucune chambre disponible,
segment invalide). Sprint 2 bufferisait (`202`) faute de
reservation-service — voir `docs/decisions/D6-*.md` pour l'historique.

`establishment_id` en query param sur le webhook : simplification (pas de
vraies credentials OTA, donc pas de vraie distinction d'URL/token par
connexion — non-goal, toujours vrai en Sprint 3).

### Événements RabbitMQ

Publie `channel.booking_received` (inclut désormais `internal_booking_id`)
et `channel.sync_failed` sur l'exchange `amh.channel`. Consomme `booking.#`
(exchange `amh.booking`, queue `channel.booking_events`) — la réservation
étant maintenant créée en synchrone dans le webhook lui-même, ce consumer
reste au niveau "journalisation" (`inventory_update_pending`) pour les
événements émis par d'autres flux (ex: modification manuelle d'une
réservation déjà liée à une OTA), pas pour la création initiale.

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec channel-manager-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec channel-manager-service pytest
```
