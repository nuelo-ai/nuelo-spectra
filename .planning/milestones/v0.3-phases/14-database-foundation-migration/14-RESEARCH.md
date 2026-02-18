# Phase 14: Database Foundation & Migration - Research

**Researched:** 2026-02-11
**Domain:** Database schema refactoring, SQLAlchemy 2.0 ORM, Alembic migrations, LangGraph checkpoint migration
**Confidence:** HIGH

## Summary

Phase 14 requires restructuring the data model from file-centric (current: one file = one conversation) to session-centric (v0.3: chat sessions can have multiple files, files can belong to multiple sessions). This involves creating a new ChatSession entity, establishing a many-to-many relationship between sessions and files via an association table, migrating existing chat_messages to belong to sessions (not files), and crucially, migrating LangGraph PostgreSQL checkpoints from file-based thread IDs to session-based thread IDs while preserving conversation history.

The technical stack is FastAPI + SQLAlchemy 2.0 async ORM + Alembic + PostgreSQL + LangGraph checkpoint-postgres. The migration strategy requires multi-phase execution: (1) schema changes (new tables, relationships), (2) data migration (create sessions from existing file conversations, populate association table), (3) checkpoint migration (update thread_id in LangGraph checkpoint tables), and (4) application code updates (change thread_id generation from file-based to session-based).

**Primary recommendation:** Use a three-migration strategy with separate schema, data, and checkpoint migrations. Do NOT attempt to do everything in one migration. Test checkpoint migration thoroughly in staging as LangGraph conversation memory is the most fragile part of this phase.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | 2.0+ | Async ORM with declarative mapping | Industry standard for Python ORMs, excellent async support, type-safe with Mapped annotations |
| Alembic | 1.13+ | Database schema migrations | Official migration tool for SQLAlchemy, autogenerate capability, versioning |
| asyncpg | 0.29+ | PostgreSQL async driver | Fastest PostgreSQL driver for Python, required for SQLAlchemy async |
| langgraph-checkpoint-postgres | 3.0.4 | LangGraph checkpoint persistence | Official checkpoint backend for LangGraph, handles conversation memory |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psycopg | 3.1+ (binary) | PostgreSQL adapter for LangGraph | Required by langgraph-checkpoint-postgres for checkpoint storage |
| pydantic | 2.0+ | Data validation and schemas | Already in use for FastAPI request/response validation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Alembic | Django Migrations | Django migrations are more automatic but tied to Django ORM, not SQLAlchemy |
| Association table pattern | Association object pattern | Association object adds extra entity class, only needed if relationship itself needs data/timestamps |

**Installation:**
```bash
# Already installed in backend/pyproject.toml
# No additional dependencies needed
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── models/
│   ├── chat_session.py      # New: ChatSession entity
│   ├── session_file.py       # New: Association table model (optional, can be Core Table)
│   ├── chat_message.py       # Modified: session_id FK instead of file_id
│   ├── file.py               # Modified: add sessions relationship
│   └── user.py               # Modified: add chat_sessions relationship
├── alembic/versions/
│   ├── XXXX_create_chat_sessions_table.py           # Migration 1: Schema
│   ├── YYYY_migrate_file_conversations_to_sessions.py  # Migration 2: Data
│   └── ZZZZ_migrate_langgraph_checkpoints.py        # Migration 3: Checkpoints
└── services/
    ├── chat_session.py       # New: CRUD for sessions
    └── chat.py               # Modified: query by session_id
```

### Pattern 1: Many-to-Many with Association Table (SQLAlchemy 2.0)

**What:** Use a Core `Table` object for the association table with bidirectional relationships using `back_populates`.

**When to use:** When the relationship itself doesn't need extra data (timestamps, ordering). This is the case for session-file linking.

**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html

from sqlalchemy import Table, Column, ForeignKey
from app.models.base import Base

# Association table as Core Table (not a class)
session_files = Table(
    "session_files",
    Base.metadata,
    Column("session_id", ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", ForeignKey("files.id", ondelete="CASCADE"), primary_key=True),
)

# In chat_session.py
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    # Many-to-many: session has many files
    files: Mapped[list["File"]] = relationship(
        secondary=session_files,
        back_populates="sessions"
    )

    # One-to-many: session has many messages
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )

# In file.py
class File(Base):
    # ... existing fields ...

    # Many-to-many: file belongs to many sessions
    sessions: Mapped[list["ChatSession"]] = relationship(
        secondary=session_files,
        back_populates="files"
    )

    # IMPORTANT: Remove or deprecate chat_messages relationship
    # Messages now belong to sessions, not files
```

**Key points:**
- Both FKs in association table are PRIMARY KEY to prevent duplicates
- Use `ondelete="CASCADE"` on FKs so deleting session/file removes association rows
- SQLAlchemy auto-manages INSERT/DELETE on association table when adding/removing from collections
- Use `List` collection type for ordered results, `Set` for uniqueness (List is recommended here)

### Pattern 2: Cascade Behavior for Many-to-Many

**What:** Configure cascade DELETE behavior correctly to avoid orphaned data or unintended deletions.

**When to use:** Always consider cascade rules when defining relationships.

**Example:**
```python
# Source: https://docs.sqlalchemy.org/20/orm/cascades.html

# CORRECT: When deleting a ChatSession
class ChatSession(Base):
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"  # Delete messages when session deleted
    )

    files: Mapped[list["File"]] = relationship(
        secondary=session_files,
        back_populates="sessions"
        # NO cascade="all, delete" - we don't want to delete files when session deleted
    )

# CORRECT: When deleting a File
class File(Base):
    sessions: Mapped[list["ChatSession"]] = relationship(
        secondary=session_files,
        back_populates="files"
        # NO cascade="all, delete" - we don't want to delete sessions when file deleted
    )
```

**Cascade rules for this phase:**
- **session.messages**: `cascade="all, delete-orphan"` - deleting session deletes its messages
- **session.files**: NO cascade - deleting session only removes association rows, keeps files
- **file.sessions**: NO cascade - deleting file only removes association rows, keeps sessions
- **Database-level**: Use `ON DELETE CASCADE` in association table FKs to auto-remove rows

### Pattern 3: Data Migration in Alembic

**What:** Separate data transformations from schema changes using multiple migrations and optional execution flags.

**When to use:** When refactoring existing data into new schema (exactly this phase's case).

**Example:**
```python
# Source: https://alembic.sqlalchemy.org/en/latest/cookbook.html

# Migration 1: Schema changes (safe, reversible)
def upgrade():
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'session_files',
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('file_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id', 'file_id')
    )

    # Add session_id to chat_messages (nullable initially for data migration)
    op.add_column('chat_messages', sa.Column('session_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('fk_chat_messages_session_id', 'chat_messages', 'chat_sessions', ['session_id'], ['id'], ondelete='CASCADE')

# Migration 2: Data transformation (requires careful testing)
def upgrade():
    from sqlalchemy import table, column, select
    from uuid import uuid4

    # Use Alembic's table() construct for data operations
    files = table('files', column('id'), column('user_id'), column('created_at'))
    chat_sessions = table('chat_sessions', column('id'), column('user_id'), column('title'), column('created_at'), column('updated_at'))
    session_files_assoc = table('session_files', column('session_id'), column('file_id'))
    chat_messages = table('chat_messages', column('id'), column('file_id'), column('session_id'))

    conn = op.get_bind()

    # For each file, create a chat session
    file_rows = conn.execute(select(files.c.id, files.c.user_id, files.c.created_at)).fetchall()

    for file_row in file_rows:
        file_id, user_id, created_at = file_row
        session_id = uuid4()

        # Create session for this file's conversation
        conn.execute(chat_sessions.insert().values(
            id=session_id,
            user_id=user_id,
            title=f"Conversation (migrated)",  # Can enhance with first message or filename
            created_at=created_at,
            updated_at=created_at
        ))

        # Link session to file
        conn.execute(session_files_assoc.insert().values(
            session_id=session_id,
            file_id=file_id
        ))

        # Update all messages for this file to belong to new session
        conn.execute(
            chat_messages.update()
            .where(chat_messages.c.file_id == file_id)
            .values(session_id=session_id)
        )

# Migration 3: Cleanup and constraints
def upgrade():
    # Now that all chat_messages have session_id, make it non-nullable
    op.alter_column('chat_messages', 'session_id', nullable=False)

    # IMPORTANT: Keep file_id for now for backward compatibility
    # Can be removed in future migration after application code fully migrated
```

### Pattern 4: LangGraph Checkpoint Migration

**What:** Update thread_id in LangGraph checkpoint tables from file-based to session-based format.

**When to use:** After data migration creates sessions, before application switches to session-based thread IDs.

**Example:**
```python
# Migration: Migrate LangGraph checkpoints to session-based thread IDs
def upgrade():
    from sqlalchemy import table, column, select

    # LangGraph checkpoint schema (from source inspection)
    checkpoints = table('checkpoints',
        column('thread_id'),
        column('checkpoint_ns'),
        column('checkpoint_id')
    )
    checkpoint_blobs = table('checkpoint_blobs', column('thread_id'))
    checkpoint_writes = table('checkpoint_writes', column('thread_id'))

    # Our domain tables
    chat_messages = table('chat_messages', column('file_id'), column('session_id'))

    conn = op.get_bind()

    # Get mapping of old thread_id (file_XXXX_user_YYYY) to new thread_id (session_ZZZZ_user_YYYY)
    # Query distinct file_id, session_id, user_id from chat_messages
    mapping_query = """
        SELECT DISTINCT
            cm.file_id,
            cm.session_id,
            cm.user_id
        FROM chat_messages cm
        WHERE cm.session_id IS NOT NULL
    """

    mappings = conn.execute(mapping_query).fetchall()

    for file_id, session_id, user_id in mappings:
        old_thread_id = f"file_{file_id}_user_{user_id}"
        new_thread_id = f"session_{session_id}_user_{user_id}"

        # Update checkpoints table
        conn.execute(
            checkpoints.update()
            .where(checkpoints.c.thread_id == old_thread_id)
            .values(thread_id=new_thread_id)
        )

        # Update checkpoint_blobs table
        conn.execute(
            checkpoint_blobs.update()
            .where(checkpoint_blobs.c.thread_id == old_thread_id)
            .values(thread_id=new_thread_id)
        )

        # Update checkpoint_writes table
        conn.execute(
            checkpoint_writes.update()
            .where(checkpoint_writes.c.thread_id == old_thread_id)
            .values(thread_id=new_thread_id)
        )

def downgrade():
    # Reverse migration would require storing old thread_id mapping
    # Recommend backup before running this migration
    raise NotImplementedError("Downgrade requires pre-migration backup")
```

**Critical notes:**
- LangGraph stores thread_id as strings in `checkpoints`, `checkpoint_blobs`, and `checkpoint_writes` tables
- Current format: `file_{file_id}_user_{user_id}`
- Target format: `session_{session_id}_user_{user_id}`
- This migration MUST happen before application code switches thread_id generation
- Test extensively in staging - conversation history corruption would be catastrophic

### Pattern 5: FastAPI Async Session Best Practices

**What:** Use dependency injection for async sessions with proper lifecycle management and error handling.

**When to use:** All database operations in FastAPI endpoints (already in use, ensure consistency).

**Example:**
```python
# Source: Current backend/app/database.py (already correct)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

engine = create_async_engine(
    settings.database_url,
    echo=True,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # CRITICAL: prevents MissingGreenlet errors
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# In services
class ChatSessionService:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: UUID,
        title: str
    ) -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def link_file_to_session(
        db: AsyncSession,
        session_id: UUID,
        file_id: UUID
    ) -> None:
        # SQLAlchemy handles association table automatically
        session = await db.get(ChatSession, session_id)
        file = await db.get(File, file_id)
        session.files.append(file)  # Auto-inserts into session_files table
        await db.commit()
```

**Key configuration:**
- `expire_on_commit=False`: Allows using ORM objects after commit without additional queries
- `echo=True`: Log SQL in development for debugging
- Session scoped to request lifecycle via dependency injection
- Always use try/finally to ensure session cleanup

### Anti-Patterns to Avoid

- **Don't mix schema and data in one migration:** Alembic autogenerate can overwrite manual data operations. Use separate migrations.
- **Don't use bidirectional cascade="all, delete" on many-to-many:** Will cascade delete through all connected entities, deleting everything.
- **Don't forget to index foreign keys:** Association table FKs should have indexes for query performance (Alembic creates them by default).
- **Don't migrate checkpoints without backup:** LangGraph conversation memory is difficult to reconstruct if corrupted.
- **Don't change thread_id format in application before migrating checkpoint data:** Will break conversation history continuity.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Migration versioning | Custom SQL scripts with manual tracking | Alembic migrations | Alembic handles version tracking, dependency resolution, autogenerate, and rollback. Custom scripts are error-prone. |
| Many-to-many relationship management | Manual INSERT/DELETE to association table | SQLAlchemy relationship() with secondary | ORM handles association table operations automatically, prevents orphaned rows, ensures referential integrity. |
| Async database connection pooling | Custom connection pool manager | SQLAlchemy async engine with built-in pooling | Engine handles pool_size, max_overflow, connection recycling, pre_ping health checks. Custom pools miss edge cases. |
| Checkpoint schema management | Custom checkpoint storage | LangGraph PostgresSaver with .setup() | LangGraph handles schema creation, versioning, migration, and data format evolution automatically. |

**Key insight:** Database schema evolution is deceptively complex. Edge cases like concurrent migrations, partial failures, constraint violations during multi-step data transformations, and checkpoint format compatibility are already handled by established tools. Hand-rolled solutions inevitably rediscover these problems the hard way.

## Common Pitfalls

### Pitfall 1: Not Testing Migration Rollback

**What goes wrong:** Migration succeeds in dev but fails in production due to data differences. No tested downgrade path means manual recovery.

**Why it happens:** Developers test `upgrade()` but not `downgrade()`. Production has data patterns dev doesn't (null values, constraint violations, large volumes).

**How to avoid:**
- Test both upgrade and downgrade on production-like data (anonymized dump)
- Use database transactions in migrations when possible (`op.execute()` is transactional in PostgreSQL)
- Back up production database before migration
- For complex migrations, implement idempotency checks (e.g., skip if session already exists for file)

**Warning signs:**
- Migration takes >5 seconds in dev with 10 rows
- SQL errors in Alembic output that you ignore
- Downgrade function is `pass` or `raise NotImplementedError`

### Pitfall 2: Forgetting to Update Application Thread ID Generation

**What goes wrong:** Migration updates checkpoint tables to session-based thread IDs, but application code still generates file-based thread IDs. New conversations create orphaned checkpoints; old conversations can't be loaded.

**Why it happens:** Migration and application code are updated separately without coordination.

**How to avoid:**
- Update thread_id generation IMMEDIATELY after checkpoint migration completes
- Deploy migration and code change together (or in quick succession with downtime)
- Add logging to verify thread_id format in production after deployment
- Consider feature flag: switch thread_id format via config, migrate data, flip flag, monitor

**Warning signs:**
- Conversation history loads as empty after deployment
- New messages don't appear in subsequent queries
- LangGraph checkpoint errors in logs

### Pitfall 3: Cascade Delete Misconfiguration

**What goes wrong:** User deletes a file, expecting it to be removed from sessions but messages preserved. Instead, cascade delete wipes all sessions and messages linked to that file.

**Why it happens:** Misunderstanding SQLAlchemy cascade vs database-level ON DELETE CASCADE. Setting `cascade="all, delete"` on many-to-many relationship.

**How to avoid:**
- For many-to-many: NO cascade on relationship(), only ON DELETE CASCADE on association table FKs
- For one-to-many (session→messages): Use `cascade="all, delete-orphan"` to delete messages when session deleted
- Test deletion scenarios in staging with real data
- Document cascade behavior in model docstrings

**Warning signs:**
- Deleting one entity unexpectedly deletes related entities
- Foreign key constraint violations during delete operations
- Association table rows not auto-deleted when parent deleted

### Pitfall 4: Nullable Foreign Keys During Migration

**What goes wrong:** Add `session_id` column to `chat_messages` as NOT NULL immediately. Migration fails because existing rows have no session_id value yet.

**Why it happens:** Trying to do schema change and data migration in one step.

**How to avoid:**
- Add column as nullable initially
- Populate data in separate migration
- Make column non-nullable in third migration after verifying all rows populated
- Or use multi-step Alembic batch operations with default values

**Warning signs:**
- Migration fails with "column X violates non-null constraint"
- Need to manually fix database after failed migration
- `alembic downgrade` leaves database in inconsistent state

### Pitfall 5: Missing Indexes on Association Table

**What goes wrong:** Query performance degrades when filtering sessions by file or files by session. Full table scans on association table.

**Why it happens:** Assuming primary key index is enough. Forgetting to index foreign key columns for reverse lookups.

**How to avoid:**
- Alembic automatically creates indexes on FK columns (verify in generated migration)
- For association table with composite PK (session_id, file_id), PostgreSQL creates index on first column by default
- Manually add index on second column if needed: `CREATE INDEX idx_session_files_file_id ON session_files(file_id)`

**Warning signs:**
- Slow query performance on session/file joins
- `EXPLAIN ANALYZE` shows Seq Scan on session_files table
- Database CPU spikes when loading session file lists

### Pitfall 6: LangGraph Checkpoint Table Not Initialized

**What goes wrong:** Application starts, tries to use checkpointer, fails with "table checkpoints does not exist" error.

**Why it happens:** Forgetting to call `await checkpointer.setup()` in application startup. LangGraph doesn't auto-create tables without explicit setup call.

**How to avoid:**
- Call `.setup()` in FastAPI lifespan or startup event (already done in backend/app/main.py)
- Ensure setup runs BEFORE any endpoint uses checkpointer
- Make setup idempotent (LangGraph's setup() is idempotent by design)
- Log successful setup for debugging

**Warning signs:**
- "relation checkpoints does not exist" in PostgreSQL logs
- Fresh database deployments fail immediately
- Checkpointing works in dev but not in new staging environment

## Code Examples

Verified patterns from official sources:

### Creating ChatSession Model with Many-to-Many

```python
# File: backend/app/models/chat_session.py
# Source: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html

from sqlalchemy import String, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.file import File
    from app.models.chat_message import ChatMessage

# Association table as Core Table
session_files = Table(
    "session_files",
    Base.metadata,
    Column("session_id", ForeignKey("chat_sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", ForeignKey("files.id", ondelete="CASCADE"), primary_key=True),
)

class ChatSession(Base):
    """Chat session model - conversations can have multiple files."""

    __tablename__ = "chat_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")

    # Many-to-many: session can have multiple files
    files: Mapped[list["File"]] = relationship(
        secondary=session_files,
        back_populates="sessions"
    )

    # One-to-many: session has many messages
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
```

### Updating File Model

```python
# File: backend/app/models/file.py
# Add to existing File class:

from app.models.chat_session import session_files

class File(Base):
    # ... existing fields ...

    # Many-to-many: file can belong to multiple sessions
    sessions: Mapped[list["ChatSession"]] = relationship(
        secondary=session_files,
        back_populates="files"
    )

    # IMPORTANT: chat_messages relationship should be removed or marked deprecated
    # Messages now belong to sessions, not files directly
```

### Updating ChatMessage Model

```python
# File: backend/app/models/chat_message.py
# Modify existing ChatMessage class:

class ChatMessage(Base):
    """Chat message model - now belongs to session, not file."""

    __tablename__ = "chat_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # NEW: session_id replaces file_id as primary relationship
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    # KEEP file_id for backward compatibility during migration, remove later
    file_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        index=True,
        nullable=True  # Changed from False
    )

    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chat_messages")
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    # file relationship deprecated, remove in future version
```

### Alembic Migration: Schema Changes

```python
# File: alembic/versions/XXXX_create_chat_sessions_table.py
# Source: https://alembic.sqlalchemy.org/en/latest/tutorial.html

"""create chat sessions table

Revision ID: XXXX
Revises: e49613642cfe
Create Date: 2026-02-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'XXXX'
down_revision: Union[str, Sequence[str], None] = 'e49613642cfe'

def upgrade() -> None:
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)

    # Create session_files association table
    op.create_table(
        'session_files',
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('file_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id', 'file_id')
    )
    # Indexes for association table (reverse lookup performance)
    op.create_index(op.f('ix_session_files_session_id'), 'session_files', ['session_id'], unique=False)
    op.create_index(op.f('ix_session_files_file_id'), 'session_files', ['file_id'], unique=False)

    # Add session_id to chat_messages (nullable for migration)
    op.add_column('chat_messages', sa.Column('session_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'fk_chat_messages_session_id',
        'chat_messages',
        'chat_sessions',
        ['session_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_constraint('fk_chat_messages_session_id', 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'session_id')

    op.drop_index(op.f('ix_session_files_file_id'), table_name='session_files')
    op.drop_index(op.f('ix_session_files_session_id'), table_name='session_files')
    op.drop_table('session_files')

    op.drop_index(op.f('ix_chat_sessions_user_id'), table_name='chat_sessions')
    op.drop_table('chat_sessions')
```

### Alembic Migration: Data Migration

```python
# File: alembic/versions/YYYY_migrate_file_conversations_to_sessions.py
# Source: https://alembic.sqlalchemy.org/en/latest/cookbook.html

"""migrate file conversations to sessions

Revision ID: YYYY
Revises: XXXX
Create Date: 2026-02-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column, select
from uuid import uuid4

revision: str = 'YYYY'
down_revision: Union[str, Sequence[str], None] = 'XXXX'

def upgrade() -> None:
    # Define table references for data operations
    files_table = table('files',
        column('id'),
        column('user_id'),
        column('original_filename'),
        column('created_at')
    )
    chat_sessions = table('chat_sessions',
        column('id'),
        column('user_id'),
        column('title'),
        column('created_at'),
        column('updated_at')
    )
    session_files_assoc = table('session_files',
        column('session_id'),
        column('file_id')
    )
    chat_messages = table('chat_messages',
        column('id'),
        column('file_id'),
        column('session_id')
    )

    conn = op.get_bind()

    # For each file, create a corresponding chat session
    file_rows = conn.execute(
        select(
            files_table.c.id,
            files_table.c.user_id,
            files_table.c.original_filename,
            files_table.c.created_at
        )
    ).fetchall()

    print(f"Migrating {len(file_rows)} file conversations to sessions...")

    for file_id, user_id, filename, created_at in file_rows:
        session_id = uuid4()

        # Create session for this file's conversation
        # Title uses filename for better UX
        conn.execute(
            chat_sessions.insert().values(
                id=session_id,
                user_id=user_id,
                title=f"{filename}",  # or "Conversation - {filename}"
                created_at=created_at,
                updated_at=created_at
            )
        )

        # Link session to file via association table
        conn.execute(
            session_files_assoc.insert().values(
                session_id=session_id,
                file_id=file_id
            )
        )

        # Update all messages for this file to belong to new session
        conn.execute(
            chat_messages.update()
            .where(chat_messages.c.file_id == file_id)
            .values(session_id=session_id)
        )

    print(f"Migration complete: created {len(file_rows)} sessions")

def downgrade() -> None:
    # Downgrade: delete all sessions and clear session_id from messages
    conn = op.get_bind()

    chat_messages = table('chat_messages', column('session_id'))

    conn.execute(
        chat_messages.update().values(session_id=None)
    )

    conn.execute("DELETE FROM session_files")
    conn.execute("DELETE FROM chat_sessions")
```

### Alembic Migration: LangGraph Checkpoint Migration

```python
# File: alembic/versions/ZZZZ_migrate_langgraph_checkpoints.py

"""migrate langgraph checkpoints to session-based thread_ids

Revision ID: ZZZZ
Revises: YYYY
Create Date: 2026-02-11

CRITICAL: This migration updates LangGraph checkpoint tables.
Back up database before running. Test in staging first.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column

revision: str = 'ZZZZ'
down_revision: Union[str, Sequence[str], None] = 'YYYY'

def upgrade() -> None:
    # Define table references
    chat_messages = table('chat_messages',
        column('file_id'),
        column('session_id'),
        column('user_id')
    )
    checkpoints = table('checkpoints', column('thread_id'))
    checkpoint_blobs = table('checkpoint_blobs', column('thread_id'))
    checkpoint_writes = table('checkpoint_writes', column('thread_id'))

    conn = op.get_bind()

    # Get mapping of file_id -> session_id -> user_id
    # Use DISTINCT to handle case where file has messages from multiple users (shouldn't happen, but be safe)
    mapping_query = """
        SELECT DISTINCT
            cm.file_id::text,
            cm.session_id::text,
            cm.user_id::text
        FROM chat_messages cm
        WHERE cm.session_id IS NOT NULL
    """

    mappings = conn.execute(mapping_query).fetchall()

    print(f"Migrating {len(mappings)} checkpoint thread_ids from file-based to session-based...")

    migrated_count = 0
    for file_id, session_id, user_id in mappings:
        old_thread_id = f"file_{file_id}_user_{user_id}"
        new_thread_id = f"session_{session_id}_user_{user_id}"

        # Update checkpoints table
        result = conn.execute(
            checkpoints.update()
            .where(checkpoints.c.thread_id == old_thread_id)
            .values(thread_id=new_thread_id)
        )

        if result.rowcount > 0:
            # Update checkpoint_blobs table
            conn.execute(
                checkpoint_blobs.update()
                .where(checkpoint_blobs.c.thread_id == old_thread_id)
                .values(thread_id=new_thread_id)
            )

            # Update checkpoint_writes table
            conn.execute(
                checkpoint_writes.update()
                .where(checkpoint_writes.c.thread_id == old_thread_id)
                .values(thread_id=new_thread_id)
            )

            migrated_count += 1

    print(f"Checkpoint migration complete: updated {migrated_count} thread_ids")

def downgrade() -> None:
    # Downgrade not supported - would require storing old thread_id mapping
    # Recommendation: restore from backup if downgrade needed
    raise NotImplementedError(
        "Downgrade not supported for checkpoint migration. "
        "Restore database from backup if rollback is required."
    )
```

### Updating Thread ID Generation in Application

```python
# File: backend/app/routers/chat.py
# Update thread_id generation from file-based to session-based

# BEFORE (v0.2 - file-centric):
thread_id = f"file_{file_id}_user_{current_user.id}"

# AFTER (v0.3 - session-centric):
thread_id = f"session_{session_id}_user_{current_user.id}"

# Example endpoint update:
@router.post("/{session_id}/query")
async def query_session(
    session_id: UUID,
    body: ChatQueryRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request
):
    # Verify session ownership
    session = await ChatSessionService.get_user_session(db, session_id, current_user.id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate session-based thread_id for LangGraph checkpointing
    thread_id = f"session_{session_id}_user_{current_user.id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Rest of endpoint logic...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| File-centric conversations | Session-centric with multi-file support | v0.3 (this milestone) | Conversations can span multiple files, files can be reused across sessions |
| thread_id = file_{id}_user_{id} | thread_id = session_{id}_user_{id} | v0.3 (this phase) | LangGraph checkpoints organized by session instead of file |
| Messages belong to files | Messages belong to sessions | v0.3 (this phase) | Clearer conversation context, messages persist when file removed from session |
| One conversation per file | Multiple sessions can reference same file | v0.3 (this phase) | Users can have different conversations about same data |
| Association object pattern | Association table pattern | SQLAlchemy 2.0+ | Simpler for relationships without extra data, less boilerplate |

**Deprecated/outdated:**
- **ShallowPostgresSaver (LangGraph)**: Deprecated in langgraph-checkpoint-postgres 2.0.20, use PostgresSaver with durability='exit' instead
- **SQLAlchemy 1.x relationship() syntax**: Use Mapped[] type annotations in SQLAlchemy 2.0+
- **Synchronous database drivers**: Use asyncpg for async FastAPI, not psycopg2

## Open Questions

1. **Should session title be auto-generated from first message or manual?**
   - What we know: Migration creates sessions with filename as title
   - What's unclear: v0.3 UX requirements don't specify if users can customize session title
   - Recommendation: Allow manual title editing in UI, auto-generate from first user message as default (truncate to 255 chars)

2. **How to handle orphaned LangGraph checkpoints (thread_ids with no matching session)?**
   - What we know: Checkpoints may exist for deleted files
   - What's unclear: Should migration clean them up or preserve for potential recovery?
   - Recommendation: Log count of orphaned checkpoints but don't delete (preserve for 30 days, then manual cleanup)

3. **Should deleting a file from session also delete associated messages?**
   - What we know: Requirement DATA-06 says "deleting a file removes it from linked sessions but does not delete session messages"
   - What's unclear: Does "removing file from session" mean different from "deleting file permanently"?
   - Recommendation: Two operations: (1) Unlink file from session = remove association row only, keep messages; (2) Delete file permanently = remove from all sessions but keep messages. Session delete = delete messages.

4. **Migration performance for large datasets?**
   - What we know: Migration creates one session per file, updates all messages
   - What's unclear: Performance impact on databases with 100k+ messages
   - Recommendation: Test on production-like data volume, consider batching if needed, run during maintenance window

## Sources

### Primary (HIGH confidence)
- [SQLAlchemy 2.0 Basic Relationship Patterns](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html) - Many-to-many with association tables
- [SQLAlchemy 2.0 Cascades Documentation](https://docs.sqlalchemy.org/20/orm/cascades.html) - Cascade delete behavior
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) - Data migration patterns
- [LangGraph Checkpoint Postgres GitHub](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py) - Checkpoint schema and thread_id storage
- Project codebase: backend/app/models/, backend/app/database.py (current SQLAlchemy 2.0 async patterns)

### Secondary (MEDIUM confidence)
- [LangGraph Checkpoint PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/) - Version 3.0.4 (2026-01-31)
- [FastAPI SQLAlchemy 2.0 Best Practices 2026](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026) - Async session patterns
- [Alembic Data Migration Basics](https://medium.com/@csakash03/alembic-data-migration-basics-780c89333583) - Multi-step migration strategies

### Tertiary (LOW confidence)
- None - all critical findings verified against official documentation or source code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use (pyproject.toml), versions verified
- Architecture: HIGH - SQLAlchemy 2.0 patterns verified in official docs, existing codebase uses async correctly
- Pitfalls: HIGH - Cascade behavior, migration patterns, checkpoint schema verified in official sources
- Migration strategy: MEDIUM-HIGH - Data migration pattern verified, but LangGraph checkpoint migration less documented (verified via source code inspection)

**Research date:** 2026-02-11
**Valid until:** 2026-03-31 (stable ecosystem, SQLAlchemy/Alembic patterns unlikely to change)
