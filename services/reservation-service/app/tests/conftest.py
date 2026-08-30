import pytest

from app.dependencies import CurrentUser


@pytest.fixture
def admin_user() -> CurrentUser:
    return CurrentUser(
        sub="33333333-3333-3333-3333-333333333333",
        email="admin@riadyasmine.amhhospitality.com",
        roles=["admin"],
        establishment_ids=["22222222-2222-2222-2222-222222222222"],
        is_super_admin=False,
    )


@pytest.fixture
def receptionniste_user() -> CurrentUser:
    return CurrentUser(
        sub="55555555-5555-5555-5555-555555555555",
        email="reception@riadyasmine.amhhospitality.com",
        roles=["receptionniste"],
        establishment_ids=["22222222-2222-2222-2222-222222222222"],
        is_super_admin=False,
    )
