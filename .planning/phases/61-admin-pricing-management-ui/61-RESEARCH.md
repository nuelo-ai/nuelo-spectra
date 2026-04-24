# Phase 61: Admin Pricing Management UI - Research

**Researched:** 2026-04-23
**Domain:** Admin UI (Next.js + shadcn/ui), FastAPI backend endpoints, dynamic pricing rendering
**Confidence:** HIGH

## Summary

Phase 61 extends the existing admin billing-settings page to support full CRUD for subscription pricing and credit packages, adds password-confirmed edit/reset flows, and makes the public-facing Plan Selection and Billing pages render dynamically from config/database instead of hardcoded values.

The existing codebase provides strong foundations: the billing-settings page (207 lines) already has the Monetization toggle and subscription pricing inputs, the `pricing_sync.py` service already implements `reset_subscription_pricing()`, `reset_credit_packages()`, and `check_stripe_readiness()`, and the public Plan Selection page already renders dynamically from the `/subscriptions/plans` API. The primary work is (1) refactoring the admin billing-settings page from inline inputs to click-to-edit modal pattern, (2) adding credit package management cards, (3) creating backend endpoints for credit package CRUD and pricing resets with password verification, (4) making the `/subscriptions/plans` endpoint dynamic instead of hardcoded, and (5) adding `features:` lists to `user_classes.yaml`.

**Primary recommendation:** Extend the existing `billing_settings.py` router for subscription operations and create a new `admin/credit_packages.py` router for credit package endpoints. Keep all admin UI on the single billing-settings page per D-01.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Extend the existing billing-settings page -- single page for all pricing management, no separate pages or tabs
- **D-02:** Page section order: Monetization Toggle -> Subscription Pricing -> Credit Packages -> Save Button
- **D-03:** Keep the page title as "Billing Settings" -- existing name is broad enough
- **D-04:** Each editable field shows an inline hint underneath: "Default: $29.00" showing the config-file default value
- **D-05:** No visual indicator (dot/badge) when DB value differs from config default -- the inline hint is sufficient
- **D-06:** Click-to-edit modal pattern for BOTH subscription pricing and credit packages. The existing inline price inputs for subscription pricing must be replaced with the same click-to-edit modal UX for consistency
- **D-07:** Credit package cards in view mode show full details: name, price, credits, display_order, active status, and Stripe Price ID (read-only/uneditable)
- **D-08:** Edit modal allows changing: name, price, credits, display_order, active status. Stripe Price ID is never editable by admin (auto-created by system)
- **D-09:** All pricing changes (subscription edits, credit package edits, AND resets) require a confirmation dialog that: (1) explains the impact of the changes, (2) requires password re-entry to confirm
- **D-10:** The confirmation dialog has an inline password field. Password is sent alongside the save/reset request to the backend, which verifies before executing
- **D-11:** Per-section "Reset to Defaults" buttons -- one at the bottom of Subscription Pricing card, one at the bottom of Credit Packages card. Each resets only its section
- **D-12:** Pre-check approach for the monetization toggle: when Stripe is not ready, the toggle is disabled with a checklist of missing items shown in the Monetization card
- **D-13:** Add a `features:` list to each tier in `user_classes.yaml` -- config-driven plan benefit bullets instead of hardcoded in Python backend
- **D-14:** The `/subscriptions/plans` endpoint reads tiers with `has_plan: true` from config and builds the response dynamically instead of hardcoding 3 plans
- **D-15:** Plan Selection page (`/settings/plan`) already renders dynamically from API -- backend changes are sufficient, no frontend changes needed for plan rendering
- **D-16:** Billing page (`/settings/billing`) shows dynamic credit package cards rendered from the database. Each card shows package name, price, credits, and a "Buy" button. Replaces any hardcoded credit package references
- **D-17:** Password sent in each save/reset request body (not a separate verify endpoint). Backend verifies atomically with the action. Returns 401 if password wrong
- **D-18:** Router and endpoint design: Claude's discretion -- pick the approach that best fits existing admin API patterns

### Claude's Discretion
- Exact modal component implementation (reuse existing Dialog from shadcn/ui)
- API response shapes and error formats
- Router organization (extend billing-settings vs new credit-packages router)
- Reset endpoint shape (dedicated per-section vs single with scope param)
- Impact text wording in confirmation dialogs
- Stripe readiness checklist UI component design

### Deferred Ideas (OUT OF SCOPE)
- Admin creating new credit packages from scratch -- out of scope per REQUIREMENTS.md; config-defined packages only
- Admin deleting credit packages -- deactivate via is_active flag instead; preserves payment history references
- Admin-editable feature bullet points in UI -- features are config-driven in user_classes.yaml; admin editing would need DB schema changes
- Stripe webhook status dashboard -- showing webhook delivery history in admin portal

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SUB-05 | Admin can view all subscription pricing plans with their config defaults and current DB values | Existing `billing_settings.py` GET endpoint returns current DB values. Config defaults available via `get_user_classes()`. Frontend refactored to view mode with default hints (D-04) |
| SUB-06 | Admin can edit subscription pricing plans | Existing `billing_settings.py` PUT endpoint handles price changes + Stripe Price creation. Frontend refactored from inline inputs to click-to-edit modal (D-06) with password confirmation (D-09) |
| SUB-07 | Admin can reset subscription pricing to config-file defaults | `pricing_sync.reset_subscription_pricing()` already implemented. Need new backend endpoint to expose it with password verification |
| PKG-04 | Admin can view all credit packages from the database | Need new GET endpoint on admin router returning all credit packages (including inactive). Frontend renders as cards per D-07 |
| PKG-05 | Admin can edit credit packages (name, price, credits, active status) | Need new PUT endpoint for credit package updates with Stripe Price creation on price change. Click-to-edit modal per D-06 |
| PKG-06 | Admin can reset credit packages to config-file defaults | `pricing_sync.reset_credit_packages()` already implemented. Need new backend endpoint with password verification |
| UI-01 | Plan Selection page dynamically renders subscription plans from tiers with `has_plan: true` | Backend `/subscriptions/plans` currently hardcodes 3 plans. Must be refactored to iterate `get_user_classes()` filtering by `has_plan: true`. Frontend already dynamic (D-15) |
| UI-02 | Billing page displays credit packages and pricing as defined in the database | Frontend billing page already renders from `useCreditPackages()` hook which hits `/credits/packages`. Already database-driven. Verify no hardcoded references remain |

</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Subscription pricing view/edit/reset | API / Backend | Admin Frontend | Business logic, Stripe integration, password verification all in backend. Frontend is display + modal forms |
| Credit package view/edit/reset | API / Backend | Admin Frontend | Same as subscription -- all mutations through backend with password verification |
| Dynamic plan rendering | API / Backend | -- | D-15 confirms frontend already dynamic. Backend endpoint change only |
| Dynamic billing page | Database / Storage | -- | Already database-driven via `/credits/packages`. Verify no hardcoded refs |
| Config defaults display | API / Backend | -- | Backend must expose config defaults alongside DB values in GET response |
| Password re-entry confirmation | API / Backend | Admin Frontend | Backend verifies password atomically. Frontend collects via PasswordConfirmDialog |
| Stripe readiness check | API / Backend | Admin Frontend | Backend `check_stripe_readiness()` returns missing items. Frontend renders checklist |

## Standard Stack

### Core (already in project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 15.x | Admin frontend framework | Already used in admin-frontend [VERIFIED: codebase] |
| FastAPI | latest | Backend API framework | Already used in backend [VERIFIED: codebase] |
| TanStack Query | v5 | Data fetching + cache invalidation | Already used via `useQuery`/`useMutation` in admin hooks [VERIFIED: codebase] |
| shadcn/ui (new-york preset) | -- | UI components (Card, Dialog, Button, Input, Switch, Badge) | Already installed and used throughout admin-frontend [VERIFIED: codebase] |
| Sonner | -- | Toast notifications | Already used via `toast.success()`/`toast.error()` [VERIFIED: codebase] |
| Lucide React | -- | Icons (Pencil, Check, X, AlertTriangle) | Already used in frontend and admin-frontend [VERIFIED: codebase] |
| SQLAlchemy (async) | -- | Database ORM | Already used for CreditPackage model and platform_settings [VERIFIED: codebase] |
| Pydantic v2 | -- | Request/response schemas | Already used in all backend schemas [VERIFIED: codebase] |
| pwdlib | -- | Password hashing (Argon2) | Already used via `verify_password()` in security utils [VERIFIED: codebase] |

### No New Dependencies Required

This phase requires zero new package installations. All needed components (Dialog, Badge, Switch, etc.) are already installed in admin-frontend.

## Architecture Patterns

### System Architecture Diagram

```
Admin Browser                      Backend API                           External
    |                                  |                                    |
    |-- GET /api/admin/billing-settings -->                                 |
    |   (subscription pricing + defaults + stripe readiness)                |
    |                                  |                                    |
    |-- GET /api/admin/credit-packages -->                                  |
    |   (all packages with defaults)   |                                    |
    |                                  |                                    |
    |-- [Click Edit] --> Edit Modal    |                                    |
    |-- [Save] --> PasswordConfirmDialog                                    |
    |-- PUT /api/admin/billing-settings (+ password) -->                    |
    |                                  |-- verify_password()                |
    |                                  |-- upsert platform_settings         |
    |                                  |-- create Stripe Price -----------> Stripe API
    |                                  |-- deactivate old Price ----------> Stripe API
    |                                  |<-- response                        |
    |<-- toast success                 |                                    |
    |                                  |                                    |
    |-- PUT /api/admin/credit-packages/{id} (+ password) -->                |
    |                                  |-- verify_password()                |
    |                                  |-- update CreditPackage row         |
    |                                  |-- create Stripe Price if needed -> Stripe API
    |                                  |<-- response                        |
    |<-- toast success                 |                                    |
    |                                  |                                    |
    |-- POST /api/admin/billing-settings/reset (+ password) -->             |
    |                                  |-- verify_password()                |
    |                                  |-- reset_subscription_pricing() --> Stripe API
    |                                  |<-- response                        |
    |                                  |                                    |
    |-- POST /api/admin/credit-packages/reset (+ password) -->              |
    |                                  |-- verify_password()                |
    |                                  |-- reset_credit_packages() -------> Stripe API
    |                                  |<-- response                        |

Public Browser                     Backend API
    |                                  |
    |-- GET /subscriptions/plans ----->|
    |                                  |-- get_user_classes() (filter has_plan)
    |                                  |-- get_platform_settings() (DB prices)
    |                                  |-- build dynamic plan list
    |<-- PlanPricingResponse           |
```

### Recommended Project Structure

```
admin-frontend/src/
  app/(admin)/billing-settings/
    page.tsx                          # Refactored: view-mode cards + modals (was inline inputs)
  components/shared/
    PasswordConfirmDialog.tsx         # NEW: Reusable password confirmation dialog
  hooks/
    useBilling.ts                     # Extended: new types, new hooks for credit packages + reset

backend/app/
  routers/admin/
    billing_settings.py              # Extended: add password to PUT, add reset endpoint, add defaults in GET
    credit_packages.py               # NEW: GET all, PUT single, POST reset (admin credit package management)
    __init__.py                      # Updated: register new credit_packages router
  schemas/
    admin_billing.py                 # Extended: add password fields, config defaults, credit package admin schemas
  config/
    user_classes.yaml                # Extended: add features: list to tiers with has_plan
  routers/
    subscriptions.py                 # Refactored: dynamic plan building from config
```

### Pattern 1: Password-Verified Admin Mutation

**What:** All pricing mutations require the admin's password sent in the request body, verified atomically before executing the action.
**When to use:** Any destructive or financially impactful admin action (already used for credit adjustments and manual resets).
**Example:**
```python
# Source: backend/app/routers/admin/credits.py (existing pattern)
from app.utils.security import verify_password

@router.put("/{package_id}")
async def update_credit_package(
    package_id: UUID,
    body: CreditPackageUpdateRequest,  # includes password field
    db: DbSession,
    current_admin: CurrentAdmin,
):
    # Verify admin password -- use 403 (not 401) since admin IS authenticated
    if not verify_password(body.password, current_admin.hashed_password):
        raise HTTPException(status_code=403, detail="Incorrect password")

    # Execute the action...
```

### Pattern 2: Config Defaults Alongside DB Values

**What:** GET endpoints return both current DB values and config-file defaults so the frontend can display "Default: $XX.XX" hints.
**When to use:** Any admin view that shows editable config-overridable values.
**Example:**
```python
# New pattern for GET billing-settings response
class BillingSettingsResponse(BaseModel):
    monetization_enabled: bool
    price_standard_monthly_cents: int
    price_premium_monthly_cents: int
    stripe_price_standard_monthly: str
    stripe_price_premium_monthly: str
    # NEW: config defaults for hint display
    config_defaults: dict  # {"price_standard_monthly_cents": 2900, "price_premium_monthly_cents": 7900}
    stripe_readiness: dict  # {"ready": bool, "missing": [...]}
```

### Pattern 3: Click-to-Edit Modal with Confirmation Chain

**What:** View mode displays read-only data. Edit button opens a Dialog with pre-filled form. Save triggers PasswordConfirmDialog. On confirm, mutation fires.
**When to use:** D-06 mandates this for both subscription pricing and credit packages.
**Example flow:**
```typescript
// Source: UI-SPEC interaction contract
// 1. View mode: read-only display with "Edit Pricing" button
// 2. Edit modal: Dialog with Input fields + "Save Changes" button
// 3. Password confirm: PasswordConfirmDialog with impact text + password Input
// 4. API call: mutation with {data + password} payload
// 5. Success: close both dialogs, toast.success(), invalidate queries
```

### Anti-Patterns to Avoid
- **Inline editing for pricing fields:** D-06 explicitly replaces the existing inline Input approach with click-to-edit modals. Do not keep inline inputs for subscription pricing.
- **Separate password verification endpoint:** D-17 mandates password is sent alongside the data payload, not verified in a separate step.
- **401 for wrong confirmation password:** The existing codebase pattern uses 403 (not 401) for incorrect confirmation passwords because the admin IS authenticated -- 401 would trigger the `adminApiClient` auto-redirect to login. Use 403 to match the established pattern.
- **Hardcoding plan lists in the `/subscriptions/plans` endpoint:** D-14 requires dynamic iteration over `get_user_classes()` filtering by `has_plan: true`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal dialogs | Custom overlay/backdrop | shadcn/ui `Dialog` component | Already installed, handles focus trapping, escape key, aria attributes [VERIFIED: codebase] |
| Password hashing/verification | Custom bcrypt/argon2 wrapper | `verify_password()` from `app.utils.security` | Already using pwdlib with Argon2, consistent with credit adjustment pattern [VERIFIED: codebase] |
| Toast notifications | Custom notification system | Sonner `toast.success()`/`toast.error()` | Already used throughout admin-frontend [VERIFIED: codebase] |
| Data fetching/cache invalidation | Manual fetch + useState | TanStack Query `useQuery`/`useMutation` with `invalidateQueries` | Already used in `useBilling.ts` hooks [VERIFIED: codebase] |
| Currency formatting | Manual string manipulation | Existing `centsToDisplay()`/`displayToCents()` utilities | Already defined in billing-settings page [VERIFIED: codebase] |
| Config file parsing | Custom YAML loader | Existing `get_user_classes()`/`get_credit_packages()` from `user_class.py` | 30s TTL cache, error handling already implemented [VERIFIED: codebase] |
| Pricing reset logic | Custom DB update loops | Existing `reset_subscription_pricing()`/`reset_credit_packages()` from `pricing_sync.py` | Handles Stripe Price deactivation/creation, package deactivation, full reset flow [VERIFIED: codebase] |
| Stripe readiness check | Custom query logic | Existing `check_stripe_readiness()` from `pricing_sync.py` | Checks all tiers + all packages + STRIPE_SECRET_KEY [VERIFIED: codebase] |

**Key insight:** Phase 60 already built the heavy backend logic (reset functions, readiness checks, config loading). Phase 61 is primarily about exposing these through endpoints and building the admin UI.

## Common Pitfalls

### Pitfall 1: 401 vs 403 for Wrong Confirmation Password
**What goes wrong:** Using 401 status code for incorrect confirmation password causes the `adminApiClient` to auto-redirect to the login page, logging the admin out.
**Why it happens:** D-17 in CONTEXT.md says "Returns 401" but the existing codebase pattern (admin credit adjustments) deliberately uses 403 with the comment "Use 403 (not 401) -- admin IS authenticated, just wrong confirmation password."
**How to avoid:** Use 403 for incorrect confirmation passwords. Use 401 only for actual authentication failures (expired/invalid JWT). The frontend PasswordConfirmDialog should handle 403 by showing inline error, not redirecting.
**Warning signs:** Admin gets logged out when entering wrong confirmation password.

### Pitfall 2: Stale Query Data After Mutation
**What goes wrong:** After a successful edit or reset, the UI shows old data until the next cache refresh (30s TTL on backend, staleTime on frontend).
**Why it happens:** TanStack Query caches responses. Without explicit invalidation, the view mode shows stale data.
**How to avoid:** Call `queryClient.invalidateQueries({ queryKey: [...] })` in the mutation's `onSuccess` callback for all relevant query keys (billing-settings, credit-packages). Backend must also call `invalidate_cache()` on platform_settings after changes.
**Warning signs:** Values snap back to old state momentarily after save.

### Pitfall 3: Stripe Price Creation Failure Breaking Save
**What goes wrong:** Admin saves a price change but Stripe API fails, leaving the DB updated without a corresponding Stripe Price.
**Why it happens:** The existing `billing_settings.py` PUT endpoint creates Stripe Prices inline and raises 500 on failure, but the price_cents value may have already been upserted.
**How to avoid:** The existing endpoint already handles this correctly -- it creates the Stripe Price before upserting the DB value, and raises HTTPException on failure. Maintain this pattern for credit package updates.
**Warning signs:** Price shows as updated in admin but checkout fails for users.

### Pitfall 4: Missing Config Defaults for Dynamic Tiers
**What goes wrong:** If a new tier is added to `user_classes.yaml` with `has_plan: true` but the platform_settings keys don't exist yet (no startup sync run), the GET endpoint falls back to hardcoded defaults.
**Why it happens:** Platform settings DEFAULTS dict has hardcoded keys (`price_standard_monthly_cents`, `price_premium_monthly_cents`) that don't dynamically match tier names.
**How to avoid:** For the GET billing-settings endpoint, iterate over `get_user_classes()` tiers with `has_plan: true` and construct the response dynamically, falling back to `tier_config["price_cents"]` from YAML if no DB value exists.
**Warning signs:** New tiers don't appear in the admin billing settings page.

### Pitfall 5: Credit Package Price Change Without Stripe Price Recreation
**What goes wrong:** Admin changes a credit package price in DB but the old Stripe Price ID remains, causing users to be charged the old price at checkout.
**Why it happens:** Forgetting to create a new Stripe Price when `price_cents` changes on a credit package update.
**How to avoid:** In the PUT credit package endpoint, detect if `price_cents` changed. If so, deactivate the old Stripe Price, create a new one, and store the new `stripe_price_id` on the CreditPackage row. Follow the same pattern as `billing_settings.py` lines 104-166.
**Warning signs:** Admin sees updated price but users see old price at Stripe checkout.

## Code Examples

### Admin Credit Package GET Endpoint (all packages + defaults)
```python
# Source: Pattern derived from existing credits.py GET /packages + admin context
@router.get("", response_model=list[AdminCreditPackageResponse])
async def get_admin_credit_packages(
    admin: CurrentAdmin,
    db: DbSession,
):
    """Return all credit packages (including inactive) with config defaults."""
    result = await db.execute(
        select(CreditPackage).order_by(CreditPackage.display_order.asc())
    )
    packages = result.scalars().all()
    config_packages = get_credit_packages()  # from user_class.py
    config_by_name = {p["name"]: p for p in config_packages}

    return [
        AdminCreditPackageResponse(
            id=str(pkg.id),
            name=pkg.name,
            price_cents=pkg.price_cents,
            credit_amount=pkg.credit_amount,
            display_order=pkg.display_order,
            is_active=pkg.is_active,
            stripe_price_id=pkg.stripe_price_id or "",
            config_defaults=config_by_name.get(pkg.name),  # None if not in config
        )
        for pkg in packages
    ]
```

### PasswordConfirmDialog Component
```typescript
// Source: Pattern from UI-SPEC + existing Dialog usage in admin-frontend
interface PasswordConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  impactText: string;
  confirmLabel: string;
  variant?: "default" | "destructive";  // destructive for resets
  isPending: boolean;
  onConfirm: (password: string) => void;
  error?: string | null;  // "Incorrect password" from 403 response
}

function PasswordConfirmDialog({ ... }: PasswordConfirmDialogProps) {
  const [password, setPassword] = useState("");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{impactText}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="confirm-password">Enter your password to confirm</Label>
            <Input
              id="confirm-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-2"
            />
            {error && (
              <p className="text-sm text-destructive mt-1">{error}</p>
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Go Back
          </Button>
          <Button
            variant={variant}
            disabled={!password || isPending}
            onClick={() => onConfirm(password)}
          >
            {isPending ? "Confirming..." : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Dynamic Plan Building (refactored /subscriptions/plans)
```python
# Source: Refactoring existing subscriptions.py lines 91-152
@router.get("/plans", response_model=PlanPricingResponse)
async def get_plans(db: DbSession, current_user: CurrentUser):
    platform_settings = await get_platform_settings(db)
    tiers = get_user_classes()

    plans = []
    for tier_name, tier_config in tiers.items():
        if not tier_config.get("has_plan"):
            continue

        price_key = f"price_{tier_name}_monthly_cents"
        price_cents = json.loads(platform_settings.get(price_key, str(tier_config.get("price_cents", 0))))

        plans.append(PlanInfo(
            tier_key=tier_name,
            display_name=tier_config.get("display_name", tier_name.title()),
            price_cents=price_cents,
            price_display=f"${price_cents / 100:.2f}/month" if price_cents > 0 else "Pay as you go",
            credit_allocation=tier_config.get("credits", 0),
            features=tier_config.get("features", []),  # NEW: from user_classes.yaml
            is_popular=(tier_name == "standard"),  # convention
        ))

    # Also include on_demand if it exists (no has_plan, but shown in plan selection)
    # ... handle on_demand tier separately

    return PlanPricingResponse(plans=plans, current_tier=current_user.user_class)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Inline price inputs on billing-settings page | Click-to-edit modal pattern (D-06) | Phase 61 | Existing inline inputs must be replaced |
| Hardcoded 3-plan list in `/subscriptions/plans` | Dynamic plan building from `user_classes.yaml` | Phase 61 | Backend endpoint refactored, frontend unchanged |
| Hardcoded feature bullets in Python backend | Config-driven `features:` list in `user_classes.yaml` (D-13) | Phase 61 | Features maintained in config, not code |
| No password on billing settings changes | Password re-entry for all pricing mutations (D-09) | Phase 61 | Existing PUT endpoint must add password field |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `on_demand` tier should still appear in Plan Selection even though it has `has_plan: false` | Code Examples (dynamic plans) | On Demand tier would disappear from the plan selection page. Need to handle it as a special case or add `has_plan: true` to on_demand in config |
| A2 | Credit package price changes should follow the same Stripe Price creation pattern as subscription pricing (deactivate old, create new) | Pitfall 5 | If credit packages use a different Stripe flow, the implementation would be wrong. But this matches the existing `_sync_stripe_packages` pattern in pricing_sync.py |

## Open Questions

1. **Password status code: 401 vs 403**
   - What we know: CONTEXT.md D-17 says "Returns 401 if password wrong." The existing codebase pattern (admin credits router) uses 403 with explicit comment: "Use 403 (not 401) -- admin IS authenticated, just wrong confirmation password."
   - What's unclear: Whether D-17's "401" was intentional or the user meant "auth error" generically.
   - Recommendation: Use 403 to match existing codebase convention. Using 401 would trigger the `adminApiClient` auto-redirect to `/login`, logging the admin out -- clearly unintended behavior. Flag this in planning as a deviation from D-17's literal text.

2. **On Demand tier in dynamic plan building**
   - What we know: Currently hardcoded as first plan in `/subscriptions/plans`. It has `has_plan: false` in config.
   - What's unclear: Should on_demand be included in dynamic plan listing even though `has_plan: false`? Or should config be updated to include it?
   - Recommendation: Add a `show_in_plan_selection: true` flag to on_demand tier in config, or handle it as a special case in the dynamic plan builder. The simplest approach: keep on_demand as a special case in the endpoint since it behaves differently (no subscription, no price).

3. **Billing settings GET response shape expansion**
   - What we know: Current GET returns flat fields for standard + premium pricing. Phase 61 needs dynamic tier support + config defaults + stripe readiness.
   - What's unclear: Whether to restructure as a list of tiers or keep flat with dynamic key generation.
   - Recommendation: Add `subscription_tiers: [...]` list alongside existing flat fields for backwards compatibility, plus `config_defaults` and `stripe_readiness` top-level keys.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (backend) |
| Config file | `backend/pyproject.toml` (no explicit pytest section found) |
| Quick run command | `cd backend && python -m pytest tests/test_pricing_sync.py -x` |
| Full suite command | `cd backend && python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SUB-05 | GET billing-settings returns tiers with defaults | unit | `pytest tests/test_billing_settings_api.py::test_get_includes_defaults -x` | No -- Wave 0 |
| SUB-06 | PUT billing-settings with password updates pricing | unit | `pytest tests/test_billing_settings_api.py::test_update_pricing_with_password -x` | No -- Wave 0 |
| SUB-07 | POST billing-settings/reset resets to config defaults | unit | `pytest tests/test_billing_settings_api.py::test_reset_subscription_pricing -x` | No -- Wave 0 |
| PKG-04 | GET credit-packages returns all packages with defaults | unit | `pytest tests/test_admin_credit_packages.py::test_get_all_packages -x` | No -- Wave 0 |
| PKG-05 | PUT credit-packages/{id} updates package with password | unit | `pytest tests/test_admin_credit_packages.py::test_update_package -x` | No -- Wave 0 |
| PKG-06 | POST credit-packages/reset resets to config defaults | unit | `pytest tests/test_admin_credit_packages.py::test_reset_packages -x` | No -- Wave 0 |
| UI-01 | GET /subscriptions/plans returns dynamic tiers from config | unit | `pytest tests/test_subscription_plans_dynamic.py::test_dynamic_plans -x` | No -- Wave 0 |
| UI-02 | GET /credits/packages returns DB-driven packages | unit | `pytest tests/test_pricing_sync.py -x` (partial coverage exists) | Partial |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_billing_settings_api.py tests/test_admin_credit_packages.py -x`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_billing_settings_api.py` -- covers SUB-05, SUB-06, SUB-07
- [ ] `tests/test_admin_credit_packages.py` -- covers PKG-04, PKG-05, PKG-06
- [ ] `tests/test_subscription_plans_dynamic.py` -- covers UI-01

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Password re-entry verification via `verify_password()` from pwdlib/Argon2 for all pricing mutations |
| V3 Session Management | no | Handled by existing JWT + AdminTokenReissueMiddleware |
| V4 Access Control | yes | `CurrentAdmin` dependency ensures only authenticated admins access endpoints |
| V5 Input Validation | yes | Pydantic v2 schemas with `Field(ge=0)` constraints for price fields, string length limits |
| V6 Cryptography | no | No new crypto -- password hashing already uses Argon2 via pwdlib |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Price manipulation via direct API call | Tampering | Password re-entry required for all pricing mutations (D-09). Backend verifies atomically (D-17) |
| Mass reset attack | Denial of Service | Password verification prevents unauthorized resets. Audit logging recommended |
| Stripe Price ID injection | Tampering | Stripe Price ID is never admin-editable (D-08). Auto-created by system only |
| Stale Stripe Prices after reset | Information Disclosure | Old Stripe Prices deactivated on reset. `reset_subscription_pricing()` and `reset_credit_packages()` handle this |

## Project Constraints (from CLAUDE.md)

No CLAUDE.md file exists in the project root. [VERIFIED: file read returned "File does not exist"]

Project conventions inferred from codebase:
- Admin pages use `max-w-2xl mx-auto space-y-6` layout pattern [VERIFIED: billing-settings page.tsx]
- TanStack Query hooks follow `use{Resource}` naming convention [VERIFIED: useBilling.ts, useCreditPackages.ts]
- Backend routers use `APIRouter(prefix="/...", tags=["..."])` pattern [VERIFIED: billing_settings.py, credits.py]
- Password re-entry uses 403 (not 401) for incorrect confirmation [VERIFIED: admin/credits.py line 89-91]
- Admin API is mounted at `/api/admin` prefix [VERIFIED: main.py line 421]
- Public API endpoints use `/` prefix (no `/api` prefix) [VERIFIED: subscriptions.py, credits.py]

## Sources

### Primary (HIGH confidence)
- `admin-frontend/src/app/(admin)/billing-settings/page.tsx` -- existing billing settings page (207 lines), full code reviewed
- `admin-frontend/src/hooks/useBilling.ts` -- existing TanStack Query hooks and TypeScript types
- `backend/app/routers/admin/billing_settings.py` -- existing GET/PUT endpoints with Stripe Price creation
- `backend/app/services/pricing_sync.py` -- reset functions, readiness check, seeding logic
- `backend/app/routers/admin/credits.py` -- password verification pattern (lines 88-91)
- `backend/app/utils/security.py` -- `verify_password()` implementation
- `backend/app/config/user_classes.yaml` -- tier and credit package configuration
- `backend/app/models/credit_package.py` -- CreditPackage SQLAlchemy model
- `backend/app/services/platform_settings.py` -- DEFAULTS dict, upsert, get_all, validate_setting
- `backend/app/routers/subscriptions.py` -- current hardcoded `/plans` endpoint
- `frontend/src/app/(dashboard)/settings/plan/page.tsx` -- Plan Selection page (already dynamic)
- `frontend/src/app/(dashboard)/settings/billing/page.tsx` -- Billing page (already uses useCreditPackages)
- `frontend/src/hooks/useCreditPackages.ts` -- credit packages hook (already DB-driven)
- `admin-frontend/src/lib/admin-api-client.ts` -- admin API client with 401 auto-redirect
- `.planning/phases/61-admin-pricing-management-ui/61-UI-SPEC.md` -- full UI design contract
- `.planning/phases/61-admin-pricing-management-ui/61-CONTEXT.md` -- all locked decisions D-01 through D-18
- `backend/app/schemas/admin_billing.py` -- existing Pydantic schemas
- `backend/app/routers/admin/__init__.py` -- router registration pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, zero new dependencies
- Architecture: HIGH -- extending existing patterns with well-documented decisions
- Pitfalls: HIGH -- based on verified codebase patterns (especially 401 vs 403 issue)

**Research date:** 2026-04-23
**Valid until:** 2026-05-23 (stable -- internal project, no external dependency changes)
