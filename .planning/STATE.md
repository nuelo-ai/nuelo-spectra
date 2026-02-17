# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-16)

**Core value:** Accurate data analysis through correct, safe Python code generation
**Current focus:** v0.5 Admin Portal -- Phase 31 Dashboard & Admin Frontend

## Current Position

Phase: 31 of 31 (Dashboard & Admin Frontend)
Plan: 3 of 5 complete
Status: In Progress
Last activity: 2026-02-17 -- Completed 31-03 Dashboard Page

Progress: v0.1 ✅ | v0.2 ✅ | v0.3 ✅ | v0.4 ✅ | v0.5 [████████░░] ~75%

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
- In-memory token revocation set with TTL for immediate logout on user deactivation (same single-instance caveat)
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

- Credit deduction timing with SSE streaming: resolved -- deduct before agent, no refund on failure (implemented in 27-03)
- SearchQuota coexistence: web searches keep separate quota for now (not deducting credits)
- E2B sandboxes created per-execution (no warm pools) -- acceptable for now

## Session Continuity

Last session: 2026-02-17
Stopped at: Completed 31-03-PLAN.md (Dashboard Page)
Resume with: `/gsd:execute-phase 31` to continue with Plan 04
