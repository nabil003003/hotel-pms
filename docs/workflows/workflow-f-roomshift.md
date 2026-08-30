# Workflow F — Room Shifting

Le spec original imagine un planning drag & drop ; ce frontend n'en a pas
(décision confirmée en Sprint 7, D14 : Scénario 4 E2E hors-scope pour cette
raison). Le changement de chambre est un dialogue de formulaire sur la
table des réservations. Simplifications actées en D8 (Sprint 3) :
`same_category` fourni par le frontend, pas de `ROOM_BLOCKED`, pas de
cascade automatique de conflits.

```mermaid
sequenceDiagram
    actor R as Réceptionniste
    participant FE as Frontend
    participant RES as reservation-service
    participant AG as auth-gateway-service
    participant REDIS as Redis
    participant DB as reserv_db

    R->>FE: Ouvre "Changer de chambre" sur une réservation
    FE->>RES: POST /bookings/{id}/shift { new_room_id, same_category }
    RES->>REDIS: SETNX room_shift_lock:{booking_id}
    alt upsell (same_category = false)
        RES-->>FE: 403 UPSELL_REQUIRES_VALIDATION
        FE->>AG: POST /auth/elevate (manager saisit ses identifiants)
        AG-->>FE: elevation_token (usage unique)
        FE->>RES: POST /bookings/{id}/shift { new_room_id, elevation_token }
        RES->>AG: POST /auth/elevate/consume (invalide le token après usage)
        AG-->>RES: 200 (consommé)
    end
    RES->>DB: SELECT bookings WHERE room_id=new_room_id (chevauchement)
    alt conflit détecté
        RES-->>FE: 409 ROOM_CONFLICT
    else libre
        RES->>DB: UPDATE booking.room_id, recalcule le delta tarifaire
        RES->>DB: INSERT booking_status_history
        RES-->>FE: 200 { booking, delta }
        RES->>RES: publish booking.room_changed
    end
    RES->>REDIS: DEL room_shift_lock:{booking_id}
```

**Vérifié Sprint 7** (`test_integration_sprint7.py`) : le conflit 409 est
un des 5 scénarios bord-de-cas jamais exercé par les smoke tests
précédents.
