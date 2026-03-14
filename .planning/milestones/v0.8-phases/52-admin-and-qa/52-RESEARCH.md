# Phase 52: Admin and QA - Research

**Researched:** 2026-03-09
**Domain:** FastAPI schema extension, TanStack Query hook pattern, pytest unittest.mock, smoke test authoring
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Admin settings gap — workspace_credit_cost_pulse**
- Add `workspace_credit_cost_pulse` field to `SettingsResponse` and `SettingsUpdateRequest` Pydantic schemas in `backend/app/schemas/platform_settings.py`
- Field lives inside the existing Credits card in `SettingsForm.tsx` — below "Default Credit Cost per Message", same card, same Save button
- Label: "Pulse Detection Cost per Run" — mirrors existing label style
- Saves with the same Save button as all other settings (single PATCH request, no separate save)
- Frontend validates before submitting: toast error if value <= 0 (same pattern as existing `defaultCreditCost` validation)
- Admin frontend `types/settings.ts` `PlatformSettings` type needs `workspace_credit_cost_pulse: number` added

**Credit cost wiring — live endpoint**
- New GET /credit-costs endpoint on the backend (registered without prefix in `main.py`, same as `/collections`, `/auth`, `/files`)
- Frontend calls it as GET /api/credit-costs — Next.js proxy strips `/api` and forwards to backend
- Requires standard auth (CurrentUser, not admin) — workspace is auth-gated anyway
- Response shape: `{ chat: number, pulse_run: number }` — future keys (investigate, whatif) added as v0.9+ features arrive
- `chat` value reads from `default_credit_cost` platform setting; `pulse_run` reads from `workspace_credit_cost_pulse`
- Frontend uses TanStack Query with staleTime ~5 minutes (credit costs rarely change mid-session)
- While loading: button shows a loading animation (spinner/skeleton) — does not show hardcoded fallback
- Removes `const CREDIT_COST = 5` hardcode from `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx`

**QA — automated tier gating tests**
- New file: `backend/tests/test_tier_gating.py`
- Test scenarios:
  1. Workspace access 403: `free` and `free_trial` tier users hit `GET /collections` and `POST /collections` → expect 403 with "workspace access not available on your plan"
  2. Collection limit enforcement: `free_trial` tier user creates 1 collection (201 OK), second POST → expect 403 with "Collection limit reached"
  3. Unlimited tiers: `standard`, `premium`, `internal` tier users can create collections without hitting a limit (201 OK on multiple creates)
- Tests use existing pytest fixtures for DB and HTTP test client
- Does NOT include a credit cost config test (out of scope for this phase's automated tests)

**Smoke test — manual QA checklist**
- Scope: workspace and Pulse flows only (not existing chat/files)
- Format: markdown checklist in `52-SMOKE-TEST.md` inside the phase directory
- Checklist covers four flows:
  1. Tier access gating UI — log in as free-tier user, confirm `/workspace` shows access-gated state (not 500, not blank)
  2. Collection + Pulse flow — create collection, upload file, trigger Pulse, wait for results, verify signals + report appear
  3. Credit cost display — verify "Run Detection (N credits)" button shows live value from platform settings
  4. Admin settings round-trip — change `workspace_credit_cost_pulse` in Admin Portal, verify new value reflects in Run Detection button within ~5 minutes (after cache TTL)

### Claude's Discretion
- `GET /credit-costs` router file location and module structure
- Exact TanStack Query hook name and query key for credit costs
- Loading animation style on Run Detection button (spinner vs skeleton vs `—` placeholder)
- Test fixture design for creating users with specific user_class values
- Smoke test checklist formatting and step detail level

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 52 is a verification and gap-fill phase, not a feature phase. It delivers four concrete outputs: (1) add `workspace_credit_cost_pulse` to the admin settings schema and form, (2) a new `/credit-costs` backend endpoint wired to a TanStack Query hook that replaces the hardcoded `CREDIT_COST = 5` constant in the collection detail page, (3) automated tier gating tests in `backend/tests/test_tier_gating.py`, and (4) a manual smoke test checklist document.

All the code infrastructure already exists and works correctly — the backend service reads both `default_credit_cost` and `workspace_credit_cost_pulse` from `platform_settings`, validates them, and the 30-second TTL cache is in place. The gap is only that the admin form doesn't expose `workspace_credit_cost_pulse` yet, and the frontend still uses a hardcoded constant instead of the live value. The tier gating logic in `require_workspace_access` and collection limit enforcement in `create_collection` are already implemented and tested partially in `test_collections.py` — Phase 52 adds more comprehensive coverage across all five tiers via a dedicated test file.

**Primary recommendation:** Follow the established pattern exactly. Schema, form state, validation, and hook patterns are all readable in existing code — copy the pattern, don't invent new approaches.

---

## Standard Stack

### Core (already in use — no new installs needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI + Pydantic v2 | current (0.115+) | Backend schema extension | Already in use; `model_validator(mode="after")` pattern in `SettingsUpdateRequest` |
| pytest + pytest-asyncio | current | Backend unit tests | Already in use; all existing tests follow this pattern |
| unittest.mock | stdlib | Mocking dependencies without a live DB | Already the project's test approach — `test_collections.py` uses it exclusively |
| TanStack Query v5 | current | Frontend data fetching | Already in use in `useWorkspace.ts`, `useCredits.ts` |
| Next.js API proxy (`[...slug]/route.ts`) | current | `/api/*` → backend strip | Already in use; all workspace hooks use `apiClient.get("/collections")` |

### No New Dependencies

This phase adds no new packages. All libraries are already installed.

---

## Architecture Patterns

### Backend: Extending SettingsResponse / SettingsUpdateRequest

The existing `platform_settings.py` schema has a `model_validator(mode="after")` that checks at least one field is set. When adding `workspace_credit_cost_pulse` to `SettingsUpdateRequest`, it must also be added to the `all(v is None for v in [...])` list inside `at_least_one_field`, or the validator will not recognize the new field.

The backend service already handles `workspace_credit_cost_pulse` in `DEFAULTS`, `VALID_KEYS`, and `validate_setting()`. The gap is only at the Pydantic schema level — the service is complete.

**Pattern for schema field addition:**
```python
# In SettingsResponse — just add the field:
workspace_credit_cost_pulse: float

# In SettingsUpdateRequest — add field AND add to validator list:
workspace_credit_cost_pulse: float | None = None

# In at_least_one_field validator — extend the list:
if all(
    v is None
    for v in [
        self.allow_public_signup,
        ...,
        self.workspace_credit_cost_pulse,  # ADD THIS
    ]
):
```

The admin settings router (`admin/settings.py`) reads all settings via `platform_settings.get_all()` and constructs `SettingsResponse(**parsed)`. Because `workspace_credit_cost_pulse` is already in `DEFAULTS`, it will be present in `parsed` automatically once added to `SettingsResponse`.

### Backend: New /credit-costs Router

Register in `main.py` under the `if mode in ("public", "dev"):` block alongside `collections.router`, `auth.router`, etc. No prefix — the Next.js proxy strips `/api`.

**Pattern (mirroring existing public routers):**
```python
# main.py — in the public routes block:
from app.routers import credit_costs
app.include_router(credit_costs.router)
```

**Router structure:**
```python
# backend/app/routers/credit_costs.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.dependencies import CurrentUser, DbSession
from app.services import platform_settings as ps

router = APIRouter(prefix="/credit-costs", tags=["Credit Costs"])

class CreditCostsResponse(BaseModel):
    chat: float
    pulse_run: float

@router.get("", response_model=CreditCostsResponse)
async def get_credit_costs(
    current_user: CurrentUser,
    db: DbSession,
) -> CreditCostsResponse:
    settings = await ps.get_all(db)
    import json
    chat = json.loads(settings.get("default_credit_cost", '"1.0"'))
    pulse_run = json.loads(settings.get("workspace_credit_cost_pulse", '"5.0"'))
    return CreditCostsResponse(chat=float(chat), pulse_run=float(pulse_run))
```

Note: `default_credit_cost` is stored as a JSON-encoded string `"1.0"` (see DEFAULTS in `platform_settings.py`) — `json.loads()` is required, matching how the admin settings router reads values.

### Frontend: useCreditCosts Hook

**Pattern (mirroring `useCredits.ts`):**
```typescript
// frontend/src/hooks/useCreditCosts.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface CreditCosts {
  chat: number;
  pulse_run: number;
}

export function useCreditCosts() {
  return useQuery<CreditCosts>({
    queryKey: ["credit-costs"],
    queryFn: async () => {
      const res = await apiClient.get("/credit-costs");
      if (!res.ok) throw new Error("Failed to fetch credit costs");
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
```

`apiClient.get("/credit-costs")` resolves to `GET /api/credit-costs` via `BASE_URL = "/api"` in `api-client.ts`. The Next.js proxy strips `/api` and forwards to `GET /credit-costs` on the backend.

### Frontend: Replace CREDIT_COST Constant

In `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx`:

1. Remove `const CREDIT_COST = 5` at the top of the file
2. Add `useCreditCosts` hook call: `const { data: creditCosts } = useCreditCosts()`
3. Replace all `CREDIT_COST` references with `creditCosts?.pulse_run`
4. While loading (creditCosts is undefined): show a loading spinner or `—` placeholder in the button

`CREDIT_COST` is used in three places in the current file:
- Line 38: the `const CREDIT_COST = 5` declaration
- Line 232: `{CREDIT_COST} credits / run` in the header badge
- Line 258: `creditsUsed={CREDIT_COST}` in `OverviewStatCards`
- Line 511: `creditCost={CREDIT_COST}` in `RerunDetectionDialog`

All four must be updated.

### Admin Frontend: SettingsForm.tsx Extension

Add below the existing "Default Credit Cost per Message" input inside the Credits card, with a `<Separator />` between them. The new field follows the exact same JSX and state pattern as `defaultCreditCost`:

```typescript
// New state variable (alongside existing ones):
const [pulseCreditCost, setPulseCreditCost] = useState(5);

// In useEffect sync block:
setPulseCreditCost(settings.workspace_credit_cost_pulse);

// In handleSave validation:
if (pulseCreditCost <= 0) {
  toast.error("Pulse detection cost must be greater than 0");
  return;
}

// In updateSettings.mutate payload:
workspace_credit_cost_pulse: pulseCreditCost,
```

`PlatformSettingsUpdate` is `Partial<PlatformSettings>` — once `workspace_credit_cost_pulse` is added to `PlatformSettings`, it is automatically included in the update type.

### Backend Tests: test_tier_gating.py Pattern

The existing `test_collections.py` shows the exact pattern. Tests call router functions directly, mock dependencies with `patch()`, use `_make_mock_user(user_class="free")` helpers, and assert `HTTPException` status codes.

The conftest.py only provides `clear_config_caches` which runs automatically. Tests do NOT need a live database — all DB calls are `AsyncMock`.

**Key insight:** For the "workspace access 403" scenario, the test needs to mock `app.dependencies.get_class_config` (used inside `require_workspace_access`) — the same pattern already in `test_collections.py` line 102. For "collection limit enforcement" it mocks `app.routers.collections.get_class_config` and `CollectionService.count_user_collections`.

For `free_trial` workspace access 403: note that `free_trial` has `workspace_access: True` per `user_classes.yaml`. The CONTEXT.md says both `free` AND `free_trial` should hit 403 on workspace access — but `free_trial` actually has workspace access. Re-read the CONTEXT.md test scenario carefully:

> **Workspace access 403**: `free` and `free_trial` tier users hit `GET /collections` and `POST /collections` → expect 403 with "workspace access not available on your plan"

This conflicts with the known tier config (`free_trial: workspace_access = True`). The test must mock `get_class_config` to return `{"workspace_access": False}` for `free_trial` to produce a 403 — OR the test description in CONTEXT.md contains an error and should only cover `free` tier for workspace 403. The planner must resolve this ambiguity: test the behavior exactly as specified (mock the dependency to return 403 for free_trial), OR scope the workspace 403 test only to `free` tier and test free_trial's collection limit separately. **This is a flag for the planner to clarify — do not assume.**

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Settings cache invalidation | Custom cache reset | `platform_settings.invalidate_cache()` already exists | Already implemented; admin settings PATCH already calls it after every upsert |
| Pydantic schema validation | Custom validator | `model_validator(mode="after")` + `validate_setting()` | Both patterns already in place; `validate_setting("workspace_credit_cost_pulse", value)` already validates > 0 |
| JSON decode of stored settings | Custom parser | `json.loads(raw)` | Stored as JSON-encoded strings per DEFAULTS pattern; must use json.loads, not float() directly |
| TanStack Query cache management | Manual invalidation | `staleTime: 5 * 60 * 1000` | Keeps the credit costs fresh without refetching on every render |

---

## Common Pitfalls

### Pitfall 1: Forgetting the at_least_one_field validator list
**What goes wrong:** `workspace_credit_cost_pulse` is added as a field to `SettingsUpdateRequest` but not added to the `all(v is None for v in [...])` list. The validator still works correctly — but a PATCH sending only `workspace_credit_cost_pulse` would fail validation with "At least one setting must be provided" because the validator doesn't see the new field in its list.
**How to avoid:** Add the new field to both the field declaration AND the validator list in `at_least_one_field`.

### Pitfall 2: Reading platform settings with float() instead of json.loads()
**What goes wrong:** `default_credit_cost` is stored as the JSON string `"1.0"` (with quotes), not the number `1.0`. Calling `float(settings["default_credit_cost"])` raises `ValueError` because `float('"1.0"')` fails. The value `"5.0"` (with quotes) also fails.
**How to avoid:** Always use `json.loads(raw)` then `float(...)` on the result, consistent with how `platform_settings.get()` and the admin settings router work.

### Pitfall 3: Registering /credit-costs in the wrong mode block
**What goes wrong:** New router registered in the admin block (`mode in ("admin", "dev")`) instead of the public block (`mode in ("public", "dev")`). The workspace frontend runs in public mode and can't reach the endpoint.
**How to avoid:** Register in the `if mode in ("public", "dev"):` block alongside `collections.router`.

### Pitfall 4: CREDIT_COST used in four places, not two
**What goes wrong:** Developer finds `CREDIT_COST` in the header badge and the `RerunDetectionDialog` but misses `creditsUsed={CREDIT_COST}` in `OverviewStatCards` (line 258). The stat card continues showing a hardcoded 5.
**How to avoid:** Search the file for all four occurrences before replacing.

### Pitfall 5: free_trial tier workspace access ambiguity in tests
**What goes wrong:** The test spec in CONTEXT.md says `free` and `free_trial` users get 403 on workspace access. But `user_classes.yaml` and `test_user_classes_workspace.py` confirm `free_trial` has `workspace_access: True`. Writing a test that asserts `free_trial` gets a 403 from `require_workspace_access` without mocking will actually PASS workspace access and not raise.
**How to avoid:** Clarify with the planner. Most likely the intention is: `free` gets workspace 403, `free_trial` passes workspace access but hits collection limit 403 on second create. See Open Questions.

### Pitfall 6: Loading state for button shows stale hardcoded value
**What goes wrong:** While `useCreditCosts` is loading, `creditCosts` is `undefined`. Displaying `undefined credits` or `NaN credits` is a bad user experience.
**How to avoid:** Show a spinner or `—` placeholder while loading. The CONTEXT.md decision is: "button shows a loading animation (spinner/skeleton) — does not show hardcoded fallback."

---

## Code Examples

### Existing pattern: admin settings get_settings reads all keys via json.loads
```python
# Source: backend/app/routers/admin/settings.py (line 24-26)
raw = await platform_settings.get_all(db)
parsed = {k: json.loads(v) for k, v in raw.items()}
return SettingsResponse(**parsed)
```
The `workspace_credit_cost_pulse` key is already in `raw` (comes from DEFAULTS). Once the field is added to `SettingsResponse`, it will be populated automatically.

### Existing pattern: useCredits hook (staleTime pattern to follow)
```typescript
// Source: frontend/src/hooks/useCredits.ts
return useQuery<CreditBalance>({
  queryKey: ["credits", "balance"],
  queryFn: async () => {
    const res = await apiClient.get("/api/credits/balance");
    if (!res.ok) throw new Error("Failed to fetch credits");
    return res.json();
  },
  refetchInterval: 60000,
  staleTime: 30000,
});
```
Note: `useCreditCosts` should use `staleTime: 5 * 60 * 1000` (5 min) per CONTEXT.md. No `refetchInterval` needed — credit costs change only when admin edits settings.

### Existing test pattern: mock user + mock dependency
```python
# Source: backend/tests/test_collections.py (lines 28-34, 97-108)
def _make_mock_user(user_class: str = "standard", user_id=None):
    user = MagicMock()
    user.id = user_id or uuid4()
    user.user_class = user_class
    user.is_active = True
    return user

async def test_workspace_access_denied_free_tier(self):
    user = _make_mock_user(user_class="free")
    with patch(
        "app.dependencies.get_class_config",
        return_value={"workspace_access": False, "max_active_collections": 0},
    ):
        with pytest.raises(HTTPException) as exc_info:
            await require_workspace_access(user)
        assert exc_info.value.status_code == 403
```

### Existing pattern: public router registration in main.py
```python
# Source: backend/app/main.py (lines 389-399)
if mode in ("public", "dev"):
    app.include_router(auth.router)
    app.include_router(files.router)
    app.include_router(collections.router)
    app.include_router(chat.router)
    app.include_router(chat_sessions.router)
    app.include_router(search.router)

    from app.routers import credits
    app.include_router(credits.router)
```
New router follows the same lazy import pattern shown for `credits`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `const CREDIT_COST = 5` hardcoded in page.tsx | Live value from `GET /credit-costs` | Phase 52 | Button reflects admin-configured value without redeployment |
| Admin settings form missing pulse credit cost | `workspace_credit_cost_pulse` field in Credits card | Phase 52 | Admin can update the value at runtime |

---

## Open Questions

1. **free_trial workspace access 403 ambiguity**
   - What we know: `user_classes.yaml` gives `free_trial` `workspace_access: True` (confirmed by `test_user_classes_workspace.py`). The CONTEXT.md test spec says both `free` and `free_trial` should get 403 from workspace access endpoints.
   - What's unclear: Is the intent to test `free_trial` as a workspace-blocked tier (incorrect per config), OR is the test spec describing collection-limit blocking (403 on second create, not workspace access)?
   - Recommendation: Planner should scope workspace-access 403 tests to `free` only. For `free_trial`: test that workspace access is allowed (201 on first create), second create returns 403 with "Collection limit reached". This matches the actual tier config and the success criteria in the phase description.

2. **Loading state implementation for Run Detection button**
   - What we know: CONTEXT.md says "loading animation (spinner vs skeleton vs — placeholder)" is Claude's discretion.
   - What's unclear: Which component renders the button text — `RunDetectionBanner` or `StickyActionBar`? Both may show a "Run Detection" button.
   - Recommendation: Planner should read `RunDetectionBanner.tsx` to determine where the button text is rendered and pass `creditCosts?.pulse_run` as a prop with a `isLoadingCreditCosts` flag.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `backend/pytest.ini` or `backend/pyproject.toml` (check at implementation time) |
| Quick run command | `cd backend && python -m pytest tests/test_tier_gating.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -q` |

### Phase Requirements to Test Map

Phase 52 has no new requirement IDs — it verifies ADMIN-01 and ADMIN-02 end-to-end.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADMIN-01 | `free` tier blocked at workspace access (403) | unit | `pytest tests/test_tier_gating.py::TestWorkspaceAccess::test_free_blocked -x` | ❌ Wave 0 |
| ADMIN-01 | `free_trial` passes workspace access, blocked at collection limit on 2nd create (403) | unit | `pytest tests/test_tier_gating.py::TestCollectionLimit::test_free_trial_limit -x` | ❌ Wave 0 |
| ADMIN-01 | `standard`, `premium`, `internal` can create collections without limit (201) | unit | `pytest tests/test_tier_gating.py::TestUnlimitedTiers -x` | ❌ Wave 0 |
| ADMIN-02 | `workspace_credit_cost_pulse` readable via `GET /credit-costs` (live value) | manual smoke | 52-SMOKE-TEST.md flow 3 | ❌ Wave 0 |
| ADMIN-02 | Admin settings round-trip: update pulse cost, verify button reflects new value | manual smoke | 52-SMOKE-TEST.md flow 4 | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_tier_gating.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_tier_gating.py` — covers ADMIN-01 all tiers
- [ ] `backend/app/routers/credit_costs.py` — new router file (not a test gap, but prerequisite for smoke tests)
- [ ] `52-SMOKE-TEST.md` — manual QA checklist (created as part of this phase)

*(No new test framework install needed — pytest already configured)*

---

## Sources

### Primary (HIGH confidence)
- Direct source code inspection — all findings verified against live project files
  - `backend/app/schemas/platform_settings.py` — SettingsResponse, SettingsUpdateRequest, validator list
  - `backend/app/services/platform_settings.py` — DEFAULTS, VALID_KEYS, validate_setting, TTL cache
  - `backend/app/main.py` — router registration pattern for public routes
  - `backend/app/routers/admin/settings.py` — PATCH pattern with json.loads
  - `backend/app/dependencies.py` — CurrentUser, WorkspaceUser, require_workspace_access
  - `backend/tests/test_collections.py` — mock pattern, _make_mock_user, workspace access test
  - `backend/tests/test_user_classes_workspace.py` — confirmed free_trial workspace_access=True
  - `admin-frontend/src/components/settings/SettingsForm.tsx` — Credits card, useState pattern
  - `admin-frontend/src/types/settings.ts` — PlatformSettings interface
  - `admin-frontend/src/hooks/useSettings.ts` — useUpdateSettings, PlatformSettingsUpdate usage
  - `frontend/src/hooks/useCredits.ts` — staleTime pattern to follow
  - `frontend/src/lib/api-client.ts` — BASE_URL="/api", apiClient.get() usage
  - `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` — all four CREDIT_COST usage sites

---

## Metadata

**Confidence breakdown:**
- Backend schema extension: HIGH — pattern is explicit in existing code, no guesswork
- New /credit-costs router: HIGH — pattern is explicit; only module path is discretionary
- Admin frontend form changes: HIGH — SettingsForm.tsx and types/settings.ts both read; exact pattern clear
- Frontend hook (useCreditCosts): HIGH — follows useCredits.ts exactly with different staleTime
- Test structure: HIGH — test_collections.py provides exact pattern; free_trial ambiguity flagged
- Smoke test checklist: HIGH — scope and four flows are fully specified in CONTEXT.md

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable codebase, no external dependencies changing)
