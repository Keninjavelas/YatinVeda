"""add_audit_log_entries_table

Revision ID: d1e2f3a4b5c6
Revises: b996c085fe3d
Create Date: 2025-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, None] = "b996c085fe3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("user_email", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="SUCCESS"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_log_entries_timestamp", "audit_log_entries", ["timestamp"])
    op.create_index("ix_audit_log_entries_action", "audit_log_entries", ["action"])
    op.create_index("ix_audit_log_entries_resource_type", "audit_log_entries", ["resource_type"])
    op.create_index("ix_audit_log_entries_user_id", "audit_log_entries", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_entries_user_id")
    op.drop_index("ix_audit_log_entries_resource_type")
    op.drop_index("ix_audit_log_entries_action")
    op.drop_index("ix_audit_log_entries_timestamp")
    op.drop_table("audit_log_entries")
