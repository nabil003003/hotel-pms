#!/bin/sh
# Seed Sprint 2 : peuple pricing-service, partner-service,
# establishment-service (ota_mappings) et channel-manager-service pour le
# Riad Yasmine déjà créé par scripts/seed_sprint1.sh.
#
# Prérequis : `docker compose --profile core up -d` healthy, seed_sprint1.sh
# déjà exécuté, RIAD_YASMINE_ID exporté (affiché par seed_sprint1.sh).
# Utilise python (json) pour parser les réponses — pas de dépendance à jq.

set -e

export PYTHONIOENCODING=utf-8

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
PRICING_URL="${PRICING_URL:-http://localhost:8004}"
PARTNER_URL="${PARTNER_URL:-http://localhost:8005}"
CHANNEL_URL="${CHANNEL_URL:-http://localhost:8006}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
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
  # json_get <python-expression-on-data>  (lit le JSON depuis stdin)
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

SEASON_MAP="$(mktemp)"
PARTNER_MAP="$(mktemp)"
trap 'rm -f "$SEASON_MAP" "$PARTNER_MAP"' EXIT

map_get() {
  # map_get <file> <label>
  grep -F "$2	" "$1" | tail -n1 | cut -f2
}

echo "==> Creating seasons"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for s in json.load(f)['seasons']:
        print(json.dumps(s))
" | while IFS= read -r season_json; do
  RESP=$(curl -s -X POST "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/seasons" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$season_json")
  SEASON_ID=$(echo "$RESP" | json_get "data['id']")
  LABEL=$(echo "$season_json" | json_get "data['label']")
  printf '%s\t%s\n' "$LABEL" "$SEASON_ID" >> "$SEASON_MAP"
  echo "    -> $LABEL: $SEASON_ID"
done

echo "==> Creating rate_grid rows"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for r in json.load(f)['rate_grid']:
        print(json.dumps(r))
" | while IFS= read -r row_json; do
  SEASON_LABEL=$(echo "$row_json" | json_get "data['season_label']")
  SEASON_ID=$(map_get "$SEASON_MAP" "$SEASON_LABEL")
  BODY=$(echo "$row_json" | python -c "
import json, sys
row = json.load(sys.stdin)
row.pop('season_label')
row['season_id'] = '$SEASON_ID'
print(json.dumps(row))
")
  curl -s -X POST "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/rate-grid" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$BODY" > /dev/null
  echo "    -> rate_grid created for season $SEASON_LABEL"
done

echo "==> Creating taxes_config rows"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for t in json.load(f)['taxes_config']:
        print(json.dumps(t))
" | while IFS= read -r tax_json; do
  curl -s -X POST "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/taxes" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$tax_json" > /dev/null
done
echo "    -> taxes_config seeded"

echo "==> Creating extras_catalog rows"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for e in json.load(f)['extras_catalog']:
        print(json.dumps(e))
" | while IFS= read -r extra_json; do
  curl -s -X POST "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/extras" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$extra_json" > /dev/null
done
echo "    -> extras_catalog seeded"

echo "==> Creating partners"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for p in json.load(f)['partners']:
        print(json.dumps(p))
" | while IFS= read -r partner_json; do
  RESP=$(curl -s -X POST "$PARTNER_URL/api/v1/partners/$RIAD_YASMINE_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$partner_json")
  PARTNER_ID=$(echo "$RESP" | json_get "data['id']")
  NOM=$(echo "$partner_json" | json_get "data['nom']")
  printf '%s\t%s\n' "$NOM" "$PARTNER_ID" >> "$PARTNER_MAP"
  echo "    -> $NOM: $PARTNER_ID"
done

echo "==> Creating partner_rates"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for pr in json.load(f)['partner_rates']:
        print(json.dumps(pr))
" | while IFS= read -r pr_json; do
  PARTNER_NOM=$(echo "$pr_json" | json_get "data['partner_nom']")
  SEASON_LABEL=$(echo "$pr_json" | json_get "data['season_label']")
  PARTNER_ID=$(map_get "$PARTNER_MAP" "$PARTNER_NOM")
  SEASON_ID=$(map_get "$SEASON_MAP" "$SEASON_LABEL")
  BODY=$(echo "$pr_json" | python -c "
import json, sys
row = json.load(sys.stdin)
row.pop('partner_nom')
row.pop('season_label')
row['partner_id'] = '$PARTNER_ID'
row['season_id'] = '$SEASON_ID'
print(json.dumps(row))
")
  curl -s -X POST "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/partner-rates" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$BODY" > /dev/null
  echo "    -> partner_rate created for $PARTNER_NOM / $SEASON_LABEL"
done

echo "==> Creating ota_mappings (establishment-service)"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for m in json.load(f)['ota_mappings']:
        print(json.dumps(m))
" | while IFS= read -r mapping_json; do
  curl -s -X POST "$ESTABLISHMENT_URL/api/v1/establishments/$RIAD_YASMINE_ID/ota-mappings" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$mapping_json" > /dev/null
done
echo "    -> ota_mappings seeded"

echo "==> Creating channel_connections"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    for c in json.load(f)['channel_connections']:
        print(json.dumps(c))
" | while IFS= read -r conn_json; do
  curl -s -X POST "$CHANNEL_URL/api/v1/channel/connections/$RIAD_YASMINE_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d "$conn_json" > /dev/null
done
echo "    -> channel_connections seeded"

echo ""
echo "==> Sprint 2 seed complete for establishment $RIAD_YASMINE_ID"
