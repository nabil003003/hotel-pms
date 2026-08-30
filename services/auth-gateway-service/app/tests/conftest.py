import pytest

from app.dependencies import CurrentUser


@pytest.fixture
def receptionniste_user() -> CurrentUser:
    return CurrentUser(
        sub="11111111-1111-1111-1111-111111111111",
        email="reception@riadyasmine.amhhospitality.com",
        roles=["receptionniste"],
        establishment_ids=["22222222-2222-2222-2222-222222222222"],
        is_super_admin=False,
    )


@pytest.fixture
def super_admin_user() -> CurrentUser:
    return CurrentUser(
        sub="00000000-0000-0000-0000-000000000000",
        email="sidi.omar@amhhospitality.com",
        roles=["admin"],
        establishment_ids=[],
        is_super_admin=True,
    )
