# Workflow J — Dashboard Analytics (Temps Réel + Historique)

Pas de Celery/job planifié (D10, Sprint 4) : `analytics-service` incrémente
ses agrégats en temps réel à partir des événements consommés, plutôt que
de les recalculer périodiquement. Les agrégats mensuels, eux, sont
recalculés à la demande à partir des snapshots journaliers.

```mermaid
sequenceDiagram
    participant RES as reservation-service
    participant FO as front-office-service
    participant CM as channel-manager-service
    participant NA as night-audit-service
    participant AN as analytics-service
    participant DB as analytics_db
    actor M as Manager
    participant FE as Frontend

    par Événements consommés en continu
        RES->>AN: booking.checked_in
        FO->>AN: folio.charge_added
        CM->>AN: channel.booking_received
        NA->>AN: audit.closed
    end
    AN->>DB: UPDATE daily_kpi_snapshot (nuitées, CA brut/HT/TVA, TO%, ADR, RevPAR, pax)
    M->>FE: Ouvre le dashboard Analytics
    FE->>AN: GET /analytics/kpi/today, /segments/revenue, /channel/performance, ...
    AN->>DB: SELECT daily_kpi_snapshot (jour) ou agrégation à la demande (mois)
    AN-->>FE: KPIs
    opt Super-admin
        FE->>AN: GET /analytics/consolidated (claims.is_super_admin requis)
        AN-->>FE: KPIs multi-établissements
    end
```

**Champs volontairement à 0** (D10, pas de source fiable en Sprint 4) :
`dms` (durée moyenne de séjour) et la `commission` par réservation — non
fabriqués plutôt que faussement précis.
