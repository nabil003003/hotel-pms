#!/bin/sh
# Seed Sprint 5 : night-audit-service et notification-service n'ont pas de
# données de configuration propres (pas de schéma spec pour notif_db, D11 ;
# audit_runs/system_state sont générés par le workflow lui-même, pas
# pré-remplis). Ce script se contente de vérifier que les prérequis
# (Sprint 1-4) sont en place avant de lancer smoke_test_sprint5.sh.
#
# Prérequis : `docker compose --profile core up -d` healthy, seed_sprint1.sh
# + seed_sprint2.sh + seed_sprint3.sh + seed_sprint4.sh déjà exécutés,
# RIAD_YASMINE_ID exporté.

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
FRONT_OFFICE_URL="${FRONT_OFFICE_URL:-http://localhost:8008}"
ANALYTICS_URL="${ANALYTICS_URL:-http://localhost:8009}"
REALM="amh-hospitality"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

echo "==> Obtaining admin token"
TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=pms-frontend" \
  -d "username=sidi.omar" -d "password=ChangeMe123!" \
  | json_get "data['access_token']")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
  echo "Failed to obtain admin token — is Keycloak up?" >&2
  exit 1
fi

echo "==> Checking front-office-service reports are reachable (Sprint 4 prerequisite)"
TODAY=$(python -c "import datetime; print(datetime.date.today().isoformat())")
curl -sf -G "$FRONT_OFFICE_URL/api/v1/folios/reports/daily-debits" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" --data-urlencode "date=$TODAY" \
  -H "Authorization: Bearer $TOKEN" > /dev/null
echo "    -> front-office-service reports OK"

echo "==> Checking analytics-service is reachable (Sprint 4 prerequisite)"
curl -sf -G "$ANALYTICS_URL/api/v1/kpi/today" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" -H "Authorization: Bearer $TOKEN" > /dev/null
echo "    -> analytics-service OK"

echo ""
echo "==> Sprint 5 prerequisites OK for establishment $RIAD_YASMINE_ID"
echo "    Run ./scripts/smoke_test_sprint5.sh next (it creates its own test bookings)."
