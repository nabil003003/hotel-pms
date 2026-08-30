# Workflow H — Gestion Housekeeping (Mobile/Tablette)

Mobile Housekeeping = PWA installable dans le même frontend Next.js (D13,
Sprint 6), pas une app Expo/React Native séparée. Propagation temps réel
vérifiée en vrai par le scénario E2E Sprint 7 (deux contextes navigateur
distincts, WebSocket, pas un simple refetch).

```mermaid
sequenceDiagram
    actor G as Gouvernante
    participant FE1 as Frontend (acteur)
    participant FE2 as Frontend (observateur)
    participant HK as housekeeping-service
    participant DB as hk_db
    participant REDIS as Redis (pub/sub)

    G->>FE1: "Commencer nettoyage" sur une chambre (Sale → Nettoyage)
    FE1->>HK: PATCH /rooms/{id}/status { statut: "Nettoyage" }
    HK->>DB: Vérifie ALLOWED_TRANSITIONS (Sale → Nettoyage autorisé)
    HK->>DB: UPDATE rooms.statut, INSERT room_status_history
    HK->>REDIS: PUBLISH room.status_changed { room_id, old, new }
    HK-->>FE1: 200 (refetch local, l'acteur voit le changement)
    REDIS-->>FE2: message pub/sub (WebSocket useRoomsWebSocket)
    FE2-->>FE2: met à jour la ligne sans action de l'observateur
```

**Bascule de fin de journée (Night Audit → J+1)** : housekeeping-service ne
suit pas d'état "Occupée" dans `Room.statut` — au clôture (Workflow I),
il interroge reservation-service pour les réservations
`status_checked_in`, puis **force** ces chambres à `Sale` en contournant
`ALLOWED_TRANSITIONS` (reset système légitime, pas une action manuelle).

**Incidents** : `fetchRoomHistory`/dialogue "Détails" par chambre expose
l'historique des statuts + incidents signalés (`room_incidents`) —
surfacé côté frontend lors de la passe de couverture post-Sprint 6.
