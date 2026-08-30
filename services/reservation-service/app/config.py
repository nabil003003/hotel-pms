from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "reservation-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/reserv_db"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"
    redis_url: str = "redis://localhost:6379/2"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-reservation"
    keycloak_client_secret: str = "dev-secret-reservation"

    cors_origins: list[str] = ["http://localhost:3000"]

    pricing_service_url: str = "http://localhost:8004"
    establishment_service_url: str = "http://localhost:8002"
    auth_gateway_service_url: str = "http://localhost:8001"

    option_expiry_hours: int = 48
    option_expiry_poll_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
