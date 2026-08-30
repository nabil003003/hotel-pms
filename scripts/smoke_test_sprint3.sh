#!/bin/sh
# Smoke test Sprint 3 — vérifie reservation-service de bout en bout :
# healthz -> réservation walk-in (option) -> réservation B2B (voucher, tarif
# négocié) -> room shift même catégorie -> upsell refusé sans élévation puis
# accepté avec élévation -> webhook OTA (channel-manager-service, chemin
# synchrone D6) -> annulation manuelle.
#
# Prérequis : `docker compose --profile core up -d` + seed_sprint1.sh +
# seed_sprint2.sh + seed_sprint3.sh déjà exécutés. Nécessite RIAD_YASMINE_ID.

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
AUTH_GATEWAY_URL="${AUTH_GATEWAY_URL:-http://localhost:8001}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
PARTNER_URL="${PARTNER_URL:-http://localhost:8005}"
CHANNEL_URL="${CHANNEL_URL:-http://localhost:8006}"
RESERVATION_URL="${RESERVATION_URL:-http://localhost:8007}"
REALM="amh-hospitality"
WEBHOOK_HMAC_SECRET="${WEBHOOK_HMAC_SECRET:-dev-webhook-hmac-secret}"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

winpath() {
  if command -v cygpath > /dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

echo "==> Waiting for /healthz on auth-gateway/reservation/channel-manager"
for url in "$AUTH_GATEWAY_URL" "$RESERVATION_URL" "$CHANNEL_URL"; do
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

echo "==> Logging in as sidi.omar (super-admin, Direct Access Grant)"
TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" -d "client_id=pms-frontend" \
  -d "username=sidi.omar" -d "password=ChangeMe123!" \
  | json_get "data['access_token']")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
  echo "Login failed" >&2
  exit 1
fi

echo "==> 401 checks (no token)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Content-Type: application/json" -d '{}')
if [ "$STATUS" != "401" ]; then
  echo "Expected 401 creating a booking without auth, got $STATUS" >&2
  exit 1
fi
echo "    -> POST /bookings rejects unauthenticated requests"

echo "==> Walk-in booking (Workflow A) — Chambre Standard, 2026-07-10..2026-07-12 (haute saison)"
BOOKING1=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "DIRECT",
    "room_category": "Chambre Standard",
    "check_in_date": "2026-07-10",
    "check_out_date": "2026-07-12",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 2,
    "customer": {"first_name": "Amine", "last_name": "Test"},
    "source": "walk_in"
  }')
BOOKING1_ID=$(echo "$BOOKING1" | json_get "data['id']")
BOOKING1_STATUS=$(echo "$BOOKING1" | json_get "data['status']")
BOOKING1_TOTAL=$(echo "$BOOKING1" | json_get "data['total_amount']")
BOOKING1_ROOM=$(echo "$BOOKING1" | json_get "data['room_id']")
echo "    -> booking=$BOOKING1_ID status=$BOOKING1_STATUS total=$BOOKING1_TOTAL room=$BOOKING1_ROOM"
if [ "$BOOKING1_STATUS" != "status_option" ]; then
  echo "Expected status_option for a walk-in booking without deposit, got $BOOKING1_STATUS" >&2
  exit 1
fi
if [ "$BOOKING1_TOTAL" != "1600.0" ] && [ "$BOOKING1_TOTAL" != "1600.00" ]; then
  echo "Expected total_amount=1600.0 (2 nights x 800.00), got $BOOKING1_TOTAL" >&2
  exit 1
fi

echo "==> Availability check on the now-booked room/dates"
AVAIL=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings/check-availability" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "room_id": "'"$BOOKING1_ROOM"'", "check_in_date": "2026-07-10", "check_out_date": "2026-07-12"}')
AVAILABLE=$(echo "$AVAIL" | json_get "data['available']")
if [ "$AVAILABLE" != "False" ]; then
  echo "Expected the just-booked room/dates to be unavailable, got available=$AVAILABLE" >&2
  exit 1
fi
echo "    -> correctly reported unavailable"

echo "==> Resolving Atlas Voyages partner_id for B2B booking"
PARTNER_ID=$(curl -sf -G "$PARTNER_URL/api/v1/partners/$RIAD_YASMINE_ID" \
  --data-urlencode "type=AGENCE" -H "Authorization: Bearer $TOKEN" | json_get "data[0]['id']")

echo "==> B2B booking (Workflow B) — tarif négocié Atlas Voyages, 2026-07-15..2026-07-16"
BOOKING2=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "PARTENAIRES",
    "partner_id": "'"$PARTNER_ID"'",
    "room_category": "Chambre Standard",
    "check_in_date": "2026-07-15",
    "check_out_date": "2026-07-16",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 2,
    "customer": {"first_name": "Agency", "last_name": "Guest"},
    "source": "b2b_agency"
  }')
BOOKING2_STATUS=$(echo "$BOOKING2" | json_get "data['status']")
BOOKING2_TOTAL=$(echo "$BOOKING2" | json_get "data['total_amount']")
echo "    -> status=$BOOKING2_STATUS total=$BOOKING2_TOTAL"
if [ "$BOOKING2_STATUS" != "status_voucher" ]; then
  echo "Expected status_voucher for a B2B booking, got $BOOKING2_STATUS" >&2
  exit 1
fi
if [ "$BOOKING2_TOTAL" != "700.0" ] && [ "$BOOKING2_TOTAL" != "700.00" ]; then
  echo "Expected total_amount=700.0 (1 night x negotiated rate), got $BOOKING2_TOTAL" >&2
  exit 1
fi

echo "==> Resolving another Chambre Standard room for a same-category shift"
STD_ROOMS=$(curl -sf -G "$ESTABLISHMENT_URL/api/v1/establishments/$RIAD_YASMINE_ID/rooms" \
  --data-urlencode "categorie=Chambre Standard" -H "Authorization: Bearer $TOKEN")
NEW_ROOM_ID=$(echo "$STD_ROOMS" | python -c "
import json, sys
data = json.load(sys.stdin)
current = '$BOOKING1_ROOM'
other = next(r['id'] for r in data if r['id'] != current)
print(other)
")
echo "    -> shifting booking $BOOKING1_ID from $BOOKING1_ROOM to $NEW_ROOM_ID (same category)"

SHIFT1=$(curl -sf -X PATCH "$RESERVATION_URL/api/v1/bookings/$BOOKING1_ID/room" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"new_room_id": "'"$NEW_ROOM_ID"'", "same_category": true, "keep_current_rate": true}')
SHIFT1_NEW_ROOM=$(echo "$SHIFT1" | json_get "data['new_room_id']")
if [ "$SHIFT1_NEW_ROOM" != "$NEW_ROOM_ID" ]; then
  echo "Room shift did not apply — response: $SHIFT1" >&2
  exit 1
fi
echo "    -> same-category shift succeeded, delta=$(echo "$SHIFT1" | json_get "data['delta']")"

echo "==> Resolving a Chambre Deluxe room for an upsell test"
DELUXE_ROOM_ID=$(curl -sf -G "$ESTABLISHMENT_URL/api/v1/establishments/$RIAD_YASMINE_ID/rooms" \
  --data-urlencode "categorie=Chambre Deluxe" -H "Authorization: Bearer $TOKEN" \
  | json_get "data[0]['id']")

echo "==> Upsell shift WITHOUT elevation token — expect 409 UPSELL_REQUIRES_MANAGER"
UPSELL_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$RESERVATION_URL/api/v1/bookings/$BOOKING1_ID/room" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"new_room_id": "'"$DELUXE_ROOM_ID"'", "new_room_category": "Chambre Deluxe", "same_category": false}')
if [ "$UPSELL_STATUS" != "409" ]; then
  echo "Expected 409 for an upsell without elevation, got $UPSELL_STATUS" >&2
  exit 1
fi
echo "    -> correctly rejected"

echo "==> Obtaining an elevation token (manager/admin re-auth scaffold)"
ELEVATE=$(curl -sf -X POST "$AUTH_GATEWAY_URL/api/v1/auth/elevate" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'"}')
ELEVATION_TOKEN=$(echo "$ELEVATE" | json_get "data['token']")

echo "==> Upsell shift WITH elevation token — expect success + rate recalculation"
SHIFT2=$(curl -sf -X PATCH "$RESERVATION_URL/api/v1/bookings/$BOOKING1_ID/room" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"new_room_id": "'"$DELUXE_ROOM_ID"'", "new_room_category": "Chambre Deluxe", "same_category": false, "elevation_token": "'"$ELEVATION_TOKEN"'"}')
SHIFT2_NEW_AMOUNT=$(echo "$SHIFT2" | json_get "data['new_amount']")
echo "    -> upsell succeeded, new_amount=$SHIFT2_NEW_AMOUNT delta=$(echo "$SHIFT2" | json_get "data['delta']")"

echo "==> Re-using the same elevation token — expect 401 (single use)"
REUSE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X PATCH "$RESERVATION_URL/api/v1/bookings/$BOOKING1_ID/room" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"new_room_id": "'"$DELUXE_ROOM_ID"'", "new_room_category": "Chambre Deluxe", "same_category": false, "elevation_token": "'"$ELEVATION_TOKEN"'"}')
if [ "$REUSE_STATUS" != "401" ]; then
  echo "Expected 401 reusing a consumed elevation token, got $REUSE_STATUS" >&2
  exit 1
fi
echo "    -> correctly rejected (token already consumed)"

echo "==> OTA webhook (channel-manager-service, chemin synchrone D6)"
BODY_FILE=$(mktemp)
printf '{"ota_reference":"SPRINT3-SMOKE-001","property_id":"riad-yasmine-12345","room_type_id":"std-room","guest_name":"Jane Doe","guest_email":"jane.doe@example.com","check_in":"2026-08-05","check_out":"2026-08-07","adults":2,"children":0,"total_amount":1600,"currency":"MAD","status":"new"}' > "$BODY_FILE"
SIGNATURE=$(python -c "
import hashlib, hmac, sys
with open(sys.argv[1], 'rb') as f:
    body = f.read()
print(hmac.new(sys.argv[2].encode('utf-8'), body, hashlib.sha256).hexdigest())
" "$(winpath "$BODY_FILE")" "$WEBHOOK_HMAC_SECRET")
WEBHOOK_RESP=$(curl -sf -X POST "$CHANNEL_URL/api/v1/channel/webhook/booking_com?establishment_id=$RIAD_YASMINE_ID" \
  -H "X-OTA-Signature: $SIGNATURE" -H "Content-Type: application/json" --data-binary "@$BODY_FILE")
rm -f "$BODY_FILE"
OTA_BOOKING_ID=$(echo "$WEBHOOK_RESP" | json_get "data['internal_booking_id']")
OTA_BOOKING_STATUS=$(echo "$WEBHOOK_RESP" | json_get "data['status']")
echo "    -> internal_booking_id=$OTA_BOOKING_ID status=$OTA_BOOKING_STATUS"
if [ "$OTA_BOOKING_STATUS" != "status_confirmed" ]; then
  echo "Expected status_confirmed for an OTA booking, got $OTA_BOOKING_STATUS" >&2
  exit 1
fi

echo "==> Verifying the OTA booking is visible on reservation-service"
OTA_BOOKING=$(curl -sf "$RESERVATION_URL/api/v1/bookings/$OTA_BOOKING_ID" -H "Authorization: Bearer $TOKEN")
OTA_SOURCE=$(echo "$OTA_BOOKING" | json_get "data['source']")
if [ "$OTA_SOURCE" != "ota_booking" ]; then
  echo "Expected source=ota_booking, got $OTA_SOURCE" >&2
  exit 1
fi
echo "    -> confirmed: source=$OTA_SOURCE"

echo "==> Manual cancel of the walk-in booking"
CANCEL=$(curl -sf -X PATCH "$RESERVATION_URL/api/v1/bookings/$BOOKING1_ID/status" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"new_status": "status_cancelled", "reason": "Smoke test cleanup"}')
CANCEL_STATUS=$(echo "$CANCEL" | json_get "data['status']")
if [ "$CANCEL_STATUS" != "status_cancelled" ]; then
  echo "Expected status_cancelled, got $CANCEL_STATUS" >&2
  exit 1
fi
echo "    -> booking cancelled"

echo ""
echo "==> Sprint 3 smoke test complete."
