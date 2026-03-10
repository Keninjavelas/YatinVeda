"""fix_guru_user_id_unique_constraint

Revision ID: 499ef1ea01ab
Revises: 57d2c0670675
Create Date: 2025-12-28 22:07:20.938250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '499ef1ea01ab'
down_revision: Union[str, Sequence[str], None] = '57d2c0670675'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix unique constraint on gurus.user_id."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'gurus' not in tables:
        return

    existing_indexes = {idx.get('name') for idx in inspector.get_indexes('gurus')}
    if 'uq_gurus_user_id' not in existing_indexes:
        op.create_index('uq_gurus_user_id', 'gurus', ['user_id'], unique=True)


def downgrade() -> None:
    """Remove unique constraint on gurus.user_id."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if 'gurus' not in tables:
        return

    existing_indexes = {idx.get('name') for idx in inspector.get_indexes('gurus')}
    if 'uq_gurus_user_id' in existing_indexes:
        op.drop_index('uq_gurus_user_id', table_name='gurus')
