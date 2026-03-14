---
phase: 52-admin-and-qa
plan: 01
subsystem: api
tags: [pydantic, fastapi, pytest, tier-gating, platform-settings, credits]

# Dependency graph
requires:
  - phase: 47-backend-foundations
    provides: workspace_credit_cost_pulse stored as JSON string "5.0" in platform_settings
  - phase: 48-collections
    provides: CollectionService, create_collection route, WorkspaceUser dependency
provides:
  - GET /credit-costs endpoint returning {chat, pulse_run} for authenticated users
  - SettingsResponse and SettingsUpdateRequest extended with workspace_credit_cost_pulse
  - test_tier_gating.py with 7 passing tests covering all 5 tiers
  - 52-SMOKE-TEST.md with 4-flow manual QA checklist
affects: [52-02, frontend workspace credit cost display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "credit_costs router uses json.loads() for JSON-encoded string settings, not float() directly"
    - "tier gating tests use unittest.mock with patch on app.routers.collections.get_class_config and CollectionService.count_user_collections"
    - "require_workspace_access tested by calling the async function directly with mocked get_class_config"

key-files:
  created:
    - backend/app/routers/credit_costs.py
    - backend/tests/test_tier_gating.py
    - .planning/phases/52-admin-and-qa/52-SMOKE-TEST.md
  modified:
    - backend/app/schemas/platform_settings.py
    - backend/app/main.py

key-decisions:
  - "CreditCostsResponse uses chat and pulse_run keys (not default_credit_cost/workspace_credit_cost_pulse) for frontend-friendly naming and v0.9 extensibility"
  - "TestWorkspaceAccess covers free tier only — free_trial has workspace_access=True per user_classes.yaml; CONTEXT.md spec was incorrect"
  - "TestCollectionLimit tests free_trial tier (passes workspace, blocked on 2nd collection) matching actual tier config"

patterns-established:
  - "Pattern 1: All settings read via json.loads(settings.get(key, default)) — never float() directly on raw string"
  - "Pattern 2: Tier gating tests use direct async function calls with mocked dependencies, no TestClient/live server needed"

requirements-completed: [ADMIN-01, ADMIN-02]

# Metrics
duration: 4min
completed: 2026-03-09
---

# Phase 52 Plan 01: Admin Settings and Tier Gating Summary

**Pydantic schemas extended with workspace_credit_cost_pulse, GET /credit-costs endpoint added, 7 tier gating tests passing across all 5 tiers, 4-flow smoke test checklist created**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-09T17:12:47Z
- **Completed:** 2026-03-09T17:16:12Z
- **Tasks:** 3
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments
- Extended SettingsResponse and SettingsUpdateRequest with workspace_credit_cost_pulse including validator list update
- Created GET /credit-costs endpoint registered in public/dev mode block, returning CreditCostsResponse {chat, pulse_run}
- Implemented 7 tier gating tests across all 5 tiers (free, free_trial, standard, premium, internal) — all pass with unittest.mock, no live DB
- Created 52-SMOKE-TEST.md with 4 manual QA flows covering tier access gating, collection/pulse happy path, credit cost display, and admin settings round-trip

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Wave 0 test stubs and smoke test document** - `61def35` (test)
2. **Task 2: Extend platform settings schemas and create credit_costs router** - `d69092f` (feat)
3. **Task 3: Implement tier gating tests** - `a7268da` (test)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `backend/app/schemas/platform_settings.py` - Added workspace_credit_cost_pulse to SettingsResponse and SettingsUpdateRequest; updated validator list
- `backend/app/routers/credit_costs.py` - New GET /credit-costs endpoint with CreditCostsResponse {chat, pulse_run}
- `backend/app/main.py` - Registered credit_costs.router in public/dev block via lazy import
- `backend/tests/test_tier_gating.py` - 7 passing tests: TestWorkspaceAccess (2), TestCollectionLimit (2), TestUnlimitedTiers (3)
- `.planning/phases/52-admin-and-qa/52-SMOKE-TEST.md` - 4-flow manual QA checklist

## Decisions Made
- CreditCostsResponse uses `chat` and `pulse_run` keys for frontend-friendly naming and extensibility (v0.9+ adds investigate/whatif without breaking change)
- TestWorkspaceAccess covers free tier only — CONTEXT.md spec said "free AND free_trial" get workspace 403, but free_trial has workspace_access=True per user_classes.yaml. Tests match actual config.
- TestCollectionLimit tests free_trial tier: passes workspace access, blocked on 2nd collection create

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failures in test_code_checker.py, test_graph_visualization.py, test_llm_providers.py, test_pulse_agent.py, test_pulse_service.py, test_routing.py, test_user_classes_workspace.py confirmed as pre-existing before Phase 52 changes (25 total). Documented in deferred-items.md. No regressions introduced by this plan.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- GET /credit-costs endpoint ready for frontend workspace to consume via TanStack Query
- workspace_credit_cost_pulse PATCH endpoint ready for admin portal to configure
- Smoke test checklist ready for manual QA execution
- Phase 52-02 can proceed (admin frontend settings panel)

## Self-Check: PASSED

All created files found on disk. All task commits verified in git log.

---
*Phase: 52-admin-and-qa*
*Completed: 2026-03-09*
