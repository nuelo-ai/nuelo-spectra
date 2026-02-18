---
phase: 14-database-foundation-migration
plan: 01
subsystem: database
tags: [sqlalchemy, pydantic, orm, chat-sessions, many-to-many]

# Dependency graph
requires:
  - phase: 02-file-based-chat
    provides: "ChatMessage, File, and User models with single-file chat architecture"
provides:
  - "ChatSession ORM model with session_files M2M association table"
  - "Updated ChatMessage, File, and User models with session relationships"
  - "Pydantic schemas for ChatSession CRUD operations"
affects: [14-02-migration-script, 14-03-session-service, 14-04-session-routes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "M2M relationships via SQLAlchemy Core Table (session_files) with composite PK"
    - "Nullable FK for migration compatibility (ChatMessage.session_id)"
    - "TYPE_CHECKING imports to avoid circular dependencies"
    - "Pydantic v2 schemas with from_attributes=True for ORM compatibility"

key-files:
  created:
    - backend/app/models/chat_session.py
    - backend/app/schemas/chat_session.py
  modified:
    - backend/app/models/chat_message.py
    - backend/app/models/file.py
    - backend/app/models/user.py
    - backend/app/models/__init__.py
    - backend/app/schemas/chat.py

key-decisions:
  - "ChatMessage.session_id is nullable for migration compatibility (will be made NOT NULL after data migration)"
  - "session_files association table uses CASCADE deletes on both FKs (deleting session removes associations, not files)"
  - "File-to-Session M2M has no cascade delete from File side (deleting file removes associations, not sessions)"

patterns-established:
  - "Association tables use SQLAlchemy Core Table, not ORM class"
  - "Relationships use back_populates for bidirectional consistency"
  - "Pydantic schemas separate Create/Update/Response/Detail/List concerns"

# Metrics
duration: 3min
completed: 2026-02-11
---

# Phase 14 Plan 01: ChatSession Model & Schemas Summary

**ChatSession ORM model with M2M file associations via session_files table, nullable session_id FK in ChatMessage for migration compatibility, and complete Pydantic schema set for CRUD operations**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-11T17:49:35Z
- **Completed:** 2026-02-11T17:52:40Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Created ChatSession model with id, user_id, title, created_at, updated_at fields and three relationships (user, files, messages)
- Created session_files association table with composite PK (session_id, file_id) and CASCADE deletes
- Updated ChatMessage with nullable session_id FK pointing to chat_sessions (migration compatibility)
- Updated File model with sessions M2M relationship via session_files
- Updated User model with chat_sessions O2M relationship with cascade delete-orphan
- Created complete Pydantic schema set: ChatSessionCreate, ChatSessionUpdate, ChatSessionFileLink, ChatSessionResponse, ChatSessionDetail, ChatSessionList, FileBasicInfo
- Updated ChatMessageResponse schema with nullable session_id field

## Task Commits

Each task was committed atomically:

1. **Task 1: Create ChatSession model with session_files association table and update existing models** - `dbf0951` (feat)
2. **Task 2: Create ChatSession Pydantic schemas and update ChatMessage schemas** - `8d429e2` (feat)

## Files Created/Modified

### Created
- `backend/app/models/chat_session.py` - ChatSession ORM model and session_files association table
- `backend/app/schemas/chat_session.py` - Pydantic schemas for session CRUD operations

### Modified
- `backend/app/models/chat_message.py` - Added nullable session_id FK and session relationship
- `backend/app/models/file.py` - Added sessions M2M relationship via session_files
- `backend/app/models/user.py` - Added chat_sessions O2M relationship with cascade delete-orphan
- `backend/app/models/__init__.py` - Imported and exported ChatSession and session_files
- `backend/app/schemas/chat.py` - Added nullable session_id field to ChatMessageResponse

## Decisions Made

1. **ChatMessage.session_id is nullable**: Made nullable for migration compatibility. Existing messages don't have sessions yet. Will be made NOT NULL in a future migration after data migration completes.

2. **session_files CASCADE behavior**: Both FKs use `ondelete="CASCADE"`:
   - Deleting a ChatSession removes all session_files associations (expected)
   - Deleting a File removes all session_files associations but NOT the ChatSession (sessions can exist without files)

3. **No cascade delete from File to ChatSession**: The M2M relationship has no cascade from File side. Deleting a file only removes the association row, not the session. This preserves conversation history even if files are deleted.

4. **TYPE_CHECKING imports**: All cross-model imports use `TYPE_CHECKING` guard to avoid circular dependency errors at runtime while maintaining type checking during development.

5. **SQLAlchemy Core Table for association**: Used `Table()` constructor (not ORM class) for session_files association table, following SQLAlchemy best practices for pure M2M associations.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. Type annotation syntax error**
- **Issue:** Initial implementation used `Mapped["ChatSession" | None]` which raised `TypeError: unsupported operand type(s) for |: 'str' and 'NoneType'`
- **Root cause:** Union operator `|` cannot be used inside string literal type annotations
- **Fix:** Changed to `Mapped[Optional["ChatSession"]]` with `Optional` import from `typing`
- **Resolution:** Import succeeded, all models load without errors

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for next plans:**
- Plan 02 (Migration Script): ChatSession table schema and relationships defined, ready for Alembic migration generation
- Plan 03 (Session Service): ORM models and schemas ready for service layer implementation
- Plan 04 (Session Routes): Schemas ready for FastAPI endpoint implementation

**Blockers:** None

**Notes:**
- ChatMessage.session_id remains nullable until data migration completes (Plan 02 creates migration, future plan populates data)
- No existing code depends on these new models yet, so changes are purely additive and safe

## Self-Check: PASSED

Verified all claims in this summary:
- ✓ Created files exist (backend/app/models/chat_session.py, backend/app/schemas/chat_session.py)
- ✓ Commits exist (dbf0951, 8d429e2)

---
*Phase: 14-database-foundation-migration*
*Completed: 2026-02-11*
