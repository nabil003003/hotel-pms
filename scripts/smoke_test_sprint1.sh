#!/bin/sh
# Smoke test Sprint 1 — vérifie la stack `core` de bout en bout :
# healthz -> login réceptionniste -> lecture chambres -> transition de statut
# -> historique -> (best-effort) WebSocket temps réel.
#
# Prérequis : `docker compose --profile core up -d` + `scripts/seed_sprint1.sh`
# déjà exécutés. Nécessite RIAD_YASMINE_ID (affiché par seed_sprint1.sh).

set -e

# Force python (interpréteur natif Windows) à lire/écrire stdin/stdout en
# UTF-8 — sans ça, `curl ... | python -m json.tool` mésinterprète les octets
# UTF-8 des statuts accentués (Contrôlée) en les décodant avec le codepage
# ANSI par défaut de la console, produisant un affichage doublement échappé
# (ex: Ã´ au lieu de ô). Les données stockées restent
# correctes dans tous les cas — ceci ne corrige qu'un artefact d'affichage,
# constaté en vérification Sprint 1.
export PYTHONIOENCODING=utf-8

KEYCLOAK_URL="${KEYCLOAK_URL:-http://localhost:8080}"
AUTH_GATEWAY_URL="${AUTH_GATEWAY_URL:-http://localhost:8001}"
ESTABLISHMENT_URL="${ESTABLISHMENT_URL:-http://localhost:8002}"
HOUSEKEEPING_URL="${HOUSEKEEPING_URL:-http://localhost:8003}"
REALM="amh-hospitality"

if [ -z "$RIAD_YASMINE_ID" ]; then
  echo "RIAD_YASMINE_ID is not set — run scripts/seed_sprint1.sh first and export the printed ID." >&2
  exit 1
fi

json_get() {
  python -c "import json,sys; data=json.load(sys.stdin); print($1)"
}

# `python` ici est l'interpréteur natif Windows — ne comprend pas les
# chemins /c/... (no-op si cygpath est absent, ex CI Linux).
winpath() {
  if command -v cygpath > /dev/null 2>&1; then
    cygpath -w "$1"
  else
    printf '%s' "$1"
  fi
}

echo "==> Waiting for /healthz on all 3 Sprint 1 services"
for url in "$AUTH_GATEWAY_URL" "$ESTABLISHMENT_URL" "$HOUSEKEEPING_URL"; do
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

echo "==> Logging in as test.gouvernante (Direct Access Grant)"
TOKEN=$(curl -s -X POST \
  "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=pms-frontend" \
  -d "username=test.gouvernante" \
  -d "password=ChangeMe123!" \
  | json_get "data['access_token']")

if [ -z "$TOKEN" ] || [ "$TOKEN" = "None" ]; then
  echo "Login failed — did scripts/seed_sprint1.sh update establishment_ids for test.gouvernante?" >&2
  exit 1
fi

echo "==> GET /auth/me"
curl -sf "$AUTH_GATEWAY_URL/api/v1/auth/me" -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo "==> GET /rooms (establishment=$RIAD_YASMINE_ID)"
ROOMS=$(curl -sf -G "$HOUSEKEEPING_URL/api/v1/rooms" \
  --data-urlencode "establishment_id=$RIAD_YASMINE_ID" \
  -H "Authorization: Bearer $TOKEN")

ROOM_COUNT=$(echo "$ROOMS" | json_get "len(data)")
echo "    -> $ROOM_COUNT rooms visible"
if [ "$ROOM_COUNT" -lt 1 ]; then
  echo "No rooms found — did the establishment.rooms_imported event reach housekeeping-service?" >&2
  echo "    Fallback: POST $HOUSEKEEPING_URL/api/v1/internal/resync/$RIAD_YASMINE_ID (super-admin token)" >&2
  exit 1
fi

ROOM_ID=$(echo "$ROOMS" | json_get "data[0]['id']")
OLD_STATUS=$(echo "$ROOMS" | json_get "data[0]['statut']")
echo "==> Using room $ROOM_ID (current status: $OLD_STATUS)"

if [ "$OLD_STATUS" = "Propre" ]; then
  NEW_STATUS="Contrôlée"
elif [ "$OLD_STATUS" = "Sale" ]; then
  NEW_STATUS="Nettoyage"
else
  echo "Room in unexpected seed status ($OLD_STATUS) for this smoke test — skipping status change." >&2
  NEW_STATUS=""
fi

if [ -n "$NEW_STATUS" ]; then
  echo "==> PATCH /rooms/$ROOM_ID/status -> $NEW_STATUS"
  # Le corps JSON est écrit dans un fichier temporaire puis envoyé via
  # `--data-binary @file` plutôt que `-d "..."` : les statuts accentués
  # (Contrôlée) passés en argument de ligne de commande à curl.exe OU en
  # variable d'env à python.exe sur ce Git Bash/Windows finissent tous les
  # deux mal réencodés (mismatch UTF-8 au passage argv/env vers un exe natif
  # Win32) — constaté en vérification Sprint 1. `printf` est un builtin bash
  # (pas d'exec() vers un .exe externe) : écrire directement via printf
  # préserve les octets UTF-8 tels quels dans le fichier.
  BODY_FILE=$(mktemp)
  printf '{"new_status": "%s"}' "$NEW_STATUS" > "$BODY_FILE"

  curl -sf -X PATCH "$HOUSEKEEPING_URL/api/v1/rooms/$ROOM_ID/status" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json; charset=utf-8" \
    --data-binary "@$BODY_FILE" | python -m json.tool
  rm -f "$BODY_FILE"

  echo "==> GET /rooms/$ROOM_ID/history"
  curl -sf "$HOUSEKEEPING_URL/api/v1/rooms/$ROOM_ID/history" -H "Authorization: Bearer $TOKEN" | python -m json.tool
fi

echo "==> (best-effort) WebSocket check on /ws/rooms"
python - "$HOUSEKEEPING_URL" "$RIAD_YASMINE_ID" "$TOKEN" <<'PYEOF'
import asyncio
import sys

base_url, establishment_id, token = sys.argv[1], sys.argv[2], sys.argv[3]
ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
ws_url = f"{ws_url}/api/v1/ws/rooms?establishment_id={establishment_id}&token={token}"

try:
    import websockets
except ImportError:
    print("    -> 'websockets' package not installed locally, skipping (not a hard failure)")
    sys.exit(0)


async def main():
    try:
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            print("    -> WebSocket connected, waiting up to 5s for a message...")
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"    -> received: {message}")
            except asyncio.TimeoutError:
                print("    -> connected but no message received within 5s (ok if no status change happened concurrently)")
    except Exception as exc:  # noqa: BLE001
        print(f"    -> WebSocket check failed (non-fatal for this smoke test): {exc}")


asyncio.run(main())
PYEOF

echo ""
echo "==> Sprint 1 smoke test complete."
