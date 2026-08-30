"""initial schema — folios, folio_charges, payments, business_date_locks

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
        "folios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(1), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="open"),
        sa.Column("third_party_ref", postgresql.UUID(as_uuid=True)),
        sa.Column("total_charges", sa.Numeric(12, 2), server_default="0"),
        sa.Column("total_payments", sa.Numeric(12, 2), server_default="0"),
        sa.Column(
            "balance", sa.Numeric(12, 2),
            sa.Computed("total_charges - total_payments", persisted=True),
        ),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("closed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.CheckConstraint("type IN ('A','B')", name="chk_folios_type"),
        sa.CheckConstraint("status IN ('open','closed')", name="chk_folios_status"),
    )
    op.create_index("idx_folios_establishment", "folios", ["establishment_id"])
    op.create_index("idx_folios_booking", "folios", ["booking_id"])
    op.create_index("idx_folios_status", "folios", ["status"], postgresql_where=sa.text("status = 'open'"))
    op.create_index("idx_folios_business_date", "folios", ["business_date"])

    op.create_table(
        "folio_charges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("folio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("folios.id"), nullable=False),
        sa.Column("poste_comptable", sa.String(10), nullable=False),
        sa.Column("libelle", sa.String(255), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="1"),
        sa.Column("unit_price_ht", sa.Numeric(12, 2), nullable=False),
        sa.Column("montant_ht", sa.Numeric(12, 2), nullable=False),
        sa.Column("tva_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("tva_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("montant_ttc", sa.Numeric(12, 2), nullable=False),
        sa.Column("visible_on_print", sa.Boolean(), server_default=sa.true()),
        sa.Column("source_service", sa.String(50)),
        sa.Column("catalog_item_id", postgresql.UUID(as_uuid=True)),
        sa.Column("correction_of", postgresql.UUID(as_uuid=True), sa.ForeignKey("folio_charges.id")),
        sa.Column("corrects_date", sa.Date()),
        sa.Column("correction_reason", sa.Text()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_folio_charges_quantity_positive"),
        sa.CheckConstraint("tva_rate IN (0,10,20)", name="chk_folio_charges_tva_rate"),
        sa.CheckConstraint(
            "poste_comptable IN ('HEB','PDJ','RES','BAR','SPA','ACT','TS','TPT','REM','HAM','TRF','DIN','EXC')",
            name="chk_folio_charges_poste",
        ),
    )
    op.create_index("idx_charges_folio", "folio_charges", ["folio_id"])
    op.create_index("idx_charges_poste", "folio_charges", ["poste_comptable", "business_date"])
    op.create_index("idx_charges_business_date", "folio_charges", ["business_date"])

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("folio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("folios.id"), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False),
        sa.Column("montant", sa.Numeric(12, 2), nullable=False),
        sa.Column("reference", sa.String(100)),
        sa.Column("encaisse_par", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("encaisse_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.CheckConstraint("mode IN ('CB','ESP','CHQ','Virement','Débiteur')", name="chk_payments_mode"),
        sa.CheckConstraint("montant > 0", name="chk_payments_montant_positive"),
    )
    op.create_index("idx_payments_folio", "payments", ["folio_id"])
    op.create_index("idx_payments_mode", "payments", ["mode", "business_date"])
    op.create_index("idx_payments_business_date", "payments", ["business_date"])

    op.create_table(
        "business_date_locks",
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_date", sa.Date(), primary_key=True),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.false()),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("locked_by", postgresql.UUID(as_uuid=True)),
        sa.Column("audit_run_id", postgresql.UUID(as_uuid=True)),
    )


def downgrade() -> None:
    op.drop_table("business_date_locks")
    op.drop_index("idx_payments_business_date", table_name="payments")
    op.drop_index("idx_payments_mode", table_name="payments")
    op.drop_index("idx_payments_folio", table_name="payments")
    op.drop_table("payments")
    op.drop_index("idx_charges_business_date", table_name="folio_charges")
    op.drop_index("idx_charges_poste", table_name="folio_charges")
    op.drop_index("idx_charges_folio", table_name="folio_charges")
    op.drop_table("folio_charges")
    op.drop_index("idx_folios_business_date", table_name="folios")
    op.drop_index("idx_folios_status", table_name="folios")
    op.drop_index("idx_folios_booking", table_name="folios")
    op.drop_index("idx_folios_establishment", table_name="folios")
    op.drop_table("folios")
