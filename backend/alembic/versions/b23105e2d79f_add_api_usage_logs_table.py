"""add api_usage_logs table

Revision ID: b23105e2d79f
Revises: 4ee63775d127
Create Date: 2026-02-24 11:30:19.253414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b23105e2d79f'
down_revision: Union[str, Sequence[str], None] = '4ee63775d127'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('api_usage_logs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('api_key_id', sa.Uuid(), nullable=True),
    sa.Column('endpoint', sa.String(length=200), nullable=False),
    sa.Column('method', sa.String(length=10), nullable=False),
    sa.Column('status_code', sa.Integer(), nullable=False),
    sa.Column('credits_used', sa.Float(), nullable=False),
    sa.Column('response_time_ms', sa.Integer(), nullable=False),
    sa.Column('error_code', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_usage_logs_api_key_id'), 'api_usage_logs', ['api_key_id'], unique=False)
    op.create_index(op.f('ix_api_usage_logs_created_at'), 'api_usage_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_api_usage_logs_user_id'), 'api_usage_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_api_usage_logs_user_id'), table_name='api_usage_logs')
    op.drop_index(op.f('ix_api_usage_logs_created_at'), table_name='api_usage_logs')
    op.drop_index(op.f('ix_api_usage_logs_api_key_id'), table_name='api_usage_logs')
    op.drop_table('api_usage_logs')
