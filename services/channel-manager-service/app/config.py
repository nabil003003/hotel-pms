from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "channel-manager-service"
    database_url: str = "postgresql+asyncpg://amh:amh_dev_password@localhost:5432/channel_db"
    rabbitmq_url: str = "amqp://amh:amh_dev_password@localhost:5672/"

    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer_url: str = "http://localhost:8080"
    keycloak_realm: str = "amh-hospitality"
    keycloak_client_id: str = "svc-channel-manager"
    keycloak_client_secret: str = "dev-secret-channel-manager"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Clé Fernet dev — dupliquée depuis partner-service (D2, pas de lib
    # partagée). Chiffre ChannelConnection.credentials_encrypted.
    encryption_key: str = "7IpIh0To2OH4J_p692DHNPLM4p7QHDh2SU8TGqd0riM="

    establishment_service_url: str = "http://localhost:8002"
    # Sprint 3 (D6) : le webhook appelle reservation-service en synchrone
    # pour créer la réservation, au lieu de simplement journaliser+bufferiser.
    reservation_service_url: str = "http://localhost:8007"

    # Secret HMAC dev partagé pour la vérification de signature webhook OTA
    # (X-OTA-Signature). En prod, un secret par connexion OTA serait attendu ;
    # simplifié en Sprint 2 car aucune vraie intégration OTA n'existe encore
    # (voir décision D6).
    webhook_hmac_secret: str = "dev-webhook-hmac-secret"


@lru_cache
def get_settings() -> Settings:
    return Settings()
