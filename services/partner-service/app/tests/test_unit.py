import uuid

import pytest
from cryptography.fernet import InvalidToken
from fastapi import HTTPException

from app.dependencies import assert_path_establishment_access
from app.infrastructure.crypto import decrypt, encrypt


def test_crypto_roundtrip():
    plaintext = "user:secret_api_key_12345"
    ciphertext = encrypt(plaintext)
    assert ciphertext != plaintext
    assert decrypt(ciphertext) == plaintext


def test_crypto_ciphertext_not_plaintext_substring():
    plaintext = "booking_com_credentials"
    ciphertext = encrypt(plaintext)
    assert plaintext not in ciphertext


def test_crypto_nondeterministic_ciphertext():
    # Fernet inclut un IV aléatoire — deux chiffrements du même texte en
    # clair ne doivent jamais produire le même ciphertext (sécurité §7.5).
    plaintext = "same_secret_value"
    assert encrypt(plaintext) != encrypt(plaintext)


def test_crypto_tampered_ciphertext_rejected():
    ciphertext = encrypt("some_credentials")
    tampered = ciphertext[:-4] + ("A" * 4)
    with pytest.raises(InvalidToken):
        decrypt(tampered)


def test_assert_path_establishment_access_allows_own(admin_user):
    establishment_id = uuid.UUID(admin_user.establishment_ids[0])
    assert_path_establishment_access(admin_user, establishment_id)  # no raise


def test_assert_path_establishment_access_denies_other(admin_user):
    other_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(admin_user, other_id)
    assert exc_info.value.status_code == 403
