"""read_at + message channel — in-app unread tracking, direct messages

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-07

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True)))
    op.drop_constraint("chk_notifications_channel", "notifications", type_="check")
    op.create_check_constraint(
        "chk_notifications_channel", "notifications", "channel IN ('email','push','sms','message')"
    )


def downgrade() -> None:
    op.drop_constraint("chk_notifications_channel", "notifications", type_="check")
    op.create_check_constraint(
        "chk_notifications_channel", "notifications", "channel IN ('email','push','sms')"
    )
    op.drop_column("notifications", "read_at")
