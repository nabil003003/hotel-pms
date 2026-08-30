import pytest
from fastapi import HTTPException

from app.dependencies import CurrentUser, assert_path_establishment_access, require_super_admin
from app.domain.exceptions import NotificationNotFoundError
from app.events.handlers import _BOOKING_HANDLERS

ESTABLISHMENT_ID = "4f9cb82b-4ded-491c-b85d-ba2cd6d36fda"


def test_booking_handlers_cover_appendix_c_consumers():
    assert set(_BOOKING_HANDLERS.keys()) == {
        "booking.created", "booking.checked_in", "booking.checked_out", "booking.cancelled",
    }


def test_assert_path_establishment_access_super_admin_bypasses():
    user = CurrentUser(sub="svc", is_super_admin=True, establishment_ids=[])
    assert_path_establishment_access(user, ESTABLISHMENT_ID)


def test_assert_path_establishment_access_denies_other_establishment():
    user = CurrentUser(sub="u1", is_super_admin=False, establishment_ids=["other-id"])
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(user, ESTABLISHMENT_ID)
    assert exc_info.value.status_code == 403


def test_require_super_admin_allows_super_admin():
    user = CurrentUser(sub="svc", is_super_admin=True)
    assert require_super_admin(user) is user


def test_require_super_admin_denies_regular_user():
    user = CurrentUser(sub="u1", is_super_admin=False, roles=["manager"])
    with pytest.raises(HTTPException) as exc_info:
        require_super_admin(user)
    assert exc_info.value.status_code == 403


def test_notification_not_found_error_message():
    notification_id = "abc-123"
    exc = NotificationNotFoundError(notification_id)
    assert str(exc) == notification_id
