# Workflow E — Ajout d'un Extra en Cours de Séjour

Charge manuelle sur un folio ouvert (Workflow E du spec). Le prix catalogue
(`pricing-service.extras_catalog`) est **autoritaire** sur un prix fourni
par le client — le frontend propose un sélecteur de catalogue en plus de
la saisie manuelle (ajouté lors du passage de couverture frontend post-
Sprint 6). Couvert par le scénario E2E Sprint 7.

```mermaid
sequenceDiagram
    actor R as Réceptionniste
    participant FE as Frontend
    participant FO as front-office-service
    participant PRC as pricing-service
    participant DB as fo_db
    participant AN as analytics-service

    R->>FE: Ajoute "Massage" (catalogue) ou saisie libre
    FE->>FO: POST /folios/{id}/charges { poste_comptable, libelle, quantity, unit_price_ht, catalog_item_id? }
    alt catalog_item_id fourni
        FO->>PRC: GET /extras/{id} (prix catalogue autoritaire)
        PRC-->>FO: unit_price_ht catalogue
        FO->>FO: écrase le prix client par le prix catalogue
    end
    FO->>DB: Vérifie Folio.status == 'open'
    FO->>FO: Calcule TVA selon poste comptable (10% ou 20%)
    FO->>DB: INSERT folio_charges (montant_ht, tva, montant_ttc)
    FO->>DB: UPDATE folios.total_charges (balance = GENERATED ALWAYS)
    FO-->>FE: 201 { charge }
    FO->>FO: publish folio.charge_added
    AN-->>AN: incrémente le CA du jour (segment/poste)
```
