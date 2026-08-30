from datetime import date

import pytest

from app.domain.exceptions import InvalidPeriodError
from app.domain.services import POSTE_TVA_RATES, _month_range, _parse_period

ALL_POSTES = {"HEB", "PDJ", "RES", "BAR", "SPA", "ACT", "TS", "TPT", "REM", "HAM", "TRF", "DIN", "EXC"}


def test_month_range_regular_month():
    start, end = _month_range(2026, 7)
    assert start == date(2026, 7, 1)
    assert end == date(2026, 8, 1)


def test_month_range_january_stays_in_year():
    start, end = _month_range(2026, 1)
    assert start == date(2026, 1, 1)
    assert end == date(2026, 2, 1)


def test_month_range_december_rolls_to_next_year():
    start, end = _month_range(2026, 12)
    assert start == date(2026, 12, 1)
    assert end == date(2027, 1, 1)


def test_month_range_invalid_month_raises():
    with pytest.raises(InvalidPeriodError):
        _month_range(2026, 13)


def test_month_range_zero_month_raises():
    with pytest.raises(InvalidPeriodError):
        _month_range(2026, 0)


def test_poste_tva_rates_matches_front_office_duplicate():
    # Dupliqué de front-office-service (D2, pas de lib partagée) — les deux
    # copies doivent rester en phase, cf. docstring de analytics/services.py.
    assert set(POSTE_TVA_RATES.keys()) == ALL_POSTES
    for poste in ("HEB", "PDJ", "RES", "DIN"):
        assert POSTE_TVA_RATES[poste] == 10
    for poste in ("BAR", "SPA", "ACT", "HAM", "TRF", "EXC"):
        assert POSTE_TVA_RATES[poste] == 20
    for poste in ("TS", "TPT", "REM"):
        assert POSTE_TVA_RATES[poste] == 0


def test_parse_period_valid():
    assert _parse_period("2026-07") == (2026, 7)


def test_parse_period_invalid_raises():
    with pytest.raises(InvalidPeriodError):
        _parse_period("not-a-period")
