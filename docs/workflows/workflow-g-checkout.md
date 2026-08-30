# Workflow G — Check-out

Exige un solde Folio A **exactement à zéro** (pas de dépassement/reste
toléré) ; le Folio B (tiers payeur), lui, est réglé automatiquement via un
paiement mode `Débiteur` quel que soit son solde restant. Couvert par le
scénario E2E Sprint 7.

```mermaid
sequenceDiagram
    actor R as Réceptionniste
    participant FE as Frontend
    participant FO as front-office-service
    participant DB as fo_db

    R->>FE: Encaisse le solde puis clique "Check-out"
    FE->>FO: POST /folios/{id}/payments { mode, montant }
    FO->>DB: INSERT payments, recalcule balance (colonne générée)
    FE->>FO: POST /folios/check-out { booking_id }
    FO->>DB: SELECT Folio A WHERE booking_id
    alt Folio A.balance != 0
        FO-->>FE: 422 (solde non nul, check-out refusé)
    else Folio A.balance == 0
        opt Folio B existe avec un solde restant
            FO->>DB: INSERT payment (mode="Débiteur", montant=balance B)
        end
        FO->>DB: UPDATE Folio A/B SET status='closed', closed_at=now()
        FO->>RES: PATCH /bookings/{id}/status { status: "status_checked_out" }
        FO-->>FE: 200 { folios }
        FO->>FO: publish booking.checked_out
    end
```

**Consommateurs de `booking.checked_out`** : housekeeping-service (bascule
la chambre en "Sale"), analytics-service, notification-service,
channel-manager-service (sync retour vers l'OTA si applicable).
