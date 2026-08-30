"""initial schema — market_segments, customers, bookings,
booking_status_history, audit_log

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
        "market_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("category IN ('DIRECT','OTA','PARTENAIRES')", name="chk_market_segments_category"),
        sa.UniqueConstraint("establishment_id", "code", name="uq_market_segments_establishment_code"),
    )

    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(20)),
        sa.Column("id_number", sa.String(50)),
        sa.Column("nationality", sa.String(3)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("historical_notes", postgresql.JSONB(), server_default="{}"),
        sa.Column("is_vip", sa.Boolean(), server_default=sa.false()),
        sa.Column("preferences", postgresql.JSONB(), server_default="{}"),
        sa.Column("consent_marketing", sa.Boolean(), server_default=sa.false()),
        sa.Column("anonymized_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_customers_establishment", "customers", ["establishment_id"])
    op.create_index("idx_customers_name", "customers", ["establishment_id", "last_name", "first_name"])
    op.create_index(
        "idx_customers_email", "customers", ["establishment_id", "email"],
        postgresql_where=sa.text("anonymized_at IS NULL"),
    )
    op.execute(
        "CREATE INDEX idx_customers_fts ON customers USING GIN ("
        "to_tsvector('french', coalesce(first_name,'') || ' ' || coalesce(last_name,'') || ' ' || coalesce(email,'')))"
    )

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("market_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("market_segments.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("option_expiry_date", sa.DateTime(timezone=True)),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("check_out_date", sa.Date(), nullable=False),
        sa.Column("regime", sa.String(5), nullable=False),
        sa.Column("partner_id", postgresql.UUID(as_uuid=True)),
        sa.Column("taxes_payment_mode", sa.String(20), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2)),
        sa.Column("deposit_amount", sa.Numeric(12, 2), server_default="0"),
        sa.Column("adults", sa.Integer(), nullable=False),
        sa.Column("children", sa.Integer(), server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column("source", sa.String(30), nullable=False, server_default="walk_in"),
        sa.Column("ota_reference", sa.String(100)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('status_option','status_confirmed','status_voucher','status_checked_in',"
            "'status_checked_out','status_no_show','status_cancelled')",
            name="chk_bookings_status",
        ),
        sa.CheckConstraint("regime IN ('BB','DP','PC')", name="chk_bookings_regime"),
        sa.CheckConstraint("taxes_payment_mode IN ('at_booking','on_site')", name="chk_bookings_taxes_payment_mode"),
        sa.CheckConstraint("adults > 0", name="chk_bookings_adults_positive"),
        sa.CheckConstraint("children >= 0", name="chk_bookings_children_non_negative"),
        sa.CheckConstraint(
            "source IN ('walk_in','phone','email','website','ota_booking','ota_expedia','ota_airbnb','b2b_agency')",
            name="chk_bookings_source",
        ),
        sa.CheckConstraint("check_out_date > check_in_date", name="chk_dates"),
        sa.CheckConstraint("status != 'status_option' OR option_expiry_date IS NOT NULL", name="chk_option_date"),
    )
    op.create_index("idx_bookings_establishment", "bookings", ["establishment_id"])
    op.create_index("idx_bookings_dates", "bookings", ["check_in_date", "check_out_date"])
    op.create_index(
        "idx_bookings_room", "bookings", ["establishment_id", "room_id"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index(
        "idx_bookings_status", "bookings", ["establishment_id", "status"], postgresql_where=sa.text("deleted_at IS NULL")
    )
    op.create_index("idx_bookings_customer", "bookings", ["customer_id"])
    op.create_index("idx_bookings_segment", "bookings", ["market_segment_id"])
    op.create_index("idx_bookings_created_at", "bookings", ["created_at"])
    op.create_index(
        "idx_bookings_ota_reference", "bookings", ["ota_reference"], postgresql_where=sa.text("ota_reference IS NOT NULL")
    )

    op.create_table(
        "booking_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bookings.id"), nullable=False),
        sa.Column("old_status", sa.String(20)),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("reason", sa.Text()),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True)),
    )
    op.create_index("idx_booking_status_history_booking", "booking_status_history", ["booking_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("table_name", sa.String(50), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(10), nullable=False),
        sa.Column("old_data", postgresql.JSONB()),
        sa.Column("new_data", postgresql.JSONB()),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("ip_address", postgresql.INET()),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint("action IN ('INSERT','UPDATE','DELETE')", name="chk_audit_log_action"),
    )
    op.create_index("idx_audit_log_record", "audit_log", ["table_name", "record_id"])


def downgrade() -> None:
    op.drop_index("idx_audit_log_record", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("idx_booking_status_history_booking", table_name="booking_status_history")
    op.drop_table("booking_status_history")
    op.drop_index("idx_bookings_ota_reference", table_name="bookings")
    op.drop_index("idx_bookings_created_at", table_name="bookings")
    op.drop_index("idx_bookings_segment", table_name="bookings")
    op.drop_index("idx_bookings_customer", table_name="bookings")
    op.drop_index("idx_bookings_status", table_name="bookings")
    op.drop_index("idx_bookings_room", table_name="bookings")
    op.drop_index("idx_bookings_dates", table_name="bookings")
    op.drop_index("idx_bookings_establishment", table_name="bookings")
    op.drop_table("bookings")
    op.execute("DROP INDEX IF EXISTS idx_customers_fts")
    op.drop_index("idx_customers_email", table_name="customers")
    op.drop_index("idx_customers_name", table_name="customers")
    op.drop_index("idx_customers_establishment", table_name="customers")
    op.drop_table("customers")
    op.drop_table("market_segments")
