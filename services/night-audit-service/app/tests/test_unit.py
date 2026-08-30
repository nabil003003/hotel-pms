import pytest

from app.domain.exceptions import (
    AuditAlreadyClosedError,
    AuditTokenInvalidError,
    DiscrepancyError,
    NoActiveAuditError,
)
from app.domain.pdf import render_report
from app.domain.services import DISCREPANCY_TOLERANCE


def test_render_report_produces_pdf_bytes():
    data = render_report("Titre", "sous-titre", [("A", "B"), ("1", "2")])
    assert data.startswith(b"%PDF")


def test_render_report_handles_empty_rows():
    data = render_report("Titre vide", "sous-titre", [])
    assert data.startswith(b"%PDF")


def test_render_report_multi_page():
    # 100 lignes doit forcer un saut de page (seuil ~y < 20mm dans render_report)
    rows = [("Poste", "Montant")] + [(f"L{i}", str(i)) for i in range(100)]
    data = render_report("Titre long", "sous-titre", rows)
    assert data.startswith(b"%PDF")


def test_discrepancy_tolerance_matches_spec():
    # Spec ligne 610 : tolérance 0.01 MAD
    assert DISCREPANCY_TOLERANCE == 0.01


def test_discrepancy_error_carries_amount():
    exc = DiscrepancyError("Discrepancy of 5.00", 5.00)
    assert exc.discrepancy == 5.00
    assert "5.00" in str(exc)


@pytest.mark.parametrize("exc_cls", [AuditTokenInvalidError, NoActiveAuditError, AuditAlreadyClosedError])
def test_plain_exceptions_carry_message(exc_cls):
    exc = exc_cls("some detail")
    assert str(exc) == "some detail"
