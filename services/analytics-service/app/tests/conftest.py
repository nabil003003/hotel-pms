import pytest

from app.dependencies import CurrentUser


@pytest.fixture
def manager_user() -> CurrentUser:
    return CurrentUser(
        sub="44444444-4444-4444-4444-444444444444",
        email="manager@riadyasmine.amhhospitality.com",
        roles=["manager"],
        establishment_ids=["22222222-2222-2222-2222-222222222222"],
        is_super_admin=False,
    )
