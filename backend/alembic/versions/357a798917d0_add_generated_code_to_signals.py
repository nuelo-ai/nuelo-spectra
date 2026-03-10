"""add_generated_code_to_signals

Revision ID: 357a798917d0
Revises: d3b8cf781e1e
Create Date: 2026-03-08 15:08:00.670430

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '357a798917d0'
down_revision: Union[str, Sequence[str], None] = 'd3b8cf781e1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add generated_code column to signals table for code audit trail."""
    op.add_column('signals', sa.Column('generated_code', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove generated_code column from signals table."""
    op.drop_column('signals', 'generated_code')
