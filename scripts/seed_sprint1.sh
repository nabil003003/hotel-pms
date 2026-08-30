#!/bin/sh
# Seed Sprint 1 : crée le Riad Yasmine (fixtures/seed_riad_yasmine.json) via
# establishment-service, puis met à jour les attributs `establishment_ids`
# des utilisateurs de test Keycloak (placeholders __RIAD_YASMINE_ID__ dans
# infra/keycloak/realm-export.json — l'UUID réel n'existe qu'après ce seed).
#
# Prérequis : `docker compose --profile core up -d` déjà lancé et healthy.
# Utilise python (json) pour parser les réponses — pas de dépendance à jq.

set -e

# Voir smoke_test_sprint1.sh pour le détail — force un décodage UTF-8
# cohérent de stdin/stdout côté python (interpréteur natif Windows).
export PYTHONIOENCODING=utf-8

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
REALM="amh-hospitality"
FIXTURES="$ROOT/fixtures/seed_riad_yasmine.json"
TMP_ROOMS_RESP="$ROOT/scripts/.rooms_create_resp.json"

# `python` ici est l'interpréteur natif Windows (aucun python POSIX
# disponible dans ce Git Bash) — il ne comprend pas les chemins /c/...
# convertis en C:\... via cygpath quand disponible (no-op ailleurs, ex CI Linux).
winpath() {
  if command -v cygpath > /dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

FIXTURES_NATIVE="$(winpath "$FIXTURES")"
TMP_ROOMS_RESP_NATIVE="$(winpath "$TMP_ROOMS_RESP")"

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
  echo "Failed to obtain admin token — is Keycloak up and the realm imported?" >&2
  exit 1
fi

echo "==> Creating establishment 'Riad Yasmine'"
ESTABLISHMENT_JSON=$(python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    print(json.dumps(json.load(f)['establishment']))
")

CREATE_RESP=$(curl -s -X POST "$ESTABLISHMENT_URL/api/v1/establishments" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$ESTABLISHMENT_JSON")

ESTABLISHMENT_ID=$(echo "$CREATE_RESP" | json_get "data['id']")

if [ -z "$ESTABLISHMENT_ID" ] || [ "$ESTABLISHMENT_ID" = "None" ]; then
  echo "Failed to create establishment. Response: $CREATE_RESP" >&2
  exit 1
fi

echo "==> Establishment created: $ESTABLISHMENT_ID"

echo "==> Importing rooms"
ROOMS_JSON=$(python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    print(json.dumps(json.load(f)['rooms']))
")

curl -s -X POST "$ESTABLISHMENT_URL/api/v1/establishments/$ESTABLISHMENT_ID/rooms" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$ROOMS_JSON" > "$TMP_ROOMS_RESP"

ROOM_COUNT=$(python -c "import json; print(len(json.load(open(r'$TMP_ROOMS_RESP_NATIVE', encoding='utf-8'))))")
rm -f "$TMP_ROOMS_RESP"
echo "    -> $ROOM_COUNT rooms created"

echo "==> Creating establishment services (Hammam, Transfert, Excursion, Dîner, Cours de cuisine)"
python -c "
import json
with open(r'$FIXTURES_NATIVE', encoding='utf-8') as f:
    services = json.load(f)['establishment_services']
for s in services:
    print(json.dumps(s))
" | while IFS= read -r service_json; do
  curl -s -X POST "$ESTABLISHMENT_URL/api/v1/establishments/$ESTABLISHMENT_ID/services" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$service_json" > /dev/null
done

echo "==> Updating Keycloak test users' establishment_ids attribute"
KC_ADMIN_TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/master/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin_dev_password" \
  | json_get "data['access_token']")

for username in test.receptionniste test.gouvernante test.femmedechambre; do
  USER_ID=$(curl -s -G "$KEYCLOAK_URL/admin/realms/$REALM/users" \
    --data-urlencode "username=$username" --data-urlencode "exact=true" \
    -H "Authorization: Bearer $KC_ADMIN_TOKEN" \
    | json_get "data[0]['id']")

  if [ -z "$USER_ID" ] || [ "$USER_ID" = "None" ]; then
    echo "    !! user not found: $username (skipping)" >&2
    continue
  fi

  curl -s -X PUT "$KEYCLOAK_URL/admin/realms/$REALM/users/$USER_ID" \
    -H "Authorization: Bearer $KC_ADMIN_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"attributes\": {\"establishment_ids\": [\"$ESTABLISHMENT_ID\"], \"is_super_admin\": [\"false\"]}}" \
    > /dev/null
  echo "    -> $username scoped to $ESTABLISHMENT_ID"
done

echo ""
echo "==> Seed complete. Establishment ID: $ESTABLISHMENT_ID"
echo "    export RIAD_YASMINE_ID=$ESTABLISHMENT_ID  # utile pour scripts/smoke_test_sprint1.sh"
