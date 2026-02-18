"""add_last_login_at_to_users

Revision ID: a66a91bbb9fa
Revises: dfe836ff84e9
Create Date: 2026-02-16 17:14:39.399435

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a66a91bbb9fa'
down_revision: Union[str, Sequence[str], None] = 'dfe836ff84e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_login_at')
