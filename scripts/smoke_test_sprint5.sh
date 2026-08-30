#!/bin/sh
# Smoke test Sprint 5 — vérifie night-audit-service et notification-service
# de bout en bout : verify (débits==crédits) -> token d'audit -> close
# (6 rapports PDF archivés MinIO, business_date bascule J+1, audit.closed
# publié) -> notification-service a reçu l'email de rapport -> le verrou
# business_date bloque une nouvelle réservation sur reservation-service ->
# housekeeping-service a basculé la chambre encore occupée en "Sale".
#
# Prérequis : `docker compose --profile core up -d` + seed_sprint1..5.sh
# déjà exécutés. Nécessite RIAD_YASMINE_ID.

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
HOUSEKEEPING_URL="${HOUSEKEEPING_URL:-http://localhost:8003}"
RESERVATION_URL="${RESERVATION_URL:-http://localhost:8007}"
FRONT_OFFICE_URL="${FRONT_OFFICE_URL:-http://localhost:8008}"
ANALYTICS_URL="${ANALYTICS_URL:-http://localhost:8009}"
NIGHT_AUDIT_URL="${NIGHT_AUDIT_URL:-http://localhost:8010}"
NOTIFICATION_URL="${NOTIFICATION_URL:-http://localhost:8011}"
COMPOSE_FILE="${COMPOSE_FILE:-infra/docker-compose.yml}"
REALM="amh-hospitality"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

echo "==> Waiting for /healthz on night-audit/notification"
for url in "$NIGHT_AUDIT_URL" "$NOTIFICATION_URL"; do
  n=0
  until curl -sf "$url/healthz" > /dev/null; do
    n=$((n + 1))
    if [ "$n" -gt 30 ]; then
      echo "Timed out waiting for $url/healthz" >&2
      exit 1
    fi
    sleep 2
  done
  echo "    -> $url OK"
done

echo "==> Logging in as sidi.omar (super-admin)"
TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=pms-frontend" \
  -d "username=sidi.omar" -d "password=ChangeMe123!" \
  | json_get "data['access_token']")
if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
  echo "Login failed" >&2
  exit 1
fi

echo "==> 401 check (no token) on /night-audit/verify"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$NIGHT_AUDIT_URL/api/v1/night-audit/verify" \
  -H "Content-Type: application/json" -d '{}')
if [ "$STATUS" != "401" ]; then
  echo "Expected 401 for verify without auth, got $STATUS" >&2
  exit 1
fi
echo "    -> POST /night-audit/verify rejects unauthenticated requests"

TODAY=$(python -c "import datetime; print(datetime.date.today().isoformat())")
TOMORROW=$(python -c "import datetime; print((datetime.date.today() + datetime.timedelta(days=1)).isoformat())")

echo "==> Clearing any stale business_date lock for $TODAY (artifact of a same-day Sprint 4/5 rerun)"
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U amh -d fo_db \
  -c "DELETE FROM business_date_locks WHERE business_date = '$TODAY';" > /dev/null
docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U amh -d reserv_db \
  -c "DELETE FROM business_date_locks WHERE business_date = '$TODAY';" > /dev/null

ensure_room_ready() {
  room_id="$1"
  status=$(curl -sf "$HOUSEKEEPING_URL/api/v1/rooms/$room_id/status" -H "Authorization: Bearer $TOKEN" | json_get "data['statut']")
  if [ "$status" != "Propre" ] && [ "$status" != "Contrôlée" ]; then
    BODY_FILE=$(mktemp)
    printf '{"new_status": "Propre"}' > "$BODY_FILE"
    curl -sf -X PATCH "$HOUSEKEEPING_URL/api/v1/rooms/$room_id/status" \
      -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json; charset=utf-8" \
      --data-binary "@$BODY_FILE" > /dev/null
    rm -f "$BODY_FILE"
  fi
}

echo "==> Booking 1 : walk-in, check-in + settle + check-out today (balanced debits/credits for /verify)"
BOOKING1=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "DIRECT",
    "room_category": "Chambre Standard",
    "check_in_date": "'"$TODAY"'",
    "check_out_date": "'"$TOMORROW"'",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 2,
    "customer": {"first_name": "Sprint5a", "last_name": "SmokeTest"},
    "source": "walk_in",
    "deposit_paid": true
  }')
BOOKING1_ID=$(echo "$BOOKING1" | json_get "data['id']")
BOOKING1_ROOM=$(echo "$BOOKING1" | json_get "data['room_id']")
ensure_room_ready "$BOOKING1_ROOM"

CHECKIN1=$(curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-in" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "booking_id": "'"$BOOKING1_ID"'"}')
FOLIO1_ID=$(echo "$CHECKIN1" | json_get "data['folio_ids'][0]")

FOLIO1=$(curl -sf "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO1_ID" -H "Authorization: Bearer $TOKEN")
BALANCE1=$(echo "$FOLIO1" | json_get "data['balance']")
curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO1_ID/payments" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"mode": "CB", "montant": '"$BALANCE1"'}' > /dev/null

curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-out" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "booking_id": "'"$BOOKING1_ID"'"}' > /dev/null
echo "    -> booking1=$BOOKING1_ID checked in, settled ($BALANCE1), checked out"

echo "==> Booking 2 : walk-in, check-in + settle but stays occupied (proves housekeeping end-of-day turnover)"
BOOKING2=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "DIRECT",
    "room_category": "Chambre Standard",
    "check_in_date": "'"$TODAY"'",
    "check_out_date": "'"$TOMORROW"'",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 1,
    "customer": {"first_name": "Sprint5b", "last_name": "SmokeTest"},
    "source": "walk_in",
    "deposit_paid": true
  }')
BOOKING2_ID=$(echo "$BOOKING2" | json_get "data['id']")
BOOKING2_ROOM=$(echo "$BOOKING2" | json_get "data['room_id']")
ensure_room_ready "$BOOKING2_ROOM"

CHECKIN2=$(curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-in" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "booking_id": "'"$BOOKING2_ID"'"}')
FOLIO2_ID=$(echo "$CHECKIN2" | json_get "data['folio_ids'][0]")

FOLIO2=$(curl -sf "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO2_ID" -H "Authorization: Bearer $TOKEN")
BALANCE2=$(echo "$FOLIO2" | json_get "data['balance']")
curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO2_ID/payments" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"mode": "CB", "montant": '"$BALANCE2"'}' > /dev/null
echo "    -> booking2=$BOOKING2_ID checked in, settled ($BALANCE2), room=$BOOKING2_ROOM stays occupied"

echo "==> POST /night-audit/verify (debits should equal credits)"
VERIFY=$(curl -sf -X POST "$NIGHT_AUDIT_URL/api/v1/night-audit/verify" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "business_date": "'"$TODAY"'"}')
DISCREPANCY=$(echo "$VERIFY" | json_get "data['discrepancy']")
AUDIT_TOKEN=$(echo "$VERIFY" | json_get "data['token_audit']")
echo "    -> discrepancy=$DISCREPANCY token_audit=$(echo "$AUDIT_TOKEN" | cut -c1-8)..."
if [ "$DISCREPANCY" != "0.0" ] && [ "$DISCREPANCY" != "0.00" ] && [ "$DISCREPANCY" != "0" ]; then
  echo "Expected discrepancy=0, got $DISCREPANCY" >&2
  exit 1
fi
if [ -z "$AUDIT_TOKEN" ] || [ "$AUDIT_TOKEN" = "None" ]; then
  echo "Expected a non-empty token_audit" >&2
  exit 1
fi

echo "==> GET /night-audit/discrepancy-report (should be empty)"
DISCREPANCY_REPORT=$(curl -sf -G "$NIGHT_AUDIT_URL/api/v1/night-audit/discrepancy-report" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" --data-urlencode "date=$TODAY" \
  -H "Authorization: Bearer $TOKEN")
REPORT_COUNT=$(echo "$DISCREPANCY_REPORT" | json_get "len(data)")
echo "    -> $REPORT_COUNT discrepant folio(s)"

echo "==> POST /night-audit/close (X-Audit-Token) — irreversible"
CLOSE=$(curl -sf -X POST "$NIGHT_AUDIT_URL/api/v1/night-audit/close" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "X-Audit-Token: $AUDIT_TOKEN" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "business_date": "'"$TODAY"'"}')
REPORT_HASH=$(echo "$CLOSE" | json_get "data['report_hash']")
NEW_BUSINESS_DATE=$(echo "$CLOSE" | json_get "data['new_business_date']")
REPORT_COUNT2=$(echo "$CLOSE" | json_get "len(data['report_urls'])")
echo "    -> report_hash=$(echo "$REPORT_HASH" | cut -c1-12)... new_business_date=$NEW_BUSINESS_DATE reports=$REPORT_COUNT2"
if [ "$NEW_BUSINESS_DATE" != "$TOMORROW" ]; then
  echo "Expected new_business_date=$TOMORROW, got $NEW_BUSINESS_DATE" >&2
  exit 1
fi
if [ "$REPORT_COUNT2" != "6" ]; then
  echo "Expected 6 report URLs, got $REPORT_COUNT2" >&2
  exit 1
fi

echo "==> Re-closing with the same (now-consumed) token must be rejected"
REUSE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$NIGHT_AUDIT_URL/api/v1/night-audit/close" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "X-Audit-Token: $AUDIT_TOKEN" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "business_date": "'"$TODAY"'"}')
if [ "$REUSE_STATUS" != "401" ]; then
  echo "Expected 401 on audit token reuse, got $REUSE_STATUS" >&2
  exit 1
fi
echo "    -> correctly rejected (401)"

echo "==> GET /night-audit/business-date reflects the rollover"
BD=$(curl -sf -G "$NIGHT_AUDIT_URL/api/v1/night-audit/business-date" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" -H "Authorization: Bearer $TOKEN" | json_get "data['business_date']")
if [ "$BD" != "$TOMORROW" ]; then
  echo "Expected business-date=$TOMORROW, got $BD" >&2
  exit 1
fi
echo "    -> business_date=$BD"

echo "==> Polling notification-service for the report-ready email (up to 20s)"
n=0
FOUND=""
while [ "$n" -lt 10 ]; do
  NOTIFS=$(curl -sf -G "$NOTIFICATION_URL/api/v1/notifications" \
    --data-urlencode "establishment_id=$RIAD_YASMINE_ID" --data-urlencode "event_type=audit.report_ready" \
    -H "Authorization: Bearer $TOKEN")
  COUNT=$(echo "$NOTIFS" | json_get "len(data)")
  if [ "$COUNT" -gt 0 ]; then
    FOUND="yes"
    break
  fi
  n=$((n + 1))
  sleep 2
done
if [ -z "$FOUND" ]; then
  echo "Expected at least one audit.report_ready notification" >&2
  exit 1
fi
echo "    -> report-ready notification recorded"

echo "==> Reservation-service must reject a new booking dated on the now-locked $TODAY (423)"
LOCK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "DIRECT",
    "room_category": "Chambre Standard",
    "check_in_date": "'"$TODAY"'",
    "check_out_date": "'"$TOMORROW"'",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 1,
    "customer": {"first_name": "Sprint5c", "last_name": "SmokeTest"},
    "source": "walk_in",
    "deposit_paid": true
  }')
if [ "$LOCK_STATUS" != "423" ]; then
  echo "Expected 423 LOCKED creating a booking on a closed business_date, got $LOCK_STATUS" >&2
  exit 1
fi
echo "    -> correctly rejected (423)"

echo "==> Polling housekeeping-service for booking2's room turning Sale (up to 20s)"
n=0
TURNED=""
while [ "$n" -lt 10 ]; do
  ROOM2_STATUS=$(curl -sf "$HOUSEKEEPING_URL/api/v1/rooms/$BOOKING2_ROOM/status" -H "Authorization: Bearer $TOKEN" | json_get "data['statut']")
  if [ "$ROOM2_STATUS" = "Sale" ]; then
    TURNED="yes"
    break
  fi
  n=$((n + 1))
  sleep 2
done
if [ -z "$TURNED" ]; then
  echo "Expected room $BOOKING2_ROOM to turn 'Sale' after audit.closed (got $ROOM2_STATUS)" >&2
  exit 1
fi
echo "    -> room $BOOKING2_ROOM turned Sale"

echo "==> GET analytics-service occupancy forecast for $TOMORROW"
FORECAST=$(curl -sf -G "$ANALYTICS_URL/api/v1/forecast/occupancy" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" --data-urlencode "date=$TOMORROW" \
  -H "Authorization: Bearer $TOKEN")
ARRIVALS=$(echo "$FORECAST" | json_get "data['arrivals_count']")
echo "    -> arrivals_count=$ARRIVALS"

echo ""
echo "==> Sprint 5 smoke test complete."
