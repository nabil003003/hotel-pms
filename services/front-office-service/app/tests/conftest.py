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
