"""add_dual_user_registration_support

Revision ID: 57d2c0670675
Revises: 0ed3d82eb5ae
Create Date: 2025-12-28 21:58:23.749482

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57d2c0670675'
down_revision: Union[str, Sequence[str], None] = '0ed3d82eb5ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add dual user registration support with role and verification status fields."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    def column_exists(table: str, column: str) -> bool:
        columns = [col['name'] for col in inspector.get_columns(table)]
        return column in columns
    
    def index_exists(table: str, name: str) -> bool:
        return any(idx.get('name') == name for idx in inspector.get_indexes(table))
    
    # Add role and verification_status columns to users table
    if not column_exists('users', 'role'):
        op.add_column('users', sa.Column('role', sa.String(20), nullable=False, server_default='user'))
    
    if not column_exists('users', 'verification_status'):
        op.add_column('users', sa.Column('verification_status', sa.String(30), nullable=False, server_default='active'))
    
    # Use batch mode for SQLite to add foreign key constraints to gurus table
    with op.batch_alter_table('gurus', schema=None) as batch_op:
        # Add user_id foreign key to gurus table if it doesn't exist
        if not column_exists('gurus', 'user_id'):
            batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_gurus_user_id', 'users', ['user_id'], ['id'])
            batch_op.create_unique_constraint('uq_gurus_user_id', ['user_id'])
        
        # Add verification fields to gurus table
        if not column_exists('gurus', 'certification_details'):
            batch_op.add_column(sa.Column('certification_details', sa.JSON(), nullable=True))
        
        if not column_exists('gurus', 'verification_documents'):
            batch_op.add_column(sa.Column('verification_documents', sa.JSON(), nullable=True))
        
        if not column_exists('gurus', 'verified_at'):
            batch_op.add_column(sa.Column('verified_at', sa.DateTime(), nullable=True))
        
        if not column_exists('gurus', 'verified_by'):
            batch_op.add_column(sa.Column('verified_by', sa.Integer(), nullable=True))
            batch_op.create_foreign_key('fk_gurus_verified_by', 'users', ['verified_by'], ['id'])
    
    # Create performance indexes
    if not index_exists('users', 'idx_users_role'):
        op.create_index('idx_users_role', 'users', ['role'])
    
    if not index_exists('users', 'idx_users_verification_status'):
        op.create_index('idx_users_verification_status', 'users', ['verification_status'])
    
    if not index_exists('gurus', 'idx_gurus_user_id'):
        op.create_index('idx_gurus_user_id', 'gurus', ['user_id'])
    
    if not index_exists('gurus', 'idx_gurus_verified_by'):
        op.create_index('idx_gurus_verified_by', 'gurus', ['verified_by'])


def downgrade() -> None:
    """Remove dual user registration support."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    def column_exists(table: str, column: str) -> bool:
        columns = [col['name'] for col in inspector.get_columns(table)]
        return column in columns
    
    def index_exists(table: str, name: str) -> bool:
        return any(idx.get('name') == name for idx in inspector.get_indexes(table))
    
    # Drop indexes
    if index_exists('gurus', 'idx_gurus_verified_by'):
        op.drop_index('idx_gurus_verified_by', table_name='gurus')
    
    if index_exists('gurus', 'idx_gurus_user_id'):
        op.drop_index('idx_gurus_user_id', table_name='gurus')
    
    if index_exists('users', 'idx_users_verification_status'):
        op.drop_index('idx_users_verification_status', table_name='users')
    
    if index_exists('users', 'idx_users_role'):
        op.drop_index('idx_users_role', table_name='users')
    
    # Use batch mode for SQLite to drop foreign key constraints
    with op.batch_alter_table('gurus', schema=None) as batch_op:
        # Drop foreign key constraints
        try:
            batch_op.drop_constraint('fk_gurus_verified_by', type_='foreignkey')
        except:
            pass
        
        try:
            batch_op.drop_constraint('fk_gurus_user_id', type_='foreignkey')
        except:
            pass
        
        try:
            batch_op.drop_constraint('uq_gurus_user_id', type_='unique')
        except:
            pass
        
        # Drop columns from gurus table
        if column_exists('gurus', 'verified_by'):
            batch_op.drop_column('verified_by')
        
        if column_exists('gurus', 'verified_at'):
            batch_op.drop_column('verified_at')
        
        if column_exists('gurus', 'verification_documents'):
            batch_op.drop_column('verification_documents')
        
        if column_exists('gurus', 'certification_details'):
            batch_op.drop_column('certification_details')
        
        if column_exists('gurus', 'user_id'):
            batch_op.drop_column('user_id')
    
    # Drop columns from users table
    if column_exists('users', 'verification_status'):
        op.drop_column('users', 'verification_status')
    
    if column_exists('users', 'role'):
        op.drop_column('users', 'role')
