from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "night-audit-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/audit_db"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"
    redis_url: str = "redis://localhost:6379/5"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-nightaudit"
    keycloak_client_secret: str = "dev-secret-nightaudit"

    cors_origins: list[str] = ["http://localhost:3000"]

    front_office_service_url: str = "http://localhost:8008"
    reservation_service_url: str = "http://localhost:8007"
    analytics_service_url: str = "http://localhost:8009"
    notification_service_url: str = "http://localhost:8011"

    minio_endpoint_url: str = "http://localhost:9000"
    minio_access_key: str = "amh"
    minio_secret_key: str = "amh_dev_password"
    minio_bucket: str = "audit-reports"

    audit_token_ttl_seconds: int = 1800
    business_date_cache_seconds: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
