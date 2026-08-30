"""add users.temp_password — retained until the user completes the Keycloak
UPDATE_PASSWORD required action, so an admin can re-display it if the user
lost it before their first login

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("temp_password", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "temp_password")
