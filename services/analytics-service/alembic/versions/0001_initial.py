"""initial schema — daily_kpi_snapshot, monthly_kpi_aggregation,
channel_performance, kpi_ytd_comparison (view)

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
        "daily_kpi_snapshot",
        sa.Column("business_date", sa.Date(), primary_key=True),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nuitees", sa.Integer(), server_default="0"),
        sa.Column("ca_brut", sa.Numeric(14, 2), server_default="0"),
        sa.Column("ca_ht", sa.Numeric(14, 2), server_default="0"),
        sa.Column("tva_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("to_pct", sa.Numeric(5, 2), server_default="0"),
        sa.Column("adr", sa.Numeric(12, 2), server_default="0"),
        sa.Column("revpar", sa.Numeric(12, 2), server_default="0"),
        sa.Column("dms", sa.Numeric(5, 2), server_default="0"),
        sa.Column("pax_total", sa.Integer(), server_default="0"),
    )
    op.create_index("idx_kpi_establishment", "daily_kpi_snapshot", ["establishment_id", "business_date"])

    op.create_table(
        "monthly_kpi_aggregation",
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("month", sa.Integer(), primary_key=True),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("segment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nuitees", sa.Integer(), server_default="0"),
        sa.Column("ca_brut", sa.Numeric(14, 2), server_default="0"),
        sa.Column("to_pct", sa.Numeric(5, 2), server_default="0"),
        sa.Column("adr", sa.Numeric(12, 2), server_default="0"),
        sa.Column("revpar", sa.Numeric(12, 2), server_default="0"),
        sa.Column("dms", sa.Numeric(5, 2), server_default="0"),
        sa.CheckConstraint("month BETWEEN 1 AND 12", name="chk_monthly_kpi_month"),
    )

    op.create_table(
        "channel_performance",
        sa.Column("business_date", sa.Date(), primary_key=True),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("channel", sa.String(50), primary_key=True),
        sa.Column("bookings_count", sa.Integer(), server_default="0"),
        sa.Column("revenue", sa.Numeric(14, 2), server_default="0"),
        sa.Column("commission", sa.Numeric(14, 2), server_default="0"),
        sa.Column("net_revenue", sa.Numeric(14, 2), server_default="0"),
    )

    op.execute(
        """
        CREATE VIEW kpi_ytd_comparison AS
        SELECT current_.year, current_.establishment_id, current_.segment_id,
            current_.ca_brut AS current_ca, previous_.ca_brut AS previous_ca,
            ROUND(((current_.ca_brut - previous_.ca_brut) / NULLIF(previous_.ca_brut, 0)) * 100, 2) AS ca_delta_pct
        FROM monthly_kpi_aggregation current_
        LEFT JOIN monthly_kpi_aggregation previous_
            ON previous_.year = current_.year - 1 AND previous_.month = current_.month
            AND previous_.establishment_id = current_.establishment_id
            AND previous_.segment_id = current_.segment_id
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS kpi_ytd_comparison")
    op.drop_table("channel_performance")
    op.drop_table("monthly_kpi_aggregation")
    op.drop_index("idx_kpi_establishment", table_name="daily_kpi_snapshot")
    op.drop_table("daily_kpi_snapshot")
