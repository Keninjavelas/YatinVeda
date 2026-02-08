"""add_mfa_tables

Revision ID: 84b054cffce6
Revises: 445283214546
Create Date: 2025-12-05 21:43:22.658027

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84b054cffce6'
down_revision: Union[str, Sequence[str], None] = '445283214546'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create mfa_settings table
    op.create_table(
        'mfa_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('secret_key', sa.String(), nullable=False),
        sa.Column('backup_codes_hash', sa.Text(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_mfa_settings_id'), 'mfa_settings', ['id'], unique=False)
    op.create_index(op.f('ix_mfa_settings_user_id'), 'mfa_settings', ['user_id'], unique=False)

    # Create trusted_devices table
    op.create_table(
        'trusted_devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mfa_settings_id', sa.Integer(), nullable=False),
        sa.Column('device_fingerprint', sa.String(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('trusted_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['mfa_settings_id'], ['mfa_settings.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_fingerprint')
    )
    op.create_index(op.f('ix_trusted_devices_device_fingerprint'), 'trusted_devices', ['device_fingerprint'], unique=False)
    op.create_index(op.f('ix_trusted_devices_id'), 'trusted_devices', ['id'], unique=False)
    op.create_index(op.f('ix_trusted_devices_mfa_settings_id'), 'trusted_devices', ['mfa_settings_id'], unique=False)

    # Create mfa_backup_codes table
    op.create_table(
        'mfa_backup_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('code_hash', sa.String(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mfa_backup_codes_code_hash'), 'mfa_backup_codes', ['code_hash'], unique=False)
    op.create_index(op.f('ix_mfa_backup_codes_id'), 'mfa_backup_codes', ['id'], unique=False)
    op.create_index(op.f('ix_mfa_backup_codes_user_id'), 'mfa_backup_codes', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mfa_backup_codes_user_id'), table_name='mfa_backup_codes')
    op.drop_index(op.f('ix_mfa_backup_codes_id'), table_name='mfa_backup_codes')
    op.drop_index(op.f('ix_mfa_backup_codes_code_hash'), table_name='mfa_backup_codes')
    op.drop_table('mfa_backup_codes')
    
    op.drop_index(op.f('ix_trusted_devices_mfa_settings_id'), table_name='trusted_devices')
    op.drop_index(op.f('ix_trusted_devices_id'), table_name='trusted_devices')
    op.drop_index(op.f('ix_trusted_devices_device_fingerprint'), table_name='trusted_devices')
    op.drop_table('trusted_devices')
    
    op.drop_index(op.f('ix_mfa_settings_user_id'), table_name='mfa_settings')
    op.drop_index(op.f('ix_mfa_settings_id'), table_name='mfa_settings')
    op.drop_table('mfa_settings')
