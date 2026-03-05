# Pitfalls Research

**Domain:** Adding Pulse Analysis (statistical detection + LLM agents) to existing LLM-powered data analytics SaaS
**Milestone:** v0.8 Spectra Pulse (Detection)
**Researched:** 2026-03-05
**Confidence:** HIGH (based on direct codebase inspection + verified patterns from previous milestones)

---

## Critical Pitfalls

### Pitfall 1: CollectionFile Model Named "File" — Direct Collision With Existing `File` Model

**What goes wrong:**
The v0.8 milestone plan names the new collection attachment model `File` (in the table labelled "Key Fields"). The existing codebase already has `app.models.file.File` (SQLAlchemy model, `__tablename__ = "files"`) which is imported in 8+ locations (`models/__init__.py`, `services/file.py`, `routers/admin/dashboard.py`, `models/user.py`, `models/chat_session.py`, etc.). Introducing a second `File` SQLAlchemy model creates a Python import collision, SQLAlchemy mapper conflict, and causes `models/__init__.py`'s `__all__` to shadow whichever `File` is imported second.

**Why it happens:**
The milestone requirements doc uses the word "File" naturally in the domain context (files attached to a collection). The developer copies the name into a new model file without noticing the existing `app.models.file.File` already occupies that class name in the global model registry.

**How to avoid:**
Name the new model `CollectionFile` with `__tablename__ = "collection_files"`. This is unambiguous in Python imports, SQLAlchemy mapper registration, and route naming. Update all references in the milestone plan to use `CollectionFile` consistently (API docs, service methods, schemas). Never introduce a SQLAlchemy model whose class name matches an existing model name.

**Warning signs:**
- `sqlalchemy.exc.InvalidRequestError: Table 'files' is already defined` at startup
- Import errors like `cannot import name 'File' from app.models` behaving unexpectedly after adding the new model
- Admin dashboard queries returning wrong row counts because the query hits the wrong table

**Phase to address:** v0.8, Phase 1 (Data Model). Must be resolved before writing any model code.

---

### Pitfall 2: Credit Deduction Before E2B Sandbox Completes — No Atomic Rollback on Partial Failure

**What goes wrong:**
The credit pre-check pattern is: (1) check balance, (2) deduct, (3) execute, (4) refund on failure. Step (2) and step (3) are not inside the same database transaction. If the Pulse agent starts (E2B sandbox created, code begins executing) and then the backend process restarts, the request times out (FastAPI `stream_timeout_seconds: 180`), or the sandbox exits with a partial result, credits are deducted but never refunded. The existing credit service uses `SELECT FOR UPDATE` within a single DB session flush — but the refund is triggered by application-level error handling. If the FastAPI worker crashes or the async context is abandoned, the refund `except` block never runs.

**Why it happens:**
Pulse runs are long-lived (statistical analysis across multiple files, multiple detection passes). The longer the operation, the higher the probability the request lifecycle ends before the refund path executes. The existing `CreditService.deduct_credit()` was designed for synchronous query runs (seconds), not for multi-second statistical analysis jobs.

**How to avoid:**
Implement a credit reservation pattern instead of immediate deduction:
1. Record a `credit_reservation` row (pending status, amount, user_id, operation_id) before executing
2. The reservation is visible to balance checks (balance = actual balance minus sum of pending reservations)
3. On success: convert reservation to a committed `CreditTransaction` and delete the reservation row
4. On failure/timeout: a background cleanup job (APScheduler, already in the stack) scans for stale reservations (older than N minutes) and cancels them

If reservation pattern is too complex for v0.8, at minimum: wrap deduct + execute + refund in a try/finally where the finally always attempts refund, and add an APScheduler job that identifies orphaned deductions (credits deducted with no corresponding Signal rows created within X minutes) and auto-refunds them.

**Warning signs:**
- Users report "lost credits" after a Pulse run that "seemed to hang"
- Credit transaction log shows deductions with no matching `pulse_run` activity log entry
- E2B `Sandbox.create()` succeeding but `sandbox.run_code()` timing out (default 60s per existing config, but Pulse analysis may need 120–300s)

**Phase to address:** v0.8, Phase 2 (Pulse Agent + Credit Integration). Design the refund safety net before implementing the Pulse endpoint.

---

### Pitfall 3: E2B Sandbox Timeout Too Short For Multi-File Statistical Analysis

**What goes wrong:**
The existing E2B configuration sets `sandbox_timeout_seconds: 60` and `stream_timeout_seconds: 180`. The existing use case — a single chat query generating pandas code for one file — typically completes in under 30 seconds. The Pulse Agent runs a fundamentally different workload: data profiling (column statistics across N files), anomaly detection (Z-scores, IQR outliers across potentially large datasets), trend analysis, and concentration analysis — all in a single sandbox session. For a Collection with 3 files of 50MB each, this could take 3–8 minutes. At 60 second sandbox timeout, the Pulse run will consistently time out and fail.

**Why it happens:**
The sandbox timeout was sized for interactive chat analysis (one question, one pandas computation). The developer reuses the same `E2BSandboxRuntime(timeout_seconds=60)` instantiation without increasing the timeout for the Pulse workload.

**How to avoid:**
- Introduce a separate `PULSE_SANDBOX_TIMEOUT_SECONDS` setting (default: 300) distinct from `sandbox_timeout_seconds`
- Instantiate `E2BSandboxRuntime(timeout_seconds=300)` in the Pulse Agent specifically
- Design the Pulse Agent to run analyses sequentially (one detection type per E2B execution), not all in one monolithic script. This both avoids single-execution timeouts and makes partial failures recoverable (if trend analysis fails, anomaly detection results are already captured)
- Cap Collection file size for Pulse at a lower limit than the 50MB chat limit (e.g., 20MB per file for Pulse), or sample large files before statistical analysis

**Warning signs:**
- E2B returns `TimeoutError` consistently for Pulse runs with more than 1 file
- Zero Signals generated despite data clearly containing anomalies
- Credit deducted but Signals table empty (which also triggers Pitfall 2)

**Phase to address:** v0.8, Phase 2 (Pulse Agent). Set timeout before writing any Pulse execution code.

---

### Pitfall 4: Dashboard Layout Wraps Workspace Pages in Chat Sidebar — Structural Mismatch

**What goes wrong:**
The main frontend's `(dashboard)/layout.tsx` unconditionally renders `ChatSidebar` (left) + `LinkedFilesPanel` (right) around all child pages. The v0.8 workspace routes (`/workspace` and `/workspace/collections/[id]`) will be placed inside the dashboard route group to benefit from auth-protection — but the mockup's workspace design expects a different sidebar (a workspace nav sidebar with "Pulse Analysis", "Chat", "Files" entries) and no right-side LinkedFilesPanel. If the workspace pages inherit the dashboard layout as-is, every workspace page renders with a Chat-specific sidebar showing chat history and a file-link panel that has no meaning in the workspace context.

**Why it happens:**
Next.js App Router route groups (`(dashboard)`) apply their `layout.tsx` to every route nested within them. Developers assume all authenticated pages share the same layout, forgetting that the workspace is a distinct top-level product area with its own navigation model.

**How to avoid:**
Create a new route group `(workspace)` at the same level as `(dashboard)`, with its own `layout.tsx` that renders the workspace-specific sidebar (migrated from `pulse-mockup/src/components/layout/`). The workspace layout should share auth-guard logic (reuse `useAuth` hook) but render an entirely different shell. Do not nest `/workspace` inside `(dashboard)`. Directory structure:
```
src/app/
  (auth)/         <- login, register
  (dashboard)/    <- chat, my-files, sessions, settings
  (workspace)/    <- workspace, workspace/collections/[id]
```

**Warning signs:**
- Workspace pages show chat session list in sidebar
- "LinkedFilesPanel" renders on the right side of the Collections detail page
- Breadcrumb or page header overlaps with ChatSidebar's user menu section

**Phase to address:** v0.8, Phase 3 (Frontend Migration). Establish route group structure before migrating any workspace components.

---

### Pitfall 5: CSS Color Token Conflict Between Mockup Hex.tech Palette and Existing Nord Palette

**What goes wrong:**
The pulse-mockup uses a Hex.tech-inspired dark palette: `--background: #0a0e1a`, `--card: #111827`, `--primary: #3b82f6`. The existing main frontend uses Nord: `--background: #2E3440`, `--card: #3B4252`. Both are defined as CSS custom properties on `:root` in `globals.css`. When workspace components migrated from the mockup are placed into the main frontend, they render with Nord's tokens (because the main `globals.css` wins), producing visually incorrect results — cards are too light, backgrounds don't match the workspace design intent, the "deep navy" atmosphere is lost.

**Why it happens:**
The mockup's design is intentionally more visually distinctive than the existing Nord theme. The milestone plan states "treat the mockup as the new design standard" — but this requires a deliberate token migration, not just copying components. Developers copy components without reconciling the global CSS.

**How to avoid:**
Before migrating any components, audit and update the main frontend's `globals.css` dark mode tokens to match the mockup's Hex.tech palette. This is a one-time `globals.css` update that affects all existing pages — which is intentional per the milestone plan ("design refresh"). The update replaces Nord dark tokens (`#2E3440`, `#3B4252`, etc.) with the mockup's dark tokens (`#0a0e1a`, `#111827`, `#1e293b`). Test existing Chat and Files pages after the token change to verify no regressions. Do not apply workspace-specific overrides via scoped CSS — the token change should be global.

**Warning signs:**
- Workspace cards appear noticeably lighter/grayer than the mockup reference
- Charts and components designed against `#111827` card background look washed out
- Existing Chat pages change appearance unexpectedly (expected and intentional — this is the design refresh, not a bug)

**Phase to address:** v0.8, Phase 3 (Frontend Migration), first step before any component migration.

---

### Pitfall 6: Missing `ThemeProvider` in Main Frontend Causes Mockup Components to Ignore Dark Mode

**What goes wrong:**
The pulse-mockup `providers.tsx` wraps children with `ThemeProvider` from `next-themes` (attribute="class", defaultTheme="dark"). The main frontend `providers.tsx` does NOT include `ThemeProvider` at the top level — it only has `QueryClientProvider` and `AuthProvider`. When workspace components migrated from the mockup use the `useTheme()` hook from `next-themes` to determine current theme, the hook returns `undefined` because there is no `ThemeProvider` ancestor, causing components to silently fall back to their hard-coded dark styles regardless of the user's theme preference.

**Why it happens:**
The mockup was a standalone app with its own provider setup. The main frontend applies theming differently. The developer migrates components without checking whether `useTheme()` is available in the main app's provider tree.

**How to avoid:**
Before migrating any theme-aware components, verify whether the main frontend already wraps a `ThemeProvider`. Check `frontend/src/app/providers.tsx` and `frontend/src/app/layout.tsx`. The `ThemeProvider` is currently absent in the main frontend's `providers.tsx`. Add it matching the mockup's configuration (`attribute="class"`, `defaultTheme="dark"`, `enableSystem={false}`). Ensure it wraps the entire app, not just the workspace layout.

**Warning signs:**
- `useTheme()` returns `undefined` in migrated workspace components
- Recharts SignalChart renders with incorrect colors in light mode (stuck on dark colors)
- No console error — silent failure where theme toggle has no effect on workspace pages

**Phase to address:** v0.8, Phase 3 (Frontend Migration), provider audit step before any component migration.

---

### Pitfall 7: Alembic Migration Table Name Inconsistency

**What goes wrong:**
If the developer creates the new CollectionFile model with `__tablename__ = "files"` (falling into Pitfall 1), the Alembic migration will generate `op.create_table('files', ...)` which fails immediately with `psycopg2.errors.DuplicateTable: relation "files" already exists`. Even if the name is changed, inconsistency between the model's `__tablename__` and the migration's `create_table()` call causes silent schema drift: the model thinks it maps to `collection_files` but the table is actually `collectionfile`.

**Why it happens:**
Developers copy a migration from a previous one and forget to update the table name string. Alembic's `--autogenerate` may not detect the mismatch depending on what's already in the migration history.

**How to avoid:**
- Always set `__tablename__` explicitly on every new SQLAlchemy model
- After `alembic revision --autogenerate`, review the generated migration file before running it — confirm every `create_table()` call matches the intended `__tablename__` exactly
- Use the three-step migration pattern established in v0.5 (`dfe836ff84e9` migration) for any column additions to existing tables: add nullable first, then backfill, then alter NOT NULL
- Run `alembic check` or inspect `alembic history` to verify no duplicate revision IDs

**Warning signs:**
- `alembic upgrade head` exits with `DuplicateTable` or `DuplicateObject`
- Backend starts but queries return 0 rows when they should return data (wrong table name in model)
- `alembic check` reports unexpected differences between model metadata and database

**Phase to address:** v0.8, Phase 1 (Data Model) — migration authoring step.

---

### Pitfall 8: Pulse Agent LLM Output Inconsistency Breaks Signal Parsing

**What goes wrong:**
The existing agent system is noted in PROJECT.md as having "Agent JSON responses not using Pydantic structured output (inconsistent across providers)". The Pulse Agent must produce structured Signal objects (title, description, severity, category, visualization config, statistical evidence) from LLM output. Without Pydantic structured output, the LLM may return JSON with missing fields, incorrect severity values outside the allowed set (`critical`, `warning`, `info`), or visualization configs with wrong chart type keys. The Signal parsing code fails, Signals are not created, and the user gets zero results from a successful (and credit-consuming) Pulse run.

**Why it happens:**
This is a known deferred issue from v0.5 (explicitly listed in PROJECT.md Known Limitations). The developer assumes the Pulse Agent will reliably return valid JSON because the Coding Agent does — but the Coding Agent's output is Python code (forgiving to parse) whereas Signals require schema-validated JSON with an enum field.

**How to avoid:**
For the Pulse Agent specifically (even while keeping the deferral for other agents):
1. Use a strict output schema: define a `PulseAgentOutput` Pydantic model with `signals: list[SignalSchema]` where `SignalSchema` validates `severity` against `Literal["critical", "warning", "info"]`
2. Implement a fallback parser: if LLM output fails Pydantic validation, attempt to extract valid Signal fields via json.loads with defaults for missing fields rather than failing the entire run
3. Add a validation step after Signal generation that rejects any Signal missing required fields and logs the failure at WARNING level
4. Test the Pulse Agent against all configured LLM providers before release — inconsistency is provider-specific

**Warning signs:**
- `pydantic.ValidationError` in Pulse endpoint logs
- Signal table contains rows with NULL severity or NULL title
- Frontend Signal cards fail to render because `signal.severity` is not in `["critical", "warning", "info"]`

**Phase to address:** v0.8, Phase 2 (Pulse Agent). Design the Signal output schema before writing the agent prompt.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Reuse existing 60s sandbox timeout for Pulse runs | No new config needed | Pulse runs consistently time out for any non-trivial dataset | Never — Pulse workload is fundamentally different from chat queries |
| Name new model `File` matching the existing `File` | Natural domain language in code | Import collisions, mapper conflicts, broken admin queries | Never — namespace collision in a shared model registry |
| Skip Pydantic structured output for Pulse Agent (continue existing pattern) | Consistent with other agents | Signal parsing failures silently discard Pulse results the user paid for | Never for Pulse — Signal schema must be validated |
| Put workspace routes inside `(dashboard)` route group | Auth protection comes for free | Chat sidebar and LinkedFilesPanel render on all workspace pages | Never — workspace needs its own layout |
| Migrate mockup components without updating `globals.css` tokens | Faster migration | Components render with wrong Nord palette instead of Hex.tech palette | Never — tokens must be reconciled before component migration |
| Use synchronous DEDUCT -> RUN -> REFUND_ON_FAIL with no safety net | Matches existing chat pattern | Long-running Pulse runs that crash leave users without credits | Never — add APScheduler orphan-refund job in same phase |
| Hardcode `platform_settings` key strings for Pulse credit cost in-line | Avoids constants file | Key strings like `workspace_credit_cost_pulse` scattered across service, router, and tests | Acceptable for v0.8 with a TODO comment, but create a constants module before v0.9 |

---

## Integration Gotchas

Common mistakes when connecting to these systems in v0.8.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| E2B sandbox (Pulse) | Uploading all Collection files at once to one monolithic sandbox execution | Split analyses across separate E2B executions per detection type (anomaly, trend, concentration) — more resilient, avoids memory limits |
| E2B sandbox (Pulse) | Using stored `file_path` to read the file from the server's filesystem inside the sandbox | The sandbox is a remote VM — files must be explicitly uploaded via `sandbox.files.write()`. Read file bytes from local disk, upload to sandbox each run |
| Platform Settings service | Adding `workspace_credit_cost_pulse` to `DEFAULTS` dict but forgetting to add it to `VALID_KEYS` | Both `DEFAULTS` and `VALID_KEYS` must be updated in `platform_settings.py` or the key is rejected as invalid |
| CreditService | Calling `deduct_credit()` from within an already-open DB transaction that later rolls back | `deduct_credit()` uses `SELECT FOR UPDATE` — the credit deduction is only rolled back if the same DB session that flushed it is explicitly rolled back. Ensure the refund path uses the same session |
| `user_classes.yaml` extension | Adding `workspace_access` field without a default for tiers that don't define it | The `get_class_config()` service must provide a safe default (`workspace_access: False`) when the key is absent, or existing tiers that predate v0.8 will raise `KeyError` |
| Next.js App Router (workspace) | Placing `workspace/collections/[id]/signals/page.tsx` inside `(dashboard)` group | Next.js will apply the dashboard layout — workspace routes must be in a separate `(workspace)` group with their own layout |
| Recharts (signal chart) | Using the chart type string from `signal.chartType` directly as a Recharts component name | Recharts component names don't map 1:1 to the mockup's chart type strings — add an explicit mapping function in `SignalChart` component |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Fetching all Signals for a Collection in a single query with no pagination | Collection detail page slow to load, DB query returns 50+ rows | Paginate or cap Signal display at top-N by severity from the start | At 20+ Signals per collection (possible for large datasets) |
| Loading full column profile JSON in `GET /collections` list endpoint | Collections list page slow for users with many collections | `GET /collections` should return summary fields only (name, status, counts) — column profiles belong on the detail endpoint | At 10+ collections per user |
| Loading full file bytes into memory to upload to E2B for large files | Backend OOM for 50MB CSV x 3 files simultaneously | Stream file bytes in chunks; consider file size cap for Pulse | 3 files x 50MB = 150MB in memory per concurrent Pulse request |
| `platform_settings.py` cache not invalidated after admin updates `workspace_credit_cost_pulse` | Pulse continues using old credit cost for up to 30s after admin change | Existing 30s TTL is acceptable — document it in Admin UI as "Changes take effect within 30 seconds" | Immediate effect expected by admin (known acceptable limitation, document it) |

---

## Security Mistakes

Domain-specific security issues for v0.8.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Pulse Agent code runs with access to all Collection files by filename — LLM-generated code could exfiltrate via filenames | Prompt injection could craft filenames to read arbitrary sandbox-accessible paths | The E2B sandbox enforces network isolation and file access limits. Verify the Pulse Agent's allowlist does not include `os`, `subprocess`, or `shutil` beyond what chat agents allow |
| Collection ownership not enforced at `GET /collections/{id}` | Horizontal privilege escalation — user A reads user B's Collection and Signals | Every Collection query must include `WHERE user_id = current_user.id` — follow the same pattern as `FileService` which scopes all queries to `user_id` |
| Signal visualization config stored as JSON — if rendered as raw HTML | XSS from LLM-generated content stored in Signal records | Never inject Signal JSON fields as raw HTML; the Recharts chart renderer must extract only typed fields (chartType, data, labels) from the JSON, not render arbitrary content |
| Tier access check happens only at Collection creation — not on `POST /collections/{id}/pulse` | User downgraded after collection creation can still run Pulse | Re-check `workspace_access` tier flag on every Pulse trigger, not just on Collection creation |

---

## UX Pitfalls

Common user experience mistakes specific to v0.8.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Detection Results page shows "0 signals found" without explaining why | User paid 5 credits and sees nothing — no idea if data had no anomalies or if analysis failed | Always explain the outcome: "No anomalies detected in this dataset" vs "Analysis failed — credits have been refunded" |
| Severity label "opportunity" used in Pulse Agent output but not in the frontend severity color scheme | Frontend SignalDetailPanel only handles `critical`, `warning`, `info` — "opportunity" renders with no color badge | The milestone plan already notes that "opportunity" is NOT in the mockup's severity scheme. Pulse Agent prompt must use only `critical`, `warning`, `info` |
| Full-page detection loading state blocks back navigation | User cannot cancel a running Pulse — stuck on loading screen if analysis takes 3+ minutes | Provide a "Cancel" action that aborts the run and triggers refund; or at minimum, allow navigation away with a toast "Detection running in background" |
| Credit cost shown as a static label ("5 credits") hardcoded in the frontend | User sees "5 credits" in UI, is charged a different amount because admin changed the platform setting | Fetch the live credit cost from the settings API before rendering the estimate — do not hardcode `5` in the frontend |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Collection creation:** Verify that the Collection is correctly owned by `current_user.id` in the POST handler, not silently created without user_id
- [ ] **Pulse endpoint credit pre-check:** Verify the check uses the live platform setting from the database (`workspace_credit_cost_pulse`), not a hardcoded `5` constant, so admin changes take effect
- [ ] **Signal severity validation:** Verify the Pulse Agent never generates `severity: "opportunity"` — check the agent prompt explicitly bans this value and that the Pydantic schema rejects it
- [ ] **CollectionFile vs File model isolation:** Verify that `GET /files` (existing user files endpoint) never returns CollectionFile rows and vice versa — check that the new model uses a different table name (`collection_files`) and separate service/router
- [ ] **E2B sandbox timeout config:** Verify the Pulse Agent instantiates `E2BSandboxRuntime` with a Pulse-specific timeout (not the default 60s)
- [ ] **Workspace auth guard:** Verify that unauthenticated requests to `/workspace` redirect to login — confirm the `(workspace)` layout.tsx implements the same `useAuth` guard as `(dashboard)` layout.tsx
- [ ] **Tier gating on Pulse trigger:** Verify `POST /collections/{id}/pulse` re-checks `workspace_access` in user's tier YAML at runtime, not just at Collection creation time
- [ ] **Credit refund on Pulse failure:** Manually test by injecting a Pulse Agent failure mid-run — confirm credits are returned to the user's balance and a refund transaction is logged
- [ ] **Detection Results page auto-selects first signal:** Verify `SignalListPanel` auto-selects the highest severity Signal on mount — otherwise the right panel is empty on first load
- [ ] **globals.css token update scope:** After updating Nord -> Hex.tech palette tokens, manually verify existing Chat and My Files pages in both light and dark modes

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| CollectionFile named "File" — mapper collision discovered after tables created | MEDIUM | Alembic `downgrade` to before the migration, rename model class and `__tablename__`, re-autogenerate migration, re-run upgrade. No data loss if caught before users create Collections. |
| Credits deducted but Pulse failed and refund path not reached | MEDIUM | Write a one-off SQL query to find `credit_transactions` with `transaction_type='usage'` in the Pulse window with no matching `Signal` rows; issue manual credit adjustments via admin portal Credit Adjust. Then add the APScheduler orphan-refund job going forward. |
| Workspace routes inside `(dashboard)` layout — Chat sidebar on workspace pages | LOW | Move route files from `(dashboard)/workspace/` to new `(workspace)/` route group, create new layout.tsx. No data changes required. |
| globals.css token update breaks existing Chat page appearance | LOW | Revert `globals.css` dark token changes, reconcile incrementally — update one token at a time and verify against both Chat and workspace components. |
| Pulse sandbox timeout causing all runs to fail | LOW | Update `PULSE_SANDBOX_TIMEOUT_SECONDS` env var or config default and redeploy. No data migration required. |
| Pulse Agent generates "opportunity" severity — frontend renders badge-less | LOW | Add a severity normalization step in Signal creation service: map `"opportunity"` -> `"info"` and log a warning. Update agent prompt in YAML and redeploy without DB changes. |

---

## Pitfall-to-Phase Mapping

How v0.8 roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| CollectionFile name collision with existing `File` model | Phase 1: Data Model — naming decision before any code | `from app.models import File, CollectionFile` in Python REPL — both resolve without shadowing |
| Credit deduction with no atomic rollback on partial failure | Phase 2: Pulse Agent + Credit Integration — design refund safety net first | Integration test: inject Pulse failure mid-run, verify credits returned |
| E2B sandbox timeout too short for Pulse workload | Phase 2: Pulse Agent — set Pulse-specific timeout before first Pulse run | Run Pulse on a 3-file collection, all analyses complete without TimeoutError |
| Dashboard layout wrapping workspace with Chat sidebar | Phase 3: Frontend Migration — create `(workspace)` route group first | Navigate to `/workspace` and verify ChatSidebar is absent from page |
| CSS token conflict Nord vs Hex.tech palette | Phase 3: Frontend Migration — update `globals.css` before any component copy | Visual comparison of workspace pages against mockup screenshots |
| Missing ThemeProvider in main frontend providers | Phase 3: Frontend Migration — provider audit before component migration | `useTheme()` returns a defined value in a workspace component |
| Alembic migration table name inconsistency | Phase 1: Data Model — review auto-generated migration before running | `alembic upgrade head` succeeds, `alembic check` shows no remaining differences |
| Pulse Agent JSON output inconsistency breaks Signal parsing | Phase 2: Pulse Agent — Pydantic output schema for Signals defined first | Send Pulse runs across all configured LLM providers, all produce valid Signals |
| Severity "opportunity" in Pulse output — frontend badge missing | Phase 2: Pulse Agent — prompt explicitly lists allowed severity values | Query `Signal` table for `severity NOT IN ('critical', 'warning', 'info')` after bulk test run |
| Live credit cost hardcoded in frontend instead of fetched from settings | Phase 3: Frontend Migration — wire credit estimate to settings API | Change `workspace_credit_cost_pulse` in admin, verify UI reflects new value without rebuild |

---

## Sources

- Direct codebase inspection: `backend/app/models/__init__.py`, `backend/app/models/file.py` — existing `File` model and import tree (8+ import sites)
- Direct codebase inspection: `backend/app/services/sandbox/e2b_runtime.py` — sandbox timeout configuration (60s default, per-execution fresh sandbox)
- Direct codebase inspection: `backend/app/config.py` — `sandbox_timeout_seconds: 60`, `stream_timeout_seconds: 180`
- Direct codebase inspection: `backend/app/services/credit.py` — `SELECT FOR UPDATE` atomic deduction pattern, no built-in orphan refund mechanism
- Direct codebase inspection: `backend/app/services/platform_settings.py` — TTL cache pattern, `DEFAULTS` and `VALID_KEYS` co-registration requirement
- Direct codebase inspection: `frontend/src/app/(dashboard)/layout.tsx` — `ChatSidebar` + `LinkedFilesPanel` hardcoded, applied to all dashboard children
- Direct codebase inspection: `pulse-mockup/src/app/globals.css` vs `frontend/src/app/globals.css` — `#0a0e1a` Hex.tech vs `#2E3440` Nord dark palette confirmed different
- Direct codebase inspection: `pulse-mockup/src/app/providers.tsx` — ThemeProvider present; `frontend/src/app/providers.tsx` — ThemeProvider absent
- Direct codebase inspection: `backend/app/agents/` directory structure — no Pydantic structured output, acknowledged in PROJECT.md Known Limitations
- Milestone plan: `requirements/Pulse-req-milestone-plan.md` — Credit Pre-Check Pattern, E2B Sandbox Reuse, Agent System Extension, Frontend Migration sections
- PROJECT.md — Known Limitations: "Agent JSON responses not using Pydantic structured output", "E2B sandboxes created per-execution (~150ms cold start per query)"
- Previous milestone pitfalls: `PITFALLS-v0.5-admin-portal.md`, `PITFALLS-v0.7-api-mcp.md` — established three-step migration pattern, credit atomicity pattern

---
*Pitfalls research for: v0.8 Spectra Pulse (Detection) — adding statistical analysis module to existing Spectra LLM platform*
*Researched: 2026-03-05*
