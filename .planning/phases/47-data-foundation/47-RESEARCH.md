# Phase 47: Data Foundation - Research

**Researched:** 2026-03-06
**Domain:** SQLAlchemy models, Alembic migrations, YAML/platform config
**Confidence:** HIGH

## Summary

Phase 47 creates the data layer for the entire v0.8 Spectra Pulse feature set. This involves 5 new SQLAlchemy models (Collection, CollectionFile, Signal, Report, PulseRun), 1 M2M junction table (pulse_run_files), a single Alembic migration, additions to `user_classes.yaml`, and a new `workspace_credit_cost_pulse` platform setting. No API routes, no frontend, no agent logic.

The codebase has well-established patterns for all of these operations. Every model uses UUID PKs via `uuid4`, `DateTime(timezone=True)` with UTC lambdas, `String(N)` for enum-like columns, and `ForeignKey("table.id", ondelete="CASCADE")` with `index=True`. The M2M junction table pattern exists in `session_files`. The platform settings service uses a DEFAULTS dict + VALID_KEYS set + validate_setting() switch. The user_classes.yaml is flat key-value per tier. All patterns are copy-and-adapt.

**Primary recommendation:** Follow existing codebase patterns exactly -- this is a mechanical, pattern-following phase with zero novel architecture decisions.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Signal storage: single JSON column for statistical evidence, inline JSON column for chart data, String(50) category, String(20) severity
- PulseRun model: tracks collection_id, status (pending/running/completed/failed), credit_cost, timestamps, error_message; M2M junction table (pulse_run_files) for selected files; Signal.pulse_run_id FK
- Re-runs keep all history: each PulseRun is immutable, new run = new PulseRun + new Signals
- Report content: Text column for markdown, report_type String(50) discriminator, polymorphic source via nullable FKs, only pulse_run_id FK in v0.8
- Detection summary Report auto-generated on PulseRun completion

### Claude's Discretion
- Exact column lengths and index strategy
- Migration revision ID and dependencies
- Model relationship cascade/lazy-loading configuration
- PulseRun status transition logic details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ADMIN-01 | Tier-based workspace access: workspace_access (bool) and max_active_collections (int, -1=unlimited) per tier in user_classes.yaml; defaults: free_trial=1, free=0, standard=5, premium=-1, internal=-1 | user_classes.yaml structure documented, exact values specified |
| ADMIN-02 | workspace_credit_cost_pulse configurable via Admin Portal platform settings; default 5.0 | platform_settings.py DEFAULTS/VALID_KEYS/validate_setting() pattern documented |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | >=2.0.0 (asyncio) | ORM models with Mapped[] type annotations | Already in use, pyproject.toml |
| Alembic | >=1.13.0 | Schema migrations | Already in use, pyproject.toml |
| asyncpg | >=0.29.0 | PostgreSQL async driver | Already in use, pyproject.toml |
| PyYAML | >=6.0.0 | user_classes.yaml parsing | Already in use, pyproject.toml |

### Supporting
No new libraries needed. This phase uses only existing dependencies.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/models/
    collection.py          # Collection + CollectionFile models
    signal.py              # Signal model
    report.py              # Report model
    pulse_run.py           # PulseRun model + pulse_run_files junction table
    __init__.py            # Add new imports + __all__ entries
backend/alembic/versions/
    f47a0001b000_add_pulse_workspace_tables.py   # Single migration for all tables
backend/app/config/
    user_classes.yaml      # Add workspace_access + max_active_collections
backend/app/services/
    platform_settings.py   # Add workspace_credit_cost_pulse key
```

### Pattern 1: Model Definition (copy from File model)
**What:** UUID PK, user_id FK, timestamps, String enum-like columns
**When to use:** Every new model
**Example:**
```python
# Source: backend/app/models/file.py (existing pattern)
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

### Pattern 2: M2M Junction Table (copy from session_files)
**What:** Association table with composite PK and CASCADE deletes
**When to use:** pulse_run_files linking PulseRun to File
**Example:**
```python
# Source: backend/app/models/chat_session.py (existing pattern)
from sqlalchemy import Table, Column, ForeignKey
from app.models.base import Base

pulse_run_files = Table(
    "pulse_run_files",
    Base.metadata,
    Column(
        "pulse_run_id",
        ForeignKey("pulse_runs.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "file_id",
        ForeignKey("files.id", ondelete="CASCADE"),
        primary_key=True
    )
)
```

### Pattern 3: Platform Settings Key (copy from default_credit_cost)
**What:** Add to DEFAULTS, VALID_KEYS, and validate_setting()
**When to use:** workspace_credit_cost_pulse
**Example:**
```python
# Source: backend/app/services/platform_settings.py (existing pattern)
DEFAULTS: dict[str, str] = {
    # ... existing keys ...
    "workspace_credit_cost_pulse": json.dumps("5.0"),
}

# In validate_setting():
elif key == "workspace_credit_cost_pulse":
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return "workspace_credit_cost_pulse must be a number"
    if value <= 0:
        return "workspace_credit_cost_pulse must be greater than 0"
```

### Pattern 4: User Classes YAML (add fields to all 5 tiers)
**What:** Add workspace_access (bool) and max_active_collections (int) to each tier
**When to use:** ADMIN-01
**Example:**
```yaml
user_classes:
  free_trial:
    display_name: "Free Trial"
    credits: 100
    reset_policy: none
    workspace_access: true
    max_active_collections: 1
  free:
    display_name: "Free"
    credits: 10
    reset_policy: weekly
    workspace_access: false
    max_active_collections: 0
  standard:
    display_name: "Standard"
    credits: 100
    reset_policy: weekly
    workspace_access: true
    max_active_collections: 5
  premium:
    display_name: "Premium"
    credits: 500
    reset_policy: monthly
    workspace_access: true
    max_active_collections: -1
  internal:
    display_name: "Internal"
    credits: 0
    reset_policy: unlimited
    workspace_access: true
    max_active_collections: -1
```

### Pattern 5: Alembic env.py Registration
**What:** Import new model modules in alembic/env.py for autogenerate detection
**When to use:** After creating model files
**Example:**
```python
# Add to alembic/env.py imports:
from app.models import (user, file, chat_message, chat_session,
    search_quota, password_reset, admin_audit_log, user_credit,
    credit_transaction, invitation, platform_setting, api_key,
    collection, signal, report, pulse_run)  # <-- add these 4
```

### Pattern 6: models/__init__.py Registration
**What:** Import and export new models/tables in __init__.py
**When to use:** After creating model files
**Example:**
```python
from app.models.collection import Collection, CollectionFile
from app.models.signal import Signal
from app.models.report import Report
from app.models.pulse_run import PulseRun, pulse_run_files

# Add to __all__:
__all__ = [
    # ... existing ...
    "Collection", "CollectionFile", "Signal", "Report",
    "PulseRun", "pulse_run_files",
]
```

### Anti-Patterns to Avoid
- **Using `__tablename__ = "files"` for CollectionFile:** This would collide with the existing `File` model. MUST use `"collection_files"`.
- **PostgreSQL ENUM types for status/category/severity:** The codebase uses String(N) to avoid ALTER TYPE migration pain. Follow the pattern.
- **Separate migration per table:** A single migration for all tables is cleaner and ensures FK ordering is correct.
- **Creating API routes or service layers:** Phase 47 is models + migration + config ONLY.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| UUID generation | Custom ID generation | `uuid4` default on mapped_column | Consistent with all existing models |
| Timestamp handling | Manual timezone logic | `DateTime(timezone=True)` + `datetime.now(timezone.utc)` lambda | Codebase-wide pattern |
| JSON serialization for settings | Custom JSON handling | `json.dumps()` / `json.loads()` in platform_settings.py | Matches existing DEFAULTS pattern |
| Migration file | Manual SQL DDL | `alembic revision --autogenerate` then review | Catches FK ordering, indexes |

## Common Pitfalls

### Pitfall 1: CollectionFile Import Collision
**What goes wrong:** Naming the table "files" or importing as `File` causes conflict with `app.models.file.File`
**Why it happens:** Natural naming instinct
**How to avoid:** Use `__tablename__ = "collection_files"` and class name `CollectionFile` -- already decided in CONTEXT.md
**Warning signs:** Import errors or table creation failures

### Pitfall 2: Migration FK Ordering
**What goes wrong:** Tables created in wrong order cause FK constraint failures
**Why it happens:** Alembic autogenerate sometimes orders tables alphabetically rather than dependency-first
**How to avoid:** Review autogenerated migration and reorder: collections -> collection_files, pulse_runs -> pulse_run_files -> signals -> reports. Or write migration manually with correct ordering.
**Warning signs:** `alembic upgrade head` fails with "relation does not exist"

### Pitfall 3: Forgetting alembic/env.py Import
**What goes wrong:** `alembic revision --autogenerate` produces empty migration
**Why it happens:** Alembic only sees models imported in env.py via Base.metadata
**How to avoid:** Add imports to env.py BEFORE running autogenerate
**Warning signs:** Migration has empty upgrade() / downgrade()

### Pitfall 4: Missing models/__init__.py Registration
**What goes wrong:** Models importable from their module but not from `app.models`
**Why it happens:** Forgetting to add to __init__.py and __all__
**How to avoid:** Add imports and __all__ entries for all new models and junction tables
**Warning signs:** ImportError when downstream code does `from app.models import Collection`

### Pitfall 5: NUMERIC vs Float for credit_cost
**What goes wrong:** Using Float for credit_cost loses precision
**Why it happens:** Float is the natural Python type
**How to avoid:** Use `NUMERIC(10, 1)` matching the existing `CreditTransaction.amount` pattern
**Warning signs:** Rounding errors in credit calculations

### Pitfall 6: Nullable FK Without Explicit nullable=True
**What goes wrong:** SQLAlchemy 2.0 Mapped[] typing can infer non-nullable when you want nullable
**Why it happens:** `Mapped[UUID | None]` needs explicit `nullable=True` on mapped_column
**How to avoid:** Always pair `Mapped[UUID | None]` with `nullable=True` on the mapped_column
**Warning signs:** Migration creates NOT NULL constraint where nullable was intended

## Code Examples

### Complete Model: Collection (with CollectionFile)
```python
# backend/app/models/collection.py
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.signal import Signal
    from app.models.report import Report
    from app.models.pulse_run import PulseRun

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="collections")
    collection_files: Mapped[list["CollectionFile"]] = relationship(
        "CollectionFile", back_populates="collection",
        cascade="all, delete-orphan"
    )
    pulse_runs: Mapped[list["PulseRun"]] = relationship(
        "PulseRun", back_populates="collection",
        cascade="all, delete-orphan"
    )
    signals: Mapped[list["Signal"]] = relationship(
        "Signal", back_populates="collection",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="collection",
        cascade="all, delete-orphan"
    )


class CollectionFile(Base):
    __tablename__ = "collection_files"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    file_id: Mapped[UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="collection_files"
    )
    file: Mapped["File"] = relationship("File")
```

### Complete Model: PulseRun (with junction table)
```python
# backend/app/models/pulse_run.py
from sqlalchemy import Table, Column, String, Text, DateTime, ForeignKey, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.file import File
    from app.models.signal import Signal
    from app.models.report import Report

pulse_run_files = Table(
    "pulse_run_files",
    Base.metadata,
    Column("pulse_run_id", ForeignKey("pulse_runs.id", ondelete="CASCADE"), primary_key=True),
    Column("file_id", ForeignKey("files.id", ondelete="CASCADE"), primary_key=True)
)

class PulseRun(Base):
    __tablename__ = "pulse_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="pending")
    credit_cost: Mapped[float] = mapped_column(NUMERIC(10, 1))
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="pulse_runs")
    files: Mapped[list["File"]] = relationship("File", secondary=pulse_run_files)
    signals: Mapped[list["Signal"]] = relationship(
        "Signal", back_populates="pulse_run",
        cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="pulse_run"
    )
```

### Complete Model: Signal
```python
# backend/app/models/signal.py
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.pulse_run import PulseRun

class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    pulse_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("pulse_runs.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255))
    severity: Mapped[str] = mapped_column(String(20))  # critical, warning, info
    category: Mapped[str] = mapped_column(String(50))   # trend, anomaly, distribution, correlation
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chart_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    chart_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # bar, line, scatter
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="signals")
    pulse_run: Mapped["PulseRun"] = relationship("PulseRun", back_populates="signals")
```

### Complete Model: Report
```python
# backend/app/models/report.py
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.pulse_run import PulseRun

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    collection_id: Mapped[UUID] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"),
        index=True, nullable=False
    )
    pulse_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("pulse_runs.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    report_type: Mapped[str] = mapped_column(String(50))  # pulse_detection, investigation, chat_session
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    collection: Mapped["Collection"] = relationship("Collection", back_populates="reports")
    pulse_run: Mapped["PulseRun"] = relationship("PulseRun", back_populates="reports")
```

### Migration Pattern (manual, FK-ordered)
```python
# Correct table creation order in migration:
# 1. collections (depends on users)
# 2. collection_files (depends on collections, files)
# 3. pulse_runs (depends on collections)
# 4. pulse_run_files (depends on pulse_runs, files)
# 5. signals (depends on collections, pulse_runs)
# 6. reports (depends on collections, pulse_runs)
```

### User Model back_populates Addition
```python
# In backend/app/models/user.py, add relationship:
collections: Mapped[list["Collection"]] = relationship(
    "Collection", back_populates="user",
    cascade="all, delete-orphan"
)
# And TYPE_CHECKING import:
from app.models.collection import Collection
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQLAlchemy 1.x Column() | SQLAlchemy 2.0 Mapped[] + mapped_column() | 2023 | This project already uses 2.0 style |
| PostgreSQL ENUM types | String(N) columns | Project decision | Avoids ALTER TYPE migration complexity |
| Separate migration per model | Single migration for related tables | Best practice | Atomic schema change, correct FK ordering |

## Open Questions

1. **Report.pulse_run_id ondelete behavior**
   - What we know: Reports reference PulseRuns; if a PulseRun is deleted, the Report may still be useful
   - What's unclear: Should it be CASCADE (delete report too) or SET NULL (keep report, lose source link)?
   - Recommendation: Use SET NULL -- reports are standalone artifacts once generated. Users may want to keep reports even if the run data is purged.

2. **User.collections relationship back_populates**
   - What we know: Adding a relationship to User model requires modifying user.py
   - What's unclear: Whether downstream code needs `user.collections` lazy-loaded
   - Recommendation: Add it for completeness -- matches existing pattern (user.files, user.chat_sessions). Use default lazy loading.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0.0 + pytest-asyncio >= 0.23.0 |
| Config file | backend/pyproject.toml (dev dependency) |
| Quick run command | `cd backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMIN-01 | user_classes.yaml has workspace_access and max_active_collections for all 5 tiers with correct defaults | unit | `cd backend && python -m pytest tests/test_user_classes_workspace.py -x` | No - Wave 0 |
| ADMIN-02 | workspace_credit_cost_pulse in DEFAULTS, VALID_KEYS, validate_setting() | unit | `cd backend && python -m pytest tests/test_platform_settings_pulse.py -x` | No - Wave 0 |
| -- | All 5 model modules import without error | unit (smoke) | `cd backend && python -c "from app.models import Collection, CollectionFile, Signal, Report, PulseRun, pulse_run_files"` | No - Wave 0 |
| -- | Migration runs cleanly (requires DB) | integration | `cd backend && alembic upgrade head` | Manual verification |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green + `alembic upgrade head` clean run

### Wave 0 Gaps
- [ ] `backend/tests/test_user_classes_workspace.py` -- validates workspace_access and max_active_collections fields exist with correct values for all 5 tiers (ADMIN-01)
- [ ] `backend/tests/test_platform_settings_pulse.py` -- validates workspace_credit_cost_pulse in DEFAULTS, VALID_KEYS, and validate_setting() accepts/rejects correct values (ADMIN-02)
- [ ] `backend/tests/test_models_import.py` -- smoke test that all new models import without errors from app.models

## Sources

### Primary (HIGH confidence)
- Existing codebase files (direct inspection):
  - `backend/app/models/file.py` -- UUID PK, FK, timestamp patterns
  - `backend/app/models/chat_session.py` -- M2M junction table pattern (session_files)
  - `backend/app/models/credit_transaction.py` -- NUMERIC(10,1) for credit amounts
  - `backend/app/services/platform_settings.py` -- DEFAULTS, VALID_KEYS, validate_setting()
  - `backend/app/config/user_classes.yaml` -- tier config structure
  - `backend/app/models/__init__.py` -- model registration pattern
  - `backend/alembic/env.py` -- model import registration for autogenerate
  - `backend/alembic/versions/b3f8a1c2d4e5_add_api_keys_table.py` -- migration pattern
  - `backend/alembic/versions/c1d2e3f4a5b6_add_api_key_id_to_credit_transactions.py` -- current Alembic HEAD

### Secondary (MEDIUM confidence)
- Phase 47 CONTEXT.md -- all implementation decisions locked by owner

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- all patterns are direct copies of existing codebase patterns
- Pitfalls: HIGH -- identified from codebase inspection and common SQLAlchemy/Alembic issues

**Key facts for planner:**
- Current Alembic HEAD revision: `c1d2e3f4a5b6`
- 5 model classes + 1 junction table across 4 new files
- 3 integration points: models/__init__.py, alembic/env.py, user.py (back_populates)
- 2 config changes: user_classes.yaml (2 new fields x 5 tiers), platform_settings.py (1 new key)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable domain, no external dependencies)
