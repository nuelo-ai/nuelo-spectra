"""create chat sessions and session files tables

Revision ID: 845e02834ad7
Revises: 9c47b2cc24f2
Create Date: 2026-02-11 12:56:39.065285

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '845e02834ad7'
down_revision: Union[str, Sequence[str], None] = '9c47b2cc24f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create chat_sessions table
    op.create_table('chat_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)

    # Create session_files association table
    op.create_table('session_files',
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('file_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('session_id', 'file_id')
    )
    op.create_index(op.f('ix_session_files_file_id'), 'session_files', ['file_id'], unique=False)

    # Add session_id column to chat_messages (nullable for migration)
    op.add_column('chat_messages', sa.Column('session_id', sa.Uuid(), nullable=True))
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)
    op.create_foreign_key('fk_chat_messages_session_id', 'chat_messages', 'chat_sessions', ['session_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop session_id from chat_messages
    op.drop_constraint('fk_chat_messages_session_id', 'chat_messages', type_='foreignkey')
    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_column('chat_messages', 'session_id')

    # Drop session_files table
    op.drop_index(op.f('ix_session_files_file_id'), table_name='session_files')
    op.drop_table('session_files')

    # Drop chat_sessions table
    op.drop_index(op.f('ix_chat_sessions_user_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')
