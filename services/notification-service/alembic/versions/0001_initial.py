"""initial schema — notifications (D11)

Revision ID: 0001
Revises:
Create Date: 2026-07-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("channel", sa.String(10), nullable=False),
        sa.Column("recipient_role", sa.String(30), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("channel IN ('email','push','sms')", name="chk_notifications_channel"),
        sa.CheckConstraint("status IN ('pending','sent','failed')", name="chk_notifications_status"),
    )
    op.create_index("idx_notifications_establishment", "notifications", ["establishment_id", "created_at"])
    op.create_index("idx_notifications_event_type", "notifications", ["establishment_id", "event_type"])


def downgrade() -> None:
    op.drop_index("idx_notifications_event_type", table_name="notifications")
    op.drop_index("idx_notifications_establishment", table_name="notifications")
    op.drop_table("notifications")
