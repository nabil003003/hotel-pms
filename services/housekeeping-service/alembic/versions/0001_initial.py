"""initial schema — rooms, room_status_history, room_planning, room_incidents

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
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("numero", sa.String(10), nullable=False),
        sa.Column("categorie", sa.String(50), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False),
        sa.Column("statut", sa.String(20), nullable=False, server_default="Propre"),
        sa.Column("motif_blocage", sa.String(20)),
        sa.Column("blocked_reason", sa.Text()),
        sa.Column("blocked_by", postgresql.UUID(as_uuid=True)),
        sa.Column("blocked_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("statut IN ('Sale','Nettoyage','Propre','Contrôlée','Bloquée')", name="chk_rooms_statut"),
        sa.CheckConstraint(
            "motif_blocage IS NULL OR motif_blocage IN ('Day Use','Panne','Départ tardif','Travaux')",
            name="chk_rooms_motif_blocage",
        ),
        sa.UniqueConstraint("establishment_id", "numero", name="uq_hk_rooms_establishment_numero"),
    )
    op.create_index("idx_rooms_establishment", "rooms", ["establishment_id"])
    op.create_index("idx_rooms_statut", "rooms", ["statut"], postgresql_where=sa.text("is_active = TRUE"))
    op.create_index("idx_rooms_categorie", "rooms", ["establishment_id", "categorie"])

    op.create_table(
        "room_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("old_status", sa.String(20)),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("reason", sa.Text()),
    )
    op.create_index("idx_room_status_history", "room_status_history", ["room_id", "changed_at"])

    op.create_table(
        "room_planning",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.UniqueConstraint("establishment_id", "room_id", "date", name="uq_planning_establishment_room_date"),
    )
    op.create_index("idx_planning_establishment", "room_planning", ["establishment_id"])
    op.create_index("idx_planning_date", "room_planning", ["date"])
    op.create_index("idx_planning_room", "room_planning", ["room_id"])

    op.create_table(
        "room_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rooms.id"), nullable=False),
        sa.Column("incident_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("reported_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reported_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.CheckConstraint(
            "incident_type IN ('Panne technique','Manque de linge','Problème sanitaire','Autre')",
            name="chk_incidents_type",
        ),
    )
    op.create_index("idx_incidents_establishment", "room_incidents", ["establishment_id"])
    op.create_index("idx_incidents_room", "room_incidents", ["room_id"])


def downgrade() -> None:
    op.drop_table("room_incidents")
    op.drop_table("room_planning")
    op.drop_index("idx_room_status_history", table_name="room_status_history")
    op.drop_table("room_status_history")
    op.drop_table("rooms")
