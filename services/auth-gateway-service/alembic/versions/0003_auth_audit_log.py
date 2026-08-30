"""add auth_audit_log — mirror of Keycloak login/login_error admin events
(biom.txt deliverable), polled by app/infrastructure/audit_poller.py

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Pas de contrainte FK vers users.id : `users` n'est qu'un cache
        # rempli au premier /me (ensure_user_cached) — un login raté ou un
        # premier login jamais suivi d'un appel /me n'y aura pas de ligne.
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("error", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("session_id", sa.String(64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        # Clé de dédup synthétique — l'API Admin Events de Keycloak n'expose
        # aucun id d'événement stable, voir audit_poller.py.
        sa.Column("keycloak_event_id", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_auth_audit_log_occurred_at", "auth_audit_log", ["occurred_at"])
    op.create_index("idx_auth_audit_log_user_id", "auth_audit_log", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_auth_audit_log_user_id", table_name="auth_audit_log")
    op.drop_index("idx_auth_audit_log_occurred_at", table_name="auth_audit_log")
    op.drop_table("auth_audit_log")
