import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from app.dependencies import assert_path_establishment_access
from app.domain.services import ALLOWED_STATUS_TRANSITIONS, _nights_between


def test_nights_between_single_night():
    assert _nights_between(date(2026, 8, 1), date(2026, 8, 2)) == [date(2026, 8, 1)]


def test_nights_between_multiple_nights():
    nights = _nights_between(date(2026, 8, 1), date(2026, 8, 4))
    assert nights == [date(2026, 8, 1), date(2026, 8, 2), date(2026, 8, 3)]


def test_nights_between_same_day_empty():
    assert _nights_between(date(2026, 8, 1), date(2026, 8, 1)) == []


def test_status_transition_table_covers_every_status():
    all_statuses = {
        "status_option", "status_confirmed", "status_voucher", "status_checked_in",
        "status_checked_out", "status_no_show", "status_cancelled",
    }
    assert set(ALLOWED_STATUS_TRANSITIONS.keys()) == all_statuses


def test_status_transition_terminal_states_have_no_outgoing_edges():
    for terminal in ("status_checked_out", "status_no_show", "status_cancelled"):
        assert ALLOWED_STATUS_TRANSITIONS[terminal] == set()


def test_status_transition_checked_in_only_allows_checkout():
    assert ALLOWED_STATUS_TRANSITIONS["status_checked_in"] == {"status_checked_out"}


def test_status_transition_option_allows_cancel_and_confirm():
    allowed = ALLOWED_STATUS_TRANSITIONS["status_option"]
    assert "status_cancelled" in allowed
    assert "status_confirmed" in allowed
    assert "status_checked_in" not in allowed  # doit passer par confirmed/voucher d'abord


def test_assert_path_establishment_access_allows_own(admin_user):
    establishment_id = uuid.UUID(admin_user.establishment_ids[0])
    assert_path_establishment_access(admin_user, establishment_id)  # no raise


def test_assert_path_establishment_access_denies_other(admin_user):
    other_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(admin_user, other_id)
    assert exc_info.value.status_code == 403
