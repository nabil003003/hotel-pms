import pytest
from fastapi import HTTPException

from app.dependencies import require_establishment_access, require_roles
from app.infrastructure.audit_poller import _dedup_key


async def test_require_roles_allows_matching_role(receptionniste_user):
    checker = require_roles("receptionniste", "manager")
    result = await checker(user=receptionniste_user)
    assert result is receptionniste_user


async def test_require_roles_rejects_missing_role(receptionniste_user):
    checker = require_roles("admin")
    with pytest.raises(HTTPException) as exc_info:
        await checker(user=receptionniste_user)
    assert exc_info.value.status_code == 403


async def test_require_roles_bypasses_for_super_admin(super_admin_user):
    checker = require_roles("gouvernante")
    result = await checker(user=super_admin_user)
    assert result is super_admin_user


async def test_establishment_access_granted_when_assigned(receptionniste_user):
    establishment_id = receptionniste_user.establishment_ids[0]
    result = await require_establishment_access(
        x_establishment_id=establishment_id, user=receptionniste_user
    )
    assert result == establishment_id


async def test_establishment_access_forbidden_when_not_assigned(receptionniste_user):
    with pytest.raises(HTTPException) as exc_info:
        await require_establishment_access(
            x_establishment_id="99999999-9999-9999-9999-999999999999", user=receptionniste_user
        )
    assert exc_info.value.status_code == 403


async def test_establishment_access_bypassed_for_super_admin(super_admin_user):
    result = await require_establishment_access(
        x_establishment_id="anything", user=super_admin_user
    )
    assert result == "anything"


def test_dedup_key_stable_for_same_event():
    event = {"time": 1723600000000, "type": "LOGIN", "userId": "u1", "sessionId": "s1", "ipAddress": "1.2.3.4"}
    assert _dedup_key(event) == _dedup_key(dict(event))


def test_dedup_key_differs_when_time_differs():
    base = {"time": 1723600000000, "type": "LOGIN", "userId": "u1", "sessionId": "s1", "ipAddress": "1.2.3.4"}
    later = {**base, "time": 1723600000001}
    assert _dedup_key(base) != _dedup_key(later)
