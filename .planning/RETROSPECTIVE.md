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

### Top Lessons (Verified Across Milestones)

1. **UAT gap closure phases are essential** — Discovered in v0.3 (Phase 19), reinforced in v0.5, v0.6, v0.7. Plan for a gap closure plan at the end of complex phases.
2. **New DB tables need corresponding admin view updates** — Missed in v0.5 (credit stats) and v0.7 (API usage in admin). Always audit admin dashboards when adding usage-tracking tables.
3. **New deployment modes need isolated container testing** — Both v0.6 (Dokploy config) and v0.7 (api mode) had post-ship hotfixes that only appeared in real container deployments.
