#!/bin/sh
# Démarre toute la stack PMS AMH Hospitality en une seule commande :
# infra Docker (profil core) -> provisioning Keycloak -> migrations Alembic
# (11 services) -> frontend Next.js. Idempotent — sans danger de relancer
# sur une stack déjà up (Keycloak/migrations font un no-op si déjà à jour).
#
# Usage: ./scripts/start_all.sh [--build] [--no-frontend]
#   --build         reconstruit les images avant de démarrer (code backend modifié)
#   --no-frontend   n'installe/ne lance pas le frontend (infra + migrations seulement)

set -e

cd "$(dirname "$0")/.."

BUILD_FLAG=""
START_FRONTEND=1
for arg in "$@"; do
  case "$arg" in
    --build) BUILD_FLAG="--build" ;;
    --no-frontend) START_FRONTEND=0 ;;
  esac
done

SERVICES="auth-gateway-service establishment-service housekeeping-service pricing-service partner-service channel-manager-service reservation-service front-office-service analytics-service night-audit-service notification-service"

echo "==> 1/4 Infra + microservices (docker compose --profile core up -d $BUILD_FLAG)"
if [ -n "$BUILD_FLAG" ]; then
  (cd infra && docker compose -f docker-compose.yml --profile core up -d --build)
else
  (cd infra && docker compose -f docker-compose.yml --profile core up -d)
fi

echo "==> Attente des services healthy (timeout 120s)..."
PATTERN=$(echo "$SERVICES" | tr ' ' '|')
UNHEALTHY=""
i=0
while [ "$i" -lt 60 ]; do
  UNHEALTHY=$(docker ps --format '{{.Names}}\t{{.Status}}' | grep -E "^infra-(${PATTERN})-1" | grep -v "healthy" || true)
  if [ -z "$UNHEALTHY" ]; then
    break
  fi
  i=$((i + 1))
  sleep 2
done
if [ -n "$UNHEALTHY" ]; then
  echo "ATTENTION: certains services ne sont pas healthy après 120s:" >&2
  echo "$UNHEALTHY" >&2
fi

echo "==> 2/4 Provisioning Keycloak (idempotent)"
python scripts/keycloak_setup.py

echo "==> 3/4 Migrations Alembic (idempotent, 11 services)"
for svc in $SERVICES; do
  echo "  -- $svc"
  (cd infra && docker compose -f docker-compose.yml exec "$svc" alembic upgrade head)
done

if [ "$START_FRONTEND" -eq 1 ]; then
  echo "==> 4/4 Frontend (npm install + npm run dev, port 3000)"
  cd frontend
  npm install --no-audit --no-fund
  exec npm run dev
else
  echo "==> 4/4 Frontend ignoré (--no-frontend). Pour le lancer : cd frontend && npm run dev"
fi
