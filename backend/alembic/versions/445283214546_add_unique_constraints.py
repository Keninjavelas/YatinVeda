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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    unique_indexes_to_create = [
        ('post_likes', 'uq_post_likes_user_post', ['user_id', 'post_id']),
        ('comment_likes', 'uq_comment_likes_user_comment', ['user_id', 'comment_id']),
        ('user_follows', 'uq_user_follows_follower_following', ['follower_id', 'following_id']),
        ('event_registrations', 'uq_event_registrations_user_event', ['user_id', 'event_id']),
        ('guru_availability', 'uq_guru_availability_guru_date_slot', ['guru_id', 'date', 'time_slot']),
    ]

    for table, index_name, columns in unique_indexes_to_create:
        if table not in tables:
            continue
        existing_indexes = {idx.get('name') for idx in inspector.get_indexes(table)}
        if index_name in existing_indexes:
            continue
        op.create_index(index_name, table, columns, unique=True)


def downgrade() -> None:
    """Remove unique constraints using batch mode for SQLite."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    unique_indexes_to_drop = [
        ('guru_availability', 'uq_guru_availability_guru_date_slot'),
        ('event_registrations', 'uq_event_registrations_user_event'),
        ('user_follows', 'uq_user_follows_follower_following'),
        ('comment_likes', 'uq_comment_likes_user_comment'),
        ('post_likes', 'uq_post_likes_user_post'),
    ]

    for table, index_name in unique_indexes_to_drop:
        if table not in tables:
            continue
        existing_indexes = {idx.get('name') for idx in inspector.get_indexes(table)}
        if index_name not in existing_indexes:
            continue
        op.drop_index(index_name, table)
