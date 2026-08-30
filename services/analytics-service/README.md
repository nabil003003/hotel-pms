# analytics-service

KPI temps réel, dashboards, agrégations multi-établissements. Sprint 4.
Schéma transcrit du spec §5.7 (+fix `segment_id`, voir plus bas).

## Endpoints (Workflow J, spec §4.10)

| Method | Path | RBAC |
|---|---|---|
| GET | `/api/v1/kpi/today?establishment_id=` (cache Redis 5 min) | `manager`/`admin`/`comptable` |
| GET | `/api/v1/kpi/monthly?month=YYYY-MM&establishment_id=` (cache Redis 1h) | `manager`/`admin`/`comptable` |
| GET | `/api/v1/kpi/consolidated?month=YYYY-MM` | super-admin uniquement |
| GET | `/api/v1/segments/distribution?period=YYYY-MM&establishment_id=` | `manager`/`admin`/`comptable` |
| GET | `/api/v1/segments/revenue?period=YYYY-MM&establishment_id=` | `manager`/`admin`/`comptable` |
| GET | `/api/v1/segments/trend?segment={code}&granularity=month&establishment_id=` | `manager`/`admin`/`comptable` |
| GET | `/api/v1/ytd/compare?month=MM&establishment_id=` | `manager`/`admin`/`comptable` |
| GET | `/api/v1/channel/performance?period=YYYY-MM&establishment_id=` | `manager`/`admin`/`comptable` |

`/api/v1/channel/performance` est **distinct** de l'endpoint de même forme
sur channel-manager-service (Sprint 2, `sync_logs` — santé de synchronisation
OTA). Celui-ci est la vue "revenu par canal" propre à analytics-service,
alimentée par `channel.booking_received` (table `channel_performance`).
Ports différents, intentions différentes, même chemin — documenté dans les
deux README pour éviter la confusion.

## Décisions Sprint 4 (D10)

- **`segment_id` non-nullable** (fix schéma — transcription littérale le
  voulait nullable *et* clé primaire, invalide en Postgres). Totaux "tous
  segments" calculés par somme à la lecture.
- Pas de Celery : `monthly_kpi_aggregation` est recalculée à la demande
  depuis `daily_kpi_snapshot` (`recompute_monthly_aggregation`), pas via un
  job planifié.
- `daily_kpi_snapshot` alimentée en temps réel par les événements
  (`booking.checked_in`, `folio.charge_added`) plutôt qu'en un seul batch
  après `audit.closed` — `audit.closed` (night-audit-service, Sprint 5, pas
  encore construit) déclenche une re-consolidation mensuelle plutôt qu'une
  première écriture.
- `nuitees`/`pax_total` : compteurs incrémentés au `check_in`, proxy
  simplifié (pas le comptage nuit-par-nuit précis qu'une vraie clôture
  journalière ferait). `dms` reste à 0 (pas de comptage de séjours distincts
  en Sprint 4) — pas de chiffre fabriqué.
- `channel_performance.commission` reste à 0 (pas de source fiable par
  réservation au moment de l'événement).

Consomme `booking.checked_in` (`amh.booking`), `folio.charge_added`
(`amh.folio`), `channel.booking_received` (`amh.channel`), `audit.closed`
(`amh.audit`). Ne publie aucun événement.

## Développement local

```bash
docker compose -f ../../infra/docker-compose.yml --profile core up -d
docker compose -f ../../infra/docker-compose.yml exec analytics-service alembic upgrade head
docker compose -f ../../infra/docker-compose.yml exec analytics-service pytest
```
