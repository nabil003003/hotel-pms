#!/bin/sh
set -e

# Crée les 12 bases logiques (11 microservices + keycloak) sur l'unique instance
# PostgreSQL du profil `core`. Idempotent : ne recrée pas une base existante.
# Monté dans /docker-entrypoint-initdb.d/ — exécuté une seule fois, au premier
# démarrage du volume de données Postgres.

DATABASES="auth_db establishment_db hk_db pricing_db partner_db channel_db reserv_db fo_db audit_db analytics_db notif_db keycloak"

for db in $DATABASES; do
  exists=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_database WHERE datname = '$db'")
  if [ "$exists" != "1" ]; then
    echo "Creating database: $db"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE \"$db\";"
  else
    echo "Database already exists, skipping: $db"
  fi
done
