# Phase 52: Admin and QA - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify tier gating, collection limits, and `workspace_credit_cost_pulse` configuration are all working end-to-end before v0.8 ships. This phase delivers: (1) admin settings gap fix for `workspace_credit_cost_pulse`, (2) live credit cost wiring to the frontend button, (3) automated tier gating tests, and (4) a manual smoke test checklist. No new user-facing features.

</domain>

<decisions>
## Implementation Decisions

### Admin settings gap — workspace_credit_cost_pulse
- Add `workspace_credit_cost_pulse` field to `SettingsResponse` and `SettingsUpdateRequest` Pydantic schemas in `backend/app/schemas/platform_settings.py`
- Field lives inside the **existing Credits card** in `SettingsForm.tsx` — below "Default Credit Cost per Message", same card, same Save button
- Label: **"Pulse Detection Cost per Run"** — mirrors existing label style
- Saves with the same Save button as all other settings (single PATCH request, no separate save)
- Frontend validates before submitting: toast error if value ≤ 0 (same pattern as existing `defaultCreditCost` validation)
- Admin frontend `types/settings.ts` `PlatformSettings` type needs `workspace_credit_cost_pulse: number` added

### Credit cost wiring — live endpoint
- New **GET /credit-costs** endpoint on the backend (registered without prefix in `main.py`, same as `/collections`, `/auth`, `/files`)
- Frontend calls it as **GET /api/credit-costs** — Next.js proxy strips `/api` and forwards to backend
- Requires standard auth (CurrentUser, not admin) — workspace is auth-gated anyway
- Response shape: `{ chat: number, pulse_run: number }` — future keys (investigate, whatif) added as v0.9+ features arrive
- `chat` value reads from `default_credit_cost` platform setting; `pulse_run` reads from `workspace_credit_cost_pulse`
- Frontend uses TanStack Query with **staleTime ~5 minutes** (credit costs rarely change mid-session)
- While loading: button shows a **loading animation** (spinner/skeleton) — does not show hardcoded fallback
- Removes `const CREDIT_COST = 5` hardcode from `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx`

### QA — automated tier gating tests
- New file: `backend/tests/test_tier_gating.py`
- Test scenarios:
  1. **Workspace access 403**: `free` and `free_trial` tier users hit `GET /collections` and `POST /collections` → expect 403 with "workspace access not available on your plan"
  2. **Collection limit enforcement**: `free_trial` tier user creates 1 collection (201 OK), second `POST /collections` → expect 403 with "Collection limit reached"
  3. **Unlimited tiers**: `standard`, `premium`, `internal` tier users can create collections without hitting a limit (201 OK on multiple creates)
- Tests use existing pytest fixtures for DB and HTTP test client
- Does NOT include a credit cost config test (out of scope for this phase's automated tests)

### Smoke test — manual QA checklist
- Scope: **workspace and Pulse flows only** (not existing chat/files)
- Format: markdown checklist in `52-SMOKE-TEST.md` inside the phase directory
- Checklist covers four flows:
  1. **Tier access gating UI** — log in as free-tier user, confirm `/workspace` shows access-gated state (not 500, not blank)
  2. **Collection + Pulse flow** — create collection, upload file, trigger Pulse, wait for results, verify signals + report appear
  3. **Credit cost display** — verify "Run Detection (N credits)" button shows live value from platform settings
  4. **Admin settings round-trip** — change `workspace_credit_cost_pulse` in Admin Portal, verify new value reflects in Run Detection button within ~5 minutes (after cache TTL)

### Claude's Discretion
- `GET /credit-costs` router file location and module structure
- Exact TanStack Query hook name and query key for credit costs
- Loading animation style on Run Detection button (spinner vs skeleton vs `—` placeholder)
- Test fixture design for creating users with specific user_class values
- Smoke test checklist formatting and step detail level

</decisions>

<specifics>
## Specific Ideas

- The `/api/credit-costs` endpoint is designed for future extensibility — v0.9+ adds `investigate` and `whatif` keys to the same response without a breaking change
- Admin settings round-trip smoke test: change the value, wait for cache TTL (~5 min), reload the collection page, and verify the button reflects the new value — proves the platform setting is live and not permanently cached

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/platform_settings.py`: `get_all()` function — reads `workspace_credit_cost_pulse` and `default_credit_cost`; use to build credit costs response
- `backend/app/dependencies.py`: `CurrentUser` dependency — use to gate `GET /credit-costs` endpoint
- `backend/app/routers/admin/settings.py`: existing PATCH pattern — backend schema changes follow same structure
- `admin-frontend/src/components/settings/SettingsForm.tsx`: existing Credits card with `defaultCreditCost` field — add `pulseCreditCost` field below it
- `admin-frontend/src/types/settings.ts` / `useSettings` hook: add `workspace_credit_cost_pulse` field to `PlatformSettings` type
- `frontend/src/lib/api-client.ts`: `BASE_URL = "/api"` — new hook calls `GET /api/credit-costs`
- `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx`: `const CREDIT_COST = 5` hardcode to replace with live value

### Established Patterns
- Backend router registration: no prefix in `main.py` for public frontend routers (e.g., `app.include_router(collections.router)`)
- Frontend proxy: Next.js `[...slug]/route.ts` strips `/api` prefix before forwarding to backend
- TanStack Query hooks: `useQuery` in `frontend/src/hooks/` with typed API functions
- Admin frontend settings: `SettingsResponse` Pydantic schema drives both the GET response and form sync via `useEffect`

### Integration Points
- `backend/app/schemas/platform_settings.py`: add `workspace_credit_cost_pulse: float` to `SettingsResponse` and `SettingsUpdateRequest`
- `backend/app/main.py`: register new `credit_costs` router (no prefix)
- `admin-frontend/src/types/settings.ts`: add `workspace_credit_cost_pulse: number`
- `admin-frontend/src/components/settings/SettingsForm.tsx`: add form state, input field, and validation
- `frontend/src/hooks/`: add `useCreditCosts()` hook fetching `GET /api/credit-costs`
- `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx`: replace `CREDIT_COST` constant with hook value
- `backend/tests/test_tier_gating.py`: new test file

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 52-admin-and-qa*
*Context gathered: 2026-03-09*
