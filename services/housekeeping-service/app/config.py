from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "housekeeping-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/hk_db"
    redis_url: str = "redis://localhost:6379/1"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"  # iss attendu dans le JWT (KC_HOSTNAME fixe), voir infra/docker-compose.yml
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-housekeeping"
    keycloak_client_secret: str = "dev-secret-housekeeping"

    establishment_service_url: str = "http://localhost:8002"
    reservation_service_url: str = "http://localhost:8007"

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
