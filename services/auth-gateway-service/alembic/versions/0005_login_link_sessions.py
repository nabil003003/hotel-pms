"""add login_link_sessions — QR login relay (biom.txt Flux B), for the
desktop-not-yet-authenticated case (unlike phone_link_sessions, which
assumes an already-logged-in desktop). Holds tokens only transiently:
deleted the moment the desktop claims them, or on expiry.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "login_link_sessions",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("id_token", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("login_link_sessions")
