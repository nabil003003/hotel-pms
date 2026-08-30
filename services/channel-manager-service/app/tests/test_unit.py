import hashlib
import hmac
import uuid

import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.dependencies import assert_path_establishment_access
from app.domain.services import _verify_signature

settings = get_settings()


def _sign(body: bytes) -> str:
    return hmac.new(settings.webhook_hmac_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def test_verify_signature_valid():
    body = b'{"ota_reference": "ABC123"}'
    assert _verify_signature(body, _sign(body)) is True


def test_verify_signature_invalid():
    body = b'{"ota_reference": "ABC123"}'
    assert _verify_signature(body, "deadbeef") is False


def test_verify_signature_tampered_body_rejected():
    body = b'{"ota_reference": "ABC123"}'
    signature = _sign(body)
    tampered = b'{"ota_reference": "XYZ999"}'
    assert _verify_signature(tampered, signature) is False


def test_assert_path_establishment_access_allows_own(admin_user):
    establishment_id = uuid.UUID(admin_user.establishment_ids[0])
    assert_path_establishment_access(admin_user, establishment_id)  # no raise


def test_assert_path_establishment_access_denies_other(admin_user):
    other_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(admin_user, other_id)
    assert exc_info.value.status_code == 403
