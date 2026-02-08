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
    
    # User queries - email/username lookups (already indexed in model, but ensuring)
    # These are defined in the User model, so we skip them here
    
    # Guru queries - search by specialization, active status, rating
    op.create_index('idx_gurus_is_active', 'gurus', ['is_active'])
    op.create_index('idx_gurus_rating', 'gurus', ['rating'])
    
    # Booking queries - filter by user, guru, status, dates
    op.create_index('idx_bookings_status', 'guru_bookings', ['status'])
    op.create_index('idx_bookings_payment_status', 'guru_bookings', ['payment_status'])
    op.create_index('idx_bookings_booking_date', 'guru_bookings', ['booking_date'])
    op.create_index('idx_bookings_user_guru', 'guru_bookings', ['user_id', 'guru_id'])
    
    # Availability queries - filter by guru, date, availability
    op.create_index('idx_availability_guru_date', 'guru_availability', ['guru_id', 'date'])
    op.create_index('idx_availability_is_available', 'guru_availability', ['is_available'])
    
    # Payment queries - lookup by order_id, payment_id, status
    op.create_index('idx_payments_status', 'payments', ['status'])
    op.create_index('idx_payments_user_id', 'payments', ['user_id'])
    op.create_index('idx_payments_created_at', 'payments', ['created_at'])
    
    # Wallet queries - lookup by user
    # user_id already has unique constraint, which creates index
    
    # Wallet transaction queries - filter by wallet, type, date
    op.create_index('idx_wallet_txn_wallet_id', 'wallet_transactions', ['wallet_id'])
    op.create_index('idx_wallet_txn_type', 'wallet_transactions', ['transaction_type'])
    op.create_index('idx_wallet_txn_created_at', 'wallet_transactions', ['created_at'])
    
    # Chart queries - filter by user, public status, primary
    op.create_index('idx_charts_user_id', 'charts', ['user_id'])
    op.create_index('idx_charts_is_public', 'charts', ['is_public'])
    op.create_index('idx_charts_is_primary', 'charts', ['is_primary'])
    
    # Community post queries - filter by user, public, created date, tags
    op.create_index('idx_posts_user_id', 'community_posts', ['user_id'])
    op.create_index('idx_posts_is_public', 'community_posts', ['is_public'])
    op.create_index('idx_posts_created_at', 'community_posts', ['created_at'])
    op.create_index('idx_posts_post_type', 'community_posts', ['post_type'])
    
    # Comment queries - filter by post, user, parent
    op.create_index('idx_comments_post_id', 'post_comments', ['post_id'])
    op.create_index('idx_comments_user_id', 'post_comments', ['user_id'])
    op.create_index('idx_comments_parent_id', 'post_comments', ['parent_comment_id'])
    op.create_index('idx_comments_created_at', 'post_comments', ['created_at'])
    
    # Like queries - lookup by post/comment and user
    op.create_index('idx_post_likes_post_user', 'post_likes', ['post_id', 'user_id'])
    op.create_index('idx_comment_likes_comment_user', 'comment_likes', ['comment_id', 'user_id'])
    
    # Follow queries - lookup followers/following
    op.create_index('idx_follows_follower', 'user_follows', ['follower_id'])
    op.create_index('idx_follows_following', 'user_follows', ['following_id'])
    op.create_index('idx_follows_pair', 'user_follows', ['follower_id', 'following_id'])
    
    # Event queries - filter by organizer, date, public status
    op.create_index('idx_events_organizer', 'community_events', ['organizer_id'])
    op.create_index('idx_events_event_date', 'community_events', ['event_date'])
    op.create_index('idx_events_is_public', 'community_events', ['is_public'])
    op.create_index('idx_events_event_type', 'community_events', ['event_type'])
    
    # Event registration queries - lookup by event and user
    op.create_index('idx_event_reg_event_user', 'event_registrations', ['event_id', 'user_id'])
    op.create_index('idx_event_reg_status', 'event_registrations', ['status'])
    
    # Notification queries - filter by user, read status, type
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_type', 'notifications', ['notification_type'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    
    # Prescription queries - lookup by booking, guru, user
    op.create_index('idx_prescriptions_booking', 'prescriptions', ['booking_id'])
    op.create_index('idx_prescriptions_guru', 'prescriptions', ['guru_id'])
    op.create_index('idx_prescriptions_user', 'prescriptions', ['user_id'])
    
    # Prescription reminder queries - filter by prescription, user, sent status, date
    op.create_index('idx_reminders_prescription', 'prescription_reminders', ['prescription_id'])
    op.create_index('idx_reminders_user', 'prescription_reminders', ['user_id'])
    op.create_index('idx_reminders_is_sent', 'prescription_reminders', ['is_sent'])
    op.create_index('idx_reminders_reminder_date', 'prescription_reminders', ['reminder_date'])
    
    # Chat history queries - filter by user, date
    op.create_index('idx_chat_user_id', 'chat_history', ['user_id'])
    op.create_index('idx_chat_created_at', 'chat_history', ['created_at'])


def downgrade() -> None:
    """Remove performance indexes."""
    
    # Drop all indexes in reverse order
    op.drop_index('idx_chat_created_at', 'chat_history')
    op.drop_index('idx_chat_user_id', 'chat_history')
    
    op.drop_index('idx_reminders_reminder_date', 'prescription_reminders')
    op.drop_index('idx_reminders_is_sent', 'prescription_reminders')
    op.drop_index('idx_reminders_user', 'prescription_reminders')
    op.drop_index('idx_reminders_prescription', 'prescription_reminders')
    
    op.drop_index('idx_prescriptions_user', 'prescriptions')
    op.drop_index('idx_prescriptions_guru', 'prescriptions')
    op.drop_index('idx_prescriptions_booking', 'prescriptions')
    
    op.drop_index('idx_notifications_created_at', 'notifications')
    op.drop_index('idx_notifications_type', 'notifications')
    op.drop_index('idx_notifications_is_read', 'notifications')
    op.drop_index('idx_notifications_user_id', 'notifications')
    
    op.drop_index('idx_event_reg_status', 'event_registrations')
    op.drop_index('idx_event_reg_event_user', 'event_registrations')
    
    op.drop_index('idx_events_event_type', 'community_events')
    op.drop_index('idx_events_is_public', 'community_events')
    op.drop_index('idx_events_event_date', 'community_events')
    op.drop_index('idx_events_organizer', 'community_events')
    
    op.drop_index('idx_follows_pair', 'user_follows')
    op.drop_index('idx_follows_following', 'user_follows')
    op.drop_index('idx_follows_follower', 'user_follows')
    
    op.drop_index('idx_comment_likes_comment_user', 'comment_likes')
    op.drop_index('idx_post_likes_post_user', 'post_likes')
    
    op.drop_index('idx_comments_created_at', 'post_comments')
    op.drop_index('idx_comments_parent_id', 'post_comments')
    op.drop_index('idx_comments_user_id', 'post_comments')
    op.drop_index('idx_comments_post_id', 'post_comments')
    
    op.drop_index('idx_posts_post_type', 'community_posts')
    op.drop_index('idx_posts_created_at', 'community_posts')
    op.drop_index('idx_posts_is_public', 'community_posts')
    op.drop_index('idx_posts_user_id', 'community_posts')
    
    op.drop_index('idx_charts_is_primary', 'charts')
    op.drop_index('idx_charts_is_public', 'charts')
    op.drop_index('idx_charts_user_id', 'charts')
    
    op.drop_index('idx_wallet_txn_created_at', 'wallet_transactions')
    op.drop_index('idx_wallet_txn_type', 'wallet_transactions')
    op.drop_index('idx_wallet_txn_wallet_id', 'wallet_transactions')
    
    op.drop_index('idx_payments_created_at', 'payments')
    op.drop_index('idx_payments_user_id', 'payments')
    op.drop_index('idx_payments_status', 'payments')
    
    op.drop_index('idx_availability_is_available', 'guru_availability')
    op.drop_index('idx_availability_guru_date', 'guru_availability')
    
    op.drop_index('idx_bookings_user_guru', 'guru_bookings')
    op.drop_index('idx_bookings_booking_date', 'guru_bookings')
    op.drop_index('idx_bookings_payment_status', 'guru_bookings')
    op.drop_index('idx_bookings_status', 'guru_bookings')
    
    op.drop_index('idx_gurus_rating', 'gurus')
    op.drop_index('idx_gurus_is_active', 'gurus')
