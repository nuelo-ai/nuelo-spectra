"""add_query_suggestions_to_files

Revision ID: a0f950162812
Revises: aac4786a6d7e
Create Date: 2026-02-08 16:01:53.747768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0f950162812'
down_revision: Union[str, Sequence[str], None] = 'aac4786a6d7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('files', sa.Column('query_suggestions', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('files', 'query_suggestions')
