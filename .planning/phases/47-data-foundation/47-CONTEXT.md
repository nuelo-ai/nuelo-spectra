# Phase 47: Data Foundation - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

SQLAlchemy models (Collection, CollectionFile, Signal, Report, PulseRun), Alembic migration creating all tables, user_classes.yaml config for workspace access and collection limits, and platform_settings key for Pulse credit cost. No API routes, no frontend, no agent logic.

</domain>

<decisions>
## Implementation Decisions

### Signal storage shape
- Statistical evidence stored as a single JSON column — Signals are read-whole for the detail panel, never queried by individual evidence fields
- Chart data (labels, values, axis config) stored as inline JSON column on Signal row — typically <50KB per signal, simple single-query reads
- Category field as String(50) column — flexible, no fixed enum, Pulse Agent outputs the category value (e.g., 'trend', 'anomaly', 'distribution', 'correlation')
- Severity as String(20) column — matches existing user_class pattern, validated at API layer via Pydantic Literal["critical","warning","info"]

### Detection run tracking
- PulseRun model groups Signals from a single detection execution — records collection_id, status (pending/running/completed/failed), credit_cost, timestamps, and error_message
- PulseRun tracks selected files via M2M junction table (pulse_run_files) — proper FK constraints, consistent with session_files M2M pattern
- Signal.pulse_run_id FK links each Signal to its originating PulseRun
- Re-runs keep all history — each PulseRun is immutable, new run creates new PulseRun + new Signals, UI shows latest run by default
- Error_message as nullable Text column on PulseRun — stores failure reason for debugging and refund audit trail

### Report content storage
- Markdown content stored as Text column in DB — simple reads, transactional consistency, reports typically <100KB, matches data_summary pattern on File model
- Report model uses report_type String(50) discriminator ('pulse_detection', 'investigation', 'chat_session') to identify source
- Polymorphic source via nullable FKs — only the relevant FK is populated per report; for v0.8 only pulse_run_id FK exists, additional FKs (investigation_id, chat_session_id) added via migration when those features ship
- Detection summary Report auto-generated on PulseRun completion — user sees it immediately in Reports tab without extra action

### Claude's Discretion
- Exact column lengths and index strategy
- Migration revision ID and dependencies
- Model relationship cascade/lazy-loading configuration
- PulseRun status transition logic details

</decisions>

<specifics>
## Specific Ideas

- Reports are polymorphic by source: Pulse detection, Investigation (v0.10), Chat sessions (bridge feature). All grouped under one Collection. The report_type + nullable FK pattern must accommodate future source types without schema redesign.
- Only pulse_run_id FK ships in v0.8 — no placeholder columns for tables that don't exist yet.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `PlatformSetting` model + `platform_settings.py` service: DEFAULTS dict and VALID_KEYS set pattern — add `workspace_credit_cost_pulse` key following exact same pattern
- `user_classes.yaml` structure: simple key-value per tier — add `workspace_access` (bool) and `max_active_collections` (int) fields
- `File` model (`backend/app/models/file.py`): UUID PK, user_id FK, created_at/updated_at pattern — template for new models
- `session_files` M2M table (`backend/app/models/chat_session.py`): junction table pattern — reuse for pulse_run_files

### Established Patterns
- UUID primary keys via `uuid4` default across all models
- `String(20)` for enum-like fields (user_class) instead of PostgreSQL ENUM — avoids ALTER TYPE migration pain
- `DateTime(timezone=True)` with `datetime.now(timezone.utc)` lambdas for timestamps
- `Base` from `app.models.base` as DeclarativeBase for all models
- `__init__.py` re-exports all models with `__all__` list
- `ForeignKey("table.id", ondelete="CASCADE")` with index=True on FK columns

### Integration Points
- `backend/app/models/__init__.py`: new models must be registered here for Alembic autogenerate
- `backend/app/config/user_classes.yaml`: add workspace fields to all 5 tiers
- `backend/app/services/platform_settings.py`: add key to DEFAULTS and VALID_KEYS, add validation in validate_setting()
- `backend/alembic/versions/`: new migration file

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 47-data-foundation*
*Context gathered: 2026-03-06*
