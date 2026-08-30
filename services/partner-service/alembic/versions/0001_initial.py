"""initial schema — partners

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
        "partners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("nom", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("phone", sa.String(20)),
        sa.Column("ice", sa.String(15)),
        sa.Column("rc", sa.String(50)),
        sa.Column("address", sa.Text()),
        sa.Column("payment_terms", sa.Integer(), server_default="30"),
        sa.Column("ota_credentials_encrypted", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('AGENCE','TO','CORPORATE','OTA')", name="chk_partners_type"),
    )
    op.create_index(
        "idx_partners_establishment", "partners", ["establishment_id"], postgresql_where=sa.text("is_active = TRUE")
    )
    op.create_index("idx_partners_type", "partners", ["establishment_id", "type"])
    op.create_index(
        "idx_partners_active_name", "partners", ["establishment_id", "nom"],
        postgresql_where=sa.text("is_active = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("idx_partners_active_name", table_name="partners")
    op.drop_index("idx_partners_type", table_name="partners")
    op.drop_index("idx_partners_establishment", table_name="partners")
    op.drop_table("partners")
