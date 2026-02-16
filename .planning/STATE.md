# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** v0.5 Admin Portal -- Phase 27 Credit System

## Current Position

Phase: 27 of 31 (Credit System)
Plan: 4 of 4 (27-04 complete -- Phase 27 complete)
Status: Phase Complete
Last activity: 2026-02-16 -- Completed 27-04 scheduled credit reset

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 ✅ | v0.5 [███░░░░░░░] ~20%

## Performance Metrics

**Velocity (v0.1):**
- Total plans completed: 36
- Total execution time: ~5 days (Feb 1-6, 2026)
- Plans per day: ~7 plans/day

**Velocity (v0.2):**
- Total plans completed: 19
- Total execution time: ~4 days (Feb 7-10, 2026)
- Plans per day: ~5 plans/day

**Velocity (v0.3):**
- Total plans completed: 23
- Total execution time: ~3 days (Feb 10-12, 2026)
- Plans per day: ~8 plans/day

**Velocity (v0.4):**
- Total plans completed: 15 (Phases 20-25 complete)
- Total execution time: ~3 days (Feb 12-14, 2026)
- Plans per day: ~5 plans/day

## Accumulated Context

### Decisions

See PROJECT.md Key Decisions table for full decision log.

v0.5 Architecture decisions (from requirements + research):
- Split-horizon deployment: same FastAPI codebase, `SPECTRA_MODE` env var (public/admin/dev)
- Lazy import of admin_router inside mode check to avoid loading admin code in public mode
- Catch-all /api/admin/* in public mode logs WARNING for security monitoring
- X-Admin-Token exposed in CORS headers for sliding window token reissue
- Admin frontend: separate Next.js app (`admin-frontend/`), not a route in existing frontend
- Credit system: NUMERIC(10,1) precision, SELECT FOR UPDATE for atomicity, deduct before agent runs
- Static user tiers: defined in `user_classes.yaml`, admin edits credit overrides in platform_settings
- Platform settings: key-value DB table with 30s TTL cache, runtime changes without restart
- Admin auth: `is_admin` flag on users table, first admin seeded via CLI, defense-in-depth (JWT + DB check)
- No separate admin refresh token; sliding window reissue via AdminTokenReissueMiddleware
- In-memory login lockout for admin (upgrade to Redis for multi-instance)
- Audit entries added to caller's transaction (no separate commit)
- String(20) for user_class (not PostgreSQL ENUM) to avoid ALTER TYPE migration pain
- Three-step migration pattern: add columns with server_default, create tables, backfill data
- One new backend dep (APScheduler), one new frontend lib (Recharts)

### Pending Todos

- [ ] Create Dokploy Docker deployment package (deployment)
- [ ] Query safety filter in Manager Agent (security)
- [ ] Show suggestions in Data Summary sidebar panel (ui)
- [ ] Use Pydantic structured output for agent JSON responses (consistency)

### Blockers/Concerns

- Credit deduction timing with SSE streaming: deduct before agent, no refund on failure (matches LLM billing patterns)
- SearchQuota coexistence: decide during Phase 27 whether web searches deduct credits or keep separate quota
- E2B sandboxes created per-execution (no warm pools) -- acceptable for now

## Session Continuity

Last session: 2026-02-16
Stopped at: Completed Phase 27 Credit System (all 4 plans)
Resume with: Verification running, then Phase 28
