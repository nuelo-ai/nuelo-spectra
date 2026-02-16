"""add admin portal tables and user fields

Revision ID: dfe836ff84e9
Revises: c3bf6a1e6238
Create Date: 2026-02-16 11:25:08.662160

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dfe836ff84e9'
down_revision: Union[str, Sequence[str], None] = 'c3bf6a1e6238'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add admin portal tables and user fields.

    Three-step pattern:
    1. Add columns to users table (with server_default for existing rows)
    2. Create 5 new tables
    3. Backfill user_credits for existing users
    """
    # Step 1: Add columns to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('users', sa.Column('user_class', sa.String(length=20), server_default='free', nullable=False))

    # Step 2: Create 5 new tables
    op.create_table('platform_settings',
    sa.Column('key', sa.String(length=100), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_by', sa.Uuid(), nullable=True),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('admin_audit_log',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('admin_id', sa.Uuid(), nullable=True),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('target_type', sa.String(length=50), nullable=False),
    sa.Column('target_id', sa.String(length=255), nullable=True),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_audit_log_action'), 'admin_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_admin_audit_log_created_at'), 'admin_audit_log', ['created_at'], unique=False)
    op.create_table('credit_transactions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('amount', sa.NUMERIC(precision=10, scale=1), nullable=False),
    sa.Column('balance_after', sa.NUMERIC(precision=10, scale=1), nullable=False),
    sa.Column('transaction_type', sa.String(length=30), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('admin_id', sa.Uuid(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_transactions_created_at'), 'credit_transactions', ['created_at'], unique=False)
    op.create_index(op.f('ix_credit_transactions_user_id'), 'credit_transactions', ['user_id'], unique=False)
    op.create_table('invitations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('token_hash', sa.String(length=128), nullable=False),
    sa.Column('invited_by', sa.Uuid(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invitations_email'), 'invitations', ['email'], unique=False)
    op.create_index(op.f('ix_invitations_token_hash'), 'invitations', ['token_hash'], unique=True)
    op.create_table('user_credits',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('balance', sa.NUMERIC(precision=10, scale=1), nullable=False),
    sa.Column('last_reset_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_credits_user_id'), 'user_credits', ['user_id'], unique=True)

    # Step 3: Backfill user_credits for existing users
    op.execute("""
        INSERT INTO user_credits (id, user_id, balance, created_at)
        SELECT gen_random_uuid(), id, 0, NOW()
        FROM users
        WHERE id NOT IN (SELECT user_id FROM user_credits)
    """)


def downgrade() -> None:
    """Downgrade schema: remove admin portal tables and user fields."""
    # Drop tables in reverse dependency order
    op.drop_index(op.f('ix_user_credits_user_id'), table_name='user_credits')
    op.drop_table('user_credits')
    op.drop_index(op.f('ix_invitations_token_hash'), table_name='invitations')
    op.drop_index(op.f('ix_invitations_email'), table_name='invitations')
    op.drop_table('invitations')
    op.drop_index(op.f('ix_credit_transactions_user_id'), table_name='credit_transactions')
    op.drop_index(op.f('ix_credit_transactions_created_at'), table_name='credit_transactions')
    op.drop_table('credit_transactions')
    op.drop_index(op.f('ix_admin_audit_log_created_at'), table_name='admin_audit_log')
    op.drop_index(op.f('ix_admin_audit_log_action'), table_name='admin_audit_log')
    op.drop_table('admin_audit_log')
    op.drop_table('platform_settings')

    # Drop user columns
    op.drop_column('users', 'user_class')
    op.drop_column('users', 'is_admin')
