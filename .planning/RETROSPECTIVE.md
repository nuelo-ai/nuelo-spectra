# Project Retrospective: Spectra

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v0.7 — API Services & MCP

**Shipped:** 2026-02-25 (final production patch: v0.7.10 on 2026-02-27)
**Phases:** 4 (Phases 38-41) | **Plans:** 15

### What Was Built

- API key infrastructure with SHA-256 hashing, `spe_` prefix, user self-service + admin management, and Alembic migration
- Public REST API v1 — file management (upload, list, download, delete), file context (get/update/suggestions), synchronous query endpoint
- Credit deduction and API usage logging middleware on all `/v1/` requests with structured request/error logging and credit refund on failure
- `SPECTRA_MODE=api` as 5th deployment mode (standalone Dokploy service) with wildcard CORS
- MCP server with 6 curated `spectra_` tools via FastMCP 3.0.2 mounted at `/mcp/` with Streamable HTTP transport
- Bearer token auth middleware for MCP with per-request validation on tool calls and tool listing
- Post-ship: 7 hotfix patches (v0.7.4–v0.7.10) addressing MCP auth, chart decoding, admin credit display, and API query attribution

### What Worked

- **Loopback architecture for MCP:** MCP tools calling REST API via httpx loopback kept the billing/logging chain intact with zero duplication — clean single responsibility for both layers
- **Unified auth dependency:** `get_authenticated_user()` with JWT fast-path + SHA-256 key fallback meant zero changes to existing frontend auth; API keys "just worked"
- **FastMCP manual curation over auto-generation:** Manually describing each of the 6 tools produced far better LLM tool descriptions than auto-generated ones would have
- **Stateless HTTP transport for MCP:** No session state requirement simplified deployment and load-balancer compatibility from day one
- **UAT gap closure phases:** Dedicating Phase 39 UAT round 2 and Phase 40 gap closure plan (40-04) to production-found issues caught real bugs (context update flush/commit, error envelope mismatch) before final tag

### What Was Inefficient

- **7 post-ship hotfixes:** MCP async state bugs, loopback URL misconfiguration, binary Plotly array decoding, and admin credit display were all caught post-ship rather than in UAT — better MCP integration tests would have caught these earlier
- **Credit usage display for API users:** Admin panels didn't show API query data in activity/sessions tabs at launch — this was a predictable gap given the new api_usage_logs table, should have been included in Phase 38 requirements
- **SPECTRA_MODE=api not tested in Docker Compose locally:** All testing done against dev mode; the 5th Dokploy service had startup issues (v0.7.5) that only appeared in a real api-mode container

### Patterns Established

- **`spe_` prefix convention:** Recognizable prefix on API keys (and `spectra_` prefix on MCP tools) makes them easy to identify in logs, configs, and API references
- **Phase X-04 gap closure plan:** Pattern of a dedicated gap closure plan (e.g., 39-04, 39-05, 40-04) at the end of each phase for UAT-discovered issues has proven reliable across v0.5, v0.6, v0.7
- **API_MCP_REFERENCE.md:** Adding a structured API reference doc (created in v0.7.8) alongside DEPLOYMENT.md as a developer-facing artifact is valuable for external users

### Key Lessons

1. **MCP async state requires end-to-end integration tests** — Unit tests don't catch ASGI lifecycle bugs (await set_state/get_state); need a real MCP host connection test
2. **New data sources require admin display updates** — When adding api_usage_logs, immediately identify all admin dashboard views that aggregate user activity and extend them; don't leave it for post-ship
3. **Test all SPECTRA_MODE values in Docker** — Dev mode and api mode behave differently; startup validation and CORS config should be smoke-tested in each mode before tagging

### Cost Observations

- Model profile: quality (claude-opus-4-6 for planning/research, claude-sonnet-4-6 for execution)
- 4 phases, 15 plans, 88 commits across 4 days (Feb 21-24, 2026) + 7 hotfixes over 3 days (Feb 24-27)
- 161 files changed, +21,470 / -3,106 lines (including hotfixes)

---

## Milestone: v0.7.12 — Spectra Pulse Mockup

**Shipped:** 2026-03-05
**Phases:** 5 (42–46) | **Plans:** 17

### What Was Built
- App shell + Hex.tech dark palette with sidebar collapse, credit indicator, and theme toggle (Phase 42)
- Collection list/detail, Run Detection flow with credit estimate and loading state, Signal results with severity-sorted panel (Phase 42)
- Collections four-tab hub, full-page markdown report reader, Chat-to-Collection bridge modal (Phase 43)
- Guided Investigation Q&A with doctor-style flow, progress indicator, root cause summary, history list, and related signals (Phase 44)
- What-If Scenarios: objective selection, scenario cards, per-scenario refinement chat overlay, comparison view, generated report section (Phase 45)
- Admin Workspace Activity Dashboard (line/donut/bar/funnel/stacked charts), per-user Workspace tab, Settings (8 credit cost inputs + dismissable alerts) (Phase 46)

### What Worked
- **Separate Next.js app** (`pulse-mockup/`) was the right call — zero interference with production code, independent deploy, no bundling concerns
- **Hex.tech dark palette** as a single design constraint kept all screens visually coherent across 5 different feature areas
- **GSD phase grouping by feature area** (not by page count) made each phase self-contained and easy to UAT
- **key={selectedScenarioId} remount pattern** for chat components is a clean React idiom — no manual state cleanup
- **Violet for What-If, blue for Investigation** — color-coding feature themes is intuitive and worth formalizing for v0.8+

### What Was Inefficient
- COLL-01 (archive/unarchive status indicators) and COLL-02 (collection limit display) were never checked off — checkbox hygiene in REQUIREMENTS.md lagged behind implementation
- v0.7.12 was a post-ship polish commit but not called out as a separate GSD plan — should have been a quick task or plan 46-04 to keep execution history clean
- Phase 42–43 SUMMARY.md files didn't capture `one_liner` fields — made automated accomplishment extraction fail (gsd-tools returned empty)

### Patterns Established
- **Mockup-first milestone before feature implementation** — creates concrete design artifact with zero backend risk; reviewers get full E2E flow before a line of real code is written
- **Feature color theming** — violet/What-If, blue/Investigation — should be documented as a design system decision in v0.8 implementation plan
- **Admin layout without shared Header** — each page owns its own title; simpler and more flexible for admin-specific layouts

### Key Lessons
- When closing a mockup milestone, explicitly check REQUIREMENTS.md checkbox parity against what was actually built during each phase execution
- Post-ship polish commits (like v0.7.12) should either be a named quick task or an explicit plan to maintain clean execution history
- SUMMARY.md `one_liner` field should be filled — GSD tooling depends on it for MILESTONES.md auto-population

### Cost Observations
- Sessions: ~8 across 3 days
- All work in a standalone Next.js app made context much cheaper — no backend complexity in scope
- Phase-by-phase execution was efficient; no rework rounds needed

---

## Milestone: v0.8 — Spectra Pulse (Detection)

**Shipped:** 2026-03-10
**Phases:** 8 (47–52.1, including 2 inserted decimal phases) | **Plans:** 20

### What Was Built
- Data Foundation: 5 SQLAlchemy models with Alembic migration and tier config
- Backend CRUD API: 11 collection endpoints with WorkspaceAccess tier gating and Pydantic schemas
- Pulse Agent: LangGraph pipeline with E2B sandbox (300s), Pydantic-validated Signal output, credit pre-check/deduction/refund
- Frontend Migration: All workspace screens in main Next.js app with Hex.tech palette, (workspace) route group, and Plotly charts
- Pipeline Refactor (Phase 51.1): Monolith → multi-agent orchestrator with structured output, inline progress, toast, re-run dialog
- Admin & QA + Collection Management: Tier gating verified E2E, Pulse credit cost in admin settings, delete/rename collection

### What Worked
- **Mockup-first reference** (v0.7.12) made Phase 51 migration very efficient — every screen had a pixel-perfect reference to match
- **Phased E2B work** (Phase 49 before frontend) caught Pulse Agent schema issues early, before any UI existed
- **Decimal phase insertions** (51.1, 52.1) are the right pattern for urgent mid-milestone additions — no renumbering disruption
- **Pydantic structured output** on all reasoning LLM calls eliminated JSON parsing failures that plagued the old pipeline
- **Inline progress banner** (not full-page overlay) was the correct UX decision — users can navigate freely during long-running detection

### What Was Inefficient
- SIGNAL-03 was shipped but not checked off in REQUIREMENTS.md — requirement tracking lagged behind implementation
- The Pipeline Refactor (Phase 51.1) was inserted mid-milestone after the monolith showed quality issues in testing; ideally would have been planned from the start
- Several post-execution fixes after Phase 52.1 (kebab nav, per-collection Zustand state, 402 toast) — these should have been caught in Phase 52 QA

### Patterns Established
- **Workspace route group pattern**: `(workspace)` parallel to `(dashboard)` — prevents sidebar layout inheritance across feature areas
- **Per-collectionId Zustand state**: Scoping detection state by collectionId via `collectionDetection[id]` map, with reactive selectors (not getter functions)
- **Pulse orchestrator architecture**: Brain node → per-hypothesis sub-agent loop (Coder → Validator → Sandbox → Interpreter → Viz) → Report Writer
- **CollectionFile naming convention**: `__tablename__ = "collection_files"` to avoid collision with `app.models.file.File`

### Key Lessons
1. **Schema-validate Pulse output before building UI** — Phase 49 (Pulse Agent first) was the right call; late schema discovery would have required UI rework
2. **Structured Pydantic output is non-negotiable for multi-step pipelines** — Raw LLM JSON parsing fails silently; structured output fails loudly and is debuggable
3. **DropdownMenu inside Link requires e.preventDefault() on trigger** — React's event propagation through Link elements is a recurring frontend gotcha worth documenting
4. **Reactive Zustand selectors required for per-ID state** — Getter functions are not subscriptions; `useStore(s => s.map[id]?.field)` is the correct pattern

### Cost Observations
- Model mix: quality profile (claude-sonnet-4-6) throughout
- Sessions: 8+ sessions across 4 days
- Notable: Phase 51.1 pipeline refactor was the most expensive phase (full rewrite of pulse.py + frontend UX); Phase 47 data foundation was the cheapest (schema-only, no LLM calls in execution)

---

## Milestone: v0.8.1 — UI Fixes & Enhancement

**Shipped:** 2026-03-10
**Phases:** 2 (53–54) | **Plans:** 10

### What Was Built
- Shell & Navigation Fixes: SidebarTrigger added to all workspace sub-views (Collection Detail, Signal View all 4 render states, Report View all 3 render states); nav icon alignment fixed via SidebarGroup wrapper; Spectra logo removed from Chat and Files panel headers; Chat rightbar toggle pinned to viewport right edge
- Pulse Analysis Fixes: Credits Used stat card wired to actual aggregate subquery; date+time timestamps in activity feed and file tables via toLocaleString; mobile-responsive Signal View with showDetail toggle; Chat bridge button in SignalDetailPanel opening new tab

### What Worked
- **Verification plan pattern (53-04, 54-04):** Human visual verification plans caught 2 LBAR gaps before milestone close — gap closure plans 53-05 and 53-06 resolved them cleanly
- **Root cause analysis before fixing:** LBAR-02 required two attempts (pl-1 removal first, then SidebarGroup wrapper) — the second fix was found by tracing the shadcn padding inheritance chain rather than guessing
- **toLocaleString discovery:** Found a real browser compatibility gotcha (toLocaleDateString silently ignoring time options) — immediately documented as a pattern for future timestamp work

### What Was Inefficient
- LBAR-02 required two plan passes (53-01 and then 53-06) — the pl-1 fix alone was insufficient; root cause (missing SidebarGroup) should have been identified in the first plan
- Phase 53-04 verification identified a gap ("Chat with Spectra" button) that was actually PULSE-03 scope — migrating it to Phase 54 was the right call but could have been avoided with tighter initial scoping

### Patterns Established
- **SidebarTrigger header strip pattern:** `shrink-0 border-b` div above `flex-1 overflow-y-auto` — not sticky/fixed; now the standard for all pages needing persistent header above scrollable content
- **SidebarGroup wraps SidebarMenu for nav alignment:** SidebarMenu alone lacks `p-2` context; SidebarGroup wrapper required for icon alignment with chat history list
- **toLocaleString for timestamps:** Never use `toLocaleDateString` when time display is needed — use `toLocaleString` with explicit locale options

### Key Lessons
1. **Verify padding inheritance chain before fixing alignment** — Don't patch child padding; find the correct parent context provider (SidebarGroup in shadcn case)
2. **Timestamp formatting: toLocaleString ≠ toLocaleDateString** — `toLocaleDateString` with `hour`/`minute` options appears correct but silently ignores them in all browsers
3. **Visual verification plans reveal real gaps** — Plans 53-04 and 54-04 caught actual defects post-implementation; always include a human-verify plan for UI-heavy phases

### Cost Observations
- Model profile: quality (claude-sonnet-4-6)
- 2 phases, 10 plans, 2 days — fastest milestone to date
- Patch milestone scope (UI-only, no backend schema changes) kept context very cheap

---

## Milestone: v0.9 — Monetization

**Shipped:** 2026-04-14
**Phases:** 5 (Phases 55-59) | **Plans:** 15

### What Was Built

- 5-tier model (Free Trial, On Demand, Basic, Premium) with dual-balance credit tracking (subscription + purchased) and subscription-first deduction
- Trial expiration enforcement with backend 402 blocking, countdown banner with amber urgency, and full blocking overlay
- Stripe billing backend: SubscriptionService with 9 operations, webhook router with signature verification and event deduplication, checkout endpoints for subscriptions and credit top-ups (31 passing tests)
- Billing UI: Plan Selection with live pricing and proration preview, Manage Plan with subscription status, credit balances, top-up purchase, billing history
- Admin billing tools: force-set tier with Stripe sync, refund with proportional credit deduction, billing settings with Stripe Price auto-creation, discount codes with Stripe Coupon/Promotion Code sync
- Settings restructured with tab navigation (Profile, API Keys, Plan, Billing)

### What Worked

- **Phase dependency chain (55→56→57→58→59):** Linear dependencies meant each phase built cleanly on the previous — no merge conflicts or integration surprises
- **Hosted Stripe Checkout over embedded:** Owner decision to use redirect instead of embedded Checkout eliminated @stripe/stripe-js dependency and simplified the frontend significantly
- **Webhook-driven architecture:** Making Stripe webhooks the source of truth for subscription state kept the system consistent without polling or sync complexity
- **Dual-balance credit model designed upfront:** Separating subscription and purchased credits in Phase 55 prevented refactoring in later phases when billing flows needed to distinguish credit types

### What Was Inefficient

- **REQUIREMENTS.md checkbox tracking:** 27 of 59 requirement checkboxes weren't ticked despite all work being complete — traceability table showed "Pending" for phases 58-59 even after UAT passed. Manual checkbox maintenance doesn't scale.
- **Parallel worktree conflicts (Phase 58):** Plans 58-01 and 58-02 ran in parallel worktrees but 58-02 depended on subscription.py from 58-01, causing a blocking merge conflict
- **Stripe SDK v14 migration pain:** Multiple fixes needed for client.v1 namespace, items.data[0] period dates, and create_preview API — SDK upgrade documentation was insufficient

### Patterns Established

- **Hosted checkout pattern:** Use Stripe redirect checkout for all payment flows, not embedded — simpler, fewer deps
- **Webhook idempotency via dedup table:** stripe_events table with event_id uniqueness prevents duplicate processing
- **Admin billing tab pattern:** User detail gets a billing tab (6th position) with subscription card, payment history, and Stripe event log

### Key Lessons

- **Stripe SDK upgrades need a research phase:** v14 changed namespaces, parameter locations, and API patterns. Research phase caught most issues but some only surfaced during execution.
- **Parallel worktree plans must not share files_modified:** Phase 58 worktree conflict was avoidable — plan checker should enforce no overlap in files_modified between parallel plans.
- **Trial enforcement path exemptions are tricky:** Multiple auth paths (web, API, MCP) each needed independent trial checking — easy to miss one.

### Cost Observations
- Model profile: quality (opus)
- 5 phases, 15 plans, 8 days (2026-03-18 → 2026-03-26)
- 174 files changed, +25,065 / -6,547 lines
- Most complex milestone to date: Stripe integration, webhooks, billing UI, admin tools

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Timeline | Key Process Change |
|-----------|--------|-------|----------|--------------------|
| v0.1 | 6 | 36 | 5 days | Initial GSD setup, no retro |
| v0.2 | 7 | 19 | 4 days | Added UAT rounds per phase |
| v0.3 | 6 | 23 | 3 days | Gap closure phases for UAT issues |
| v0.4 | 6 | 11 | 3 days | Non-fatal error handling pattern established |
| v0.5 | 7 | 24 | 2 days | Audit milestone before complete; deferred reqs tracked |
| v0.6 | 5 | 10 | 3 days | Docker multi-stage; all modes tested in containers |
| v0.7 | 4 | 15 | 4 days (+3 patches) | MCP loopback arch; 7 hotfixes post-ship |
| v0.7.12 | 5 | 17 | 3 days (+1 polish patch) | Mockup-first milestone pattern; separate Next.js app |
| v0.8 | 8 | 20 | 4 days | Decimal phase insertions for mid-milestone urgents; Pydantic structured output on all pipelines |
| v0.8.1 | 2 | 10 | 2 days | Patch milestone pattern; verification plans catching post-impl gaps before close |
| v0.9 | 5 | 15 | 8 days | Stripe webhook-driven billing; hosted checkout over embedded; dual-balance credit model |

### Cumulative Quality

| Milestone | Requirements | Satisfaction | Known Deferred |
|-----------|-------------|-------------|----------------|
| v0.1 | 42 | 100% | 0 |
| v0.2 | 54 | 100% | 0 |
| v0.3 | 37 | 100% | 0 |
| v0.4 | 43 | 100% | 0 |
| v0.5 | 86 | 95% | 3 (CREDIT-11, SETTINGS-06, TIER-02) |
| v0.6 | 28 | 100% | 0 |
| v0.7 | 30 | 100% | 0 |
| v0.7.12 | 34 | 94% | 2 (COLL-01, COLL-02) |
| v0.8 | 35 | 100% | 0 |
| v0.8.1 | 12 | 100% | 0 |
| v0.9 | 59 | 100% | 0 |

### Top Lessons (Verified Across Milestones)

1. **UAT gap closure phases are essential** — Discovered in v0.3 (Phase 19), reinforced in v0.5, v0.6, v0.7. Plan for a gap closure plan at the end of complex phases.
2. **New DB tables need corresponding admin view updates** — Missed in v0.5 (credit stats) and v0.7 (API usage in admin). Always audit admin dashboards when adding usage-tracking tables.
3. **New deployment modes need isolated container testing** — Both v0.6 (Dokploy config) and v0.7 (api mode) had post-ship hotfixes that only appeared in real container deployments.
