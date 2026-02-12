"""add user_modified to chat_sessions

Revision ID: c3bf6a1e6238
Revises: 2792e8318130
Create Date: 2026-02-11 19:59:38.192663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3bf6a1e6238'
down_revision: Union[str, Sequence[str], None] = '2792e8318130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user_modified boolean column to chat_sessions."""
    op.add_column('chat_sessions', sa.Column('user_modified', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    """Remove user_modified column from chat_sessions."""
    op.drop_column('chat_sessions', 'user_modified')
