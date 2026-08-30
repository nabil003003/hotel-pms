# D10 — Calcul des KPI analytics-service sans scheduler réel

**Statut** : Adopté, Sprint 4.

## Contexte

Le spec décrit `daily_kpi_snapshot` comme rempli "une fois par jour après
`audit.closed`" et `monthly_kpi_aggregation` comme "recalculée en fin de
mois (job Celery)". Aucun service de ce monorepo n'utilise Celery (choix
constant depuis le Sprint 3 — voir `reservation-service`,
`channel-manager-service` : boucles asyncio en tâche de fond à la place).
`night-audit-service` (seul émetteur prévu de `audit.closed`) n'existe pas
avant le Sprint 5.

## Décision

- **Pas de Celery.** `daily_kpi_snapshot` est alimentée **en temps réel**
  par les événements (`booking.checked_in` → `nuitees`/`pax_total`,
  `folio.charge_added` → `ca_brut`/`ca_ht`/`tva_total`) plutôt qu'en un
  seul batch après clôture — cohérent avec "KPI temps réel" (description du
  service, ligne 117 du spec). `audit.closed` (consommé, pas encore publié
  par personne avant Sprint 5) déclenche une **re-consolidation** de
  `monthly_kpi_aggregation` pour le mois concerné plutôt qu'une première
  écriture.
- `monthly_kpi_aggregation` est recalculée à la demande
  (`recompute_monthly_aggregation`, appelée par `GET /kpi/monthly`, les
  endpoints `/segments/*`, `/ytd/compare`, et par `audit.closed`) — toujours
  juste, aucune tâche planifiée nécessaire.
- **Compteurs non calculés, documentés plutôt que fabriqués** :
  - `nuitees`/`pax_total` sont incrémentés du nombre de nuits/pax **au
    check-in** — un proxy simplifié ("séjour démarré aujourd'hui"), pas le
    comptage nuit-par-nuit précis qu'une vraie clôture journalière ferait
    (chaque nuit d'un séjour de 5 jours devrait apparaître dans 5 snapshots
    différents ; ici tout est crédité au jour du check-in). À corriger
    quand night-audit-service fera le calcul réel au Sprint 5.
  - `dms` (durée moyenne de séjour) reste à 0 — nécessiterait un comptage de
    séjours distincts non tenu en Sprint 4.
  - `channel_performance.commission` reste à 0 —
    `partner_rates.commission_pct` est lié à des combinaisons
    saison/catégorie, pas une valeur unique consultable par réservation au
    moment de l'événement `channel.booking_received`.
- `kpi_ytd_comparison` (vue SQL, déjà anticipée dans le docstring du fichier
  modèle) créée via migration Alembic (`op.execute`), interrogée
  directement par `GET /ytd/compare`.
- **Fix schéma** : `segment_id` sur `daily_kpi_snapshot` et
  `monthly_kpi_aggregation` rendu non-nullable — la transcription littérale
  le voulait nullable *et* membre de la clé primaire, ce que Postgres
  rejette (colonne de PK = NOT NULL obligatoire). Chaque ligne reste scopée
  à un segment réel ; les totaux "tous segments" sont sommés à la lecture.

## Conséquences

- Sprint 5 (night-audit-service) : publier `audit.closed` réellement, et
  envisager de corriger `nuitees` pour un vrai comptage nuit-par-nuit
  (remplacerait le proxy check-in par un job nocturne qui compte les
  réservations `status_checked_in` actives chaque nuit).
- `GET /api/v1/channel/performance` existe maintenant sur **deux**
  services (channel-manager-service depuis Sprint 2, analytics-service
  depuis ce sprint) avec des sens différents — voir les deux README pour la
  distinction (santé de sync OTA vs. revenu par canal).
