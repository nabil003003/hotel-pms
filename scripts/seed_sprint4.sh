#!/bin/sh
# Seed Sprint 4 : front-office-service et analytics-service n'ont pas de
# données de configuration propres (pas de "seasons"/"segments" à créer ici)
# — ils opèrent sur les réservations créées par reservation-service. Ce
# script se contente de vérifier que les prérequis (Sprint 1-3) sont en
# place avant de lancer smoke_test_sprint4.sh, qui crée sa propre réservation
# de test à la volée.
#
# Prérequis : `docker compose --profile core up -d` healthy, seed_sprint1.sh
# + seed_sprint2.sh + seed_sprint3.sh déjà exécutés, RIAD_YASMINE_ID exporté.

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
RESERVATION_URL="${RESERVATION_URL:-http://localhost:8007}"
PARTNER_URL="${PARTNER_URL:-http://localhost:8005}"
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

echo "==> Checking market segments exist (Sprint 3 seed)"
SEGMENT_COUNT=$(curl -sf "$RESERVATION_URL/api/v1/market-segments/$RIAD_YASMINE_ID" \
  -H "Authorization: Bearer $TOKEN" | json_get "len(data)")
if [ "$SEGMENT_COUNT" -lt 1 ]; then
  echo "No market segments found — run scripts/seed_sprint3.sh first." >&2
  exit 1
fi
echo "    -> $SEGMENT_COUNT market segment(s) found"

echo "==> Checking Atlas Voyages partner exists (Sprint 2 seed)"
PARTNER_COUNT=$(curl -sf -G "$PARTNER_URL/api/v1/partners/$RIAD_YASMINE_ID" \
  --data-urlencode "type=AGENCE" -H "Authorization: Bearer $TOKEN" | json_get "len(data)")
if [ "$PARTNER_COUNT" -lt 1 ]; then
  echo "No AGENCE partner found — run scripts/seed_sprint2.sh first." >&2
  exit 1
fi
echo "    -> $PARTNER_COUNT partner(s) found"

echo ""
echo "==> Sprint 4 prerequisites OK for establishment $RIAD_YASMINE_ID"
echo "    Run ./scripts/smoke_test_sprint4.sh next (it creates its own test booking)."
