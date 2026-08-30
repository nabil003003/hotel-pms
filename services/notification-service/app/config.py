from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "notification-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/notif_db"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-notification"
    keycloak_client_secret: str = "dev-secret-notification"

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
