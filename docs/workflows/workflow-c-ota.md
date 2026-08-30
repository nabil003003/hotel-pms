# Workflow C — Réservation OTA (Booking.com, Expedia, Airbnb)

D6 (résolu Sprint 3) : le webhook OTA appelle `reservation-service`
**synchroniquement** (pas de file d'attente tampon) et retourne un vrai
`200 {internal_booking_id, status}`, conforme au contrat initial du spec.
Le mapping `room_type_id` (OTA) → catégorie interne est indispensable — son
absence est un des 5 scénarios bord-de-cas ajoutés en Sprint 7
(`scripts/test_integration_sprint7.py`, `test_ota_webhook_unmapped`, 422
`MAPPING_ERROR`).

```mermaid
sequenceDiagram
    participant OTA as OTA (Booking.com/...)
    participant CM as channel-manager-service
    participant EST as establishment-service
    participant RES as reservation-service
    participant DB as reserv_db

    OTA->>CM: POST /webhooks/{channel} (signé HMAC)
    CM->>CM: Vérifie la signature HMAC (dev secret)
    CM->>EST: GET /ota-mappings (résout room_type_id → room_category interne)
    alt mapping absent
        EST-->>CM: pas de mapping trouvé
        CM-->>OTA: 422 MAPPING_ERROR (pas de booking créé)
    else mapping trouvé
        EST-->>CM: room_category interne
        CM->>RES: POST /bookings (compte de service svc-channel-manager,\nis_super_admin=true — bypass require_roles + tenant check)
        RES->>DB: INSERT booking (status_confirmed, source="ota_...")
        RES-->>CM: 201 { booking }
        CM-->>OTA: 200 { internal_booking_id, status }
    end
    RES->>RES: publish booking.created / channel.booking_received
```

**Statut résultant** : toujours `status_confirmed` directement (une
réservation OTA reçue est déjà garantie côté OTA, pas d'étape d'option).
