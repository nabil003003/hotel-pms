from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "partner-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/partner_db"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-partner"
    keycloak_client_secret: str = "dev-secret-partner"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Clé Fernet dev (32 bytes urlsafe-base64) pour ota_credentials_encrypted.
    # Ne PAS réutiliser en prod — voir infra/docker-compose.yml.
    encryption_key: str = "7IpIh0To2OH4J_p692DHNPLM4p7QHDh2SU8TGqd0riM="


@lru_cache
def get_settings() -> Settings:
    return Settings()
