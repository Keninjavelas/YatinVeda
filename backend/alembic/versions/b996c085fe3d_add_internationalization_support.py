"""add_internationalization_support

Revision ID: b996c085fe3d
Revises: c1d2e3f4a5b6
Create Date: 2026-03-10 15:57:02.118024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b996c085fe3d'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add internationalization support: multi-currency, timezones, localization."""
    
    # Add internationalization fields to users table
    op.add_column('users', sa.Column('timezone', sa.String(50), nullable=True, server_default='UTC'))
    op.add_column('users', sa.Column('preferred_currency', sa.String(3), nullable=True, server_default='USD'))
    op.add_column('users', sa.Column('country', sa.String(2), nullable=True))  # ISO 3166-1 alpha-2
    op.add_column('users', sa.Column('language_preference', sa.String(10), nullable=True, server_default='en'))
    
    # Add currency fields to payments table
    op.add_column('payments', sa.Column('currency', sa.String(3), nullable=False, server_default='INR'))
    op.add_column('payments', sa.Column('exchange_rate', sa.Numeric(10, 4), nullable=True))
    op.add_column('payments', sa.Column('base_currency', sa.String(3), nullable=True, server_default='INR'))
    
    # Add currency fields to guru_bookings table
    op.add_column('guru_bookings', sa.Column('currency', sa.String(3), nullable=False, server_default='INR'))
    op.add_column('guru_bookings', sa.Column('exchange_rate', sa.Numeric(10, 4), nullable=True))
    
    # Add currency fields to refunds table
    op.add_column('refunds', sa.Column('currency', sa.String(3), nullable=False, server_default='INR'))
    
    # Create exchange_rates table for currency conversion
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('base_currency', sa.String(3), nullable=False, index=True),
        sa.Column('target_currency', sa.String(3), nullable=False, index=True),
        sa.Column('rate', sa.Numeric(10, 6), nullable=False),
        sa.Column('provider', sa.String(50), nullable=True),  # e.g., 'openexchangerates', 'manual'
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create composite index for efficient lookups
    op.create_index(
        'idx_exchange_rates_currencies',
        'exchange_rates',
        ['base_currency', 'target_currency']
    )
    
    # Create legal_consent table for GDPR compliance
    op.create_table(
        'legal_consent',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('consent_type', sa.String(50), nullable=False),  # 'terms', 'privacy', 'cookies', 'marketing'
        sa.Column('consent_version', sa.String(20), nullable=False),  # e.g., '1.0.0'
        sa.Column('consented_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create cookie_preferences table
    op.create_table(
        'cookie_preferences',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True, nullable=False, index=True),
        sa.Column('essential_cookies', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('functional_cookies', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('analytics_cookies', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('marketing_cookies', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Create data_export_requests table for GDPR
    op.create_table(
        'data_export_requests',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('request_type', sa.String(20), nullable=False),  # 'export' or 'deletion'
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),  # 'pending', 'processing', 'completed', 'failed'
        sa.Column('file_url', sa.String(500), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),  # Export link expiration (30 days)
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Add indexes for performance
    op.create_index('idx_users_country', 'users', ['country'])
    op.create_index('idx_users_timezone', 'users', ['timezone'])
    op.create_index('idx_users_preferred_currency', 'users', ['preferred_currency'])
    op.create_index('idx_payments_currency', 'payments', ['currency'])
    op.create_index('idx_guru_bookings_currency', 'guru_bookings', ['currency'])
    op.create_index('idx_legal_consent_user_type', 'legal_consent', ['user_id', 'consent_type'])
    op.create_index('idx_data_export_requests_status', 'data_export_requests', ['status'])


def downgrade() -> None:
    """Remove internationalization support."""
    
    # Drop indexes
    op.drop_index('idx_data_export_requests_status', 'data_export_requests')
    op.drop_index('idx_legal_consent_user_type', 'legal_consent')
    op.drop_index('idx_guru_bookings_currency', 'guru_bookings')
    op.drop_index('idx_payments_currency', 'payments')
    op.drop_index('idx_users_preferred_currency', 'users')
    op.drop_index('idx_users_timezone', 'users')
    op.drop_index('idx_users_country', 'users')
    
    # Drop tables
    op.drop_table('data_export_requests')
    op.drop_table('cookie_preferences')
    op.drop_table('legal_consent')
    op.drop_index('idx_exchange_rates_currencies', 'exchange_rates')
    op.drop_table('exchange_rates')
    
    # Remove columns from refunds
    op.drop_column('refunds', 'currency')
    
    # Remove columns from guru_bookings
    op.drop_column('guru_bookings', 'exchange_rate')
    op.drop_column('guru_bookings', 'currency')
    
    # Remove columns from payments
    op.drop_column('payments', 'base_currency')
    op.drop_column('payments', 'exchange_rate')
    op.drop_column('payments', 'currency')
    
    # Remove columns from users
    op.drop_column('users', 'language_preference')
    op.drop_column('users', 'country')
    op.drop_column('users', 'preferred_currency')
    op.drop_column('users', 'timezone')
