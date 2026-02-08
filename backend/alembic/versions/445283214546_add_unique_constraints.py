"""add_unique_constraints

Revision ID: 445283214546
Revises: 034100221389
Create Date: 2025-12-05 18:50:25.440865

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '445283214546'
down_revision: Union[str, Sequence[str], None] = '034100221389'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraints to prevent duplicate entries using batch mode for SQLite."""
    
    # SQLite requires batch mode for adding constraints
    with op.batch_alter_table('post_likes', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_post_likes_user_post',
            ['user_id', 'post_id']
        )
    
    with op.batch_alter_table('comment_likes', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_comment_likes_user_comment',
            ['user_id', 'comment_id']
        )
    
    with op.batch_alter_table('user_follows', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_user_follows_follower_following',
            ['follower_id', 'following_id']
        )
    
    with op.batch_alter_table('event_registrations', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_event_registrations_user_event',
            ['user_id', 'event_id']
        )
    
    with op.batch_alter_table('guru_availability', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_guru_availability_guru_date_slot',
            ['guru_id', 'date', 'time_slot']
        )


def downgrade() -> None:
    """Remove unique constraints using batch mode for SQLite."""
    
    with op.batch_alter_table('guru_availability', schema=None) as batch_op:
        batch_op.drop_constraint('uq_guru_availability_guru_date_slot', type_='unique')
    
    with op.batch_alter_table('event_registrations', schema=None) as batch_op:
        batch_op.drop_constraint('uq_event_registrations_user_event', type_='unique')
    
    with op.batch_alter_table('user_follows', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_follows_follower_following', type_='unique')
    
    with op.batch_alter_table('comment_likes', schema=None) as batch_op:
        batch_op.drop_constraint('uq_comment_likes_user_comment', type_='unique')
    
    with op.batch_alter_table('post_likes', schema=None) as batch_op:
        batch_op.drop_constraint('uq_post_likes_user_post', type_='unique')
