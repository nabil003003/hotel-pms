"""Chiffrement symétrique (Fernet) de `partners.ota_credentials_encrypted`.
Dupliqué à l'identique dans channel-manager-service (cf. D2 — pas de lib
partagée entre microservices)."""

from __future__ import annotations

from cryptography.fernet import Fernet

from app.config import get_settings

settings = get_settings()
_fernet = Fernet(settings.encryption_key.encode("utf-8"))


def encrypt(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
