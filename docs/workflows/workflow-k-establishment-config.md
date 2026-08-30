# Workflow K — Configuration d'Établissement (Admin)

CRUD admin-only sur `establishment-service` : établissement, chambres,
services de l'établissement, mappings OTA. RBAC vérifié en vrai en
Sprint 7 (`scripts/security_test_sprint7.sh` — un réceptionniste qui tente
`PATCH /establishments/{id}` reçoit 403) ainsi que l'isolation multi-tenant
(un token limité à un établissement ne peut pas lire un autre
établissement, même en `GET`).

```mermaid
sequenceDiagram
    actor A as Admin
    participant FE as Frontend
    participant EST as establishment-service
    participant DB as establishment_db

    A->>FE: Onglet "Établissements" (/admin/establishments)
    FE->>EST: PATCH /establishments/{id} { name, address, ... }
    EST->>EST: require_roles("admin") — 403 si receptionniste/gouvernante
    EST->>EST: assert_path_establishment_access (403 si establishment_id\nhors user.establishment_ids, sauf is_super_admin)
    EST->>DB: UPDATE establishments
    EST-->>FE: 200 { establishment }

    A->>FE: Ajoute une chambre / un service / un mapping OTA
    FE->>EST: POST /establishments/{id}/rooms | /services | /ota-mappings
    EST->>DB: INSERT (mêmes garde-fous RBAC + tenant)
    EST-->>FE: 201
```

**Consommateurs de la config chambres** : reservation-service (résolution
catégorie→chambre, Workflows A/B/C), channel-manager-service (mapping OTA),
housekeeping-service (réplique son propre `rooms.statut`, D1 — événements
`room.created`/`room.updated` plutôt qu'un appel REST synchrone à chaque
lecture).
