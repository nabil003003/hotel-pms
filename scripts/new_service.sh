#!/bin/sh
# Génère le squelette standard d'un microservice (spec §8.2) sous services/<name>.
# Usage: ./scripts/new_service.sh <service-name> <db_env_var_name>
# Exemple: ./scripts/new_service.sh pricing-service pricing_db
#
# Ne génère QUE la structure/stub (main.py = /healthz uniquement) — la
# logique métier (domain/models.py, endpoints réels) est ajoutée service par
# service au moment de son sprint. C'est ce script qui garantit que les 8
# services non prioritaires du Sprint 1 partagent une structure identique,
# plutôt que d'être copiés-collés à la main.

set -e

SERVICE_NAME="$1"
DB_NAME="$2"

if [ -z "$SERVICE_NAME" ] || [ -z "$DB_NAME" ]; then
  echo "Usage: $0 <service-name> <db_name>" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVC_DIR="$ROOT/services/$SERVICE_NAME"

mkdir -p "$SVC_DIR/app/api/v1" "$SVC_DIR/app/domain" "$SVC_DIR/app/infrastructure" \
         "$SVC_DIR/app/events" "$SVC_DIR/app/tests" "$SVC_DIR/alembic/versions"

touch "$SVC_DIR/app/__init__.py" "$SVC_DIR/app/api/__init__.py" "$SVC_DIR/app/api/v1/__init__.py" \
      "$SVC_DIR/app/domain/__init__.py" "$SVC_DIR/app/infrastructure/__init__.py" \
      "$SVC_DIR/app/events/__init__.py" "$SVC_DIR/app/tests/__init__.py"

cat > "$SVC_DIR/requirements.txt" <<'EOF'
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.7.1
pydantic-settings==2.2.1
pytest==8.2.0
pytest-asyncio==0.23.6
EOF

cat > "$SVC_DIR/Dockerfile" <<'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > "$SVC_DIR/pytest.ini" <<'EOF'
[pytest]
asyncio_mode = auto
testpaths = app/tests
EOF

cat > "$SVC_DIR/app/config.py" <<EOF
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "$SERVICE_NAME"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/$DB_NAME"


@lru_cache
def get_settings() -> Settings:
    return Settings()
EOF

cat > "$SVC_DIR/app/infrastructure/database.py" <<'EOF'
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
EOF

cat > "$SVC_DIR/app/infrastructure/redis_client.py" <<EOF
# $SERVICE_NAME — pas de dépendance Redis tant que ce service n'est pas
# implémenté (voir docs pour le sprint prévu). Fichier conservé pour
# respecter l'arborescence standard (spec §8.2).
EOF

cat > "$SVC_DIR/app/infrastructure/rabbitmq.py" <<EOF
# $SERVICE_NAME — publisher/consumer RabbitMQ à implémenter avec la logique
# métier du service (voir Appendix C du spec pour les événements attendus).
EOF

cat > "$SVC_DIR/app/infrastructure/keycloak.py" <<EOF
# $SERVICE_NAME — vérification JWT à implémenter sur le même modèle que
# establishment-service/app/infrastructure/keycloak.py au moment où ce
# service expose ses premiers endpoints.
EOF

cat > "$SVC_DIR/app/domain/models.py" <<EOF
# $SERVICE_NAME — schéma non encore implémenté.
# TODO: transcrire le schéma depuis PMS_PROMPT_TECHNIQUE_V3_ENHANCED.md
# quand ce service est planifié (voir README.md de ce service).
EOF

cat > "$SVC_DIR/app/domain/services.py" <<EOF
# $SERVICE_NAME — logique métier à implémenter avec les endpoints réels.
EOF

cat > "$SVC_DIR/app/domain/exceptions.py" <<EOF
# $SERVICE_NAME — exceptions métier à définir avec la logique du service.
EOF

cat > "$SVC_DIR/app/api/v1/schemas.py" <<EOF
# $SERVICE_NAME — schémas Pydantic à définir avec les premiers endpoints.
EOF

cat > "$SVC_DIR/app/api/v1/endpoints.py" <<EOF
# $SERVICE_NAME — aucun endpoint métier tant que ce service n'est pas planifié.
EOF

cat > "$SVC_DIR/app/events/publisher.py" <<EOF
# $SERVICE_NAME — voir Appendix C du spec pour les événements à publier.
EOF

cat > "$SVC_DIR/app/events/consumer.py" <<EOF
# $SERVICE_NAME — voir Appendix C du spec pour les événements à consommer.
EOF

cat > "$SVC_DIR/app/events/handlers.py" <<EOF
# $SERVICE_NAME — handlers à implémenter avec events/consumer.py.
EOF

cat > "$SVC_DIR/app/main.py" <<'EOF'
from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.service_name, version="0.1.0")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}
EOF

cat > "$SVC_DIR/app/tests/test_unit.py" <<EOF
# $SERVICE_NAME — tests unitaires à écrire avec la logique métier
# (cible >=80% sur app/domain/, spec §7.1).
EOF

cp "$ROOT/services/establishment-service/alembic.ini" "$SVC_DIR/alembic.ini"
cp "$ROOT/services/establishment-service/alembic/script.py.mako" "$SVC_DIR/alembic/script.py.mako"
sed "s/from app.domain import models  # noqa: F401.*/from app.domain import models  # noqa: F401/" \
  "$ROOT/services/establishment-service/alembic/env.py" > "$SVC_DIR/alembic/env.py"

cat > "$SVC_DIR/README.md" <<EOF
# $SERVICE_NAME

Squelette généré par \`scripts/new_service.sh\` (structure standard, spec
§8.2). Pas encore implémenté — voir la feuille de route des sprints dans
le plan (\`docs/decisions/\`) pour la date prévue.

\`main.py\` n'expose que \`/healthz\` pour l'instant : le conteneur build et
démarre, prouvant que le squelette n'est pas un artefact mort, mais aucune
route métier n'existe encore.
EOF

echo "Scaffolded $SERVICE_NAME -> $SVC_DIR"
