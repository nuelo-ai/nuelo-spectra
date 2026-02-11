"""migrate langgraph checkpoints and finalize session_id

Revision ID: 2792e8318130
Revises: ad17e35bacd0
Create Date: 2026-02-11 12:58:09.039197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, select, text


# revision identifiers, used by Alembic.
revision: str = '2792e8318130'
down_revision: Union[str, Sequence[str], None] = 'ad17e35bacd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate LangGraph checkpoint thread_ids and finalize session_id constraint."""
    conn = op.get_bind()

    # Check if LangGraph tables exist (they may not exist in fresh dev DBs)
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='checkpoints')"
    ))
    has_checkpoints = result.scalar()

    migrated_count = 0

    if has_checkpoints:
        # Use session_files table to get all file->session mappings
        # This covers ALL files, including those with no messages but with checkpoints
        session_files_table = table(
            'session_files',
            column('session_id', sa.Uuid),
            column('file_id', sa.Uuid)
        )

        chat_sessions = table(
            'chat_sessions',
            column('id', sa.Uuid),
            column('user_id', sa.Uuid)
        )

        # Query file_id -> session_id -> user_id mappings from session_files + chat_sessions
        mappings = conn.execute(
            select(
                session_files_table.c.file_id,
                session_files_table.c.session_id,
                chat_sessions.c.user_id
            )
            .select_from(
                session_files_table.join(
                    chat_sessions,
                    session_files_table.c.session_id == chat_sessions.c.id
                )
            )
        ).fetchall()

        # Migrate checkpoint thread_ids
        for file_id, session_id, user_id in mappings:
            old_thread_id = f"file_{file_id}_user_{user_id}"
            new_thread_id = f"session_{session_id}_user_{user_id}"

            # Update checkpoints table
            result = conn.execute(text(
                "UPDATE checkpoints SET thread_id = :new WHERE thread_id = :old"
            ).bindparams(new=new_thread_id, old=old_thread_id))
            migrated_count += result.rowcount

            # Update checkpoint_blobs table
            conn.execute(text(
                "UPDATE checkpoint_blobs SET thread_id = :new WHERE thread_id = :old"
            ).bindparams(new=new_thread_id, old=old_thread_id))

            # Update checkpoint_writes table
            conn.execute(text(
                "UPDATE checkpoint_writes SET thread_id = :new WHERE thread_id = :old"
            ).bindparams(new=new_thread_id, old=old_thread_id))

        print(f"Migrated {migrated_count} checkpoint thread_ids from file-based to session-based format")
    else:
        print("LangGraph checkpoint tables do not exist, skipping checkpoint migration")

    # Make session_id NOT NULL (finalize after data migration populated all rows)
    op.alter_column('chat_messages', 'session_id', nullable=False)

    # Make file_id nullable for future decoupling (DATA-06: deleting file sets file_id to NULL)
    op.alter_column('chat_messages', 'file_id', nullable=True)

    # Update FK constraint to SET NULL on delete instead of CASCADE
    op.drop_constraint('chat_messages_file_id_fkey', 'chat_messages', type_='foreignkey')
    op.create_foreign_key(
        'chat_messages_file_id_fkey',
        'chat_messages',
        'files',
        ['file_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Reverse the migration."""
    # Restore CASCADE FK on file_id
    op.drop_constraint('chat_messages_file_id_fkey', 'chat_messages', type_='foreignkey')
    op.create_foreign_key(
        'chat_messages_file_id_fkey',
        'chat_messages',
        'files',
        ['file_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Make file_id NOT NULL again
    op.alter_column('chat_messages', 'file_id', nullable=False)

    # Make session_id nullable again
    op.alter_column('chat_messages', 'session_id', nullable=True)

    # Note: Checkpoint thread_id changes are not reversed
    raise NotImplementedError(
        "Checkpoint thread_id rollback requires database backup restoration. "
        "Use: alembic downgrade ad17e35bacd0 and restore from backup if needed."
    )
