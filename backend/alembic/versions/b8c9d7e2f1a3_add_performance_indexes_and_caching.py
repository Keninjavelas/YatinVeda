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
    tables = set(inspector.get_table_names())

    def table_exists(table: str) -> bool:
        return table in tables

    def has_columns(table: str, required_columns: list[str]) -> bool:
        if not table_exists(table):
            return False
        table_columns = {col['name'] for col in inspector.get_columns(table)}
        return all(col in table_columns for col in required_columns)
    
    def index_exists(table: str, name: str) -> bool:
        if not table_exists(table):
            return False
        indexes = inspector.get_indexes(table)
        return name in [idx.get('name') for idx in indexes]

    # User session and authentication queries
    if has_columns('refresh_tokens', ['user_id', 'expires_at']) and not index_exists('refresh_tokens', 'idx_refresh_tokens_user_expires'):
        op.create_index('idx_refresh_tokens_user_expires', 'refresh_tokens', 
                       ['user_id', 'expires_at'])
    
    if has_columns('refresh_tokens', ['revoked_at']) and not index_exists('refresh_tokens', 'idx_refresh_tokens_revoked'):
        op.create_index('idx_refresh_tokens_revoked', 'refresh_tokens', 
                       ['revoked_at'])
    
    # Community and social queries
    if has_columns('community_posts', ['created_at']) and not index_exists('community_posts', 'idx_community_posts_created_at'):
        op.create_index('idx_community_posts_created_at', 'community_posts', 
                       ['created_at'])
    
    if has_columns('community_posts', ['user_id', 'created_at']) and not index_exists('community_posts', 'idx_community_posts_user_created'):
        op.create_index('idx_community_posts_user_created', 'community_posts', 
                       ['user_id', 'created_at'])
    
    if has_columns('post_comments', ['post_id', 'created_at']) and not index_exists('post_comments', 'idx_post_comments_post_created'):
        op.create_index('idx_post_comments_post_created', 'post_comments', 
                       ['post_id', 'created_at'])
    
    # Prescription and chart queries
    if has_columns('prescriptions', ['user_id', 'created_at']) and not index_exists('prescriptions', 'idx_prescriptions_user_created'):
        op.create_index('idx_prescriptions_user_created', 'prescriptions', 
                       ['user_id', 'created_at'])
    
    if has_columns('charts', ['user_id', 'is_primary']) and not index_exists('charts', 'idx_charts_user_primary'):
        op.create_index('idx_charts_user_primary', 'charts', 
                       ['user_id', 'is_primary'])
    
    # Booking and payment queries
    if has_columns('guru_bookings', ['user_id', 'created_at']) and not index_exists('guru_bookings', 'idx_bookings_user_created'):
        op.create_index('idx_bookings_user_created', 'guru_bookings', 
                       ['user_id', 'created_at'])
    
    if has_columns('payments', ['user_id', 'created_at']) and not index_exists('payments', 'idx_payments_user_created'):
        op.create_index('idx_payments_user_created', 'payments', 
                       ['user_id', 'created_at'])
    
    # Notification queries
    if has_columns('notifications', ['user_id', 'is_read', 'created_at']) and not index_exists('notifications', 'idx_notifications_user_unread'):
        op.create_index('idx_notifications_user_unread', 'notifications', 
                       ['user_id', 'is_read', 'created_at'])
    
    # Wallet queries
    if has_columns('wallet_transactions', ['wallet_id', 'created_at']) and not index_exists('wallet_transactions', 'idx_wallet_transactions_wallet_created'):
        op.create_index('idx_wallet_transactions_wallet_created', 'wallet_transactions', 
                       ['wallet_id', 'created_at'])
    
    # MFA and security queries
    if has_columns('mfa_settings', ['user_id', 'is_enabled']) and not index_exists('mfa_settings', 'idx_mfa_settings_user_enabled'):
        op.create_index('idx_mfa_settings_user_enabled', 'mfa_settings', 
                       ['user_id', 'is_enabled'])
    
    if has_columns('trusted_devices', ['user_id', 'expires_at']) and not index_exists('trusted_devices', 'idx_trusted_devices_user_expires'):
        op.create_index('idx_trusted_devices_user_expires', 'trusted_devices', 
                       ['user_id', 'expires_at'])
    
    # Chat history queries
    if has_columns('chat_history', ['user_id', 'created_at']) and not index_exists('chat_history', 'idx_chat_history_user_created'):
        op.create_index('idx_chat_history_user_created', 'chat_history', 
                       ['user_id', 'created_at'])
    
    # Event queries
    if has_columns('community_events', ['event_date', 'is_public']) and not index_exists('community_events', 'idx_community_events_date_public'):
        op.create_index('idx_community_events_date_public', 'community_events', 
                       ['event_date', 'is_public'])
    
    if has_columns('event_registrations', ['user_id', 'created_at']) and not index_exists('event_registrations', 'idx_event_registrations_user_created'):
        op.create_index('idx_event_registrations_user_created', 'event_registrations', 
                       ['user_id', 'created_at'])
    
    # Learning progress queries
    if has_columns('learning_progress', ['user_id', 'completed', 'completed_at']) and not index_exists('learning_progress', 'idx_learning_progress_user_completed'):
        op.create_index('idx_learning_progress_user_completed', 'learning_progress', 
                       ['user_id', 'completed', 'completed_at'])


def downgrade() -> None:
    """Remove performance indexes"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    indexes_to_drop = [
        ('idx_refresh_tokens_user_expires', 'refresh_tokens'),
        ('idx_refresh_tokens_revoked', 'refresh_tokens'),
        ('idx_community_posts_created_at', 'community_posts'),
        ('idx_community_posts_user_created', 'community_posts'),
        ('idx_post_comments_post_created', 'post_comments'),
        ('idx_prescriptions_user_created', 'prescriptions'),
        ('idx_charts_user_primary', 'charts'),
        ('idx_bookings_user_created', 'guru_bookings'),
        ('idx_payments_user_created', 'payments'),
        ('idx_notifications_user_unread', 'notifications'),
        ('idx_wallet_transactions_wallet_created', 'wallet_transactions'),
        ('idx_mfa_settings_user_enabled', 'mfa_settings'),
        ('idx_trusted_devices_user_expires', 'trusted_devices'),
        ('idx_chat_history_user_created', 'chat_history'),
        ('idx_community_events_date_public', 'community_events'),
        ('idx_event_registrations_user_created', 'event_registrations'),
        ('idx_learning_progress_user_completed', 'learning_progress'),
    ]

    for index_name, table_name in indexes_to_drop:
        if table_name not in tables:
            continue
        existing = {idx.get('name') for idx in inspector.get_indexes(table_name)}
        if index_name in existing:
            op.drop_index(index_name, table_name=table_name)