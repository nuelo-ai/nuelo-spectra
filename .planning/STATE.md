# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 38 — API Key Infrastructure

## Current Position

Phase: 38 of 41 (v0.7) — API Key Infrastructure
Plan: — (ready to plan)
Status: Ready to plan
Last activity: 2026-02-23 — v0.7 roadmap created (Phases 38-41)

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 ✅ | v0.5 ✅ | v0.6 ✅ | v0.7 🚧 Phase 38 of 41

## Performance Metrics

**Velocity (v0.6):**
- Total plans completed: 10 (Phases 33-37)
- Total execution time: ~3 days (Feb 19-21, 2026)
- Plans per day: ~3-4 plans/day

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| v0.6 (33-37) | 10 | ~3 days | ~7 hrs |

**Recent Trend:**
- Last milestone: v0.6 shipped cleanly — 5 phases, 10 plans, zero deferred items
- Trend: Stable

## Accumulated Context

### Decisions

See PROJECT.md Key Decisions table for full decision log.

Recent decisions relevant to v0.7:
- API keys use SHA-256 hashing (not Argon2) — high-entropy random token; SHA-256 is industry standard (GitHub, Stripe), no performance penalty
- `spe_<secrets.token_urlsafe(32)>` prefix format — recognizable in logs and configs
- MCP tools call REST API via httpx loopback — preserves credit deduction and usage logging middleware chain
- `scopes TEXT[]` and `expires_at TIMESTAMPTZ NULL` in api_keys schema from Phase 38 — avoids migration pain for P2 features
- Unified `get_authenticated_user()` dependency — JWT fast path first, SHA-256 key fallback; existing `get_current_user` unchanged
- MCP tool descriptions manually curated — FastMCP auto-generation produces poor LLM tool descriptions (confirmed in FastMCP docs)
- 120s uvicorn timeout for `spectra-api` service — LangGraph analysis runs 10-45s; default 30s timeout silently cuts legitimate queries

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment) — this milestone
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)
- [ ] Plan production environment variable cleanup and validation (deployment)

### Blockers/Concerns

- Phase 39: `slowapi>=0.1.9` compatibility with FastAPI 0.115+ and custom `key_func` — verify before writing rate limiting middleware (MEDIUM confidence)
- Phase 41: Verify `combine_lifespans` import path in FastMCP 3.x at implementation time — API may have shifted around v3.0 release (2026-01-19)
- Phase 41: Confirm `spectra-api` and `spectra-public` share same Dokploy host before deploying — `spectra_uploads` volume sharing is automatic only on single host; different host requires S3/NFS

## Session Continuity

Last session: 2026-02-23
Stopped at: v0.7 roadmap created — Phases 38-41 defined, ROADMAP.md and STATE.md written
Resume with: `/gsd:plan-phase 38`
