import uuid

import pytest
from fastapi import HTTPException

from app.dependencies import assert_path_establishment_access
from app.domain.exceptions import InvalidCsvError
from app.domain.services import parse_rooms_csv


def test_parse_rooms_csv_valid():
    content = (
        b"numero,categorie,floor,capacity_adults,capacity_children\n"
        b"R01,Chambre Standard,0,2,1\n"
        b"R02,Chambre Deluxe,1,2,1\n"
    )
    rows = parse_rooms_csv(content)
    assert len(rows) == 2
    assert rows[0] == {
        "numero": "R01",
        "categorie": "Chambre Standard",
        "floor": 0,
        "capacity_adults": 2,
        "capacity_children": 1,
    }


def test_parse_rooms_csv_defaults_capacity():
    content = b"numero,categorie,floor\nR03,Suite Royale,2\n"
    rows = parse_rooms_csv(content)
    assert rows[0]["capacity_adults"] == 2
    assert rows[0]["capacity_children"] == 0


def test_parse_rooms_csv_missing_column_raises():
    content = b"numero,floor\nR01,0\n"
    with pytest.raises(InvalidCsvError):
        parse_rooms_csv(content)


def test_parse_rooms_csv_empty_raises():
    content = b"numero,categorie,floor\n"
    with pytest.raises(InvalidCsvError):
        parse_rooms_csv(content)


def test_parse_rooms_csv_bad_int_raises():
    content = b"numero,categorie,floor\nR01,Chambre Standard,not-a-number\n"
    with pytest.raises(InvalidCsvError):
        parse_rooms_csv(content)


def test_assert_path_establishment_access_allows_own(admin_user):
    establishment_id = uuid.UUID(admin_user.establishment_ids[0])
    assert_path_establishment_access(admin_user, establishment_id)  # no raise


def test_assert_path_establishment_access_denies_other(admin_user):
    other_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        assert_path_establishment_access(admin_user, other_id)
    assert exc_info.value.status_code == 403
