"""add_database_indexes

Revision ID: 034100221389
Revises: 402a80e4d60c
Create Date: 2025-12-05 18:46:06.291527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '034100221389'
down_revision: Union[str, Sequence[str], None] = '402a80e4d60c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes to frequently queried columns."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    indexes_to_create = [
        ('idx_gurus_is_active', 'gurus', ['is_active']),
        ('idx_gurus_rating', 'gurus', ['rating']),
        ('idx_bookings_status', 'guru_bookings', ['status']),
        ('idx_bookings_payment_status', 'guru_bookings', ['payment_status']),
        ('idx_bookings_booking_date', 'guru_bookings', ['booking_date']),
        ('idx_bookings_user_guru', 'guru_bookings', ['user_id', 'guru_id']),
        ('idx_availability_guru_date', 'guru_availability', ['guru_id', 'date']),
        ('idx_availability_is_available', 'guru_availability', ['is_available']),
        ('idx_payments_status', 'payments', ['status']),
        ('idx_payments_user_id', 'payments', ['user_id']),
        ('idx_payments_created_at', 'payments', ['created_at']),
        ('idx_wallet_txn_wallet_id', 'wallet_transactions', ['wallet_id']),
        ('idx_wallet_txn_type', 'wallet_transactions', ['transaction_type']),
        ('idx_wallet_txn_created_at', 'wallet_transactions', ['created_at']),
        ('idx_charts_user_id', 'charts', ['user_id']),
        ('idx_charts_is_public', 'charts', ['is_public']),
        ('idx_charts_is_primary', 'charts', ['is_primary']),
        ('idx_posts_user_id', 'community_posts', ['user_id']),
        ('idx_posts_is_public', 'community_posts', ['is_public']),
        ('idx_posts_created_at', 'community_posts', ['created_at']),
        ('idx_posts_post_type', 'community_posts', ['post_type']),
        ('idx_comments_post_id', 'post_comments', ['post_id']),
        ('idx_comments_user_id', 'post_comments', ['user_id']),
        ('idx_comments_parent_id', 'post_comments', ['parent_comment_id']),
        ('idx_comments_created_at', 'post_comments', ['created_at']),
        ('idx_post_likes_post_user', 'post_likes', ['post_id', 'user_id']),
        ('idx_comment_likes_comment_user', 'comment_likes', ['comment_id', 'user_id']),
        ('idx_follows_follower', 'user_follows', ['follower_id']),
        ('idx_follows_following', 'user_follows', ['following_id']),
        ('idx_follows_pair', 'user_follows', ['follower_id', 'following_id']),
        ('idx_events_organizer', 'community_events', ['organizer_id']),
        ('idx_events_event_date', 'community_events', ['event_date']),
        ('idx_events_is_public', 'community_events', ['is_public']),
        ('idx_events_event_type', 'community_events', ['event_type']),
        ('idx_event_reg_event_user', 'event_registrations', ['event_id', 'user_id']),
        ('idx_event_reg_status', 'event_registrations', ['status']),
        ('idx_notifications_user_id', 'notifications', ['user_id']),
        ('idx_notifications_is_read', 'notifications', ['is_read']),
        ('idx_notifications_type', 'notifications', ['notification_type']),
        ('idx_notifications_created_at', 'notifications', ['created_at']),
        ('idx_prescriptions_booking', 'prescriptions', ['booking_id']),
        ('idx_prescriptions_guru', 'prescriptions', ['guru_id']),
        ('idx_prescriptions_user', 'prescriptions', ['user_id']),
        ('idx_reminders_prescription', 'prescription_reminders', ['prescription_id']),
        ('idx_reminders_user', 'prescription_reminders', ['user_id']),
        ('idx_reminders_is_sent', 'prescription_reminders', ['is_sent']),
        ('idx_reminders_reminder_date', 'prescription_reminders', ['reminder_date']),
        ('idx_chat_user_id', 'chat_history', ['user_id']),
        ('idx_chat_created_at', 'chat_history', ['created_at']),
    ]

    for name, table, columns in indexes_to_create:
        if table not in tables:
            continue
        existing = {idx.get('name') for idx in inspector.get_indexes(table)}
        if name not in existing:
            op.create_index(name, table, columns)


def downgrade() -> None:
    """Remove performance indexes."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    indexes_to_drop = [
        ('idx_chat_created_at', 'chat_history'),
        ('idx_chat_user_id', 'chat_history'),
        ('idx_reminders_reminder_date', 'prescription_reminders'),
        ('idx_reminders_is_sent', 'prescription_reminders'),
        ('idx_reminders_user', 'prescription_reminders'),
        ('idx_reminders_prescription', 'prescription_reminders'),
        ('idx_prescriptions_user', 'prescriptions'),
        ('idx_prescriptions_guru', 'prescriptions'),
        ('idx_prescriptions_booking', 'prescriptions'),
        ('idx_notifications_created_at', 'notifications'),
        ('idx_notifications_type', 'notifications'),
        ('idx_notifications_is_read', 'notifications'),
        ('idx_notifications_user_id', 'notifications'),
        ('idx_event_reg_status', 'event_registrations'),
        ('idx_event_reg_event_user', 'event_registrations'),
        ('idx_events_event_type', 'community_events'),
        ('idx_events_is_public', 'community_events'),
        ('idx_events_event_date', 'community_events'),
        ('idx_events_organizer', 'community_events'),
        ('idx_follows_pair', 'user_follows'),
        ('idx_follows_following', 'user_follows'),
        ('idx_follows_follower', 'user_follows'),
        ('idx_comment_likes_comment_user', 'comment_likes'),
        ('idx_post_likes_post_user', 'post_likes'),
        ('idx_comments_created_at', 'post_comments'),
        ('idx_comments_parent_id', 'post_comments'),
        ('idx_comments_user_id', 'post_comments'),
        ('idx_comments_post_id', 'post_comments'),
        ('idx_posts_post_type', 'community_posts'),
        ('idx_posts_created_at', 'community_posts'),
        ('idx_posts_is_public', 'community_posts'),
        ('idx_posts_user_id', 'community_posts'),
        ('idx_charts_is_primary', 'charts'),
        ('idx_charts_is_public', 'charts'),
        ('idx_charts_user_id', 'charts'),
        ('idx_wallet_txn_created_at', 'wallet_transactions'),
        ('idx_wallet_txn_type', 'wallet_transactions'),
        ('idx_wallet_txn_wallet_id', 'wallet_transactions'),
        ('idx_payments_created_at', 'payments'),
        ('idx_payments_user_id', 'payments'),
        ('idx_payments_status', 'payments'),
        ('idx_availability_is_available', 'guru_availability'),
        ('idx_availability_guru_date', 'guru_availability'),
        ('idx_bookings_user_guru', 'guru_bookings'),
        ('idx_bookings_booking_date', 'guru_bookings'),
        ('idx_bookings_payment_status', 'guru_bookings'),
        ('idx_bookings_status', 'guru_bookings'),
        ('idx_gurus_rating', 'gurus'),
        ('idx_gurus_is_active', 'gurus'),
    ]

    for name, table in indexes_to_drop:
        if table not in tables:
            continue
        existing = {idx.get('name') for idx in inspector.get_indexes(table)}
        if name in existing:
            op.drop_index(name, table)
