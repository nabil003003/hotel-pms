# Workflow B — Réservation B2B (Agence Partenaire)

Même endpoint que le Workflow A (`POST /bookings`), mais avec
`source=b2b_agency` ou un segment `PARTENAIRES`, ce qui force `partner_id`
et bascule le calcul tarifaire sur `pricing-service.calculate_partner_rate`
(tarif négocié par saison, pas la grille publique). Vérifié par
`scripts/smoke_test_sprint3.sh` (bug réel trouvé et corrigé pendant ce
sprint : `tarif_negocie` est un prix par nuit, doit être multiplié par le
nombre de nuits — pas déjà un total comme `calculate_public_rate`).

```mermaid
sequenceDiagram
    actor R as Réceptionniste
    participant FE as Frontend
    participant RES as reservation-service
    participant PRC as pricing-service
    participant DB as reserv_db

    R->>FE: Réservation avec voucher partenaire
    FE->>RES: POST /bookings { partner_id, source: "b2b_agency", ... }
    RES->>DB: SELECT market_segment
    RES->>RES: requires_partner = true (segment PARTENAIRES ou source b2b_agency)
    alt partner_id absent
        RES-->>FE: 422 INVALID_SEGMENT
    else partner_id présent
        RES->>PRC: GET /pricing/{id}/seasons (résout la saison de la date d'arrivée)
        PRC-->>RES: season_id
        RES->>PRC: GET /rates/partner?partner_id&room_category&season_id
        PRC-->>RES: tarif_negocie (par nuit)
        RES->>RES: total_amount = tarif_negocie × nights
        RES->>DB: INSERT booking (status_voucher)
        RES-->>FE: 201 { booking, status: "status_voucher" }
    end
```

**Statut résultant** : toujours `status_voucher` (jamais `status_option`,
l'accord partenaire vaut confirmation) — transition ensuite vers
`status_checked_in` au Workflow D comme les autres sources.
