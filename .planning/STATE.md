# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 39 — API Key Management UI + Deployment Mode

## Current Position

Phase: 39 of 41 (v0.7) — API Key Management UI + Deployment Mode
Plan: 3 of 3 complete
Status: Phase 39 Complete
Last activity: 2026-02-24 — Completed 39-03 (Admin API Key Management UI)

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 ✅ | v0.5 ✅ | v0.6 ✅ | v0.7 🚧 Phase 39 of 41

## Performance Metrics

**Velocity (v0.6):**
- Total plans completed: 10 (Phases 33-37)
- Total execution time: ~3 days (Feb 19-21, 2026)
- Plans per day: ~3-4 plans/day

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| v0.6 (33-37) | 10 | ~3 days | ~7 hrs |
| 38-01 | 3 tasks | 3 min | 1 min |
| 38-02 | 2 tasks | 2 min | 1 min |
| 38-03 | 3 tasks | 3 min | 1 min |
| 38-04 | 3 tasks | 5 min | ~2 min |
| 39-01 | 2 tasks | 3 min | ~2 min |
| 39-02 | 2 tasks | 2 min | 1 min |
| 39-03 | 2 tasks | 2 min | 1 min |

**Recent Trend:**
- Last milestone: v0.6 shipped cleanly — 5 phases, 10 plans, zero deferred items
- Trend: Stable

## Accumulated Context

### Decisions

See PROJECT.md Key Decisions table for full decision log.

Recent decisions (v0.7 execution):
- Manual Alembic migration when no local DB available — verified via script loading and HEAD detection
- field_validator on spectra_mode rejects unknown modes at Settings construction (earlier than main.py)
- ApiKeyService authenticate() filters is_active==True in SQL WHERE clause (not post-fetch Python check)
- Service uses db.flush() not db.commit() -- FastAPI request lifecycle controls transaction boundary
- API key CRUD endpoints use CurrentUser (JWT-only), not get_authenticated_user -- users manage keys via frontend session
- get_authenticated_user uses spe_ prefix check for fast-path API key routing, skipping JWT decode
- oauth2_scheme_optional with auto_error=False for unified auth dependency manual error handling
- window.confirm() for API key revoke confirmation — matches existing settings component simplicity
- One-time key display Dialog with explicit "I have copied my key" dismissal — prevents accidental key loss (research pitfall #6)
- API mode CORS uses allow_origins=["*"] with allow_credentials=False — Bearer token auth, not cookies; wildcard+credentials is CORS-spec violation
- Credit usage always visible (even 0.0) in API key list — users see the field exists before Phase 40 populates data
- Cleaned Alembic autogenerate migration to only include api_keys changes — excluded unrelated checkpoint/chat_messages schema drift
- Named FK constraint fk_api_keys_created_by_admin for explicit downgrade support
- Added foreign_keys=[ApiKey.user_id] to User.api_keys relationship to resolve ambiguous FK from dual api_keys->users FKs
- AlertDialog UI component added to admin-frontend (copied from frontend) for revoke confirmation pattern
- Revoked keys shown inline with opacity-50 and line-through, not filtered out — admin sees full key history

Research decisions (v0.7 planning):
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

Last session: 2026-02-24
Stopped at: Completed 39-03-PLAN.md (Admin API Key Management UI) — Phase 39 complete
Resume with: Continue with Phase 40
