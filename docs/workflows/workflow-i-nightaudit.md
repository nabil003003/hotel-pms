# Workflow I — Night Audit (le plus critique)

Saga en deux temps (`verify` puis `close`), token d'audit à usage unique
(Redis TTL 30 min) entre les deux. Vérifié de bout en bout en Sprint 5
(chemin équilibré) et en Sprint 7 (chemin avec écart détecté, un des 5
scénarios bord-de-cas jamais exercé avant) + le scénario E2E Sprint 7
(manager, chemin réel via l'UI).

```mermaid
sequenceDiagram
    actor M as Manager
    participant FE as Frontend
    participant NA as night-audit-service
    participant FO as front-office-service
    participant MINIO as MinIO
    participant NOTIF as notification-service
    participant DB as audit_db

    M->>FE: Clique "Vérifier"
    FE->>NA: POST /night-audit/verify { establishment_id, business_date }
    NA->>DB: SELECT audit_runs WHERE (establishment_id, business_date)
    alt déjà clôturé pour cette date
        NA-->>FE: 409 ALREADY_CLOSED
    end
    NA->>FO: GET /reports/discrepancy (sommes débits/crédits du jour)
    alt écart > 0.01 MAD
        NA->>NOTIF: POST /notifications/send (alerte discrepancy, direct REST)
        NA-->>FE: 409 DISCREPANCY_DETECTED { discrepancy }
    else équilibré
        NA->>DB: INSERT audit_runs (status=balancing → token_audit, Redis TTL 30min)
        NA-->>FE: 200 { token_audit }
        M->>FE: Clique "Clôturer la journée"
        FE->>NA: POST /night-audit/close (header X-Audit-Token)
        NA->>NA: Génère 6 PDFs (reportlab) : CA détaillé, encaissements,\ndébiteurs, départs J+1, arrivées J+1, prévision occupation
        NA->>MINIO: Upload des 6 PDFs (bucket audit-reports)
        NA->>DB: UPDATE system_state (business_date + 1), audit_runs.status=closed
        NA->>NOTIF: email du rapport au manager
        NA-->>FE: 200 { report_hash, business_date_next }
        NA->>NA: publish audit.closed { business_date, report_hash, establishment_id }
    end
```

**4 consommateurs de `audit.closed`** : front-office-service et
analytics-service (depuis Sprint 4), reservation-service et
housekeeping-service (ajoutés Sprint 5 — verrou `business_date_locks` côté
reservation, bascule forcée des chambres occupées côté housekeeping).
