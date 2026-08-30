# Workflow A — Réservation Walk-in

Réceptionniste crée une réservation directe pour un client présent. Couvert
par le smoke test Sprint 3 et le scénario E2E Sprint 7
(`frontend/e2e/scenario1-front-office.spec.ts`, qui enchaîne A → D → E → G).

Depuis Sprint 8 (D15), la résolution de chambre (establishment-service) et
le calcul tarifaire (pricing-service) sont lancés en parallèle dès que le
segment de marché est connu, plutôt qu'en série après le verrou Redis —
voir `reservation-service/app/domain/services.py::create_booking`.

```mermaid
sequenceDiagram
    actor R as Réceptionniste
    participant FE as Frontend (Next.js)
    participant RES as reservation-service
    participant EST as establishment-service
    participant PRC as pricing-service
    participant REDIS as Redis
    participant DB as reserv_db

    R->>FE: Remplit le formulaire (dates, catégorie, client)
    FE->>RES: POST /api/v1/bookings (JWT réceptionniste)
    RES->>DB: SELECT market_segment (DIRECT)
    par Résolution chambre + tarif (parallèle, D15)
        RES->>EST: GET /rooms?categorie=... (candidates)
        EST-->>RES: liste des chambres de la catégorie
    and
        RES->>PRC: GET /rates/calculate (regime, dates)
        PRC-->>RES: tarif total TTC
    end
    RES->>DB: SELECT bookings (vérifie chevauchement par chambre candidate)
    RES->>REDIS: SETNX booking_lock:{room}:{night} (par nuit du séjour)
    REDIS-->>RES: verrou acquis
    RES->>DB: INSERT booking (status_option ou status_confirmed si acompte)
    RES->>DB: INSERT booking_status_history, audit_log
    RES->>REDIS: DEL booking_lock:* (libération, finally)
    RES->>RES: publish booking.created (RabbitMQ)
    RES-->>FE: 201 { booking }
    FE-->>R: "Réservation créée"
```

**Statut résultant** : `status_option` (expire après `option_expiry_hours`,
job asyncio en arrière-plan) sauf si `deposit_paid=true` →
`status_confirmed` directement.
