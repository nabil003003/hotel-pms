import uuid
from datetime import date

import pytest
from fastapi import HTTPException

from app.dependencies import assert_path_establishment_access
from app.domain.services import _resolve_season_for_night


def _season(id_, date_debut, date_fin):
    class _S:
        pass

    s = _S()
    s.id = id_
    s.date_debut = date_debut
    s.date_fin = date_fin
    return s


def test_resolve_season_for_night_within_range():
    season = _season(uuid.uuid4(), date(2026, 6, 1), date(2026, 9, 1))
    resolved = _resolve_season_for_night([season], date(2026, 7, 15))
    assert resolved is season


def test_resolve_season_for_night_boundary_start_inclusive():
    season = _season(uuid.uuid4(), date(2026, 6, 1), date(2026, 9, 1))
    assert _resolve_season_for_night([season], date(2026, 6, 1)) is season


def test_resolve_season_for_night_boundary_end_exclusive():
    season = _season(uuid.uuid4(), date(2026, 6, 1), date(2026, 9, 1))
    assert _resolve_season_for_night([season], date(2026, 9, 1)) is None


def test_resolve_season_for_night_no_match():
    season = _season(uuid.uuid4(), date(2026, 6, 1), date(2026, 9, 1))
    assert _resolve_season_for_night([season], date(2026, 1, 1)) is None


def test_resolve_season_for_night_picks_first_overlap_in_list_order():
    early = _season(uuid.uuid4(), date(2026, 1, 1), date(2026, 12, 31))
    late = _season(uuid.uuid4(), date(2026, 6, 1), date(2026, 9, 1))
    assert _resolve_season_for_night([early, late], date(2026, 7, 1)) is early


def test_assert_path_establishment_access_allows_own(admin_user):
    establishment_id = uuid.UUID(admin_user.establishment_ids[0])
    assert_path_establishment_access(admin_user, establishment_id)  # no raise


def test_assert_path_establishment_access_denies_other(admin_user):
    other_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(admin_user, other_id)
    assert exc_info.value.status_code == 403
