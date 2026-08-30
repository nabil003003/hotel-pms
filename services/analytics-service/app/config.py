from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "analytics-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/analytics_db"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"
    redis_url: str = "redis://localhost:6379/4"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-analytics"
    keycloak_client_secret: str = "dev-secret-analytics"

    cors_origins: list[str] = ["http://localhost:3000"]

    reservation_service_url: str = "http://localhost:8007"
    establishment_service_url: str = "http://localhost:8002"
    night_audit_service_url: str = "http://localhost:8010"

    kpi_today_cache_seconds: int = 300
    kpi_monthly_cache_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
