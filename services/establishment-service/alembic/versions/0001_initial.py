"""initial schema — establishments, rooms, establishment_services, ota_mappings

Revision ID: 0001
Revises:
Create Date: 2026-07-23

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
        "establishments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text()),
        sa.Column("city", sa.String(100), server_default="Marrakech"),
        sa.Column("country", sa.String(100), server_default="Maroc"),
        sa.Column("phone", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("total_rooms", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("total_rooms > 0", name="chk_total_rooms_positive"),
    )

    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("establishments.id"), nullable=False),
        sa.Column("numero", sa.String(10), nullable=False),
        sa.Column("categorie", sa.String(50), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("capacity_adults", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("capacity_children", sa.Integer(), server_default="0"),
        sa.Column("description", sa.Text()),
        sa.Column("amenities", postgresql.JSONB(), server_default="[]"),
        sa.Column("photos", postgresql.JSONB(), server_default="[]"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("establishment_id", "numero", name="uq_rooms_establishment_numero"),
    )
    op.create_index(
        "idx_rooms_establishment", "rooms", ["establishment_id"], postgresql_where=sa.text("is_active = TRUE")
    )
    op.create_index("idx_rooms_categorie", "rooms", ["establishment_id", "categorie"])

    op.create_table(
        "establishment_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("establishments.id"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("prix_ht", sa.Numeric(12, 2), nullable=False),
        sa.Column("tva_rate", sa.Numeric(5, 2), nullable=False, server_default="20.00"),
        sa.Column("prix_ttc", sa.Numeric(12, 2), nullable=False),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(
            "category IN ('Hammam','Transfert','Excursion','Diner','Cours_Cuisine','Autre')",
            name="chk_establishment_services_category",
        ),
    )
    op.create_index(
        "idx_services_establishment", "establishment_services", ["establishment_id"],
        postgresql_where=sa.text("is_active = TRUE"),
    )

    op.create_table(
        "ota_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("establishments.id"), nullable=False),
        sa.Column("ota_name", sa.String(50), nullable=False),
        sa.Column("ota_property_id", sa.String(100), nullable=False),
        sa.Column("ota_room_type_id", sa.String(100)),
        sa.Column("internal_room_category", sa.String(50)),
        sa.Column("credentials_encrypted", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("last_sync_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint(
            "ota_name IN ('booking_com','expedia','airbnb','direct_website')", name="chk_ota_mappings_name"
        ),
        sa.UniqueConstraint(
            "establishment_id", "ota_name", "ota_room_type_id", name="uq_ota_mappings_establishment_name_room"
        ),
    )


def downgrade() -> None:
    op.drop_table("ota_mappings")
    op.drop_index("idx_services_establishment", table_name="establishment_services")
    op.drop_table("establishment_services")
    op.drop_index("idx_rooms_categorie", table_name="rooms")
    op.drop_index("idx_rooms_establishment", table_name="rooms")
    op.drop_table("rooms")
    op.drop_table("establishments")
