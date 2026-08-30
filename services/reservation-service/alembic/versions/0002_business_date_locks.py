"""business_date_locks — D12 (Sprint 5, night-audit-service)

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "business_date_locks",
        sa.Column("establishment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("business_date", sa.Date(), primary_key=True),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.false()),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("business_date_locks")
