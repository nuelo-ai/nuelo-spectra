# Phase 32: Production Readiness - Research

**Researched:** 2026-02-17
**Domain:** Frontend URL hardcoding, FastAPI route cleanup, admin settings UI correctness
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INVITE-04 | Invite registration page must not hardcode localhost URLs; use apiClient or environment-relative URLs | Hardcoded `http://localhost:8000` confirmed on lines 41 and 74 of `frontend/src/app/(auth)/invite/[token]/page.tsx`; Next.js rewrite proxy pattern confirmed as correct fix |
| INVITE-05 | Invite flow must work correctly in localhost, staging, and production environments | Frontend `next.config.ts` rewrite `/api/:path*` -> `http://localhost:8000/:path*` already exists; invite page just needs to use relative `/api/...` paths |
| SETTINGS-05 | credit_reset_policy field in Settings UI must either be functional (driving APScheduler) or clearly labelled as read-only/informational with no misleading save behavior | UI side already fixed (SettingsForm does not send credit_reset_policy in save payload); backend `SettingsUpdateRequest` schema still accepts it as a writable field, and `SettingsResponse` still returns it — backend schema needs cleanup |
</phase_requirements>

---

## Summary

Phase 32 is a narrow, surgical gap-closure phase with exactly three issues identified in the v0.5 milestone audit. All three are well-understood from direct codebase inspection; no new libraries or architectural patterns are needed.

**Issue 1 — INVITE-04/05 (Hardcoded localhost):** The invite registration page (`frontend/src/app/(auth)/invite/[token]/page.tsx`) makes two bare `fetch()` calls directly to `http://localhost:8000`. The frontend already has a working Next.js rewrite in `next.config.ts` that proxies `/api/:path*` to the backend. The fix is to replace both `fetch("http://localhost:8000/auth/...")` calls with `apiClient.get("/api/auth/...")` and `apiClient.post("/api/auth/...", body)`. Note: the `apiClient` itself in `frontend/src/lib/api-client.ts` also hardcodes `http://localhost:8000` as its base URL — this must be fixed first, or the invite page should use plain `fetch` with relative `/api/` paths directly, bypassing `apiClient` (since the invite page flows don't require auth headers for the validation/registration calls).

**Issue 2 — SETTINGS-05 (credit_reset_policy misleading):** The admin `SettingsForm.tsx` has already been updated to show per-tier reset policies as read-only informational content (from the tiers endpoint) and does NOT include `credit_reset_policy` in its save payload. However, the backend `SettingsUpdateRequest` schema still accepts `credit_reset_policy` as a patchable field, and `SettingsResponse` still includes it as a top-level field. The APScheduler completely ignores this DB field — it reads `reset_policy` per-tier from `user_classes.yaml` instead. The fix is to remove `credit_reset_policy` from `SettingsUpdateRequest` (so PATCH no longer accepts it) and remove it from `SettingsResponse` (so GET no longer implies it is meaningful). Optionally, remove it from the `platform_settings` service DEFAULTS and validation as well.

**Issue 3 — Dead Route (TIER-06):** `PUT /api/admin/tiers/users/{user_id}` in `backend/app/routers/admin/tiers.py` is never called by any frontend. The active tier-change endpoint is `PUT /api/admin/users/{user_id}/tier` in the users router. The dead route should be removed entirely from `tiers.py`.

**Primary recommendation:** Fix all three issues sequentially — (1) update `api-client.ts` base URL to use the Next.js rewrite, then fix the invite page; (2) remove `credit_reset_policy` from backend settings schema; (3) remove the dead tiers route.

---

## Standard Stack

No new libraries are required. This phase works entirely within the existing stack.

### Core (Already in Use)

| Component | Location | Relevant To |
|-----------|----------|-------------|
| Next.js 15 rewrites | `frontend/next.config.ts` | INVITE-04/05: existing proxy already handles `/api/:path*` |
| `apiClient` | `frontend/src/lib/api-client.ts` | INVITE-04/05: existing client, hardcoded base URL needs fix |
| FastAPI `APIRouter` | `backend/app/routers/admin/tiers.py` | Dead route removal |
| Pydantic `BaseModel` | `backend/app/schemas/platform_settings.py` | SETTINGS-05 schema cleanup |
| APScheduler | `backend/app/scheduler.py` | SETTINGS-05 context: scheduler reads YAML not DB |

### No New Dependencies

All three fixes are pure code changes. No `npm install` or `pip install` required.

---

## Architecture Patterns

### Pattern 1: Next.js Rewrite Proxy (Relative URLs)

**What:** Both frontends already use Next.js rewrites to proxy API calls to the backend, avoiding hardcoded hostnames.

**Admin-frontend pattern (already correct):**
```typescript
// admin-frontend/src/lib/admin-api-client.ts
// Uses relative paths — Next.js rewrites /api/:path* to http://localhost:8000/api/:path*
const response = await fetch(path, { ...options, headers });
// Called as: adminApiClient.get("/api/admin/settings")
```

**Frontend rewrite rule:**
```typescript
// frontend/next.config.ts
async rewrites() {
  return [{ source: "/api/:path*", destination: "http://localhost:8000/:path*" }];
}
```

This means: `/api/auth/invite-validate` -> `http://localhost:8000/auth/invite-validate`

**When to use:** All frontend fetch calls should use `/api/<backend-path>` format, not `http://localhost:8000/<backend-path>`.

### Pattern 2: Fixing api-client.ts Base URL

**What:** The `apiClient` in `frontend/src/lib/api-client.ts` hardcodes `http://localhost:8000` in multiple places. The correct base URL is `/api` (empty string relative to Next.js, with `/api` prefix matching the rewrite rule).

**Before (broken):**
```typescript
let response = await fetch(`http://localhost:8000${path}`, options);
```

**After (correct):**
```typescript
const BASE_URL = "/api";
let response = await fetch(`${BASE_URL}${path}`, options);
```

Then callers pass paths like `/auth/refresh` and the resulting URL `/api/auth/refresh` is proxied correctly.

**Note:** The `apiClient.upload()` method has a mixed state — the initial call uses `http://localhost:8000${path}` but the retry call already uses `/api${path}`. This inconsistency should be corrected.

**Scope:** The invite page uses raw `fetch()` for the token-validation and registration calls (not `apiClient`), because these endpoints don't require auth headers. After fixing `api-client.ts`, the invite page can switch to `apiClient.get()` / `apiClient.post()` OR use plain `fetch("/api/auth/...")` directly — either is correct.

### Pattern 3: Invite Page Fix

**Current state of invite page:**
- Line 41: `fetch(`http://localhost:8000/auth/invite-validate?token=${...}`)` — raw fetch, no auth needed
- Line 74: `fetch("http://localhost:8000/auth/invite-register", { method: "POST", ... })` — raw fetch, no auth needed
- Line 95: `apiClient.get("/auth/me")` — uses apiClient WITH the existing hardcoded base URL

**Fix approach:** Convert lines 41 and 74 to use `/api/auth/...` relative URLs via plain `fetch()` (not `apiClient`, since invite validate/register are unauthenticated). After `api-client.ts` is fixed, line 95 will also work correctly once the base URL is `/api`.

**Two-step dependency:** Fix `api-client.ts` first, then the invite page automatically benefits for the `/auth/me` call. The validate and register calls need their own fixes regardless.

### Pattern 4: Removing credit_reset_policy from Settings Schema

**What:** `credit_reset_policy` in `platform_settings` is architecturally orphaned — stored in DB, editable via PATCH, returned by GET, but never read by the scheduler (which reads from `user_classes.yaml` per-tier). Keeping it is misleading.

**Files to change:**

1. `backend/app/schemas/platform_settings.py`:
   - Remove `credit_reset_policy: str` from `SettingsResponse`
   - Remove `credit_reset_policy: str | None = None` from `SettingsUpdateRequest`
   - Remove `self.credit_reset_policy` from the `at_least_one_field` validator list

2. `backend/app/services/platform_settings.py`:
   - Remove `"credit_reset_policy": json.dumps("weekly")` from `DEFAULTS`
   - Remove `credit_reset_policy` validation block from `validate_setting()`

3. `admin-frontend/src/types/settings.ts`:
   - Remove `credit_reset_policy: string` from `PlatformSettings` interface

**What NOT to change:**
- The `SettingsForm.tsx` credits card already shows per-tier info correctly — no UI change needed
- The `useSettings.ts` hook does not reference `credit_reset_policy` — no hook change needed
- The DB row for `credit_reset_policy` can remain (no migration needed; it just won't be served or writable)

### Pattern 5: Removing Dead Tiers Route

**What:** `PUT /api/admin/tiers/users/{user_id}` in `tiers.py` is never called by the frontend. The duplicate functionality lives at `PUT /api/admin/users/{user_id}/tier` (in `users.py`).

**Fix:** Remove the `@router.put("/users/{user_id}")` endpoint (lines 58-105) from `backend/app/routers/admin/tiers.py`.

**Imports to clean up after removal:**
- `Request` from fastapi (if no longer used)
- `log_admin_action` from audit service (if no longer used)
- `change_user_tier` from tiers service (if no longer used)
- `TierChangeRequest` from schemas (if no longer imported here; it's still in `users.py`)

Check each import — `TierChangeRequest` may still be needed if it's used in the tiers GET endpoint (it is not; GET only uses `TierSummaryResponse`).

### Anti-Patterns to Avoid

- **Hardcoding environment-specific URLs in client code:** Never use `http://localhost:8000` in frontend source. Use relative paths + Next.js rewrites.
- **Adding NEXT_PUBLIC_API_URL env var:** This project already has a working rewrite proxy. Adding an env var would introduce a second configuration layer that needs to be kept in sync. Use the rewrite approach instead.
- **Running a database migration to drop the credit_reset_policy column:** The DB cleanup is unnecessary for SETTINGS-05. The schema/API fix is sufficient. A migration adds risk with no user-facing benefit.
- **Changing the scheduler to use the DB credit_reset_policy:** The existing per-tier YAML approach is correct (different tiers have different policies). A global credit_reset_policy override does not match the data model. Don't wire the DB field to the scheduler.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Environment-aware API base URL | Custom `getApiBaseUrl()` function reading env vars | Next.js rewrite proxy with relative paths | Rewrites are already configured; env vars require additional build-time setup for each environment |
| Auth-free fetch wrapper for invite page | Custom fetch helper | Plain `fetch("/api/auth/...")` with relative path | Two calls only; no retry logic needed for unauthenticated endpoints |

---

## Common Pitfalls

### Pitfall 1: Fixing Only the Invite Page Without Fixing api-client.ts

**What goes wrong:** The invite page has its own raw `fetch()` calls (fixed) but `apiClient.get("/auth/me")` on line 95 still goes to `http://localhost:8000/auth/me` because `fetchWithAuth` in `api-client.ts` hardcodes the base URL.

**Why it happens:** The invite page is the reported problem, but the root cause is in `api-client.ts`. Fixing only the invite page leaves `apiClient` broken in staging/production for ALL pages that use it (dashboard, chat, files, etc.).

**How to avoid:** Fix `api-client.ts` first (change all `http://localhost:8000${path}` to `/api${path}`). This fixes the invite page's `/auth/me` call AND all other pages simultaneously.

**Warning signs:** Tests pass locally (localhost) but fail in staging — classic symptom of hardcoded localhost.

### Pitfall 2: Scope Creep — Other Hardcoded URLs

**What goes wrong:** While fixing the invite page, discovering other hardcoded URLs (`register/page.tsx` line 26, `useSSEStream.ts` line 112) and fixing them all in the same task.

**Why it happens:** `grep` reveals multiple files with `localhost:8000`. Fixing all is tempting.

**How to avoid:** Phase 32 requirements are INVITE-04, INVITE-05, SETTINGS-05. Fix `api-client.ts` (which benefits all pages) but scope individual page fixes to the invite page only. Other pages are out of scope for Phase 32. EXCEPTION: if fixing `api-client.ts` automatically fixes `register/page.tsx`'s `signup-status` check because that page calls `apiClient` elsewhere — verify but don't expand scope.

**Note:** `register/page.tsx` line 26 does a raw `fetch("http://localhost:8000/auth/signup-status")` that bypasses `apiClient`. This is a separate bug not in Phase 32 scope. Do not fix it here.

### Pitfall 3: Breaking the Upload Flow

**What goes wrong:** The `apiClient.upload()` method has a mixed state — initial call uses `http://localhost:8000` but retry uses `/api`. Fixing the base URL could change behavior.

**Why it happens:** The upload retry already uses the correct relative URL. Normalizing the initial call to match will fix the inconsistency.

**How to avoid:** Fix both the initial call AND the retry in `upload()` to use the same `/api` base. Test file upload after the change.

### Pitfall 4: Removing Too Much From SettingsUpdateRequest

**What goes wrong:** Removing `credit_reset_policy` from the backend schema causes existing DB rows with `credit_reset_policy` data to become orphaned, or breaks old cached responses.

**Why it happens:** There may be `platform_setting` rows with `key='credit_reset_policy'` in the database from prior sessions.

**How to avoid:** The DB rows are fine to leave — they just won't be served via the API anymore. The cache `get_all()` will still return them in the raw dict, but `SettingsResponse(**parsed)` won't include the field. Verify that the `SettingsResponse` constructor with `**parsed` dict won't raise an error if `parsed` contains a `credit_reset_policy` key that's no longer a field in the model. In Pydantic v2, extra fields in constructor kwargs raise `ValidationError` if `model_config = ConfigDict(extra="forbid")` — `SettingsResponse` does NOT have `extra="forbid"`, so extra keys are silently ignored. Safe.

### Pitfall 5: Import Cleanup After Dead Route Removal

**What goes wrong:** After removing the `change_tier` endpoint from `tiers.py`, leaving unused imports causes lint warnings or test failures.

**Why it happens:** The dead endpoint used `Request`, `log_admin_action`, `change_user_tier`, and `TierChangeRequest` — all of which become unused after removal.

**How to avoid:** After removing the endpoint, audit each import line in `tiers.py`:
- `TierChangeRequest` — not used by GET endpoint; remove
- `change_user_tier` — not used by GET endpoint; remove
- `log_admin_action` — not used by GET endpoint; remove
- `Request` — not used by GET endpoint; remove
- `UUID` — not used by GET endpoint; remove
- Keep: `APIRouter`, `HTTPException`, `func`, `select`, `CurrentAdmin`, `DbSession`, `User`, `TierSummaryResponse`, `get_user_classes`

---

## Code Examples

### Fixing api-client.ts Base URL

```typescript
// Source: frontend/src/lib/api-client.ts (after fix)
// Change: replace all occurrences of http://localhost:8000 with /api

const BASE_URL = "/api";

// In fetchWithAuth:
let response = await fetch(`${BASE_URL}${path}`, options);
// ...
response = await fetch(`${BASE_URL}${path}`, options);

// In refreshAccessToken:
const response = await fetch(`${BASE_URL}/auth/refresh`, { ... });

// In upload():
let response = await fetch(`${BASE_URL}${path}`, { ... });
// retry:
response = await fetch(`${BASE_URL}${path}`, { ... });
```

### Fixing Invite Page Fetch Calls

```typescript
// Source: frontend/src/app/(auth)/invite/[token]/page.tsx (after fix)
// Change lines 41-54: raw fetch to relative URL

fetch(`/api/auth/invite-validate?token=${encodeURIComponent(token)}`)
  .then(async (res) => { ... })
  ...

// Change lines 74-83: raw fetch to relative URL

const response = await fetch("/api/auth/invite-register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ token, first_name: firstName.trim(), ... }),
});
```

### Removing credit_reset_policy from Backend Schema

```python
# Source: backend/app/schemas/platform_settings.py (after fix)

class SettingsResponse(BaseModel):
    """Response schema for GET /api/admin/settings."""
    allow_public_signup: bool
    default_user_class: str
    invite_expiry_days: int
    # credit_reset_policy REMOVED — field is orphaned (scheduler reads from YAML)
    default_credit_cost: float
    max_pending_invites: int


class SettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allow_public_signup: bool | None = None
    default_user_class: str | None = None
    invite_expiry_days: int | None = None
    # credit_reset_policy REMOVED — cannot be meaningfully changed via API
    default_credit_cost: float | None = None
    max_pending_invites: int | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "SettingsUpdateRequest":
        if all(v is None for v in [
            self.allow_public_signup,
            self.default_user_class,
            self.invite_expiry_days,
            self.default_credit_cost,
            self.max_pending_invites,
        ]):
            raise ValueError("At least one setting must be provided")
        return self
```

### Removing Dead Tiers Route

```python
# Source: backend/app/routers/admin/tiers.py (after fix)
# Remove: entire @router.put("/users/{user_id}") endpoint (lines 58-105)
# Remove: associated imports (UUID, Request, log_admin_action, change_user_tier, TierChangeRequest)

"""Admin tier endpoints — read-only summary."""

from fastapi import APIRouter
from sqlalchemy import func, select

from app.dependencies import CurrentAdmin, DbSession
from app.models.user import User
from app.schemas.platform_settings import TierSummaryResponse
from app.services.user_class import get_user_classes

router = APIRouter(prefix="/tiers", tags=["admin-tiers"])


@router.get("", response_model=list[TierSummaryResponse])
async def get_tiers(db: DbSession, current_admin: CurrentAdmin) -> list[TierSummaryResponse]:
    """Return all tiers with user counts (TIER-05, TIER-07)."""
    # ... (unchanged)
```

### Removing credit_reset_policy from Frontend Types

```typescript
// Source: admin-frontend/src/types/settings.ts (after fix)

export interface PlatformSettings {
  allow_public_signup: boolean;
  default_user_class: string;
  invite_expiry_days: number;
  // credit_reset_policy REMOVED — not a meaningful API-writable field
  default_credit_cost: number;
  max_pending_invites: number;
}
```

---

## Key Facts: Current State of Each File

### INVITE-04/05 — Files and Current State

| File | Current State | Fix Required |
|------|---------------|--------------|
| `frontend/src/app/(auth)/invite/[token]/page.tsx` | Lines 41, 74: raw `fetch("http://localhost:8000/auth/...")` | Change to `/api/auth/...` |
| `frontend/src/lib/api-client.ts` | 4 occurrences of `http://localhost:8000` hardcoded as base URL | Change all to `/api` |
| `frontend/next.config.ts` | Rewrite `/api/:path*` -> `http://localhost:8000/:path*` already exists | No change needed |
| `frontend/src/app/(auth)/layout.tsx` | Invite path already excluded from auth redirect guard | No change needed |

### SETTINGS-05 — Files and Current State

| File | Current State | Fix Required |
|------|---------------|--------------|
| `backend/app/schemas/platform_settings.py` | `credit_reset_policy` in both `SettingsResponse` and `SettingsUpdateRequest` | Remove from both |
| `backend/app/services/platform_settings.py` | `credit_reset_policy` in DEFAULTS and validate_setting() | Remove from both |
| `admin-frontend/src/types/settings.ts` | `credit_reset_policy: string` in `PlatformSettings` interface | Remove |
| `admin-frontend/src/components/settings/SettingsForm.tsx` | Already correct — shows per-tier table, does NOT save credit_reset_policy | No change needed |
| `admin-frontend/src/hooks/useSettings.ts` | No reference to credit_reset_policy | No change needed |

### Dead Route — Files and Current State

| File | Current State | Fix Required |
|------|---------------|--------------|
| `backend/app/routers/admin/tiers.py` | `@router.put("/users/{user_id}")` endpoint at lines 58-105 | Remove endpoint + clean imports |
| `backend/app/routers/admin/users.py` | `@router.put("/{user_id}/tier")` at line 383 — this is the ACTIVE endpoint | No change needed |

---

## Open Questions

1. **Should `credit_reset_policy` DB rows be cleaned up via migration?**
   - What we know: The DB may have rows with `key='credit_reset_policy'` from prior admin sessions. Removing the field from the API schema means these rows become inert.
   - What's unclear: Whether a future phase will re-introduce per-tier override support that might read this key.
   - Recommendation: Leave DB rows in place — no migration needed for Phase 32. The `get_all()` function returns all DB rows but `SettingsResponse(**parsed)` will silently ignore unknown keys (Pydantic default behavior for models without `extra="forbid"`).

2. **Should the `register/page.tsx` and `useSSEStream.ts` hardcoded URLs be fixed in Phase 32?**
   - What we know: Both files have `http://localhost:8000` hardcoded. Fixing `api-client.ts` does NOT fix these (they use raw `fetch()`).
   - What's unclear: Whether these are in scope for Phase 32 (requirements only mention INVITE-04, INVITE-05).
   - Recommendation: Fix `api-client.ts` only for Phase 32 (it fixes invite page's `apiClient.get("/auth/me")` call). Leave `register/page.tsx` and `useSSEStream.ts` out of scope — they are separate bugs not in the Phase 32 requirements. Document them as follow-up items.

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection (all findings) — read source files, confirmed line numbers and current state
- `frontend/src/app/(auth)/invite/[token]/page.tsx` — hardcoded URLs at lines 41, 74
- `frontend/src/lib/api-client.ts` — hardcoded base URL at lines 64, 106, 118, 196
- `frontend/next.config.ts` — rewrite rule confirming `/api/:path*` proxy exists
- `backend/app/routers/admin/tiers.py` — dead route at lines 58-105
- `backend/app/schemas/platform_settings.py` — credit_reset_policy in both schemas
- `backend/app/scheduler.py` — confirmed: reads `reset_policy` from YAML, not from platform_settings DB
- `admin-frontend/src/components/settings/SettingsForm.tsx` — confirmed: does NOT send credit_reset_policy in save payload
- `.planning/v0.5-MILESTONE-AUDIT.md` — confirmed gaps and their severity

### Secondary (MEDIUM confidence)
- `.planning/debug/p28-t1-p31-t7-settings-tier-dropdown.md` — detailed diagnosis of credit_reset_policy disconnect
- `.planning/debug/p30-t4-invite-registration.md` — prior invite page diagnosis (note: some issues already fixed in current code)

---

## Metadata

**Confidence breakdown:**
- Problem diagnosis: HIGH — all three issues directly observed in source files with exact line numbers
- Fix approach: HIGH — established patterns already in use in admin-frontend (relative URLs, rewrite proxy)
- Scope: HIGH — INVITE-04/05 and SETTINGS-05 requirements are clear and narrow
- Risk: LOW — all changes are surgical; no new libraries, no DB migrations

**Research date:** 2026-02-17
**Valid until:** 2026-03-17 (stable codebase; these are not fast-moving areas)
