# D9 — front-office-service sans night-audit-service

**Statut** : Adopté, Sprint 4.

## Contexte

Le Workflow I (Night Audit, §4.9) est le propriétaire de la "date métier"
(`business_date`) : c'est lui qui la fait avancer (bascule J→J+1) et qui
verrouille les écritures d'un jour clos via `business_date_locks`. Il
appelle aussi front-office-service pour les totaux de la journée
(`daily-debits`/`daily-credits`) et produit les rapports PDF de clôture.
`night-audit-service` n'existe pas avant le Sprint 5.

## Décision

- `business_date` sur `folios`/`folio_charges`/`payments` = date serveur
  (`date.today()`) au moment de l'écriture — pas de bascule J+1 pilotée,
  puisque rien ne la déclenche encore.
- Le verrou (`assert_business_date_not_locked`, appelé avant toute écriture)
  est câblé pour de vrai : front-office-service **consomme** `audit.closed`
  (queue `fo.audit_events`, exchange `amh.audit`, déclaré depuis Sprint 1,
  jamais utilisé jusqu'ici) et pose `business_date_locks.is_locked = true`
  à la réception. Comme aucun service ne publie encore cet événement, le
  verrou ne se déclenche qu'en test (smoke test Sprint 4 : publication
  synthétique via l'API HTTP de RabbitMQ, même technique que
  `booking.created` en Sprint 2/3).
- `GET /api/v1/folios/daily-debits`, `daily-credits`, `discrepancy-report`
  sont implémentés comme de vraies requêtes d'agrégation (pas des stubs) —
  ce sont les endpoints que night-audit-service appellera au Sprint 5.
- **Aucune génération de PDF** (`ca_detaille_J.pdf`, `encaissements_J.pdf`,
  `debiteurs_J.pdf`, `departs_attendus_J+1.pdf`) — c'est
  night-audit-service qui orchestrera cette génération ; ce sprint ne
  construit que les données sources.

## Conséquences

- Quand night-audit-service sera construit (Sprint 5), il devra publier
  `audit.closed` avec `{establishment_id, business_date, report_hash}` — le
  handler côté front-office-service (`handle_audit_closed`) est déjà prêt à
  le recevoir sans modification.
- Tant que `night-audit-service` n'existe pas, aucune date n'est jamais
  verrouillée en usage réel — seulement en test. Documenté, pas un bug.
