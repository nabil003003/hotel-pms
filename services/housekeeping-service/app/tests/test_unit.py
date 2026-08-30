import itertools

import pytest

from app.domain.exceptions import InvalidTransitionError
from app.domain.models import ALLOWED_TRANSITIONS, ROOM_STATUSES
from app.domain.services import is_unblock_allowed, validate_transition

VALID_PAIRS = [
    ("Sale", "Nettoyage"),
    ("Nettoyage", "Propre"),
    ("Propre", "Contrôlée"),
    ("Contrôlée", "Bloquée"),
    ("Bloquée", "Propre"),
]


@pytest.mark.parametrize("old_status,new_status", VALID_PAIRS)
def test_valid_transitions_do_not_raise(old_status, new_status):
    validate_transition(old_status, new_status)  # no raise


@pytest.mark.parametrize(
    "old_status,new_status",
    [pair for pair in itertools.product(ROOM_STATUSES, ROOM_STATUSES) if pair not in VALID_PAIRS],
)
def test_invalid_transitions_raise(old_status, new_status):
    with pytest.raises(InvalidTransitionError) as exc_info:
        validate_transition(old_status, new_status)
    assert exc_info.value.current == old_status
    assert exc_info.value.requested == new_status
    assert exc_info.value.allowed == sorted(ALLOWED_TRANSITIONS.get(old_status, set()))


def test_every_status_has_an_explicit_transition_rule():
    """Filet anti-régression : si un statut est ajouté à ROOM_STATUSES sans
    mise à jour d'ALLOWED_TRANSITIONS, ce test échoue plutôt que de laisser
    une transition implicitement bloquée en silence."""
    assert set(ALLOWED_TRANSITIONS.keys()) == set(ROOM_STATUSES)


def test_femme_de_chambre_cannot_unblock():
    assert is_unblock_allowed(["femme_de_chambre"], is_super_admin=False) is False


@pytest.mark.parametrize("role", ["gouvernante", "manager", "admin"])
def test_supervisory_roles_can_unblock(role):
    assert is_unblock_allowed([role], is_super_admin=False) is True


def test_super_admin_can_always_unblock():
    assert is_unblock_allowed([], is_super_admin=True) is True
