---
phase: 28-platform-config
verified: 2026-02-16T21:30:00Z
status: passed
score: 13/13 must-haves verified
re_verification: false
---

# Phase 28: Platform Config Verification Report

**Phase Goal:** Admins can configure platform behavior at runtime -- tier credit allocations, signup mode, invite expiry, credit policies -- without redeployment

**Verified:** 2026-02-16T21:30:00Z

**Status:** passed

**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /api/admin/settings returns all platform settings as a flat JSON dict with parsed values (not raw JSON strings) | ✓ VERIFIED | `backend/app/routers/admin/settings.py:18-26` — GET endpoint parses all raw values with `json.loads()` and returns `SettingsResponse` with typed fields |
| 2 | PATCH /api/admin/settings accepts a partial dict and upserts changed keys to platform_settings table | ✓ VERIFIED | `backend/app/routers/admin/settings.py:29-73` — PATCH endpoint validates all changed values, upserts each via `platform_settings.upsert()`, and returns updated settings |
| 3 | Settings reads use a 30-second TTL module-level cache; writes invalidate the cache immediately | ✓ VERIFIED | `backend/app/services/platform_settings.py:19-57` — `_CACHE_TTL_SECONDS = 30.0`, cache check in `get_all()`, invalidation in line 54 after upserts |
| 4 | Invalid setting keys or values (e.g., default_user_class not in yaml, invite_expiry_days < 1) are rejected with 422 | ✓ VERIFIED | `backend/app/routers/admin/settings.py:44-47` — validates each changed key via `validate_setting()`, raises 422 on error. Validation logic in `backend/app/services/platform_settings.py:112-150` |
| 5 | GET /api/admin/tiers returns tier summary with name, display_name, credits, reset_policy, and user_count per tier | ✓ VERIFIED | `backend/app/routers/admin/tiers.py:21-55` — builds response from yaml config + DB user counts, returns list of `TierSummaryResponse` |
| 6 | All admin settings and tier endpoints require CurrentAdmin authentication and create audit log entries | ✓ VERIFIED | All endpoints use `CurrentAdmin` dependency. Settings PATCH: audit log lines 57-66. Tier change PUT: audit log lines 89-102 |
| 7 | Admin can change a user's tier via PUT /api/admin/tiers/users/{user_id} and the user's credit balance resets to the new tier's allocation | ✓ VERIFIED | `backend/app/routers/admin/tiers.py:58-105` — calls `change_user_tier()` service which atomically updates `user_class` and resets credits via `CreditService.execute_reset()` |
| 8 | Public GET /auth/signup-status returns {signup_allowed: bool} without requiring authentication | ✓ VERIFIED | `backend/app/routers/auth.py:44-51` — public endpoint (no `CurrentUser` dep), reads `allow_public_signup` from platform_settings |
| 9 | When allow_public_signup is false, POST /auth/signup without invite_token returns 403 with invite-only message | ✓ VERIFIED | `backend/app/routers/auth.py:73-83` — checks `allow_public_signup`, raises 403 "Public registration is currently disabled. An invitation is required." if false and no token |
| 10 | When allow_public_signup is false, the registration page shows the branded invite-only message instead of the form | ✓ VERIFIED | `frontend/src/app/(auth)/register/page.tsx:73-85` — conditionally renders invite-only message with exact branded text when `signupAllowed === false` |
| 11 | When allow_public_signup is true, signup works exactly as before (no regression) | ✓ VERIFIED | `backend/app/routers/auth.py:73-108` — when `allow_signup` is true, skips invite validation and proceeds to normal signup flow. Frontend shows form when `signupAllowed === true` |
| 12 | Chat credit cost reads from platform_settings instead of hardcoded Decimal('1.0') | ✓ VERIFIED | `backend/app/routers/chat.py:36-38` — reads `default_credit_cost` from platform_settings, converts to Decimal |
| 13 | Default user class for new signups reads from platform_settings instead of hardcoded 'free' | ✓ VERIFIED | `backend/app/routers/auth.py:105-108` — reads `default_user_class` from platform_settings, passes to `create_user()` |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/platform_settings.py` | PlatformSettingsService with TTL cache, get_all, get, upsert, invalidate_cache | ✓ VERIFIED | 151 lines, contains all required functions and `_CACHE_TTL_SECONDS` constant |
| `backend/app/schemas/platform_settings.py` | Pydantic schemas for settings API (SettingsResponse, SettingsUpdateRequest, TierSummaryResponse, TierChangeRequest) | ✓ VERIFIED | 62 lines, contains all 4 schemas with proper validation |
| `backend/app/routers/admin/settings.py` | GET and PATCH /api/admin/settings endpoints | ✓ VERIFIED | 74 lines, contains both endpoints with full implementation |
| `backend/app/routers/admin/tiers.py` | GET /api/admin/tiers endpoint with user counts, PUT /tiers/users/{user_id} endpoint | ✓ VERIFIED | 106 lines, contains tier summary (GET) and tier change (PUT) endpoints |
| `backend/app/services/admin/tiers.py` | change_user_tier service function with atomic credit reset | ✓ VERIFIED | 84 lines, implements tier change with row locking and credit reset |
| `backend/app/routers/auth.py` | GET /auth/signup-status public endpoint and signup gating logic | ✓ VERIFIED | Modified with signup-status endpoint (lines 44-51) and gating in signup endpoint (lines 73-108) |
| `frontend/src/app/(auth)/register/page.tsx` | Registration page with invite-only message when signup disabled | ✓ VERIFIED | 156 lines, contains signup status check (lines 25-30) and conditional message (lines 73-85) with exact branded text |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `backend/app/routers/admin/settings.py` | `backend/app/services/platform_settings.py` | get_all, upsert, invalidate_cache calls | ✓ WIRED | Lines 24, 51, 54 call service functions directly |
| `backend/app/routers/admin/tiers.py` | `backend/app/services/user_class.py` | get_user_classes() for tier definitions | ✓ WIRED | Line 40: `classes = get_user_classes()` |
| `backend/app/routers/admin/__init__.py` | `backend/app/routers/admin/settings.py` | admin_router.include_router | ✓ WIRED | Line 10: router registration found |
| `backend/app/routers/admin/__init__.py` | `backend/app/routers/admin/tiers.py` | admin_router.include_router | ✓ WIRED | Line 11: router registration found |
| `backend/app/routers/auth.py` | `backend/app/services/platform_settings.py` | platform_settings.get(db, 'allow_public_signup') check | ✓ WIRED | Lines 50, 75, 105 read from platform_settings |
| `backend/app/routers/chat.py` | `backend/app/services/platform_settings.py` | platform_settings.get(db, 'default_credit_cost') | ✓ WIRED | Lines 36-38 read credit cost from platform_settings |
| `frontend/src/app/(auth)/register/page.tsx` | `/auth/signup-status` | fetch on mount to check signup status | ✓ WIRED | Lines 25-30: useEffect fetches signup-status, sets state |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SETTINGS-01 | 28-01 | Centralized settings page for global platform configuration | ✓ SATISFIED | GET /api/admin/settings endpoint implemented |
| SETTINGS-02 | 28-01 | Signup toggle setting (allow_public_signup: true/false) | ✓ SATISFIED | Setting key exists in DEFAULTS, validated, stored |
| SETTINGS-03 | 28-01 | Default user class for new signups setting | ✓ SATISFIED | default_user_class setting implemented, wired to signup flow |
| SETTINGS-04 | 28-01 | Invite link expiry duration setting (days) | ✓ SATISFIED | invite_expiry_days setting with 1-365 validation |
| SETTINGS-05 | 28-01 | Credit reset policy setting (manual/weekly/monthly) | ✓ SATISFIED | credit_reset_policy setting stored (informational, per plan note) |
| SETTINGS-06 | Phase 28 | Credit amount overrides per user class | ⚠️ DEFERRED | Explicitly deferred per user decision (28-01-PLAN.md line 156, 28-01-SUMMARY.md line 84) |
| SETTINGS-07 | 28-01 | Default credit cost per message setting | ✓ SATISFIED | default_credit_cost setting implemented, wired to chat flow |
| SETTINGS-08 | 28-01 | Settings persisted in platform_settings table with 30s TTL cache | ✓ SATISFIED | PlatformSettingsService implements TTL cache pattern |
| TIER-01 | 28-01 | User classes defined in user_classes.yaml config file | ✓ SATISFIED | Tier summary endpoint reads from yaml via get_user_classes() |
| TIER-02 | Phase 28 | Admin can edit credit amounts per tier | ⚠️ DEFERRED | Explicitly deferred per user decision (28-01-PLAN.md line 156, 28-01-SUMMARY.md line 84) |
| TIER-03 | 28-01 | Adding/removing tiers requires config change + redeployment | ✓ SATISFIED | Tiers read from yaml, not dynamic |
| TIER-04 | 28-02 | Users table has user_class field | ✓ SATISFIED | change_user_tier modifies user_row.user_class field |
| TIER-05 | 28-01 | Admin can view all tiers with current credit allocations | ✓ SATISFIED | GET /api/admin/tiers endpoint implemented |
| TIER-06 | 28-02 | Admin can assign or change a user's tier manually | ✓ SATISFIED | PUT /api/admin/tiers/users/{user_id} endpoint implemented |
| TIER-07 | 28-01 | Admin can view how many users are in each tier | ✓ SATISFIED | Tier summary includes user_count from DB query |
| SIGNUP-01 | 28-02 | Global toggle in platform settings: allow public signup | ✓ SATISFIED | allow_public_signup setting implemented and enforced |
| SIGNUP-02 | 28-02 | When disabled, signup page shows invite-only message | ✓ SATISFIED | Frontend conditionally renders branded message |
| SIGNUP-03 | 28-02 | When disabled, only users with valid invite token can register | ✓ SATISFIED | Backend validates invite token hash against Invitation model |
| SIGNUP-04 | 28-02 | Toggle changes take effect immediately (no server restart) | ✓ SATISFIED | Settings use 30s TTL cache, invalidated on write |

**Requirements Summary:**
- Total requirements claimed: 19
- Satisfied: 17
- Deferred (documented): 2 (SETTINGS-06, TIER-02)
- Failed: 0

**Note on deferred requirements:** SETTINGS-06 and TIER-02 (tier credit overrides and admin tier editing) were explicitly scoped out per user decision, documented in both plan and summary. The roadmap requirement list remains unchanged, but implementation was consciously deferred. This is a valid product decision, not a gap.

### Anti-Patterns Found

No blocker anti-patterns found. Code quality is high:

- No TODO/FIXME/placeholder comments in implementation files
- No empty return stubs
- No console.log-only implementations
- All functions have substantive logic
- Proper error handling with HTTPException
- Atomic database operations with SELECT FOR UPDATE
- Consistent audit logging across endpoints

### Human Verification Required

#### 1. Settings API End-to-End Flow

**Test:** Start backend in dev mode, login as admin, use curl/Postman to test settings workflow:
1. GET /api/admin/settings — verify returns all 5 settings with default values
2. PATCH /api/admin/settings with `{"allow_public_signup": false}` — verify returns updated settings
3. GET /api/admin/settings again — verify `allow_public_signup` is now `false` (cache was invalidated)
4. PATCH with invalid value like `{"default_user_class": "gold"}` — verify returns 422 error
5. PATCH with out-of-range value like `{"invite_expiry_days": 500}` — verify returns 422 error

**Expected:** All operations work as described, cache invalidation is immediate, validation errors are clear

**Why human:** Requires running backend server and making authenticated requests

#### 2. Tier Summary with Live User Counts

**Test:** Start backend, login as admin:
1. GET /api/admin/tiers — verify returns list of tiers from yaml
2. Check that each tier has `name`, `display_name`, `credits`, `reset_policy`, and `user_count`
3. Verify `user_count` matches actual user records in database (create test users if needed)

**Expected:** Tier list matches yaml config, user counts are accurate

**Why human:** Requires backend server and database state inspection

#### 3. Admin Tier Change with Atomic Credit Reset

**Test:** Start backend, login as admin:
1. Create a test user or select existing user, note their current tier and credit balance
2. PUT /api/admin/tiers/users/{user_id} with `{"user_class": "premium"}` (or different tier)
3. Verify response includes `old_class`, `new_class`, and `new_balance`
4. Check database: user's `user_class` should be updated, credit balance should match new tier allocation
5. Try invalid tier: PUT with `{"user_class": "gold"}` — verify returns 400 error
6. Check audit log table for tier change entry

**Expected:** Tier change and credit reset are atomic, audit log records the action

**Why human:** Requires backend server, database inspection, and audit log verification

#### 4. Signup Gating - Backend Enforcement

**Test:** Start backend:
1. GET /auth/signup-status (no auth) — verify returns `{"signup_allowed": true}` initially
2. As admin, PATCH /api/admin/settings with `{"allow_public_signup": false}`
3. GET /auth/signup-status again — should return `{"signup_allowed": false}` within 30 seconds
4. POST /auth/signup with valid credentials but NO invite_token — verify returns 403 "Public registration is currently disabled"
5. Re-enable: PATCH with `{"allow_public_signup": true}`
6. POST /auth/signup with valid credentials — should succeed (no regression)

**Expected:** Signup gating works immediately, no bypass possible by skipping frontend

**Why human:** Requires backend server and timing verification (30s cache TTL)

#### 5. Frontend Registration Page - Invite-Only Message

**Test:** Start backend and frontend:
1. Visit registration page with `allow_public_signup: true` — verify normal form is displayed
2. As admin, toggle signup off via PATCH /api/admin/settings
3. Refresh registration page (or wait 30s if cached) — verify shows branded invite-only message: "Thank you for your interest. We are currently open for beta test invitees only. Please send us an email as per the contact if you are interested to participate."
4. Verify CardDescription shows "Registration is currently invite-only"
5. Verify "Already have an account? Log in" link is visible
6. Re-enable signup, refresh — verify form appears again

**Expected:** Frontend responds to runtime setting changes, message text matches exactly, no error-like appearance

**Why human:** Requires visual inspection of UI, message text verification, timing (cache TTL)

#### 6. Configurable Credit Cost

**Test:** Start backend, login as user with credits:
1. Note user's current credit balance
2. As admin, PATCH /api/admin/settings with `{"default_credit_cost": 2.0}`
3. As user, send a chat message (backend will use new cost within 30s due to cache)
4. Verify credit balance decreased by 2.0 (not 1.0)
5. Check credit transaction log: should show cost of 2.0
6. Reset credit cost back to 1.0

**Expected:** Credit cost changes are picked up from platform_settings at runtime

**Why human:** Requires backend server, user account, and credit transaction verification

#### 7. Configurable Default User Class

**Test:** Start backend:
1. As admin, PATCH /api/admin/settings with `{"default_user_class": "standard"}`
2. Create new user account via POST /auth/signup (public endpoint)
3. Verify new user has `user_class = "standard"` (not "free")
4. Verify new user has credit balance matching standard tier allocation (e.g., 100 credits)
5. Reset default_user_class to "free"

**Expected:** New signups get the configured default tier and matching credit allocation

**Why human:** Requires backend server and database inspection for new user record

---

## Verification Complete

All 13 must-haves verified. Phase goal achieved. All artifacts exist with substantive implementation and proper wiring. Requirements coverage is complete (17/17 in-scope requirements satisfied, 2 consciously deferred with documentation). No anti-patterns or blockers found.

The phase successfully delivers runtime platform configuration without server restarts:
- Settings API with 30s TTL cache
- Admin tier management with atomic credit reset
- Signup gating with backend enforcement and frontend response
- Configurable credit cost and default tier wired into core flows

Ready to proceed to next phase.

---

_Verified: 2026-02-16T21:30:00Z_

_Verifier: Claude (gsd-verifier)_
