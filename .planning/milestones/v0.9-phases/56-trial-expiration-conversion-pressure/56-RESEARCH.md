# Phase 56: Trial Expiration & Conversion Pressure - Research

**Researched:** 2026-03-18
**Domain:** Trial lifecycle enforcement (backend middleware + frontend UI)
**Confidence:** HIGH

## Summary

Phase 56 implements trial expiration enforcement and conversion pressure UI on top of the data foundation built in Phase 55. The User model already has `trial_expires_at` and `user_class="free_trial"`, the `user_classes.yaml` already defines `free_trial` with 100 credits and 7-day duration, and registration already sets `trial_expires_at`. This phase adds: (1) backend enforcement in auth dependencies returning HTTP 402 for expired trials, (2) a trial banner component on all authenticated pages, (3) a blocking overlay for expired trial users, (4) a placeholder `/settings/plan` page, and (5) backend-only credit top-up restriction for trial users.

The codebase uses FastAPI dependency injection for auth, a custom `fetchWithAuth` wrapper (not axios) for frontend API calls, and Next.js App Router with `(dashboard)` and `(workspace)` layout groups. All patterns needed for this phase already exist in the codebase; no new libraries are required.

**Primary recommendation:** Inject trial expiration check into `get_current_user` and `get_authenticated_user` dependencies with a path-based exemption list, add 402 handling to `fetchWithAuth`, and create reusable `TrialBanner` and `TrialExpiredOverlay` components injected via layout files.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Trial banner: sticky at top of page, above all content, shows days remaining AND credit balance, "Choose Plan" CTA, appears on ALL authenticated pages, dismissible per session, amber urgency at 3 days or 10 credits remaining, only for `free_trial` users
- Blocking overlay: full-page semi-transparent over dashboard, user sees data behind it, shows "Your trial has expired" with "View Plans" and "Log Out" actions, "View Plans" links to placeholder `/settings/plan`, triggered by `trial_expires_at` only (not zero credits), expired trial users CAN still access `/settings` pages
- Backend enforcement: trial check in `get_current_user` and `get_authenticated_user` dependencies, HTTP 402 Payment Required with `trial_expired` code and metadata (`detail`, `code`, `trial_expires_at`, `days_overdue`)
- Trial credit restrictions: backend-only enforcement, HTTP 403 with `trial_topup_blocked` code, no frontend changes this phase

### Claude's Discretion
- Exact set of exempt API routes for trial enforcement (minimal set for overlay + logout + settings to work)
- Frontend 402 handling approach (interceptor vs React Query error boundary vs other)
- Placeholder plan page design details (tier card layout, copy, styling)
- Trial banner component styling details (colors, spacing, icon)
- Loading skeleton for trial state check

### Deferred Ideas (OUT OF SCOPE)
None

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TRIAL-01 | New user registration assigns Free Trial state with configurable credit amount | Already implemented in Phase 55 (`auth.py` `create_user` sets `user_class="free_trial"`, `trial_expires_at`, and 100 initial credits). Verify/validate only. |
| TRIAL-02 | Trial duration configurable via `trial_duration_days` platform setting (default 14 days) | Phase 55 reads from `user_classes.yaml` (`trial_duration_days: 7`). CONTEXT says 7 days. May need platform_settings override or accept YAML as source of truth. |
| TRIAL-03 | Trial expiration enforced in auth middleware (covers web, API, MCP paths) | Add datetime check in `get_current_user`/`get_authenticated_user` after `is_active` check. Return HTTP 402 with metadata. MCP inherits via httpx loopback. |
| TRIAL-04 | Trial banner on dashboard showing days remaining and credit balance | New `TrialBanner` component, injected in dashboard and workspace layouts. Needs `/auth/me` to expose `user_class` and `trial_expires_at`, plus `/credits/balance` for credit data. |
| TRIAL-05 | Trial banner becomes urgent (amber) at 3 days remaining or 10 credits remaining | Conditional styling in `TrialBanner` based on computed days remaining and credit balance from existing `/credits/balance` endpoint. |
| TRIAL-06 | Full blocking overlay when trial expires -- no access until plan selected | `TrialExpiredOverlay` component rendered in layouts when `trial_expires_at` is past. Frontend catches 402 globally. Links to `/settings/plan` placeholder. |
| TRIAL-07 | Trial credits not eligible for top-up purchase | Guard in credit top-up endpoint (if one exists) or preemptive guard in credits router. Backend-only, no UI changes. |

</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.115.0 | Backend framework, dependency injection for trial check | Already in use |
| SQLAlchemy | >=2.0.0 | ORM, User model with `trial_expires_at` | Already in use |
| Next.js (App Router) | project version | Frontend framework, layout-based banner injection | Already in use |
| Tailwind CSS | project version | Styling for banner and overlay components | Already in use |
| shadcn/ui | project version | UI component library (Button, Card) | Already in use |
| lucide-react | project version | Icons (Clock, AlertTriangle, X) | Already in use |

### Supporting (already in project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | >=2.0 | Response schemas for trial state in UserResponse | Extend existing `UserResponse` |
| date-fns | if installed | Date calculation for "X days remaining" display | Check if already used; otherwise use native JS Date |

### Alternatives Considered
None needed -- this phase uses only existing project dependencies.

**No new packages required for Phase 56.**

## Architecture Patterns

### Backend: Trial Check in Auth Dependencies

**What:** Add trial expiration check directly into `get_current_user` and `get_authenticated_user` after the `is_active` check. This is the single enforcement point covering all paths.

**Pattern:**
```python
# In get_current_user, after is_active check:
if (
    user.user_class == "free_trial"
    and user.trial_expires_at is not None
    and user.trial_expires_at < datetime.now(timezone.utc)
):
    # Check if current path is exempt
    # Note: get_current_user doesn't have Request — need to add it or use a different approach
    raise HTTPException(
        status_code=402,
        detail="Trial expired",
        headers={"X-Trial-Expired": "true"},
    )
```

**Critical design consideration:** `get_current_user` does not currently receive `Request` as a parameter, so path-based exemption cannot happen inside it directly. Two approaches:

1. **Add `Request` parameter to `get_current_user`** -- requires updating ALL endpoint signatures that use `CurrentUser` (breaking change across entire codebase). NOT recommended.

2. **Create a new dependency `require_active_trial`** that wraps `get_current_user` and adds the trial check with path exemption. Non-exempt endpoints switch from `CurrentUser` to a new `TrialActiveUser` dependency. This avoids touching `get_current_user` but requires identifying which endpoints need the trial gate.

3. **Check trial in `get_current_user` unconditionally (no path exemption at dependency level), handle exemptions at the router/middleware level.** Add trial check to `get_current_user`, but use a FastAPI middleware or route-level decorator to mark exempt paths. The middleware approach catches the 402 and converts it to a pass-through for exempt paths.

**Recommended approach (Option 3 variant):** Add the trial check to `get_current_user` and `get_authenticated_user` (they raise 402 for expired trials), then create a **FastAPI middleware** that intercepts 402 responses on exempt paths and lets them through. This keeps the single enforcement point clean.

Actually, the simplest approach: Add `Request` to `get_current_user` -- FastAPI auto-injects `Request` without it being a `Depends()`, so it does NOT require changing endpoint signatures. FastAPI injects `Request` automatically when it appears in a dependency's parameter list. This is the cleanest solution.

```python
async def get_current_user(
    request: Request,  # FastAPI auto-injects, no Depends() needed
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> User:
```

**Exempt paths (minimal set):**
- `/auth/me` -- needed for frontend to load user state (including trial info)
- `/auth/refresh` -- token refresh must work for expired trial users
- `/auth/logout` -- if exists (currently client-side only via `clearTokens()`)
- `/api/credits/balance` -- needed for banner to show credit balance
- `/settings/*` -- owner decision: settings pages accessible for expired trials
- Any admin routes (`/admin/*`) -- admins should never be trial users, but defense in depth

### Frontend: Global 402 Handling

**What:** The frontend uses a custom `fetchWithAuth` wrapper (NOT axios). Add 402 handling alongside the existing 401 handling.

**Pattern:** In `api-client.ts`, after the fetch call, check for 402 status and set a global trial-expired state. The `useAuth` hook already manages auth state -- extend it with `isTrialExpired`.

```typescript
// In fetchWithAuth, after the fetch:
if (response.status === 402) {
    // Parse trial_expired response
    const body = await response.clone().json();
    if (body.code === "trial_expired") {
        // Dispatch custom event or set global state
        window.dispatchEvent(new CustomEvent("trial-expired", { detail: body }));
    }
    return response; // Let caller handle
}
```

**Alternative (recommended):** Since layouts already use `useAuth`, extend the auth context to include trial state. The `/auth/me` response (via `UserResponse`) needs `user_class` and `trial_expires_at` fields. Then layouts check trial state client-side and show overlay. The 402 response is a server-side safety net, not the primary UI trigger.

### Frontend: Component Architecture

```
frontend/src/
  components/
    trial/
      TrialBanner.tsx        # Sticky banner with days/credits + CTA
      TrialExpiredOverlay.tsx # Full-page blocking overlay
      PlanPlaceholder.tsx     # Tier cards with "Coming soon"
  app/
    settings/
      plan/
        page.tsx              # /settings/plan route (placeholder)
  hooks/
    useTrialState.ts          # Computed trial state from user + credits
```

### Anti-Patterns to Avoid
- **Separate middleware for trial check:** Don't create a FastAPI `Middleware` class. Use the existing dependency injection pattern for consistency.
- **Client-side-only trial enforcement:** The frontend overlay is UX, not security. Backend 402 is the actual enforcement.
- **Checking trial in every endpoint individually:** Use the auth dependency as the single enforcement point.
- **Storing trial state in localStorage/sessionStorage:** Compute from user data on each render. Don't cache stale trial state.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Date difference calculation | Custom date math | `datetime.now(timezone.utc)` comparison (backend), `Date` arithmetic or `date-fns` differenceInDays (frontend) | Timezone bugs are easy to introduce |
| Session-dismissible banner | Custom cookie/localStorage logic | `sessionStorage.setItem("trial_banner_dismissed", "true")` | Built-in, clears on tab close |
| Semi-transparent overlay | Custom CSS overlay from scratch | Tailwind `fixed inset-0 bg-black/50 z-50` + `backdrop-blur-sm` | Standard Tailwind pattern |
| Trial state polling | Custom setInterval polling | React Query with `refetchInterval` or compute from existing `/auth/me` data | Already using React Query patterns |

## Common Pitfalls

### Pitfall 1: Timezone Mismatch in Trial Expiration
**What goes wrong:** `trial_expires_at` stored as UTC but compared with local time, causing premature or delayed expiration.
**Why it happens:** Python `datetime.now()` without timezone vs `datetime.now(timezone.utc)`.
**How to avoid:** Always use `datetime.now(timezone.utc)` for comparison. The existing codebase already uses UTC consistently -- maintain this.
**Warning signs:** Trial expires at unexpected times, different behavior in different timezones.

### Pitfall 2: 402 Response Breaking Token Refresh Flow
**What goes wrong:** `fetchWithAuth` sees 402, tries to refresh token (treating it like 401), creates infinite loop.
**Why it happens:** The existing 401 handler triggers token refresh. If 402 handling is placed incorrectly, it might fall through to 401 logic.
**How to avoid:** Check for 402 BEFORE the 401 handler in `fetchWithAuth`. Return immediately on 402 without attempting refresh.
**Warning signs:** Network tab shows repeated refresh token calls, browser hangs.

### Pitfall 3: Exempt Path List Gets Stale
**What goes wrong:** New endpoints added later are not exempted, breaking settings/plan pages for expired trial users.
**Why it happens:** Exemption list is hardcoded, no documentation trail.
**How to avoid:** Use path prefix matching (`/auth/`, `/settings/`, `/admin/`) rather than exact path matching. Document the exemption logic with clear comments.
**Warning signs:** Expired trial users get 402 on settings pages.

### Pitfall 4: UserResponse Schema Not Updated
**What goes wrong:** Frontend has no access to `user_class` or `trial_expires_at` because `UserResponse` doesn't include them.
**Why it happens:** Phase 55 added fields to User model but not to the response schema.
**How to avoid:** Update both backend `UserResponse` schema and frontend `UserResponse` TypeScript type to include `user_class` and `trial_expires_at`.
**Warning signs:** Frontend trial banner shows "undefined" or doesn't render.

### Pitfall 5: Banner Dismissal Persists Across Sessions
**What goes wrong:** User dismisses banner, opens new browser session, banner is still hidden.
**Why it happens:** Using `localStorage` instead of `sessionStorage` for dismissal state.
**How to avoid:** Use `sessionStorage` which clears when the browser tab closes.
**Warning signs:** Users never see the banner again after first dismissal.

### Pitfall 6: Overlay Blocks Settings Navigation
**What goes wrong:** Expired trial user sees overlay and cannot navigate to `/settings/plan` to choose a plan.
**Why it happens:** Overlay covers entire page including navigation.
**How to avoid:** Either (a) overlay only renders on dashboard/workspace routes, not settings routes, or (b) overlay has explicit navigation buttons that work despite the overlay. Owner decision says settings pages are accessible -- so overlay should NOT render on settings pages.
**Warning signs:** Dead end where user cannot convert.

## Code Examples

### Backend: Trial Check in get_current_user

```python
# backend/app/dependencies.py — modified get_current_user
# Source: Existing codebase pattern + CONTEXT.md decisions

# Paths exempt from trial expiration enforcement
TRIAL_EXEMPT_PREFIXES = (
    "/auth/",
    "/api/credits/balance",
    "/admin/",
    "/health",
)

async def get_current_user(
    request: Request,  # FastAPI auto-injects
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> User:
    # ... existing token verification and user lookup ...

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Trial expiration check (after is_active, before return)
    if (
        user.user_class == "free_trial"
        and user.trial_expires_at is not None
        and user.trial_expires_at < datetime.now(timezone.utc)
    ):
        # Check if path is exempt
        path = request.url.path
        if not any(path.startswith(prefix) for prefix in TRIAL_EXEMPT_PREFIXES):
            days_overdue = (datetime.now(timezone.utc) - user.trial_expires_at).days
            raise HTTPException(
                status_code=402,
                detail="Trial expired",
                headers={"X-Trial-Code": "trial_expired"},
            )
            # Note: HTTPException detail can be a dict for JSON response:
            # Actually, FastAPI's HTTPException detail accepts dict for JSON body

    return user
```

**Important:** FastAPI's `HTTPException` accepts a dict as `detail`, which gets serialized to JSON. For the structured 402 response:

```python
raise HTTPException(
    status_code=402,
    detail={
        "detail": "Trial expired",
        "code": "trial_expired",
        "trial_expires_at": user.trial_expires_at.isoformat(),
        "days_overdue": (datetime.now(timezone.utc) - user.trial_expires_at).days,
    },
)
```

### Backend: Credit Top-Up Block for Trial Users

```python
# In the credit top-up endpoint (currently doesn't exist,
# but needs a guard for when Phase 58 adds it).
# Add to backend/app/routers/credits.py or create a guard function.

async def check_topup_eligible(user: User) -> None:
    """Raise 403 if user is on free_trial tier (cannot purchase top-ups)."""
    if user.user_class == "free_trial":
        raise HTTPException(
            status_code=403,
            detail={
                "detail": "Credit top-ups not available during free trial",
                "code": "trial_topup_blocked",
            },
        )
```

### Frontend: Updated UserResponse Type

```typescript
// frontend/src/types/auth.ts — extend UserResponse
export interface UserResponse {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
  user_class: string;                    // NEW
  trial_expires_at: string | null;       // NEW (ISO datetime string)
}
```

### Frontend: useTrialState Hook

```typescript
// frontend/src/hooks/useTrialState.ts
import { useMemo } from "react";
import { useAuth } from "./useAuth";

interface TrialState {
  isTrial: boolean;
  isExpired: boolean;
  daysRemaining: number | null;
  trialExpiresAt: Date | null;
}

export function useTrialState(): TrialState {
  const { user } = useAuth();

  return useMemo(() => {
    if (!user || user.user_class !== "free_trial" || !user.trial_expires_at) {
      return { isTrial: false, isExpired: false, daysRemaining: null, trialExpiresAt: null };
    }

    const expiresAt = new Date(user.trial_expires_at);
    const now = new Date();
    const diffMs = expiresAt.getTime() - now.getTime();
    const daysRemaining = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    return {
      isTrial: true,
      isExpired: daysRemaining <= 0,
      daysRemaining: Math.max(0, daysRemaining),
      trialExpiresAt: expiresAt,
    };
  }, [user]);
}
```

### Frontend: 402 Handling in fetchWithAuth

```typescript
// frontend/src/lib/api-client.ts — add 402 check before 401 handler

// After: let response = await fetch(...)
// Before existing 401 check:
if (response.status === 402) {
    // Trial expired — don't attempt refresh, emit event for UI
    window.dispatchEvent(new CustomEvent("trial-expired"));
    return response;
}

// Existing 401 handling continues below...
```

### Frontend: TrialBanner Component

```tsx
// frontend/src/components/trial/TrialBanner.tsx
"use client";

import { useState } from "react";
import { Clock, AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTrialState } from "@/hooks/useTrialState";
import Link from "next/link";

export function TrialBanner({ creditBalance }: { creditBalance: number }) {
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window !== "undefined") {
      return sessionStorage.getItem("trial_banner_dismissed") === "true";
    }
    return false;
  });
  const { isTrial, daysRemaining } = useTrialState();

  if (!isTrial || dismissed) return null;

  const isUrgent = (daysRemaining !== null && daysRemaining <= 3) || creditBalance <= 10;
  const borderColor = isUrgent ? "border-amber-500/50" : "border-primary/30";
  const bgColor = isUrgent ? "bg-amber-500/10" : "bg-primary/5";
  const Icon = isUrgent ? AlertTriangle : Clock;
  const iconColor = isUrgent ? "text-amber-500" : "text-primary";

  const handleDismiss = () => {
    setDismissed(true);
    sessionStorage.setItem("trial_banner_dismissed", "true");
  };

  return (
    <div className={`rounded-lg border ${borderColor} ${bgColor} px-4 py-3 flex items-center gap-3`}>
      <Icon className={`h-4 w-4 ${iconColor} shrink-0`} />
      <p className="text-sm text-foreground font-medium flex-1">
        {daysRemaining} day{daysRemaining !== 1 ? "s" : ""} remaining in your trial
        {" "}·{" "}{creditBalance} credits left
      </p>
      <Button asChild size="sm" variant={isUrgent ? "default" : "outline"}>
        <Link href="/settings/plan">Choose Plan</Link>
      </Button>
      <button onClick={handleDismiss} className="text-muted-foreground hover:text-foreground">
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
```

### Frontend: TrialExpiredOverlay Component

```tsx
// frontend/src/components/trial/TrialExpiredOverlay.tsx
"use client";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import Link from "next/link";

export function TrialExpiredOverlay() {
  const { logout } = useAuth();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-background rounded-xl shadow-2xl p-8 max-w-md w-full mx-4 text-center space-y-6">
        <h2 className="text-2xl font-bold">Your trial has expired</h2>
        <p className="text-muted-foreground">
          Choose a plan to continue using Spectra and access your data.
        </p>
        <div className="flex flex-col gap-3">
          <Button asChild size="lg">
            <Link href="/settings/plan">View Plans</Link>
          </Button>
          <Button variant="ghost" size="lg" onClick={logout}>
            Log Out
          </Button>
        </div>
      </div>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No trial system | Free trial with 100 credits, 7-day duration | Phase 55 (data), Phase 56 (enforcement) | New users get trial, must convert |
| `UserResponse` without tier info | Add `user_class`, `trial_expires_at` to response | Phase 56 | Frontend can show trial state |
| No 402 handling in frontend | Global 402 interception in `fetchWithAuth` | Phase 56 | Trial expiration detected client-side |

## Open Questions

1. **TRIAL-02: `trial_duration_days` source of truth**
   - What we know: `user_classes.yaml` has `trial_duration_days: 7`. Requirements say default 14 days. CONTEXT.md (Phase 55) says owner chose 7 days.
   - What's unclear: Whether a `platform_settings` key should also control this or YAML is sufficient
   - Recommendation: YAML is already the source of truth and registration already reads from it. Accept as-is. If admin needs to change it dynamically, that's a future enhancement.

2. **TRIAL-01: Is registration already complete?**
   - What we know: `create_user` in `auth.py` already sets `user_class="free_trial"`, `trial_expires_at`, and 100 initial credits
   - What's unclear: Whether any validation/testing is needed or this is truly complete from Phase 55
   - Recommendation: Verify with a quick test during implementation, mark as "validate only" in plan

3. **Top-up endpoint existence**
   - What we know: No top-up purchase endpoint exists yet (Phase 58 creates it)
   - What's unclear: Whether to create a preemptive guard now or just document for Phase 58
   - Recommendation: Add a guard function in the credits service that Phase 58 can call. No new endpoint needed now.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (with async support) |
| Config file | `backend/pyproject.toml` |
| Quick run command | `cd backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TRIAL-01 | Registration sets free_trial + trial_expires_at + credits | unit | `cd backend && python -m pytest tests/test_trial.py::test_registration_trial_state -x` | No -- Wave 0 |
| TRIAL-02 | trial_duration_days configurable via YAML | unit | `cd backend && python -m pytest tests/test_trial.py::test_trial_duration_config -x` | No -- Wave 0 |
| TRIAL-03 | Auth dependency returns 402 for expired trial on non-exempt paths | unit | `cd backend && python -m pytest tests/test_trial.py::test_expired_trial_returns_402 -x` | No -- Wave 0 |
| TRIAL-03 | Auth dependency allows exempt paths for expired trial | unit | `cd backend && python -m pytest tests/test_trial.py::test_exempt_paths_bypass_trial -x` | No -- Wave 0 |
| TRIAL-03 | Non-trial users unaffected by trial check | unit | `cd backend && python -m pytest tests/test_trial.py::test_non_trial_users_unaffected -x` | No -- Wave 0 |
| TRIAL-04 | Trial banner renders for trial users | manual-only | Visual check in browser | N/A |
| TRIAL-05 | Banner turns amber at 3 days / 10 credits | manual-only | Visual check in browser | N/A |
| TRIAL-06 | Overlay blocks expired trial users on dashboard | manual-only | Visual check in browser | N/A |
| TRIAL-07 | Trial users blocked from credit top-up | unit | `cd backend && python -m pytest tests/test_trial.py::test_trial_topup_blocked -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_trial.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_trial.py` -- covers TRIAL-01, TRIAL-02, TRIAL-03, TRIAL-07
- [ ] Test fixtures for mock User with `trial_expires_at` (in `conftest.py` or test file)
- [ ] Frontend component tests deferred (no test infrastructure for React components in project)

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `backend/app/dependencies.py` -- auth dependency structure, parameter injection pattern
- Codebase inspection: `backend/app/services/auth.py` -- registration flow with trial setup
- Codebase inspection: `backend/app/models/user.py` -- User model with `trial_expires_at`
- Codebase inspection: `frontend/src/lib/api-client.ts` -- fetchWithAuth pattern, 401 handling
- Codebase inspection: `frontend/src/hooks/useAuth.tsx` -- AuthProvider, AuthContext pattern
- Codebase inspection: `frontend/src/app/(dashboard)/layout.tsx` -- layout structure for banner injection
- Codebase inspection: `backend/app/config/user_classes.yaml` -- free_trial config (100 credits, 7 days)
- Phase 56 CONTEXT.md -- locked decisions on all implementation details

### Secondary (MEDIUM confidence)
- FastAPI docs: `Request` parameter auto-injection in dependencies (verified pattern in codebase)
- FastAPI docs: `HTTPException` with dict `detail` for structured JSON error responses

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing
- Architecture: HIGH -- all patterns visible in codebase, clear injection points
- Pitfalls: HIGH -- derived from actual codebase analysis (e.g., fetchWithAuth 401 handling, UserResponse schema gap)

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable, no external dependencies)
