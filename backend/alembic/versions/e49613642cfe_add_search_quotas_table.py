"""add search_quotas table

Revision ID: e49613642cfe
Revises: a0f950162812
Create Date: 2026-02-09 08:13:06.828415

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e49613642cfe'
down_revision: Union[str, Sequence[str], None] = 'a0f950162812'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('search_quotas',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('search_date', sa.Date(), nullable=False),
    sa.Column('search_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'search_date')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('search_quotas')
