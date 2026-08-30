#!/bin/sh
# Seed Sprint 3 : crée les market_segments (reservation-service) pour le
# Riad Yasmine déjà créé par scripts/seed_sprint1.sh (et pricing/partner
# déjà seedés par scripts/seed_sprint2.sh — ce script dépend de la season
# "Haute saison 2026" et du partenaire "Atlas Voyages" pour le smoke test).
#
# Prérequis : `docker compose --profile core up -d` healthy, seed_sprint1.sh
# et seed_sprint2.sh déjà exécutés, RIAD_YASMINE_ID exporté.

set -e

export PYTHONIOENCODING=utf-8

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
RESERVATION_URL="${RESERVATION_URL:-http://localhost:8007}"
REALM="amh-hospitality"
FIXTURES="$ROOT/fixtures/seed_riad_yasmine.json"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

winpath() {
  if command -v cygpath > /dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

FIXTURES_NATIVE="$(winpath "$FIXTURES")"

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

echo "==> Obtaining admin token (sidi.omar / pms-frontend, Direct Access Grant)"
ADMIN_TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=pms-frontend" \
  -d "username=sidi.omar" \
  -d "password=ChangeMe123!" \
  | json_get "data['access_token']")

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "None" ]; then
  echo "Failed to obtain admin token — is Keycloak up?" >&2
  exit 1
fi

echo "==> Creating market segments"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for s in json.load(f)['market_segments']:
        print(json.dumps(s))
" | while IFS= read -r segment_json; do
  RESP=$(curl -s -X POST "$RESERVATION_URL/api/v1/market-segments/$RIAD_YASMINE_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$segment_json")
  CODE=$(echo "$segment_json" | json_get "data['code']")
  SEGMENT_ID=$(echo "$RESP" | json_get "data.get('id', 'ERROR: ' + str(data))")
  echo "    -> $CODE: $SEGMENT_ID"
done

echo ""
echo "==> Sprint 3 seed complete for establishment $RIAD_YASMINE_ID"
