# night-audit-service

Sprint 5. Orchestrateur de la clôture journalière (Workflow I, spec §4.9) :

1. `POST /api/v1/night-audit/verify` — somme débits/crédits du jour via
   front-office-service ; si écart > 0.01 MAD, alerte
   notification-service (email+push) et bloque totalement le lancement.
   Sinon retourne `token_audit` (Redis, 30 min, usage unique).
2. `GET /api/v1/night-audit/discrepancy-report` — proxy vers
   front-office-service.
3. `POST /api/v1/night-audit/close` (header `X-Audit-Token`) — génère les 6
   rapports PDF (`reportlab`), les archive sur MinIO, verrouille la date
   pour front-office-service et reservation-service (publie `audit.closed`,
   qu'ils consomment déjà), bascule `system_state` à J+1, envoie l'email de
   rapport à la direction.
4. `GET /api/v1/night-audit/business-date` — lecture `system_state`, cache
   Redis 5 min.

Voir `docs/decisions/D12-night-audit-scope.md` pour les choix de périmètre
(génération PDF, verrous cross-service, prévisions analytics simplifiées).
