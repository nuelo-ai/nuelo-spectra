---
phase: 32-production-readiness
verified: 2026-02-17T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 32: Production Readiness Verification Report

**Phase Goal:** Fix production-blocking invite URL hardcoding, resolve misleading credit_reset_policy settings control, and remove dead tier route
**Verified:** 2026-02-17
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                        | Status     | Evidence                                                                                  |
|----|----------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------|
| 1  | Invite registration page works in staging and production — no hardcoded localhost URLs remain | VERIFIED   | `api-client.ts` line 7: `const BASE_URL = "/api"`. Zero `localhost:8000` in both files.  |
| 2  | All apiClient calls use relative /api paths via the existing Next.js rewrite proxy           | VERIFIED   | BASE_URL used at lines 66, 108, 120, 198, 213 in `api-client.ts` — 5/5 fetch calls fixed |
| 3  | PATCH /api/admin/settings rejects credit_reset_policy as an unknown/extra field              | VERIFIED   | `SettingsUpdateRequest` has `extra="forbid"` and no `credit_reset_policy` field           |
| 4  | GET /api/admin/settings does not return credit_reset_policy in the response body             | VERIFIED   | `SettingsResponse` has no `credit_reset_policy` field. `SettingsResponse` does NOT have `extra="forbid"` — orphaned DB rows will be silently ignored (safe) |
| 5  | PUT /api/admin/tiers/users/{user_id} returns 404 — route is removed                         | VERIFIED   | `tiers.py` contains only `@router.get("")`. No `@router.put` present.                    |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact                                              | Provides                                           | Exists | Substantive | Wired  | Status   |
|-------------------------------------------------------|----------------------------------------------------|--------|-------------|--------|----------|
| `frontend/src/lib/api-client.ts`                      | Auth-aware API client with relative /api base URL  | YES    | YES         | YES    | VERIFIED |
| `frontend/src/app/(auth)/invite/[token]/page.tsx`     | Invite registration page with relative fetch URLs  | YES    | YES         | YES    | VERIFIED |
| `backend/app/schemas/platform_settings.py`            | Settings schemas without credit_reset_policy       | YES    | YES         | YES    | VERIFIED |
| `backend/app/services/platform_settings.py`           | Settings service without credit_reset_policy       | YES    | YES         | YES    | VERIFIED |
| `admin-frontend/src/types/settings.ts`                | PlatformSettings interface without credit_reset_policy | YES | YES        | YES    | VERIFIED |
| `backend/app/routers/admin/tiers.py`                  | Tiers router with only GET endpoint                | YES    | YES         | YES    | VERIFIED |

**Artifact detail:**

`frontend/src/lib/api-client.ts`
- Line 7: `const BASE_URL = "/api"` — constant present
- Lines 66, 108, 120, 198, 213: all use `${BASE_URL}` — zero `localhost:8000` occurrences
- Upload initial and retry both use `${BASE_URL}${path}` — inconsistency from pre-phase also corrected
- Imported and used by `invite/[token]/page.tsx` (line 11: `import { setTokens, apiClient } from "@/lib/api-client"`)

`frontend/src/app/(auth)/invite/[token]/page.tsx`
- Line 41: `fetch('/api/auth/invite-validate?token=${encodeURIComponent(token)}')`
- Line 74: `fetch("/api/auth/invite-register", { method: "POST", ... })`
- Line 95: `apiClient.get("/auth/me")` — benefits from BASE_URL fix in api-client.ts
- Full form with state, validation, and router.push("/dashboard") — not a stub

`backend/app/schemas/platform_settings.py`
- `SettingsResponse`: 5 fields (allow_public_signup, default_user_class, invite_expiry_days, default_credit_cost, max_pending_invites). No `credit_reset_policy`.
- `SettingsUpdateRequest`: same 5 fields as Optional, plus `model_config = ConfigDict(extra="forbid")`. No `credit_reset_policy`.
- `at_least_one_field` validator references only the 5 remaining fields — no `credit_reset_policy` in validator list
- `TierChangeRequest` class retained (not imported by tiers.py; harmless per plan decision)

`backend/app/services/platform_settings.py`
- `DEFAULTS` dict: 5 keys — `allow_public_signup`, `default_user_class`, `invite_expiry_days`, `default_credit_cost`, `max_pending_invites`. No `credit_reset_policy`.
- `VALID_KEYS = set(DEFAULTS.keys())` — automatically excludes `credit_reset_policy`
- `validate_setting()` has no `credit_reset_policy` branch

`admin-frontend/src/types/settings.ts`
- `PlatformSettings` interface: 5 fields matching backend schema. No `credit_reset_policy`.
- `PlatformSettingsUpdate = Partial<PlatformSettings>` — derived type also clean

`backend/app/routers/admin/tiers.py`
- Only imports: `APIRouter`, `func`, `select`, `CurrentAdmin`, `DbSession`, `User`, `TierSummaryResponse`, `get_user_classes`
- No `HTTPException`, no `status`, no `Request`, no `UUID`, no `TierChangeRequest`, no `log_admin_action`, no `change_user_tier`
- Single endpoint: `@router.get("")` — queries DB live for user counts, reads YAML for tier configs, builds real `TierSummaryResponse` objects

---

### Key Link Verification

| From                                              | To                        | Via                             | Status   | Evidence                              |
|---------------------------------------------------|---------------------------|----------------------------------|----------|---------------------------------------|
| `frontend/src/app/(auth)/invite/[token]/page.tsx` | `/api/auth/invite-validate` | plain `fetch()` with relative URL | VERIFIED | Line 41: `fetch('/api/auth/invite-validate?token=...')` |
| `frontend/src/app/(auth)/invite/[token]/page.tsx` | `/api/auth/invite-register` | plain `fetch()` with relative URL | VERIFIED | Line 74: `fetch("/api/auth/invite-register", { method: "POST", ... })` |
| `frontend/src/lib/api-client.ts`                  | `/api/`                    | BASE_URL constant in all fetch calls | VERIFIED | Line 7: `const BASE_URL = "/api"`. Used at 5 call sites. |

---

### Requirements Coverage

| Requirement | Source Plan  | Description                                                                 | Status    | Evidence                                                                                          |
|-------------|-------------|-----------------------------------------------------------------------------|-----------|---------------------------------------------------------------------------------------------------|
| INVITE-04   | 32-01-PLAN  | Invite registration page with pre-filled, locked email (no localhost URLs)  | SATISFIED | `invite/[token]/page.tsx`: no `localhost:8000`; email populated from API response at line 47      |
| INVITE-05   | 32-01-PLAN  | Invite flow works in localhost, staging, and production via relative /api paths | SATISFIED | All fetch calls use relative `/api/auth/...` paths; Next.js rewrite in `next.config.ts` handles env routing |
| SETTINGS-05 | 32-01-PLAN  | credit_reset_policy either functional or clearly non-writable               | SATISFIED | Field removed from schema, service, and frontend type — PATCH rejects it (extra="forbid"), GET does not return it |

**Note on REQUIREMENTS.md status column:** The requirements tracker in `.planning/REQUIREMENTS.md` still shows "Pending" for all three IDs (lines 206-207, 235). This is a documentation lag — the code changes fully satisfy the requirements as defined. The "Pending" status reflects the pre-execution state of the tracker file and does not indicate a gap.

**Orphaned requirements check:** No additional IDs mapped to Phase 32 in REQUIREMENTS.md beyond INVITE-04, INVITE-05, SETTINGS-05.

---

### Anti-Patterns Found

None. No TODO/FIXME/PLACEHOLDER/stub patterns detected in any of the six modified files.

---

### Out-of-Scope Items (Documented, Not Gaps)

Two files outside Phase 32 scope still contain `localhost:8000`:

- `frontend/src/app/(auth)/register/page.tsx` line 26: `fetch("http://localhost:8000/auth/signup-status")` — raw fetch bypassing apiClient; explicitly excluded from Phase 32 scope per RESEARCH.md
- `frontend/src/hooks/useSSEStream.ts` line 112: `fetch('http://localhost:8000/chat/sessions/${sessionId}/stream', ...)` — separately tracked bug; explicitly excluded per RESEARCH.md

These are known issues documented as follow-up work, not gaps in Phase 32 goal achievement.

---

### Human Verification Required

None. All must-haves are verifiable programmatically. The behavioral correctness of the invite flow and settings API contract is fully determinable from static code analysis:

- Localhost removal: grep-verifiable (zero occurrences in scope files)
- BASE_URL wiring: grep-verifiable (5 usage sites confirmed)
- credit_reset_policy removal: grep-verifiable (absent from schema, service, frontend type)
- extra="forbid" enforcement: code-verifiable (ConfigDict present in SettingsUpdateRequest)
- Dead route removal: code-verifiable (no @router.put in tiers.py)
- Commits: git-verifiable (f753ade, ce5b6c7, b0da049 confirmed in history)

---

### Commits Verified

| Commit    | Description                                                   | Status      |
|-----------|---------------------------------------------------------------|-------------|
| `f753ade` | fix(32-01): replace hardcoded localhost URLs with relative /api paths | VERIFIED |
| `ce5b6c7` | fix(32-01): remove credit_reset_policy from settings schema, service, and types | VERIFIED |
| `b0da049` | fix(32-01): remove dead PUT /api/admin/tiers/users/{user_id} route | VERIFIED |

---

## Summary

All three production-blocking issues are resolved. The code matches the plan's must-haves exactly:

**INVITE-04/05 (Hardcoded localhost):** `api-client.ts` now defines `const BASE_URL = "/api"` and uses it at all 5 fetch call sites. The invite page's two raw fetch calls use `/api/auth/invite-validate` and `/api/auth/invite-register`. The invite page's `apiClient.get("/auth/me")` call benefits automatically from the api-client fix. The Next.js rewrite proxy in `next.config.ts` routes all `/api/:path*` calls to the backend — invite flow is now environment-agnostic.

**SETTINGS-05 (credit_reset_policy):** The field is removed from `SettingsResponse`, `SettingsUpdateRequest`, `DEFAULTS`, `validate_setting()`, and `PlatformSettings`. `SettingsUpdateRequest` enforces `extra="forbid"` — a PATCH body containing `credit_reset_policy` will receive a 422 response. `SettingsResponse` does not have `extra="forbid"` — any orphaned DB rows with `key='credit_reset_policy'` will be silently ignored by Pydantic when constructing the response (safe, no migration needed).

**Dead route:** `tiers.py` contains only the `@router.get("")` endpoint with a substantive implementation (live DB query + YAML config). All six imports that were exclusively used by the dead PUT endpoint have been removed. The active `PUT /api/admin/users/{user_id}/tier` in `users.py` is untouched.

---

_Verified: 2026-02-17_
_Verifier: Claude (gsd-verifier)_
