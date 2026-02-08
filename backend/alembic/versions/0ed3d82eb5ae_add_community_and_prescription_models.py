"""add_community_and_prescription_models

Revision ID: 0ed3d82eb5ae
Revises: 84b054cffce6
Create Date: 2025-12-05 22:03:54.544454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0ed3d82eb5ae'
down_revision: Union[str, None] = '84b054cffce6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by creating community and prescription related tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def table_exists(name: str) -> bool:
        return inspector.has_table(name)

    def index_exists(table: str, name: str) -> bool:
        return any(idx.get('name') == name for idx in inspector.get_indexes(table))

    if not table_exists('learning_progress'):
        op.create_table(
            'learning_progress',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('lesson_id', sa.Integer(), nullable=False),
            sa.Column('completed', sa.Boolean(), server_default=sa.text('0'), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_learning_progress_id'), 'learning_progress', ['id'], unique=False)
        op.create_index('idx_learning_progress_user', 'learning_progress', ['user_id'], unique=False)

    if not table_exists('chat_history'):
        op.create_table(
            'chat_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('response', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_chat_history_id'), 'chat_history', ['id'], unique=False)
        op.create_index('idx_chat_history_user', 'chat_history', ['user_id'], unique=False)

    if not table_exists('user_profiles'):
        op.create_table(
            'user_profiles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('bio', sa.Text(), nullable=True),
            sa.Column('avatar_url', sa.String(), nullable=True),
            sa.Column('location', sa.String(), nullable=True),
            sa.Column('interests', sa.JSON(), nullable=True),
            sa.Column('privacy_settings', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
        op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)

    if not table_exists('community_posts'):
        op.create_table(
            'community_posts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('post_type', sa.String(), nullable=True, server_default='text'),
            sa.Column('media_url', sa.String(), nullable=True),
            sa.Column('chart_id', sa.Integer(), nullable=True),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('likes_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('comments_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('is_public', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['chart_id'], ['charts.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_community_posts_id'), 'community_posts', ['id'], unique=False)
        op.create_index('idx_community_posts_user', 'community_posts', ['user_id'], unique=False)

    if not table_exists('community_events'):
        op.create_table(
            'community_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('organizer_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('event_date', sa.DateTime(), nullable=False),
            sa.Column('location', sa.String(), nullable=True),
            sa.Column('is_online', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('meeting_link', sa.String(), nullable=True),
            sa.Column('max_participants', sa.Integer(), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=True, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_community_events_id'), 'community_events', ['id'], unique=False)
        op.create_index('idx_community_events_organizer', 'community_events', ['organizer_id'], unique=False)

    if not table_exists('user_follows'):
        op.create_table(
            'user_follows',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('follower_id', sa.Integer(), nullable=False),
            sa.Column('following_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['follower_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['following_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('follower_id', 'following_id', name='uq_user_follows_follower_following')
        )
        op.create_index(op.f('ix_user_follows_id'), 'user_follows', ['id'], unique=False)
        op.create_index('idx_user_follows_follower', 'user_follows', ['follower_id'], unique=False)
        op.create_index('idx_user_follows_following', 'user_follows', ['following_id'], unique=False)

    if not table_exists('post_comments'):
        op.create_table(
            'post_comments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('parent_comment_id', sa.Integer(), nullable=True),
            sa.Column('likes_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['parent_comment_id'], ['post_comments.id'], ),
            sa.ForeignKeyConstraint(['post_id'], ['community_posts.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_post_comments_id'), 'post_comments', ['id'], unique=False)
        op.create_index('idx_post_comments_post', 'post_comments', ['post_id'], unique=False)
        op.create_index('idx_post_comments_user', 'post_comments', ['user_id'], unique=False)

    if not table_exists('post_likes'):
        op.create_table(
            'post_likes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('post_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['post_id'], ['community_posts.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('post_id', 'user_id', name='uq_post_likes_user_post')
        )
        op.create_index(op.f('ix_post_likes_id'), 'post_likes', ['id'], unique=False)

    if not table_exists('comment_likes'):
        op.create_table(
            'comment_likes',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('comment_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['comment_id'], ['post_comments.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('comment_id', 'user_id', name='uq_comment_likes_user_comment')
        )
        op.create_index(op.f('ix_comment_likes_id'), 'comment_likes', ['id'], unique=False)

    if not table_exists('event_registrations'):
        op.create_table(
            'event_registrations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(), nullable=True, server_default='registered'),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['event_id'], ['community_events.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_id', 'user_id', name='uq_event_registrations_user_event')
        )
        op.create_index(op.f('ix_event_registrations_id'), 'event_registrations', ['id'], unique=False)
        op.create_index('idx_event_registrations_event', 'event_registrations', ['event_id'], unique=False)

    if not table_exists('notifications'):
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('notification_type', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('link', sa.String(), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
        op.create_index('idx_notifications_user', 'notifications', ['user_id'], unique=False)

    if not table_exists('prescriptions'):
        op.create_table(
            'prescriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('booking_id', sa.Integer(), nullable=False),
            sa.Column('guru_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('remedies', sa.JSON(), nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('digital_signature', sa.String(), nullable=True),
            sa.Column('pdf_url', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['booking_id'], ['guru_bookings.id'], ),
            sa.ForeignKeyConstraint(['guru_id'], ['gurus.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_prescriptions_id'), 'prescriptions', ['id'], unique=False)
        op.create_index('idx_prescriptions_user', 'prescriptions', ['user_id'], unique=False)

    if not table_exists('prescription_reminders'):
        op.create_table(
            'prescription_reminders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('prescription_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('reminder_date', sa.DateTime(), nullable=False),
            sa.Column('reminder_type', sa.String(), nullable=True, server_default='follow_up'),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('is_sent', sa.Boolean(), nullable=True, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
            sa.ForeignKeyConstraint(['prescription_id'], ['prescriptions.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_prescription_reminders_id'), 'prescription_reminders', ['id'], unique=False)
        op.create_index('idx_prescription_reminders_user', 'prescription_reminders', ['user_id'], unique=False)
        op.create_index('idx_prescription_reminders_date', 'prescription_reminders', ['reminder_date'], unique=False)

    # Trusted devices unique index alignment
    if index_exists('trusted_devices', 'ix_trusted_devices_device_fingerprint'):
        op.drop_index('ix_trusted_devices_device_fingerprint', table_name='trusted_devices')
    if not index_exists('trusted_devices', op.f('ix_trusted_devices_device_fingerprint')):
        op.create_index(op.f('ix_trusted_devices_device_fingerprint'), 'trusted_devices', ['device_fingerprint'], unique=True)


def downgrade() -> None:
    """Downgrade schema by dropping created tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    def table_exists(name: str) -> bool:
        return inspector.has_table(name)

    def index_exists(table: str, name: str) -> bool:
        return any(idx.get('name') == name for idx in inspector.get_indexes(table))

    if not index_exists('trusted_devices', 'ix_trusted_devices_device_fingerprint'):
        op.create_index('ix_trusted_devices_device_fingerprint', 'trusted_devices', ['device_fingerprint'], unique=False)
    if index_exists('trusted_devices', op.f('ix_trusted_devices_device_fingerprint')):
        op.drop_index(op.f('ix_trusted_devices_device_fingerprint'), table_name='trusted_devices')

    if table_exists('prescription_reminders'):
        if index_exists('prescription_reminders', 'idx_prescription_reminders_date'):
            op.drop_index('idx_prescription_reminders_date', table_name='prescription_reminders')
        if index_exists('prescription_reminders', 'idx_prescription_reminders_user'):
            op.drop_index('idx_prescription_reminders_user', table_name='prescription_reminders')
        if index_exists('prescription_reminders', op.f('ix_prescription_reminders_id')):
            op.drop_index(op.f('ix_prescription_reminders_id'), table_name='prescription_reminders')
        op.drop_table('prescription_reminders')

    if table_exists('prescriptions'):
        if index_exists('prescriptions', 'idx_prescriptions_user'):
            op.drop_index('idx_prescriptions_user', table_name='prescriptions')
        if index_exists('prescriptions', op.f('ix_prescriptions_id')):
            op.drop_index(op.f('ix_prescriptions_id'), table_name='prescriptions')
        op.drop_table('prescriptions')

    if table_exists('notifications'):
        if index_exists('notifications', 'idx_notifications_user'):
            op.drop_index('idx_notifications_user', table_name='notifications')
        if index_exists('notifications', op.f('ix_notifications_id')):
            op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
        op.drop_table('notifications')

    if table_exists('event_registrations'):
        if index_exists('event_registrations', 'idx_event_registrations_event'):
            op.drop_index('idx_event_registrations_event', table_name='event_registrations')
        if index_exists('event_registrations', op.f('ix_event_registrations_id')):
            op.drop_index(op.f('ix_event_registrations_id'), table_name='event_registrations')
        op.drop_table('event_registrations')

    if table_exists('comment_likes'):
        if index_exists('comment_likes', op.f('ix_comment_likes_id')):
            op.drop_index(op.f('ix_comment_likes_id'), table_name='comment_likes')
        op.drop_table('comment_likes')

    if table_exists('post_likes'):
        if index_exists('post_likes', op.f('ix_post_likes_id')):
            op.drop_index(op.f('ix_post_likes_id'), table_name='post_likes')
        op.drop_table('post_likes')

    if table_exists('post_comments'):
        if index_exists('post_comments', 'idx_post_comments_user'):
            op.drop_index('idx_post_comments_user', table_name='post_comments')
        if index_exists('post_comments', 'idx_post_comments_post'):
            op.drop_index('idx_post_comments_post', table_name='post_comments')
        if index_exists('post_comments', op.f('ix_post_comments_id')):
            op.drop_index(op.f('ix_post_comments_id'), table_name='post_comments')
        op.drop_table('post_comments')

    if table_exists('user_follows'):
        if index_exists('user_follows', 'idx_user_follows_following'):
            op.drop_index('idx_user_follows_following', table_name='user_follows')
        if index_exists('user_follows', 'idx_user_follows_follower'):
            op.drop_index('idx_user_follows_follower', table_name='user_follows')
        if index_exists('user_follows', op.f('ix_user_follows_id')):
            op.drop_index(op.f('ix_user_follows_id'), table_name='user_follows')
        op.drop_table('user_follows')

    if table_exists('community_events'):
        if index_exists('community_events', 'idx_community_events_organizer'):
            op.drop_index('idx_community_events_organizer', table_name='community_events')
        if index_exists('community_events', op.f('ix_community_events_id')):
            op.drop_index(op.f('ix_community_events_id'), table_name='community_events')
        op.drop_table('community_events')

    if table_exists('community_posts'):
        if index_exists('community_posts', 'idx_community_posts_user'):
            op.drop_index('idx_community_posts_user', table_name='community_posts')
        if index_exists('community_posts', op.f('ix_community_posts_id')):
            op.drop_index(op.f('ix_community_posts_id'), table_name='community_posts')
        op.drop_table('community_posts')

    if table_exists('user_profiles'):
        if index_exists('user_profiles', op.f('ix_user_profiles_id')):
            op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
        op.drop_table('user_profiles')

    if table_exists('chat_history'):
        if index_exists('chat_history', 'idx_chat_history_user'):
            op.drop_index('idx_chat_history_user', table_name='chat_history')
        if index_exists('chat_history', op.f('ix_chat_history_id')):
            op.drop_index(op.f('ix_chat_history_id'), table_name='chat_history')
        op.drop_table('chat_history')

    if table_exists('learning_progress'):
        if index_exists('learning_progress', 'idx_learning_progress_user'):
            op.drop_index('idx_learning_progress_user', table_name='learning_progress')
        if index_exists('learning_progress', op.f('ix_learning_progress_id')):
            op.drop_index(op.f('ix_learning_progress_id'), table_name='learning_progress')
        op.drop_table('learning_progress')
    # ### end Alembic commands ###
