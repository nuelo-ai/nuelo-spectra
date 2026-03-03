---
phase: 38-api-key-infrastructure
verified: 2026-02-23T00:00:00Z
status: human_needed
score: 13/13 automated checks verified
re_verification: false
human_verification:
  - test: "Navigate to /settings in a running browser session and verify the API key create/copy/revoke flow"
    expected: "Empty state shows 'No API keys yet', Create dialog appears with name/description fields, full key displayed in non-closable modal with copy button, key appears in list after confirming, revoke triggers AlertDialog confirmation, revoked key shown as Revoked badge"
    why_human: "Visual rendering, dialog behavior (onOpenChange no-op prevents ESC/overlay close), clipboard API, and end-to-end HTTP lifecycle require a live browser"
  - test: "With a running backend in dev mode, test API key Bearer authentication: curl /api/v1/keys with a valid spe_ key"
    expected: "Returns 200 with key list; after revoke, same key returns 401 with 'Invalid or revoked API key'"
    why_human: "Live HTTP smoke test was not executed — Docker container ran old code. Unit tests cover the logic path but not the live HTTP lifecycle."
---

# Phase 38: API Key Infrastructure Verification Report

**Phase Goal:** Users can create, view, and revoke API keys, and the backend can authenticate API requests using those keys
**Verified:** 2026-02-23
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The api_keys table exists in the DB after running alembic upgrade head | VERIFIED | `b3f8a1c2d4e5_add_api_keys_table.py` creates table with all 11 columns, 2 indexes, CASCADE FK |
| 2 | ApiKey model maps correctly to the table (all 11 columns) | VERIFIED | `backend/app/models/api_key.py`: id, user_id, name, description, key_prefix, token_hash, is_active, scopes, expires_at, last_used_at, created_at — all confirmed |
| 3 | User.api_keys relationship exists and cascades delete-orphan | VERIFIED | `user.py` line 58: `cascade="all, delete-orphan"` on api_keys relationship |
| 4 | SPECTRA_MODE=api is accepted without ValidationError | VERIFIED | `config.py` line 90: `allowed = ("public", "admin", "dev", "api")` with field_validator; `main.py` line 291 includes "api" in allowed set |
| 5 | generate_api_key() returns (full_key, key_prefix, token_hash) with spe_ prefix and 64-char SHA-256 hash | VERIFIED | 5/5 TestGenerateApiKey tests passing; implementation in `services/api_key.py` lines 15-28 confirmed |
| 6 | ApiKeyService.create() stores only token_hash, returns (ApiKey, full_raw_key) | VERIFIED | Service stores key_prefix and token_hash only; full_key returned from create() — test_create_returns_record_and_raw_key passing |
| 7 | ApiKeyService.revoke() sets is_active=False; authenticate() with revoked key returns None | VERIFIED | revoke() queries WHERE id AND user_id, sets is_active=False; authenticate() filters `ApiKey.is_active == True` in SQL WHERE — 2/2 revoke tests and 3/3 authenticate tests passing |
| 8 | ApiKeyService.authenticate() returns User for valid key, None for invalid/revoked | VERIFIED | 12/12 tests pass in `tests/test_api_key_service.py` |
| 9 | POST /api/v1/keys creates key and returns full_key once | VERIFIED | `api_keys.py` POST endpoint calls ApiKeyService.create(), returns ApiKeyCreateResponse with full_key; `ApiKeyCreateResponse` schema has full_key field |
| 10 | GET /api/v1/keys returns list without full key values | VERIFIED | GET endpoint returns `list[ApiKeyListItem]`; `ApiKeyListItem` schema has no full_key field |
| 11 | DELETE /api/v1/keys/{id} revokes key, 404 if not found | VERIFIED | DELETE endpoint calls ApiKeyService.revoke(); raises HTTPException(404) if returns False |
| 12 | API request with valid API key in Bearer header authenticates | VERIFIED | `get_authenticated_user()` in `dependencies.py`: fast-paths on `spe_` prefix, calls ApiKeyService.authenticate(), returns User |
| 13 | api_v1_router mounted in api and dev modes, NOT in public mode | VERIFIED | `main.py` line 338: `if mode in ("api", "dev"):` — confirmed; admin and public mode blocks are separate |

**Score:** 13/13 automated truths verified

**Note on routing:** The `api_v1_router` has `prefix="/v1"` (not `/api/v1`). This is correct. The Next.js catch-all proxy at `frontend/src/app/api/[...slug]/route.ts` strips the `/api` prefix before forwarding to the backend (`backendPath = rawPathname.replace(/^\/api/, "")`). External clients calling `/api/v1/keys` hit the backend at `/v1/keys`.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/models/api_key.py` | ApiKey SQLAlchemy model with 11 columns | VERIFIED | 50 lines; all 11 columns present; ForeignKey to users.id with CASCADE; PG_ARRAY for scopes |
| `backend/alembic/versions/b3f8a1c2d4e5_add_api_keys_table.py` | Migration creating api_keys table | VERIFIED | Contains `op.create_table('api_keys'...)`; all 11 columns; 2 indexes; proper downgrade() |
| `backend/app/config.py` | Settings accepting SPECTRA_MODE=api | VERIFIED | field_validator at line 86 with `allowed = ("public", "admin", "dev", "api")` |
| `backend/tests/test_api_key_service.py` | TDD test suite for ApiKeyService | VERIFIED | 136 lines; 12 test cases across 5 classes; all passing |
| `backend/app/services/api_key.py` | ApiKeyService with 4 static methods | VERIFIED | 121 lines; generate_api_key(), create, list_for_user, revoke, authenticate — all implemented |
| `backend/app/schemas/api_key.py` | ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyListItem | VERIFIED | 32 lines; all 3 schemas with correct fields; `from_attributes=True` on ApiKeyListItem |
| `backend/app/routers/api_v1/__init__.py` | api_v1_router aggregator | VERIFIED | Exports api_v1_router; includes api_keys sub-router; prefix="/v1" |
| `backend/app/routers/api_v1/api_keys.py` | CRUD endpoints GET/POST/DELETE | VERIFIED | 47 lines; 3 endpoints; uses CurrentUser + DbSession; delegates to ApiKeyService |
| `backend/app/dependencies.py` | get_authenticated_user() + ApiAuthUser | VERIFIED | oauth2_scheme_optional (auto_error=False); full JWT+API-key unified dep; ApiAuthUser alias at line 244 |
| `backend/app/main.py` | Mode-gated api_v1_router mounting | VERIFIED | `if mode in ("api", "dev")` block at line 338 mounts api_v1_router |
| `frontend/src/hooks/useApiKeys.ts` | useApiKeys, useCreateApiKey, useRevokeApiKey | VERIFIED | 103 lines; all 3 hooks with TypeScript interfaces; calls `/v1/keys` via apiClient (BASE_URL="/api" prepended) |
| `frontend/src/components/settings/ApiKeySection.tsx` | API key management UI with 5 states | VERIFIED | 315 lines; loading, error, empty, list, create dialog, one-time display dialog, revoke AlertDialog — all implemented |
| `frontend/src/app/(dashboard)/settings/page.tsx` | Settings page with ApiKeySection | VERIFIED | Imports and renders `<ApiKeySection />` after `<AccountInfo />` at line 41 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/models/api_key.py` | `backend/app/models/user.py` | ForeignKey("users.id") + back_populates | VERIFIED | Line 21: `ForeignKey("users.id", ondelete="CASCADE")`; line 46: relationship back_populates="api_keys" |
| `backend/alembic/env.py` | `backend/app/models/api_key.py` | import in model list | VERIFIED | Line 13: `from app.models import ... api_key` |
| `backend/app/services/api_key.py` | `backend/app/models/api_key.py` | imports ApiKey model | VERIFIED | Line 11: `from app.models.api_key import ApiKey` |
| `backend/app/services/api_key.py` | `backend/app/models/user.py` | authenticate() uses get_user_by_id | VERIFIED | Line 12: `from app.services.auth import get_user_by_id`; line 120: `return await get_user_by_id(db, api_key.user_id)` |
| `backend/app/routers/api_v1/api_keys.py` | `backend/app/services/api_key.py` | ApiKeyService.create/list_for_user/revoke | VERIFIED | Lines 17, 27, 43: `ApiKeyService.list_for_user`, `ApiKeyService.create`, `ApiKeyService.revoke` |
| `backend/app/dependencies.py` | `backend/app/services/api_key.py` | ApiKeyService.authenticate in get_authenticated_user | VERIFIED | Line 141: `user = await ApiKeyService.authenticate(db, token)` |
| `backend/app/main.py` | `backend/app/routers/api_v1/__init__.py` | conditional import and include_router | VERIFIED | Line 338: `if mode in ("api", "dev"):` then `from app.routers.api_v1 import api_v1_router; app.include_router(api_v1_router)` |
| `frontend/src/hooks/useApiKeys.ts` | `/api/v1/keys` (backend) | apiClient calls GET/POST/DELETE /v1/keys | VERIFIED | Calls `/v1/keys`; apiClient prepends BASE_URL="/api" making full URL `/api/v1/keys`; proxy strips `/api` before sending to backend |
| `frontend/src/components/settings/ApiKeySection.tsx` | `frontend/src/hooks/useApiKeys.ts` | useApiKeys, useCreateApiKey, useRevokeApiKey | VERIFIED | Line 9: imports all 3 hooks; used at lines 38-40 |
| `frontend/src/app/(dashboard)/settings/page.tsx` | `frontend/src/components/settings/ApiKeySection.tsx` | `<ApiKeySection />` rendered in page | VERIFIED | Line 12: import; line 41: `<ApiKeySection />` rendered in settings sections |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| APIKEY-01 | Plans 02, 03, 04 | User can view their API keys on the Settings/API Keys page | SATISFIED | GET /v1/keys endpoint + ApiKeySection list rendering + useApiKeys hook |
| APIKEY-02 | Plans 02, 03, 04 | User can create an API key with a name and description | SATISFIED | POST /v1/keys endpoint + ApiKeySection create dialog + useCreateApiKey hook |
| APIKEY-03 | Plans 02, 03, 04 | User can revoke their own API keys | SATISFIED | DELETE /v1/keys/{id} + revoke confirmation dialog + useRevokeApiKey hook |
| APIKEY-04 | Plans 01, 02 | Revoked API keys cannot be used for authentication | SATISFIED | authenticate() filters `ApiKey.is_active == True` in SQL WHERE; revoked keys return None |
| APIKEY-05 | Plans 01, 02 | API keys are stored securely (hashed, full key shown only once) | SATISFIED | token_hash = SHA-256(full_key); full_key never stored; only returned from POST once; ApiKeyCreateResponse has full_key field, ApiKeyListItem does not |
| APISEC-01 | Plans 02, 03 | API requests authenticate via API key in `Authorization: Bearer` header | SATISFIED | get_authenticated_user() reads oauth2_scheme_optional Bearer token, fast-paths on spe_ prefix |
| APISEC-02 | Plans 02, 03 | Invalid or revoked API keys return 401 Unauthorized | SATISFIED | get_authenticated_user() raises HTTP 401 "Invalid or revoked API key" when ApiKeyService.authenticate() returns None |
| APIINFRA-01 | Plans 01, 03 | SPECTRA_MODE=api enables API routes on the existing backend | SATISFIED | config.py field_validator accepts "api"; main.py mounts api_v1_router in api mode |
| APIINFRA-02 | Plans 01, 03 | API routes are versioned under `/api/v1/` | SATISFIED | Router prefix="/v1"; proxy at `/api/[...slug]/route.ts` strips `/api`; external URL is `/api/v1/keys` |
| APIINFRA-05 | Plans 01, 03 | In SPECTRA_MODE=dev, all /api/v1/ routes are active alongside existing backend routes | SATISFIED | main.py: `if mode in ("api", "dev"):` mounts api_v1_router |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `frontend/src/components/settings/ApiKeySection.tsx` | 212, 224 | `placeholder=` | Info | HTML input placeholder attributes — not stub code, legitimate UI |

No blocker or warning anti-patterns found.

---

### Human Verification Required

#### 1. API Key UI End-to-End Flow (Browser)

**Test:** Start the full stack, navigate to `http://localhost:3000/settings`, scroll to API Keys section.
**Expected:**
- Empty state: "No API keys yet" with Create API Key button visible
- Clicking "Create API Key": dialog with Name (required) and Description (optional) fields appears
- After submit: one-time key display dialog opens showing full `spe_...` key; dialog cannot be closed by clicking overlay or pressing ESC (onOpenChange no-ops); copy button works; "I have copied my key" button dismisses dialog
- Key appears in list with name, key prefix (monospace), Active badge, created date
- Revoke button opens AlertDialog confirmation; on confirm, key shows as Revoked badge
**Why human:** Visual rendering, clipboard API behavior, dialog close prevention (ESC/overlay), and full HTTP lifecycle require a live browser session.

#### 2. API Key Bearer Authentication (Live HTTP)

**Test:** With backend running in dev mode, create an API key via POST, then use the full key as Bearer token:
```bash
curl -s http://localhost:8000/v1/keys -H "Authorization: Bearer spe_<the-key>"
```
Then revoke the key and repeat the request.
**Expected:** Pre-revoke: 200 with key list. Post-revoke: 401 `{"detail": "Invalid or revoked API key"}`.
**Why human:** The 38-03 smoke test was not executed against a live HTTP server (Docker container ran old code at time of implementation). All code paths are unit-tested but live HTTP round-trip was not confirmed.

---

### Gaps Summary

No automated gaps found. All 13 observable truths are verified, all artifacts are substantive and wired, all 10 requirement IDs are satisfied by the implemented code.

The two human verification items are confirmation steps for already-correct implementation — the unit tests, code inspection, and TypeScript compilation all pass. These items flag the live end-to-end browser and HTTP tests that were not run during implementation.

---

_Verified: 2026-02-23_
_Verifier: Claude (gsd-verifier)_
