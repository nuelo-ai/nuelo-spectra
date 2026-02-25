"""add created_by_admin_id revoked_at total_credits_used to api_keys

Revision ID: 4ee63775d127
Revises: b3f8a1c2d4e5
Create Date: 2026-02-24 08:11:38.250568

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ee63775d127'
down_revision: Union[str, Sequence[str], None] = 'b3f8a1c2d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('api_keys', sa.Column('created_by_admin_id', sa.Uuid(), nullable=True, comment='Admin who created this key on behalf of user (NULL = self-created)'))
    op.add_column('api_keys', sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when key was revoked (is_active set to False)'))
    op.add_column('api_keys', sa.Column('total_credits_used', sa.Float(), server_default='0', nullable=False, comment='Denormalized credit usage counter (populated by Phase 40)'))
    op.create_foreign_key('fk_api_keys_created_by_admin', 'api_keys', 'users', ['created_by_admin_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_api_keys_created_by_admin', 'api_keys', type_='foreignkey')
    op.drop_column('api_keys', 'total_credits_used')
    op.drop_column('api_keys', 'revoked_at')
    op.drop_column('api_keys', 'created_by_admin_id')
