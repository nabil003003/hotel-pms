#!/bin/sh
# Sprint 7 (D14) — security_test_sprint7.sh : couvre §7.5 dans la mesure de
# ce qui est réellement vérifiable contre cette stack de dev (voir D14 pour
# ce qui reste hors-scope : scan OWASP ZAP, tests WebAuthn).
#
# Vérifie contre les vrais services (pas de mocks) :
#   1. JWT falsifié (signature modifiée) -> 401
#   2. RBAC : réceptionniste tente une action admin -> 403
#   3. Idempotence : même X-Idempotency-Key rejouée -> même réponse, pas de doublon
#   4. Multi-tenant : token d'un établissement A sur une ressource de B -> 403
#   5. JWT expiré (vrai token, pas de falsification de l'exp) -> 401 —
#      nécessite d'attendre la vraie durée de vie du token (300s, config
#      réaliste de ce realm) ; lancé tôt et vérifié en dernier pour ne pas
#      bloquer les 4 autres checks sur l'attente.
#
# Prérequis : `docker compose --profile core up -d` + seed_sprint1.sh déjà
# exécuté (RIAD_YASMINE_ID connu).

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
RESERVATION_URL="${RESERVATION_URL:-http://localhost:8007}"
REALM="amh-hospitality"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

echo "==> Logging in as sidi.omar (super-admin) and test.receptionniste"
ADMIN_TOKEN=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=pms-frontend" \
  -d "username=sidi.omar" -d "password=ChangeMe123!" | json_get "data['access_token']")

RECEP_RESP=$(curl -s -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=pms-frontend" \
  -d "username=test.receptionniste" -d "password=ChangeMe123!")
RECEP_TOKEN=$(echo "$RECEP_RESP" | json_get "data['access_token']")
RECEP_ISSUED_AT=$(date +%s)
RECEP_EXPIRES_IN=$(echo "$RECEP_RESP" | json_get "data['expires_in']")

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" = "None" ] || [ -z "$RECEP_TOKEN" ] || [ "$RECEP_TOKEN" = "None" ]; then
  echo "Login failed" >&2
  exit 1
fi
echo "    -> tokens acquired (receptionniste token expires in ${RECEP_EXPIRES_IN}s)"

echo "==> [1/5] Tampered JWT -> 401"
# Flip the last character of the signature segment — still well-formed
# JWT shape (3 base64url segments), but the signature no longer verifies.
TAMPERED_TOKEN=$(python -c "
tok = '$RECEP_TOKEN'
head, payload, sig = tok.rsplit('.', 2)
last = sig[-1]
flipped = 'A' if last != 'A' else 'B'
print(f'{head}.{payload}.{sig[:-1]}{flipped}')
")
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$ESTABLISHMENT_URL/api/v1/establishments" \
  -H "Authorization: Bearer $TAMPERED_TOKEN")
if [ "$STATUS" != "401" ]; then
  echo "Expected 401 for tampered JWT, got $STATUS" >&2
  exit 1
fi
echo "    -> tampered JWT correctly rejected (401)"

echo "==> [2/5] RBAC — receptionniste attempting admin-only PATCH /establishments/{id} -> 403"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$ESTABLISHMENT_URL/api/v1/establishments/$RIAD_YASMINE_ID" \
  -H "Authorization: Bearer $RECEP_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Should Not Be Allowed"}')
if [ "$STATUS" != "403" ]; then
  echo "Expected 403 for receptionniste admin action, got $STATUS" >&2
  exit 1
fi
echo "    -> receptionniste correctly rejected from admin action (403)"

echo "==> [3/5] Idempotency — same X-Idempotency-Key replayed on POST /bookings -> same booking, no duplicate"
EPOCH=$(date +%s)
# Offset varies per run (derived from the current epoch) so re-running this
# script never collides with a booking a prior run already left behind —
# the duplicate-row check below is scoped to this exact date pair.
DAY_OFFSET=$((900 + EPOCH % 1000))
TODAY=$(python -c "import datetime; print((datetime.date.today() + datetime.timedelta(days=$DAY_OFFSET)).isoformat())")
TOMORROW=$(python -c "import datetime; print((datetime.date.today() + datetime.timedelta(days=$((DAY_OFFSET + 1)))).isoformat())")
IDEMPOTENCY_KEY="sprint7-security-$EPOCH"
BODY=$(python -c "
import json
print(json.dumps({
    'establishment_id': '$RIAD_YASMINE_ID', 'market_segment_category': 'DIRECT',
    'room_category': 'Chambre Standard', 'check_in_date': '$TODAY', 'check_out_date': '$TOMORROW',
    'regime': 'BB', 'taxes_payment_mode': 'on_site', 'adults': 1,
    'customer': {'first_name': 'Sprint7Sec', 'last_name': 'Idempotency'},
    'source': 'walk_in', 'deposit_paid': True,
}))
")
FIRST_ID=$(curl -s -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $RECEP_TOKEN" -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: $IDEMPOTENCY_KEY" -d "$BODY" | json_get "data['id']")
SECOND_ID=$(curl -s -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $RECEP_TOKEN" -H "Content-Type: application/json" \
  -H "X-Idempotency-Key: $IDEMPOTENCY_KEY" -d "$BODY" | json_get "data['id']")
if [ -z "$FIRST_ID" ] || [ "$FIRST_ID" = "None" ] || [ "$FIRST_ID" != "$SECOND_ID" ]; then
  echo "Expected identical booking id on replay, got '$FIRST_ID' then '$SECOND_ID'" >&2
  exit 1
fi
DUPLICATE_COUNT=$(docker compose -f "${COMPOSE_FILE:-infra/docker-compose.yml}" exec -T postgres psql -U amh -d reserv_db -tAc \
  "SELECT count(*) FROM bookings WHERE establishment_id = '$RIAD_YASMINE_ID' AND check_in_date = '$TODAY' AND check_out_date = '$TOMORROW';" | tr -d '[:space:]')
if [ "$DUPLICATE_COUNT" != "1" ]; then
  echo "Expected exactly 1 booking row for the idempotent request, found $DUPLICATE_COUNT" >&2
  exit 1
fi
echo "    -> replayed request returned the same booking ($FIRST_ID), exactly 1 row persisted"

echo "==> [4/5] Multi-tenant isolation — receptionniste (Riad Yasmine only) reading a different establishment -> 403"
FIXTURE_ID=$(curl -s -X POST "$ESTABLISHMENT_URL/api/v1/establishments" \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Sprint7 Security Test Fixture", "city": "Marrakech", "total_rooms": 1}' \
  | json_get "data['id']")
if [ -z "$FIXTURE_ID" ] || [ "$FIXTURE_ID" = "None" ]; then
  echo "Failed to create the throwaway establishment for the multi-tenant check" >&2
  exit 1
fi
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$ESTABLISHMENT_URL/api/v1/establishments/$FIXTURE_ID" \
  -H "Authorization: Bearer $RECEP_TOKEN")
if [ "$STATUS" != "403" ]; then
  echo "Expected 403 for cross-establishment access, got $STATUS" >&2
  exit 1
fi
echo "    -> receptionniste correctly rejected from a foreign establishment (403), fixture=$FIXTURE_ID left in place"

echo "==> [5/5] Expired JWT -> 401 (waiting out the real ${RECEP_EXPIRES_IN}s token lifetime, not a forged exp claim)"
NOW=$(date +%s)
ELAPSED=$((NOW - RECEP_ISSUED_AT))
REMAINING=$((RECEP_EXPIRES_IN - ELAPSED + 10))
if [ "$REMAINING" -gt 0 ]; then
  echo "    -> sleeping ${REMAINING}s for the token to genuinely expire"
  sleep "$REMAINING"
fi
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$ESTABLISHMENT_URL/api/v1/establishments" \
  -H "Authorization: Bearer $RECEP_TOKEN")
if [ "$STATUS" != "401" ]; then
  echo "Expected 401 for expired JWT, got $STATUS" >&2
  exit 1
fi
echo "    -> expired JWT correctly rejected (401)"

echo ""
echo "==> Sprint 7 security tests: ALL PASSED"
