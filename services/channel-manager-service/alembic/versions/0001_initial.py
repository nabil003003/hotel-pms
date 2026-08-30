"""initial schema — channel_connections, sync_logs

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
        "channel_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ota_name", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("credentials_encrypted", sa.Text()),
        sa.Column("two_way_sync_enabled", sa.Boolean(), server_default=sa.false()),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(
            "ota_name IN ('booking_com','expedia','airbnb','direct_website')",
            name="chk_channel_connections_ota_name",
        ),
        sa.UniqueConstraint("establishment_id", "ota_name", name="uq_channel_connections_establishment_ota"),
    )
    op.create_index("idx_channel_connections_establishment", "channel_connections", ["establishment_id"])

    op.create_table(
        "sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ota_name", sa.String(50), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("correlation_id", sa.String(100)),
        sa.Column("error_message", sa.Text()),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('ok','error','buffered')", name="chk_sync_logs_status"),
    )
    op.create_index("idx_sync_logs_establishment", "sync_logs", ["establishment_id", "created_at"])
    op.create_index("idx_sync_logs_ota_reference", "sync_logs", ["establishment_id", "ota_name"])


def downgrade() -> None:
    op.drop_index("idx_sync_logs_ota_reference", table_name="sync_logs")
    op.drop_index("idx_sync_logs_establishment", table_name="sync_logs")
    op.drop_table("sync_logs")
    op.drop_index("idx_channel_connections_establishment", table_name="channel_connections")
    op.drop_table("channel_connections")
