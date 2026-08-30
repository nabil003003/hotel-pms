#!/bin/sh
# Smoke test Sprint 4 — vérifie front-office-service et analytics-service de
# bout en bout : check-in (précondition chambre, Folio A + charges HEB/TS/TPT
# auto) -> charge manuelle vérifiée contre le catalogue pricing-service ->
# paiement -> check-out (solde exact) -> reopen refusé -> KPI analytics
# alimentés par les événements -> verrou business_date (audit.closed
# synthétique) bloquant un nouveau check-in.
#
# Prérequis : `docker compose --profile core up -d` + seed_sprint1/2/3/4.sh
# déjà exécutés. Nécessite RIAD_YASMINE_ID.

set -e

export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
HOUSEKEEPING_URL="${HOUSEKEEPING_URL:-http://localhost:8003}"
PRICING_URL="${PRICING_URL:-http://localhost:8004}"
RESERVATION_URL="${RESERVATION_URL:-http://localhost:8007}"
FRONT_OFFICE_URL="${FRONT_OFFICE_URL:-http://localhost:8008}"
ANALYTICS_URL="${ANALYTICS_URL:-http://localhost:8009}"
RABBITMQ_MGMT_URL="${RABBITMQ_MGMT_URL:-http://localhost:15672}"
REALM="amh-hospitality"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

echo "==> Waiting for /healthz on front-office/analytics"
for url in "$FRONT_OFFICE_URL" "$ANALYTICS_URL"; do
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

echo "==> 401 checks (no token)"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-in" \
  -H "Content-Type: application/json" -d '{}')
if [ "$STATUS" != "401" ]; then
  echo "Expected 401 for check-in without auth, got $STATUS" >&2
  exit 1
fi
echo "    -> POST /folios/check-in rejects unauthenticated requests"

# Dates aléatoires dans "Basse saison 2026" (2026-01-01..2026-06-01, cf.
# fixtures/seed_riad_yasmine.json) — un vrai rate_grid s'applique (nécessaire
# pour tester la charge HEB automatique) et chaque exécution utilise une
# fenêtre différente pour rester rejouable (4 chambres "Chambre Standard"
# seulement — des dates fixes épuiseraient le pool au bout de 4 runs).
CHECK_IN_DATE=$(python -c "
import datetime, random
random.seed()
base = datetime.date(2026, 2, 1) + datetime.timedelta(days=random.randint(0, 80))
print(base.isoformat())
")
CHECK_OUT_DATE=$(python -c "
import datetime
d = datetime.date.fromisoformat('$CHECK_IN_DATE') + datetime.timedelta(days=2)
print(d.isoformat())
")

echo "==> Creating a walk-in booking with deposit_paid=true (-> status_confirmed, required for check-in)"
echo "    dates: $CHECK_IN_DATE .. $CHECK_OUT_DATE"
BOOKING=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "DIRECT",
    "room_category": "Chambre Standard",
    "check_in_date": "'"$CHECK_IN_DATE"'",
    "check_out_date": "'"$CHECK_OUT_DATE"'",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 2,
    "customer": {"first_name": "Sprint4", "last_name": "SmokeTest"},
    "source": "walk_in",
    "deposit_paid": true
  }')
BOOKING_ID=$(echo "$BOOKING" | json_get "data['id']")
BOOKING_STATUS=$(echo "$BOOKING" | json_get "data['status']")
BOOKING_ROOM=$(echo "$BOOKING" | json_get "data['room_id']")
echo "    -> booking=$BOOKING_ID status=$BOOKING_STATUS room=$BOOKING_ROOM"
if [ "$BOOKING_STATUS" != "status_confirmed" ]; then
  echo "Expected status_confirmed, got $BOOKING_STATUS" >&2
  exit 1
fi

echo "==> Ensuring room is check-in ready (Propre/Contrôlée)"
ROOM_STATUS=$(curl -sf "$HOUSEKEEPING_URL/api/v1/rooms/$BOOKING_ROOM/status" -H "Authorization: Bearer $TOKEN" | json_get "data['statut']")
if [ "$ROOM_STATUS" != "Propre" ] && [ "$ROOM_STATUS" != "Contrôlée" ]; then
  echo "    -> room status is $ROOM_STATUS, resetting to Propre for the test"
  BODY_FILE=$(mktemp)
  printf '{"new_status": "Propre"}' > "$BODY_FILE"
  curl -sf -X PATCH "$HOUSEKEEPING_URL/api/v1/rooms/$BOOKING_ROOM/status" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "@$BODY_FILE" > /dev/null
  rm -f "$BODY_FILE"
fi

echo "==> Check-in (Workflow D)"
CHECKIN=$(curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-in" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "booking_id": "'"$BOOKING_ID"'"}')
FOLIO_ID=$(echo "$CHECKIN" | json_get "data['folio_ids'][0]")
echo "    -> folio_id=$FOLIO_ID"

FOLIO=$(curl -sf "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO_ID" -H "Authorization: Bearer $TOKEN")
CHARGES_AFTER_CHECKIN=$(echo "$FOLIO" | json_get "data['total_charges']")
echo "    -> total_charges after check-in (HEB + TS/TPT auto-charges) = $CHARGES_AFTER_CHECKIN"
if python -c "import sys; sys.exit(0 if float('$CHARGES_AFTER_CHECKIN') > 0 else 1)"; then
  :
else
  echo "Expected non-zero total_charges after check-in (HEB auto-charge missing?)" >&2
  exit 1
fi

echo "==> Resolving a SPA catalog item for a manual charge (Workflow E)"
CATALOG_ITEM=$(curl -sf "$PRICING_URL/api/v1/pricing/$RIAD_YASMINE_ID/extras" -H "Authorization: Bearer $TOKEN" \
  | python -c "import json,sys; data=json.load(sys.stdin); item=next(i for i in data if i['categorie']=='SPA'); print(json.dumps(item))")
CATALOG_ITEM_ID=$(echo "$CATALOG_ITEM" | json_get "data['id']")
CATALOG_PRICE_HT=$(echo "$CATALOG_ITEM" | json_get "data['prix_ht']")

CHARGE=$(curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO_ID/charges" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"poste_comptable": "SPA", "libelle": "Massage", "quantity": 1, "catalog_item_id": "'"$CATALOG_ITEM_ID"'"}')
CHARGE_UNIT_PRICE=$(echo "$CHARGE" | json_get "data['unit_price_ht']")
echo "    -> charge created, unit_price_ht=$CHARGE_UNIT_PRICE (catalogue: $CATALOG_PRICE_HT)"
if [ "$CHARGE_UNIT_PRICE" != "$CATALOG_PRICE_HT" ]; then
  echo "Expected charge unit_price_ht to match pricing-service catalog price" >&2
  exit 1
fi

echo "==> Settling the folio balance exactly (required for check-out)"
FOLIO=$(curl -sf "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO_ID" -H "Authorization: Bearer $TOKEN")
BALANCE=$(echo "$FOLIO" | json_get "data['balance']")
echo "    -> current balance=$BALANCE"
curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO_ID/payments" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"mode": "CB", "montant": '"$BALANCE"'}' > /dev/null

FOLIO=$(curl -sf "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO_ID" -H "Authorization: Bearer $TOKEN")
BALANCE_AFTER=$(echo "$FOLIO" | json_get "data['balance']")
if [ "$BALANCE_AFTER" != "0.0" ] && [ "$BALANCE_AFTER" != "0.00" ] && [ "$BALANCE_AFTER" != "0" ]; then
  echo "Expected balance=0 after settlement, got $BALANCE_AFTER" >&2
  exit 1
fi
echo "    -> balance settled to 0"

echo "==> Check-out (Workflow G)"
curl -sf -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-out" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "booking_id": "'"$BOOKING_ID"'"}' > /dev/null
echo "    -> checked out"

echo "==> Reopen must always be forbidden"
REOPEN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$FRONT_OFFICE_URL/api/v1/folios/$FOLIO_ID/reopen" \
  -H "Authorization: Bearer $TOKEN")
if [ "$REOPEN_STATUS" != "403" ]; then
  echo "Expected 403 on reopen, got $REOPEN_STATUS" >&2
  exit 1
fi
echo "    -> correctly rejected"

echo "==> Polling analytics-service GET /kpi/today for non-zero CA (up to 20s)"
n=0
CA_TOTAL=0
while [ "$n" -lt 10 ]; do
  KPI=$(curl -sf -G "$ANALYTICS_URL/api/v1/kpi/today" \
    --data-urlencode "establishment_id=$RIAD_YASMINE_ID" -H "Authorization: Bearer $TOKEN")
  CA_TOTAL=$(echo "$KPI" | json_get "data['ca_total']")
  if python -c "import sys; sys.exit(0 if float('$CA_TOTAL') > 0 else 1)"; then
    break
  fi
  n=$((n + 1))
  sleep 2
done
echo "    -> ca_total=$CA_TOTAL"
if python -c "import sys; sys.exit(0 if float('$CA_TOTAL') > 0 else 1)"; then
  :
else
  echo "Expected non-zero ca_total on analytics-service — RabbitMQ consumer may not have processed folio.charge_added." >&2
  exit 1
fi

echo "==> Publishing a synthetic audit.closed event (proves fo.audit_events wiring + business_date lock)"
TODAY=$(python -c "import datetime; print(datetime.date.today().isoformat())")
PUBLISH_BODY_FILE=$(mktemp)
python -c "
import json
payload = json.dumps({'establishment_id': '$RIAD_YASMINE_ID', 'business_date': '$TODAY', 'report_hash': 'smoke-test'})
print(json.dumps({'properties': {}, 'routing_key': 'audit.closed', 'payload': payload, 'payload_encoding': 'string'}))
" > "$PUBLISH_BODY_FILE"
curl -sf -u amh:amh_dev_password -X POST \
  "$RABBITMQ_MGMT_URL/api/exchanges/%2f/amh.audit/publish" \
  -H "Content-Type: application/json" --data-binary "@$PUBLISH_BODY_FILE" > /dev/null
rm -f "$PUBLISH_BODY_FILE"

CHECK_IN_DATE2=$(python -c "
import datetime, random
random.seed()
base = datetime.date(2026, 2, 1) + datetime.timedelta(days=random.randint(0, 80))
print(base.isoformat())
")
CHECK_OUT_DATE2=$(python -c "
import datetime
d = datetime.date.fromisoformat('$CHECK_IN_DATE2') + datetime.timedelta(days=1)
print(d.isoformat())
")

echo "==> Creating a second booking to verify the business_date lock blocks a new check-in (up to 20s)"
BOOKING2=$(curl -sf -X POST "$RESERVATION_URL/api/v1/bookings" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "establishment_id": "'"$RIAD_YASMINE_ID"'",
    "market_segment_category": "DIRECT",
    "room_category": "Chambre Standard",
    "check_in_date": "'"$CHECK_IN_DATE2"'",
    "check_out_date": "'"$CHECK_OUT_DATE2"'",
    "regime": "BB",
    "taxes_payment_mode": "on_site",
    "adults": 1,
    "customer": {"first_name": "Sprint4b", "last_name": "SmokeTest"},
    "source": "walk_in",
    "deposit_paid": true
  }')
BOOKING2_ID=$(echo "$BOOKING2" | json_get "data['id']")

n=0
LOCKED=""
while [ "$n" -lt 10 ]; do
  CHECKIN2_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$FRONT_OFFICE_URL/api/v1/folios/check-in" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d '{"establishment_id": "'"$RIAD_YASMINE_ID"'", "booking_id": "'"$BOOKING2_ID"'"}')
  if [ "$CHECKIN2_STATUS" = "423" ]; then
    LOCKED="yes"
    break
  fi
  n=$((n + 1))
  sleep 2
done
if [ -z "$LOCKED" ]; then
  echo "Expected 423 LOCKED on check-in after business_date lock, got $CHECKIN2_STATUS — audit.closed consumer may not have processed the message." >&2
  exit 1
fi
echo "    -> business_date lock correctly blocked the check-in (423)"

echo ""
echo "==> Sprint 4 smoke test complete."
