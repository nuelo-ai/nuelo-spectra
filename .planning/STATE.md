# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-23)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** Phase 40 — REST API v1 Endpoints

## Current Position

Phase: 40 of 41 (v0.7) — REST API v1 Endpoints
Plan: 3 of 3 complete
Status: Phase 40 Complete
Last activity: 2026-02-24 — Completed 40-03 (Query Endpoint & Usage Logging)

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 ✅ | v0.5 ✅ | v0.6 ✅ | v0.7 🚧 Phase 40 of 41

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
| 39-04 | 2 tasks | 2 min | 1 min |
| 39-05 | 2 tasks | 1 min | ~30s |

**Recent Trend:**
- Last milestone: v0.6 shipped cleanly — 5 phases, 10 plans, zero deferred items
- Trend: Stable
| 40-01 | 3 tasks | 3 min | 1 min |
| Phase 40 P02 | 2min | 2 tasks | 3 files |
| 40-03 | 2 tasks | 3 min | 1.5 min |

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
- created_by_admin_id added to base ApiKeyListItem (not just AdminApiKeyListItem) so public frontend receives it via GET /v1/keys
- Only set Content-Type: application/json when request body is present — avoids issues with 204 No Content responses on DELETE
- Use onSettled instead of onSuccess for revoke query invalidation — ensures cache refresh even if client-side error occurs after server processes

Research decisions (v0.7 planning):
- API keys use SHA-256 hashing (not Argon2) — high-entropy random token; SHA-256 is industry standard (GitHub, Stripe), no performance penalty
- `spe_<secrets.token_urlsafe(32)>` prefix format — recognizable in logs and configs
- MCP tools call REST API via httpx loopback — preserves credit deduction and usage logging middleware chain
- `scopes TEXT[]` and `expires_at TIMESTAMPTZ NULL` in api_keys schema from Phase 38 — avoids migration pain for P2 features
- Unified `get_authenticated_user()` dependency — JWT fast path first, SHA-256 key fallback; existing `get_current_user` unchanged
- MCP tool descriptions manually curated — FastMCP auto-generation produces poor LLM tool descriptions (confirmed in FastMCP docs)
- 120s uvicorn timeout for `spectra-api` service — LangGraph analysis runs 10-45s; default 30s timeout silently cuts legitimate queries
- [Phase 40]: CreditService.refund() uses SELECT FOR UPDATE pattern matching deduct_credit for atomicity
- [Phase 40]: ApiKeyService.authenticate() returns tuple (User, api_key_id) instead of just User — enables downstream api_key_id tracking
- [Phase 40]: Cleaned Alembic migration of unrelated schema drift — only api_usage_logs changes kept
- [Phase 40]: Synchronous onboarding on upload (await, not create_task) per user decision
- [Phase 40]: Download endpoint returns FileResponse (binary stream), not JSON envelope
- [Phase 40]: Hybrid logging: middleware for structured Python logs, explicit DB logging in credit-consuming endpoints
- [Phase 40]: build_chat_graph(checkpointer=None) for stateless API queries instead of get_or_create_graph()
- [Phase 40]: Messages in initial_state directly (not aupdate_state) since no checkpointer exists

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
Stopped at: Completed 40-03-PLAN.md (Query Endpoint & Usage Logging) — Phase 40 complete
Resume with: Continue with Phase 41 (MCP Integration)
