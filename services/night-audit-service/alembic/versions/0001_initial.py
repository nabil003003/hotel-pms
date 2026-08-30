"""initial schema — audit_runs, system_state, audit_snapshots (spec §5.6)

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
        "audit_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_debits", sa.Numeric(14, 2)),
        sa.Column("total_credits", sa.Numeric(14, 2)),
        sa.Column("discrepancy", sa.Numeric(14, 2)),
        sa.Column("closed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("report_urls", postgresql.JSONB()),
        sa.Column("report_hash", sa.String(64)),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('pending','balancing','balanced','error','closed')", name="chk_audit_runs_status"
        ),
        sa.UniqueConstraint("establishment_id", "business_date", name="uq_audit_runs_establishment_date"),
    )
    op.create_index("idx_audit_runs_establishment", "audit_runs", ["establishment_id", "business_date"])

    op.create_table(
        "system_state",
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("last_audit_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_runs.id")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("service_name", sa.String(50), nullable=False),
        sa.Column("snapshot_data", postgresql.JSONB(), nullable=False),
        sa.Column("snapshot_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "establishment_id", "business_date", "service_name", name="uq_audit_snapshots_establishment_date_service"
        ),
    )


def downgrade() -> None:
    op.drop_table("audit_snapshots")
    op.drop_table("system_state")
    op.drop_index("idx_audit_runs_establishment", table_name="audit_runs")
    op.drop_table("audit_runs")
