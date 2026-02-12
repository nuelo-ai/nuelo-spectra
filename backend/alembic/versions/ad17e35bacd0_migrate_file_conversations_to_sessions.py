"""migrate file conversations to sessions

Revision ID: ad17e35bacd0
Revises: 845e02834ad7
Create Date: 2026-02-11 12:57:45.304425

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, select, insert, update


# revision identifiers, used by Alembic.
revision: str = 'ad17e35bacd0'
down_revision: Union[str, Sequence[str], None] = '845e02834ad7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate existing file conversations to session-based model."""
    # Define table references using table() construct (NOT ORM models)
    files_table = table(
        'files',
        column('id', sa.Uuid),
        column('user_id', sa.Uuid),
        column('original_filename', sa.String),
        column('created_at', sa.DateTime(timezone=True))
    )

    chat_sessions = table(
        'chat_sessions',
        column('id', sa.Uuid),
        column('user_id', sa.Uuid),
        column('title', sa.String),
        column('created_at', sa.DateTime(timezone=True)),
        column('updated_at', sa.DateTime(timezone=True))
    )

    session_files_assoc = table(
        'session_files',
        column('session_id', sa.Uuid),
        column('file_id', sa.Uuid)
    )

    chat_messages = table(
        'chat_messages',
        column('id', sa.Uuid),
        column('file_id', sa.Uuid),
        column('session_id', sa.Uuid)
    )

    # Get database connection
    conn = op.get_bind()

    # Query all files
    file_rows = conn.execute(
        select(
            files_table.c.id,
            files_table.c.user_id,
            files_table.c.original_filename,
            files_table.c.created_at
        )
    ).fetchall()

    # Migrate each file to a session
    for file_row in file_rows:
        file_id = file_row[0]
        user_id = file_row[1]
        filename = file_row[2]
        created_at = file_row[3]

        # Generate session ID
        session_id = uuid4()

        # Insert into chat_sessions (use filename as session title for migrated conversations)
        conn.execute(
            insert(chat_sessions).values(
                id=session_id,
                user_id=user_id,
                title=filename,
                created_at=created_at,
                updated_at=created_at
            )
        )

        # Insert into session_files association
        conn.execute(
            insert(session_files_assoc).values(
                session_id=session_id,
                file_id=file_id
            )
        )

        # Update chat_messages to link to session
        conn.execute(
            update(chat_messages)
            .where(chat_messages.c.file_id == file_id)
            .values(session_id=session_id)
        )

    print(f"Migrated {len(file_rows)} file conversations to sessions")


def downgrade() -> None:
    """Reverse the migration."""
    # Define table references
    chat_messages = table(
        'chat_messages',
        column('session_id', sa.Uuid)
    )

    session_files_assoc = table('session_files')
    chat_sessions = table('chat_sessions')

    conn = op.get_bind()

    # Clear session_id from chat_messages
    conn.execute(
        update(chat_messages).values(session_id=None)
    )

    # Delete all session_files associations
    conn.execute(sa.text("DELETE FROM session_files"))

    # Delete all chat_sessions
    conn.execute(sa.text("DELETE FROM chat_sessions"))
