"""add api_key_id to credit_transactions

Revision ID: c1d2e3f4a5b6
Revises: b23105e2d79f
Create Date: 2026-02-27 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b23105e2d79f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add api_key_id column to credit_transactions for source attribution."""
    op.add_column(
        'credit_transactions',
        sa.Column('api_key_id', sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        'fk_credit_transactions_api_key_id',
        'credit_transactions', 'api_keys',
        ['api_key_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        op.f('ix_credit_transactions_api_key_id'),
        'credit_transactions', ['api_key_id'],
        unique=False,
    )


def downgrade() -> None:
    """Remove api_key_id column from credit_transactions."""
    op.drop_index(op.f('ix_credit_transactions_api_key_id'), table_name='credit_transactions')
    op.drop_constraint('fk_credit_transactions_api_key_id', 'credit_transactions', type_='foreignkey')
    op.drop_column('credit_transactions', 'api_key_id')
