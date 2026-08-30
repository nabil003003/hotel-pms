# Workflow D — Check-in

Saga orchestrée par `front-office-service` : crée le(s) Folio(s), charge
l'hébergement + taxes, puis bascule le statut de la réservation. Si l'appel
à reservation-service échoue, les folios déjà créés sont refermés
(compensation) plutôt que laissés orphelins. Couvert par le scénario E2E
Sprint 7 (`scenario1-front-office.spec.ts`).

```mermaid
sequenceDiagram
    actor R as Réceptionniste
    participant FE as Frontend
    participant FO as front-office-service
    participant RES as reservation-service
    participant DB as fo_db

    R->>FE: Clique "Check-in" sur une arrivée du jour
    FE->>FO: POST /folios/check-in { booking_id }
    FO->>DB: INSERT Folio A (type A, status open)
    alt tiers payeur (Folio B requis)
        FO->>DB: INSERT Folio B (type B)
    end
    FO->>DB: INSERT folio_charges (HEB + TS/TPT, poste comptable + TVA calculés)
    FO->>RES: PATCH /bookings/{id}/status { status: "status_checked_in" }
    alt échec de l'appel reservation-service
        RES-->>FO: erreur
        FO->>DB: UPDATE folios SET status='closed' (compensation, rollback)
        FO-->>FE: 500 (check-in annulé)
    else succès
        RES-->>FO: 200
        FO-->>FE: 201 { folio_ids }
        FO->>FO: publish booking.checked_in
    end
```

**Note** : la réouverture d'un folio est **définitivement interdite** (403
systématique, y compris super-admin) — corrections comptables uniquement
via écritures de régularisation datées J (règle spec §6.3, non implémentée
comme "modification" au sens strict mais comme nouvelles lignes).
