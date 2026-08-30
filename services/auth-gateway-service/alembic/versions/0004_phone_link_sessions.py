"""add phone_link_sessions + users.webauthn_linked — custom QR-relay phone
linking (biom.txt Flux A), replacing reliance on the browser's native
WebAuthn hybrid transport which proved unreliable across real devices.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("webauthn_linked", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.create_table(
        "phone_link_sessions",
        sa.Column("token", sa.String(64), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_phone_link_sessions_user_id", "phone_link_sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_phone_link_sessions_user_id", table_name="phone_link_sessions")
    op.drop_table("phone_link_sessions")
    op.drop_column("users", "webauthn_linked")
