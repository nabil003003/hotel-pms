# Guide Channel Manager

Procédures de mapping OTA et de troubleshooting pour
`channel-manager-service` (port 8006). Livrable spec §8.3 point 5, rédigé
Sprint 8 (D15) sur la base du comportement réel vérifié depuis le Sprint 3
(smoke test) et le Sprint 7 (`test_ota_webhook_unmapped`, scénario bord de
cas).

## Vue d'ensemble

Une réservation OTA arrive par webhook HTTP signé HMAC
(`POST /api/v1/channel-manager/webhook/{ota_name}`), pas par polling.
`channel-manager-service` résout le mapping chambre puis appelle
`reservation-service` **synchroniquement** (D6) — la réponse au webhook
reflète le vrai résultat de la création de réservation, pas un accusé de
réception détaché. Voir
[`docs/workflows/workflow-c-ota.md`](./docs/workflows/workflow-c-ota.md)
pour le diagramme de séquence complet.

## Créer une connexion OTA

```
POST /api/v1/channel-manager/connections
Authorization: Bearer <token manager/admin>

{
  "establishment_id": "<uuid>",
  "ota_name": "booking_com",
  "credentials": { ... }
}
```

Les identifiants sont chiffrés (Fernet) avant stockage
(`ChannelConnection.credentials_encrypted`). **Clé de chiffrement dev
partagée et codée en dur** dans `config.py` de chaque service (D-décision
Sprint 2) — à remplacer par un vrai secret manager avant tout déploiement
non-dev.

## Mapper une catégorie de chambre OTA

Le webhook OTA ne connaît qu'un `room_type_id` propre à l'OTA (ex. un ID
Booking.com), jamais une catégorie interne ni une chambre précise. Le
mapping se crée côté `establishment-service` (le mapping vit dans
`establishment_db`, pas `channel_db` — D3) :

```
POST /api/v1/establishments/{establishment_id}/ota-mappings
Authorization: Bearer <token admin>

{
  "ota_name": "booking_com",
  "ota_property_id": "<id propriété OTA>",
  "ota_room_type_id": "<id type de chambre OTA>",
  "internal_room_category": "Chambre Standard"
}
```

Consultable/gérable depuis le frontend : onglet "OTA" de
`/admin/establishments`.

## Réception d'une réservation OTA (webhook)

```
POST /api/v1/channel-manager/webhook/{ota_name}
X-Webhook-Signature: <HMAC-SHA256 du corps, hex>

{ "room_type_id": "...", "check_in": "...", "check_out": "...", ... }
```

1. La signature est vérifiée (`WEBHOOK_HMAC_SECRET`, dev : partagé,
   codé en dur — même limite que les credentials OTA ci-dessus).
2. `internal_room_category` est résolu via le mapping. **Si absent : 422
   `MAPPING_ERROR`, aucune réservation créée** — comportement vérifié
   explicitement en Sprint 7 (`test_ota_webhook_unmapped`), c'est le
   comportement voulu, pas un bug à contourner en configurant un mapping
   "fourre-tout".
3. Appel synchrone à `reservation-service` (compte de service
   `svc-channel-manager`, `is_super_admin=true` — bypass RBAC/tenant côté
   reservation-service, D1/D6).
4. Réponse `200 { internal_booking_id, status }` à l'OTA.

## Troubleshooting

| Symptôme | Cause probable | Vérification |
|---|---|---|
| Webhook retourne 401 | Signature HMAC invalide/absente | Vérifier que l'OTA (ou l'appelant de test) signe avec le même secret que `WEBHOOK_HMAC_SECRET` côté `channel-manager-service` |
| Webhook retourne 422 `MAPPING_ERROR` | Pas de mapping pour ce `room_type_id` | `GET /api/v1/establishments/{id}/ota-mappings`, comparer avec le `room_type_id` du payload webhook |
| Webhook retourne 200 mais aucune réservation visible | Réponse de reservation-service non propagée correctement, ou établissement/segment de marché mal résolu côté reservation-service | Vérifier les logs `docker logs infra-reservation-service-1` autour de l'horodatage du webhook ; `market_segment_category` doit exister pour cet établissement (voir Workflow K) |
| Sync OTA lente (> 30s, objectif spec §6.6) | Le chemin est synchrone bout en bout (D6) — aucune file d'attente tampon en Sprint 3+ | Vérifier la latence de `pricing-service`/`establishment-service` (chemin critique du webhook), pas seulement channel-manager-service lui-même |
| `GET /performance` renvoie des stats vides pour une OTA | Aucun `channel.booking_received`/`channel.sync_failed` encore publié pour cette OTA sur la période demandée | Normal si la connexion vient d'être créée ; pas une panne |

## Ce qui n'est pas implémenté

- Polling OTA (récupération planning/dispo vers l'OTA) : ce build ne couvre
  que la réception de réservations, pas la publication de disponibilité
  vers les OTA (hors scope spec Sprint 2, jamais élargi depuis).
- Vrais comptes OTA (Booking.com/Expedia/Airbnb) : tout est testé contre
  des webhooks simulés signés localement (`scripts/smoke_test_sprint3.sh`,
  `scripts/test_integration_sprint7.py`) — aucune intégration sandbox OTA
  réelle n'a été branchée.
