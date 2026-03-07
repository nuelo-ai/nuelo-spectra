"""add_deep_profile_and_user_context

Revision ID: d3b8cf781e1e
Revises: f47a0001b000
Create Date: 2026-03-06 21:37:00.135616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3b8cf781e1e'
down_revision: Union[str, Sequence[str], None] = 'f47a0001b000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add deep_profile JSON column to files and user_context Text column to pulse_runs."""
    op.add_column("files", sa.Column("deep_profile", sa.JSON(), nullable=True))
    op.add_column("pulse_runs", sa.Column("user_context", sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove deep_profile from files and user_context from pulse_runs."""
    op.drop_column("pulse_runs", "user_context")
    op.drop_column("files", "deep_profile")
