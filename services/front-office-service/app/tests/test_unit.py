import uuid

import pytest
from fastapi import HTTPException

from app.dependencies import assert_path_establishment_access
from app.domain.services import POSTE_TVA_RATES, _amounts_from_ht, _amounts_from_ttc

ALL_POSTES = {"HEB", "PDJ", "RES", "BAR", "SPA", "ACT", "TS", "TPT", "REM", "HAM", "TRF", "DIN", "EXC"}


def test_poste_tva_rates_covers_every_poste():
    assert set(POSTE_TVA_RATES.keys()) == ALL_POSTES


def test_poste_tva_rates_match_spec_table():
    for poste in ("HEB", "PDJ", "RES", "DIN"):
        assert POSTE_TVA_RATES[poste] == 10
    for poste in ("BAR", "SPA", "ACT", "HAM", "TRF", "EXC"):
        assert POSTE_TVA_RATES[poste] == 20
    for poste in ("TS", "TPT", "REM"):
        assert POSTE_TVA_RATES[poste] == 0


def test_amounts_from_ht_basic():
    ht, tva, ttc = _amounts_from_ht(unit_price_ht=100, quantity=2, tva_rate=20)
    assert ht == 200
    assert tva == 40
    assert ttc == 240


def test_amounts_from_ht_zero_tva():
    ht, tva, ttc = _amounts_from_ht(unit_price_ht=50, quantity=3, tva_rate=0)
    assert ht == 150
    assert tva == 0
    assert ttc == 150


def test_amounts_from_ttc_roundtrip_10_percent():
    ht, tva, ttc = _amounts_from_ttc(montant_ttc=1100, tva_rate=10)
    assert ht == 1000.0
    assert tva == 100.0
    assert ttc == 1100.0


def test_amounts_from_ht_and_ttc_are_consistent():
    ht1, tva1, ttc1 = _amounts_from_ht(unit_price_ht=800, quantity=1, tva_rate=10)
    ht2, tva2, ttc2 = _amounts_from_ttc(montant_ttc=ttc1, tva_rate=10)
    assert round(ht1, 2) == round(ht2, 2)
    assert round(ttc1, 2) == round(ttc2, 2)


def test_assert_path_establishment_access_allows_own(admin_user):
    establishment_id = uuid.UUID(admin_user.establishment_ids[0])
    assert_path_establishment_access(admin_user, establishment_id)  # no raise


def test_assert_path_establishment_access_denies_other(admin_user):
    other_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(admin_user, other_id)
    assert exc_info.value.status_code == 403
