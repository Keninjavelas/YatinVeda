"""add_performance_indexes_and_caching

Revision ID: b8c9d7e2f1a3
Revises: 499ef1ea01ab
Create Date: 2026-01-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c9d7e2f1a3'
down_revision: Union[str, None] = '499ef1ea01ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes for high-traffic queries and scalability"""
    
    # Performance indexes for scaling - adding them step by step for safety
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    def index_exists(table: str, name: str) -> bool:
        indexes = inspector.get_indexes(table)
        return name in [idx.get('name') for idx in indexes]

    # User session and authentication queries
    if not index_exists('refresh_tokens', 'idx_refresh_tokens_user_expires'):
        op.create_index('idx_refresh_tokens_user_expires', 'refresh_tokens', 
                       ['user_id', 'expires_at'])
    
    if not index_exists('refresh_tokens', 'idx_refresh_tokens_revoked'):
        op.create_index('idx_refresh_tokens_revoked', 'refresh_tokens', 
                       ['revoked_at'])
    
    # Community and social queries
    if not index_exists('community_posts', 'idx_community_posts_created_at'):
        op.create_index('idx_community_posts_created_at', 'community_posts', 
                       ['created_at'])
    
    if not index_exists('community_posts', 'idx_community_posts_user_created'):
        op.create_index('idx_community_posts_user_created', 'community_posts', 
                       ['user_id', 'created_at'])
    
    if not index_exists('post_comments', 'idx_post_comments_post_created'):
        op.create_index('idx_post_comments_post_created', 'post_comments', 
                       ['post_id', 'created_at'])
    
    # Prescription and chart queries
    if not index_exists('prescriptions', 'idx_prescriptions_user_created'):
        op.create_index('idx_prescriptions_user_created', 'prescriptions', 
                       ['user_id', 'created_at'])
    
    if not index_exists('charts', 'idx_charts_user_primary'):
        op.create_index('idx_charts_user_primary', 'charts', 
                       ['user_id', 'is_primary'])
    
    # Booking and payment queries
    if not index_exists('guru_bookings', 'idx_bookings_user_created'):
        op.create_index('idx_bookings_user_created', 'guru_bookings', 
                       ['user_id', 'created_at'])
    
    if not index_exists('payments', 'idx_payments_user_created'):
        op.create_index('idx_payments_user_created', 'payments', 
                       ['user_id', 'created_at'])
    
    # Notification queries
    if not index_exists('notifications', 'idx_notifications_user_unread'):
        op.create_index('idx_notifications_user_unread', 'notifications', 
                       ['user_id', 'is_read', 'created_at'])
    
    # Wallet queries
    if not index_exists('wallet_transactions', 'idx_wallet_transactions_wallet_created'):
        op.create_index('idx_wallet_transactions_wallet_created', 'wallet_transactions', 
                       ['wallet_id', 'created_at'])
    
    # MFA and security queries
    if not index_exists('mfa_settings', 'idx_mfa_settings_user_enabled'):
        op.create_index('idx_mfa_settings_user_enabled', 'mfa_settings', 
                       ['user_id', 'is_enabled'])
    
    if not index_exists('trusted_devices', 'idx_trusted_devices_user_expires'):
        op.create_index('idx_trusted_devices_user_expires', 'trusted_devices', 
                       ['user_id', 'expires_at'])
    
    # Chat history queries
    if not index_exists('chat_history', 'idx_chat_history_user_created'):
        op.create_index('idx_chat_history_user_created', 'chat_history', 
                       ['user_id', 'created_at'])
    
    # Event queries
    if not index_exists('community_events', 'idx_community_events_date_public'):
        op.create_index('idx_community_events_date_public', 'community_events', 
                       ['event_date', 'is_public'])
    
    if not index_exists('event_registrations', 'idx_event_registrations_user_created'):
        op.create_index('idx_event_registrations_user_created', 'event_registrations', 
                       ['user_id', 'created_at'])
    
    # Learning progress queries
    if not index_exists('learning_progress', 'idx_learning_progress_user_completed'):
        op.create_index('idx_learning_progress_user_completed', 'learning_progress', 
                       ['user_id', 'completed', 'completed_at'])


def downgrade() -> None:
    """Remove performance indexes"""
    # Drop all indexes in reverse order
    indexes_to_drop = [
        'idx_refresh_tokens_user_expires',
        'idx_refresh_tokens_revoked',
        'idx_community_posts_created_at',
        'idx_community_posts_user_created',
        'idx_post_comments_post_created',
        'idx_prescriptions_user_created',
        'idx_charts_user_primary',
        'idx_bookings_user_created',
        'idx_payments_user_created',
        'idx_notifications_user_unread',
        'idx_wallet_transactions_wallet_created',
        'idx_mfa_settings_user_enabled',
        'idx_trusted_devices_user_expires',
        'idx_chat_history_user_created',
        'idx_community_events_date_public',
        'idx_event_registrations_user_created',
        'idx_learning_progress_user_completed'
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, table_name=index_name.split('_')[1])
        except Exception:
            # Index might not exist, continue
            pass