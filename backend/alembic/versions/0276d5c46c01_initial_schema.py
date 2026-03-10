"""initial_schema

Revision ID: 0276d5c46c01
Revises: 
Create Date: 2025-11-30 10:37:21.758426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0276d5c46c01'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    def column_exists(table: str, column: str) -> bool:
        if table not in tables:
            return False
        return column in [col["name"] for col in inspector.get_columns(table)]

    if "charts" in tables and not column_exists("charts", "is_primary"):
        op.add_column("charts", sa.Column("is_primary", sa.Boolean(), nullable=True))

    if "refresh_tokens" in tables and not column_exists("refresh_tokens", "user_agent"):
        op.add_column("refresh_tokens", sa.Column("user_agent", sa.String(), nullable=True))

    if "refresh_tokens" in tables and not column_exists("refresh_tokens", "ip_address"):
        op.add_column("refresh_tokens", sa.Column("ip_address", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    def column_exists(table: str, column: str) -> bool:
        if table not in tables:
            return False
        return column in [col["name"] for col in inspector.get_columns(table)]

    if "refresh_tokens" in tables and column_exists("refresh_tokens", "ip_address"):
        op.drop_column("refresh_tokens", "ip_address")

    if "refresh_tokens" in tables and column_exists("refresh_tokens", "user_agent"):
        op.drop_column("refresh_tokens", "user_agent")

    if "charts" in tables and column_exists("charts", "is_primary"):
        op.drop_column("charts", "is_primary")
