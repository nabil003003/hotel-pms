# front-office-service

Check-in/out, folios A/B, facturation (charges/postes comptables),
encaissements. Sprint 4. Schéma transcrit du spec §5.3 (+`Folio.version`,
voir plus bas).

## Endpoints

| Method | Path | RBAC |
|---|---|---|
| POST | `/api/v1/folios/check-in` (idempotent) | `receptionniste`/`manager`/`admin` |
| POST | `/api/v1/folios/check-out` (idempotent) | `receptionniste`/`manager`/`admin` |
| POST | `/api/v1/folios/{id}/charges` (idempotent) | `receptionniste`/`manager`/`admin` |
| POST | `/api/v1/folios/{id}/payments` | `receptionniste`/`manager`/`admin` |
| POST | `/api/v1/folios/{id}/reopen` | toujours `403` (aucun rôle ne débloque) |
| GET | `/api/v1/folios/{id}`, `/api/v1/folios?booking_id=` | authentifié |
| GET | `/api/v1/folios/reports/{daily-debits,daily-credits,discrepancy}` | `comptable`/`manager`/`admin` |

`X-Idempotency-Key` — mandatoire selon le spec sur check-in/check-out/charges ;
implémenté via Redis (résultat JSON caché 24h), pas de colonne dédiée.

## Décisions Sprint 4

- **`Folio.version`** ajoutée (absente du DDL transcrit) pour le
  verrouillage optimiste exigé par §6.2 — incrémentée à chaque
  charge/paiement.
- **D9** — `business_date` par défaut = date serveur (pas de bascule J+1
  sans night-audit-service, Sprint 5). Le verrou `business_date_locks` est
  câblé pour de vrai (consumer `audit.closed`, queue `fo.audit_events`,
  exchange `amh.audit`) mais ne se déclenche qu'une fois night-audit-service
  construit et publiant réellement l'événement — vérifié en attendant par
  publication synthétique dans le smoke test.
- Check-in pose automatiquement une charge `HEB` (montant de la réservation)
  et `TS`/`TPT` (taxes fixes par pax x nuits, lues depuis pricing-service) sur
  le Folio A — pas de ventilation nuit par nuit en Sprint 4.
- Check-out : Folio A doit être soldé exactement (`balance = 0`) ; Folio B
  ouvert est auto-soldé par un paiement système `Débiteur` (facturation
  agence via partner-service, pas un vrai encaissement).
- Pas de génération de PDF (rapports night-audit) — non-goal Sprint 4, voir
  `docs/decisions/D9-*.md`.

Publie `booking.checked_in`/`booking.checked_out` (`amh.booking` — pas
reservation-service, cf. Appendix C du spec) et `folio.charge_added`
(`amh.folio`). Consomme `audit.closed` (`amh.audit`).

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec front-office-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec front-office-service pytest
```
