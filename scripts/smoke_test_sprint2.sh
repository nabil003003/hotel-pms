#!/bin/sh
# Smoke test Sprint 2 — vérifie pricing-service, partner-service,
# channel-manager-service (+ l'ajout ota_mappings sur establishment-service)
# de bout en bout : healthz -> calcul de tarif -> tarif négocié partenaire ->
# webhook OTA signé -> consumer RabbitMQ booking.* -> agrégat performance.
#
# Prérequis : `docker compose --profile core up -d` + scripts/seed_sprint1.sh
# + scripts/seed_sprint2.sh déjà exécutés. Nécessite RIAD_YASMINE_ID.

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
PRICING_URL="${PRICING_URL:-http://localhost:8004}"
PARTNER_URL="${PARTNER_URL:-http://localhost:8005}"
CHANNEL_URL="${CHANNEL_URL:-http://localhost:8006}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
RABBITMQ_MGMT_URL="${RABBITMQ_MGMT_URL:-http://localhost:15672}"
REALM="amh-hospitality"
WEBHOOK_HMAC_SECRET="${WEBHOOK_HMAC_SECRET:-dev-webhook-hmac-secret}"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

# `python` ici est l'interpréteur natif Windows — ne comprend pas les
# chemins /c/... produits par `mktemp` sous Git Bash (no-op si cygpath est
# absent, ex CI Linux). Voir seed_sprint1.sh pour le même motif.
winpath() {
  if command -v cygpath > /dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

echo "==> Waiting for /healthz on pricing/partner/channel-manager"
for url in "$PRICING_URL" "$PARTNER_URL" "$CHANNEL_URL"; do
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
  -d "grant_type=password" \
  -d "client_id=pms-frontend" \
  -d "username=sidi.omar" \
  -d "password=ChangeMe123!" \
  | json_get "data['access_token']")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
  echo "Login failed" >&2
  exit 1
fi

echo "==> 401 checks (no token)"
for check in \
  "POST $PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/seasons" \
  "GET $PARTNER_URL/api/v1/partners/$RIAD_YASMINE_ID" \
  "POST $CHANNEL_URL/api/v1/channel/connections/$RIAD_YASMINE_ID"; do
  method=$(echo "$check" | cut -d' ' -f1)
  url=$(echo "$check" | cut -d' ' -f2)
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$url" -H "Content-Type: application/json" -d '{}')
  if [ "$STATUS" != "401" ]; then
    echo "Expected 401 for $method $url, got $STATUS" >&2
    exit 1
  fi
done
echo "    -> all protected endpoints reject unauthenticated requests"

echo "==> GET /api/v1/rates/calculate (Chambre Standard, BB, 2026-07-01..2026-07-03 — haute saison)"
CALC=$(curl -sf -G "$PRICING_URL/api/v1/rates/calculate" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" \
  --data-urlencode "room_category=Chambre Standard" \
  --data-urlencode "regime=BB" \
  --data-urlencode "date_from=2026-07-01" \
  --data-urlencode "date_to=2026-07-03" \
  -H "Authorization: Bearer $TOKEN")
TOTAL=$(echo "$CALC" | json_get "data['total_ttc']")
echo "    -> total_ttc=$TOTAL"
if [ "$TOTAL" != "1600.0" ] && [ "$TOTAL" != "1600.00" ]; then
  echo "Expected total_ttc=1600.0 (2 nights x 800.00), got $TOTAL. Did seed_sprint2.sh run?" >&2
  exit 1
fi

echo "==> Resolving Atlas Voyages partner_id + season_id for negotiated rate check"
PARTNER_ID=$(curl -sf -G "$PARTNER_URL/api/v1/partners/$RIAD_YASMINE_ID" \
  --data-urlencode "type=AGENCE" -H "Authorization: Bearer $TOKEN" | json_get "data[0]['id']")
SEASON_ID=$(curl -sf "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/seasons" -H "Authorization: Bearer $TOKEN" \
  | json_get "next(s['id'] for s in data if s['label'] == 'Haute saison 2026')")

echo "==> GET /api/v1/rates/partner (Atlas Voyages)"
PARTNER_RATE=$(curl -sf -G "$PRICING_URL/api/v1/rates/partner" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" \
  --data-urlencode "partner_id=$PARTNER_ID" \
  --data-urlencode "room_category=Chambre Standard" \
  --data-urlencode "season_id=$SEASON_ID" \
  -H "Authorization: Bearer $TOKEN")
TARIF=$(echo "$PARTNER_RATE" | json_get "data['tarif_negocie']")
echo "    -> tarif_negocie=$TARIF"
if [ "$TARIF" != "700.0" ] && [ "$TARIF" != "700.00" ]; then
  echo "Expected tarif_negocie=700.0, got $TARIF" >&2
  exit 1
fi

echo "==> POST /api/v1/channel/webhook/booking_com (signed)"
BODY_FILE=$(mktemp)
printf '{"ota_reference":"SMOKE-TEST-001","property_id":"riad-yasmine-12345","room_type_id":"std-room","guest_name":"Smoke Test","check_in":"2026-08-01","check_out":"2026-08-03","adults":2,"children":0,"total_amount":1600,"currency":"MAD","status":"new"}' > "$BODY_FILE"
SIGNATURE=$(python -c "
import hashlib, hmac, sys
with open(sys.argv[1], 'rb') as f:
    body = f.read()
print(hmac.new(sys.argv[2].encode('utf-8'), body, hashlib.sha256).hexdigest())
" "$(winpath "$BODY_FILE")" "$WEBHOOK_HMAC_SECRET")
WEBHOOK_RESP=$(curl -s -w "\n%{http_code}" -X POST \
  "$CHANNEL_URL/api/v1/channel/webhook/booking_com?establishment_id=$RIAD_YASMINE_ID" \
  -H "X-OTA-Signature: $SIGNATURE" -H "Content-Type: application/json" --data-binary "@$BODY_FILE")
rm -f "$BODY_FILE"
WEBHOOK_STATUS=$(echo "$WEBHOOK_RESP" | tail -n1)
WEBHOOK_BODY=$(echo "$WEBHOOK_RESP" | sed '$d')
echo "    -> HTTP $WEBHOOK_STATUS: $WEBHOOK_BODY"
# Contrat Sprint 2 d'origine (202 buffered, sans reservation-service) résolu
# en Sprint 3 (voir docs/decisions/D6-*) : le webhook appelle désormais
# reservation-service en synchrone et répond 200 avec un vrai
# internal_booking_id, comme vérifié par scripts/smoke_test_sprint3.sh.
if [ "$WEBHOOK_STATUS" != "200" ]; then
  echo "Expected 200 (synchronous booking creation, D6) from webhook, got $WEBHOOK_STATUS" >&2
  exit 1
fi
INTERNAL_BOOKING_ID=$(echo "$WEBHOOK_BODY" | json_get "data['internal_booking_id']")
if [ -z "$INTERNAL_BOOKING_ID" ] || [ "$INTERNAL_BOOKING_ID" = "None" ]; then
  echo "Expected internal_booking_id in webhook response, got: $WEBHOOK_BODY" >&2
  exit 1
fi
echo "    -> booking created synchronously: $INTERNAL_BOOKING_ID"

echo "==> Publishing synthetic booking.created event (RabbitMQ management API — proves consumer wiring)"
CORRELATION_ID="smoke-$(date +%s)"
PUBLISH_BODY_FILE=$(mktemp)
python -c "
import json
payload = json.dumps({'establishment_id': '$RIAD_YASMINE_ID', 'booking_id': 'smoke-booking-1', 'correlation_id': '$CORRELATION_ID'})
print(json.dumps({'properties': {}, 'routing_key': 'booking.created', 'payload': payload, 'payload_encoding': 'string'}))
" > "$PUBLISH_BODY_FILE"
curl -sf -u amh:amh_dev_password -X POST \
  "$RABBITMQ_MGMT_URL/api/exchanges/%2f/amh.booking/publish" \
  -H "Content-Type: application/json" --data-binary "@$PUBLISH_BODY_FILE" > /dev/null
rm -f "$PUBLISH_BODY_FILE"

echo "==> Polling GET /api/v1/channel/performance for the inventory_update_pending log (up to 20s)"
CURRENT_PERIOD=$(date +%Y-%m)
n=0
FOUND=""
while [ "$n" -lt 10 ]; do
  PERF=$(curl -sf -G "$CHANNEL_URL/api/v1/channel/performance" \
    --data-urlencode "establishment_id=$RIAD_YASMINE_ID" \
    --data-urlencode "period=$CURRENT_PERIOD" \
    -H "Authorization: Bearer $TOKEN")
  COUNT=$(echo "$PERF" | json_get "data.get('by_ota', {}).get('booking_com', {}).get('buffered', 0)")
  if [ "$COUNT" -ge 1 ]; then
    # Depuis Sprint 3 (D6), le webhook direct crée un sync_log status=ok
    # (booking synchrone), pas buffered — seul le consumer booking.created
    # (inventory_update_pending) alimente ce compteur désormais.
    FOUND="yes"
    break
  fi
  n=$((n + 1))
  sleep 2
done

if [ -z "$FOUND" ]; then
  echo "Did not observe the expected sync_logs rows within 20s — RabbitMQ consumer may not have processed the message." >&2
  echo "    Last performance response: $PERF" >&2
  exit 1
fi
echo "    -> performance shows $COUNT buffered booking_com entries this month"

echo ""
echo "==> Sprint 2 smoke test complete."
