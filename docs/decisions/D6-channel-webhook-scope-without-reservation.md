# D6 — Portée du webhook OTA sans reservation-service

**Statut** : Adopté Sprint 2, résolu Sprint 3 (voir "Résolution" ci-dessous).

## Contexte

Workflow C (§4.3, lignes 307-321) décrit le webhook OTA entrant
(`POST /api/v1/channel/webhook/{ota}`) se terminant par un appel
`POST /api/v1/bookings` sur reservation-service — création automatique de
la réservation confirmée, avec verrou Redis immédiat. Mais
`reservation-service` est planifié pour un sprint ultérieur et n'existe pas
en Sprint 2 : channel-manager-service ne peut donc pas réellement créer de
réservation.

## Décision

Le webhook Sprint 2 exécute la partie réelle du Workflow C :

1. Vérification de signature HMAC (`X-OTA-Signature`).
2. Détection de conflit (`ota_reference` déjà vue → `409 OTA_CONFLICT`).
3. Résolution du mapping chambre via `establishment-service`
   (`GET /ota-mappings`, [[D3]]) → `422 MAPPING_ERROR` si absent.
4. Persistance d'un `sync_logs` (statut `buffered`) et publication
   `channel.booking_received` sur `amh.channel`.

Puis il s'arrête et répond `202 { status: "buffered", correlation_id }` —
**pas** de faux `internal_booking_id` fabriqué, contrairement à ce
qu'impliquerait une simulation de l'étape 5 du Workflow C.

## Conséquences

- Quand `reservation-service` sera implémenté, il devra soit consommer
  `channel.booking_received` pour créer la réservation de façon
  asynchrone, soit channel-manager-service devra être mis à jour pour
  l'appeler en synchrone (`POST /api/v1/bookings`) et ne répondre `200`
  qu'une fois la réservation réellement créée — à trancher à ce moment,
  pas anticipé ici.
- Le consumer `booking.#` (queue `channel.booking_events`, côté
  channel-manager-service) est câblé et fonctionnel (vérifié par le smoke
  test Sprint 2 via un événement `booking.created` synthétique publié sur
  RabbitMQ), mais son handler ne fait que journaliser
  (`inventory_update_pending`) plutôt que de pousser un inventaire OTA réel
  — aucune credential OTA réelle n'existe pour effectuer un vrai push (voir
  plan Sprint 2, non-goals).

## Résolution (Sprint 3)

Option "appel synchrone" retenue (l'autre option envisagée ci-dessus,
consommer `channel.booking_received` de façon asynchrone, a été écartée :
elle aurait empêché de renvoyer un vrai `internal_booking_id` à l'OTA dans
la réponse HTTP du webhook, ce que le contrat d'origine du spec exige).

`channel-manager-service` appelle désormais `POST /api/v1/bookings` sur
reservation-service en synchrone (`app/infrastructure/reservation_client.py`),
avec un compte de service (`svc-channel-manager`, déjà `is_super_admin`
depuis [[D3]]). Le webhook répond `200 {internal_booking_id, status}` — le
contrat d'origine du Workflow C, plus le `202 buffered` intermédiaire. Le
`market_segment` OTA et le `room_id` précis sont résolus côté
reservation-service (`market_segment_category`/`room_category` en entrée
plutôt que des ids exacts que channel-manager-service ne connaît pas) —
voir `reservation-service/README.md`.

Le consumer `booking.#` reste en place côté channel-manager-service
(journalisation seulement) pour les événements émis par d'autres flux
futurs (modification manuelle d'une réservation déjà liée à une OTA) — il
ne sert plus à la création initiale, désormais synchrone.
