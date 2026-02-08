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
    # Use batch mode for SQLite to add unique constraint
    with op.batch_alter_table('gurus', schema=None) as batch_op:
        batch_op.create_unique_constraint('uq_gurus_user_id', ['user_id'])


def downgrade() -> None:
    """Remove unique constraint on gurus.user_id."""
    with op.batch_alter_table('gurus', schema=None) as batch_op:
        batch_op.drop_constraint('uq_gurus_user_id', type_='unique')
