import pytest

from app.dependencies import CurrentUser


@pytest.fixture
def femme_de_chambre_user() -> CurrentUser:
    return CurrentUser(
        sub="44444444-4444-4444-4444-444444444444",
        email="femme.chambre@riadyasmine.amhhospitality.com",
        roles=["femme_de_chambre"],
        establishment_ids=["22222222-2222-2222-2222-222222222222"],
        is_super_admin=False,
    )


@pytest.fixture
def gouvernante_user() -> CurrentUser:
    return CurrentUser(
        sub="55555555-5555-5555-5555-555555555555",
        email="gouvernante@riadyasmine.amhhospitality.com",
        roles=["gouvernante"],
        establishment_ids=["22222222-2222-2222-2222-222222222222"],
        is_super_admin=False,
    )
