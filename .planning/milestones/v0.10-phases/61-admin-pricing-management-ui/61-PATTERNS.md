# Phase 61: Admin Pricing Management UI - Pattern Map

**Mapped:** 2026-04-23
**Files analyzed:** 10 new/modified files
**Analogs found:** 10 / 10

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `admin-frontend/src/app/(admin)/billing-settings/page.tsx` | component (page) | request-response | `admin-frontend/src/app/(admin)/billing-settings/page.tsx` (self — refactor) | exact |
| `admin-frontend/src/components/shared/PasswordConfirmDialog.tsx` | component (shared dialog) | event-driven | `admin-frontend/src/components/shared/ConfirmModal.tsx` | exact |
| `admin-frontend/src/hooks/useBilling.ts` | hook | request-response | `admin-frontend/src/hooks/useBilling.ts` (self — extend) | exact |
| `backend/app/routers/admin/credit_packages.py` | controller (router) | CRUD | `backend/app/routers/admin/credits.py` | role-match |
| `backend/app/routers/admin/billing_settings.py` | controller (router) | CRUD | `backend/app/routers/admin/billing_settings.py` (self — extend) | exact |
| `backend/app/routers/admin/__init__.py` | config (router registration) | N/A | `backend/app/routers/admin/__init__.py` (self — extend) | exact |
| `backend/app/schemas/admin_billing.py` | model (schema) | N/A | `backend/app/schemas/admin_billing.py` (self — extend) | exact |
| `backend/app/routers/subscriptions.py` | controller (router) | request-response | `backend/app/routers/subscriptions.py` (self — refactor lines 91-152) | exact |
| `backend/app/config/user_classes.yaml` | config | N/A | `backend/app/config/user_classes.yaml` (self — extend) | exact |
| `frontend/src/app/(dashboard)/settings/billing/page.tsx` | component (page) | request-response | `frontend/src/app/(dashboard)/settings/billing/page.tsx` (self — verify only) | exact |

## Pattern Assignments

### `admin-frontend/src/components/shared/PasswordConfirmDialog.tsx` (NEW component, event-driven)

**Analog:** `admin-frontend/src/components/shared/ConfirmModal.tsx`

**Imports pattern** (lines 1-12):
```typescript
"use client";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
```

**Props interface pattern** (lines 14-23):
```typescript
interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  variant?: "default" | "destructive";
  loading?: boolean;
}
```

**Dialog structure pattern** (lines 34-56):
```typescript
return (
  <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant={variant === "destructive" ? "destructive" : "default"}
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? "Processing..." : confirmLabel}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
```

**Key adaptation:** PasswordConfirmDialog extends this pattern by adding a password `Input` field between `DialogHeader` and `DialogFooter`, an `error` prop for inline "Incorrect password" display, and changing `onConfirm` signature to `(password: string) => void`. Also add `Input` and `Label` imports from `@/components/ui/`.

---

### `admin-frontend/src/app/(admin)/billing-settings/page.tsx` (REFACTOR, request-response)

**Analog:** Self (current version) + `admin-frontend/src/components/discounts/CreateDiscountDialog.tsx` for edit modal pattern

**Page layout pattern** (lines 100-107 of current billing-settings page):
```typescript
return (
  <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-bold tracking-tight">Billing Settings</h1>
      <p className="text-muted-foreground">
        Configure monetization and pricing settings
      </p>
    </div>
    <div className="max-w-2xl mx-auto space-y-6">
```

**Card section pattern** (lines 111-141):
```typescript
<Card>
  <CardHeader>
    <CardTitle className="text-base">Monetization</CardTitle>
    <CardDescription>Master switch for billing features</CardDescription>
  </CardHeader>
  <CardContent className="space-y-4">
    {isLoading || !form ? (
      <Skeleton className="h-10 w-full" />
    ) : (
      <>
        {/* content */}
      </>
    )}
  </CardContent>
</Card>
```

**Edit modal pattern** (from CreateDiscountDialog lines 43-48, 118-148):
```typescript
// Dialog with form state + mutation
export function CreateDiscountDialog({
  open,
  onOpenChange,
  initialValues,
}: CreateDiscountDialogProps) {
  const isEditMode = !!initialValues;

  // useState for each form field
  const [code, setCode] = useState("");

  // Pre-fill form in edit mode via useEffect
  useEffect(() => {
    if (initialValues) {
      setCode(initialValues.code);
      // ...
    } else {
      resetForm();
    }
  }, [initialValues]);

  async function handleSubmit() {
    // validate, then mutate, then toast + close
    try {
      await updateMutation.mutateAsync({ ... });
      toast.success("...");
      onOpenChange(false);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Operation failed");
    }
  }
```

**Currency utilities to preserve** (lines 17-23 of current page):
```typescript
function centsToDisplay(cents: number): string {
  return (cents / 100).toFixed(2);
}

function displayToCents(display: string): number {
  return Math.round(parseFloat(display) * 100);
}
```

**Error state pattern** (lines 90-98):
```typescript
if (error) {
  return (
    <div className="flex items-center justify-center py-20">
      <p className="text-destructive">
        Failed to load settings: {error.message}
      </p>
    </div>
  );
}
```

---

### `admin-frontend/src/hooks/useBilling.ts` (EXTEND, request-response)

**Analog:** Self (current version)

**Query hook pattern** (lines 68-80):
```typescript
export function useBillingSettings() {
  return useQuery<BillingSettings>({
    queryKey: ["admin", "billing-settings"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/billing-settings");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to fetch billing settings");
      }
      return res.json();
    },
  });
}
```

**Mutation hook pattern with cache invalidation** (lines 156-174):
```typescript
export function useUpdateBillingSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<BillingSettings>) => {
      const res = await adminApiClient.put(
        "/api/admin/billing-settings",
        payload
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "billing-settings"] });
    },
  });
}
```

**Key additions needed:** New hooks for `useAdminCreditPackages()` (GET), `useUpdateCreditPackage()` (PUT with password), `useResetSubscriptionPricing()` (POST with password), `useResetCreditPackages()` (POST with password). Extended `BillingSettings` type to include `config_defaults` and `stripe_readiness`. New `AdminCreditPackage` type.

---

### `backend/app/routers/admin/credit_packages.py` (NEW router, CRUD)

**Analog:** `backend/app/routers/admin/credits.py` (password verification) + `backend/app/routers/admin/billing_settings.py` (Stripe Price creation)

**Router setup pattern** (credits.py lines 1-8):
```python
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request

from app.dependencies import CurrentAdmin, DbSession
from app.models.user import User
from app.utils.security import verify_password

router = APIRouter(prefix="/credits", tags=["admin-credits"])
```

**Password verification pattern** (credits.py lines 88-91):
```python
# Verify admin password (per locked decision: password re-entry required)
# Use 403 (not 401) -- admin IS authenticated, just wrong confirmation password
if not verify_password(body.password, current_admin.hashed_password):
    raise HTTPException(status_code=403, detail="Incorrect password")
```

**GET endpoint pattern returning all rows** (billing_settings.py lines 36-58):
```python
@router.get("", response_model=BillingSettingsResponse)
async def get_billing_settings(
    admin: CurrentAdmin,
    db: DbSession,
):
    """Read all billing-related platform settings."""
    settings = await get_platform_settings(db)
    return BillingSettingsResponse(...)
```

**Stripe Price creation on price change pattern** (billing_settings.py lines 104-166):
```python
for price_field in ("price_standard_monthly_cents", "price_premium_monthly_cents"):
    if price_field not in updates:
        continue

    new_price_cents = updates[price_field]
    current_price_cents = json.loads(current_settings.get(price_field, "0"))

    if new_price_cents != current_price_cents and new_price_cents > 0:
        tier = "standard" if "standard" in price_field else "premium"
        stripe_price_key = f"stripe_price_{tier}_monthly"
        old_stripe_price_id = json.loads(current_settings.get(stripe_price_key, '""'))

        try:
            from app.services.subscription import SubscriptionService
            client = SubscriptionService._get_stripe_client()
            new_price = client.v1.prices.create(params={...})
            if old_stripe_price_id:
                try:
                    client.v1.prices.update(old_stripe_price_id, params={"active": False})
                except Exception:
                    logger.warning("Failed to deactivate old Stripe price: %s", old_stripe_price_id)
            await upsert(db, stripe_price_key, new_price.id, admin.id)
        except Exception as e:
            logger.error("Failed to create Stripe price for %s: %s", tier, str(e))
            raise HTTPException(status_code=500, detail=f"Failed to create Stripe price: {str(e)}")
```

**Reset endpoint pattern** (use pricing_sync.py functions):
```python
# From pricing_sync.py lines 93-152
async def reset_subscription_pricing(db: AsyncSession) -> None:
    """Reset subscription pricing in DB to match config values."""
    # ... iterates tiers, overwrites DB, deactivates old Stripe Prices, creates new ones

# From pricing_sync.py lines 155-212
async def reset_credit_packages(db: AsyncSession) -> None:
    """Reset credit packages in DB to match config values."""
    # ... overwrites existing rows, deactivates non-config packages, re-syncs Stripe
```

---

### `backend/app/routers/admin/billing_settings.py` (EXTEND, CRUD)

**Analog:** Self (current version)

**Key modifications needed:**
1. Add `password` field to PUT request body, verify via `verify_password()` pattern from credits.py lines 88-91
2. Add reset endpoint (`POST /billing-settings/reset`) calling `pricing_sync.reset_subscription_pricing()`
3. Extend GET response with `config_defaults` and `stripe_readiness` using `check_stripe_readiness()` from pricing_sync.py

**Config defaults injection pattern** (derive from pricing_sync.py lines 28-29 + 68-71):
```python
tiers = get_user_classes()
for tier_name, tier_config in tiers.items():
    if not tier_config.get("has_plan"):
        continue
    # tier_config["price_cents"] is the config default
```

---

### `backend/app/routers/admin/__init__.py` (EXTEND, config)

**Analog:** Self (current version)

**Router registration pattern** (lines 1-27):
```python
from app.routers.admin import billing_settings as admin_billing_settings
# ... other imports ...

admin_router = APIRouter()
admin_router.include_router(admin_billing_settings.router)
# ... other registrations ...
```

**Add:** Import and register `credit_packages` router following same two-line pattern (import + include_router).

---

### `backend/app/schemas/admin_billing.py` (EXTEND, model)

**Analog:** Self (current version)

**Pydantic schema pattern** (lines 84-95):
```python
class BillingSettingsResponse(BaseModel):
    monetization_enabled: bool
    price_standard_monthly_cents: int
    price_premium_monthly_cents: int
    stripe_price_standard_monthly: str
    stripe_price_premium_monthly: str


class BillingSettingsUpdateRequest(BaseModel):
    monetization_enabled: bool | None = None
    price_standard_monthly_cents: int | None = Field(None, ge=0)
    price_premium_monthly_cents: int | None = Field(None, ge=0)
```

**Key additions:** `password: str` field to update request, `config_defaults: dict` and `stripe_readiness: dict` to response. New `AdminCreditPackageResponse` and `CreditPackageUpdateRequest` schemas following same pattern with `Field(ge=0)` constraints.

---

### `backend/app/routers/subscriptions.py` (REFACTOR lines 91-152, request-response)

**Analog:** Self (current version)

**Current hardcoded plan building** (lines 91-152):
```python
@router.get("/plans", response_model=PlanPricingResponse)
async def get_plans(db: DbSession, current_user: CurrentUser):
    platform_settings = await get_platform_settings(db)
    standard_price = json.loads(platform_settings.get("price_standard_monthly_cents", "2900"))
    premium_price = json.loads(platform_settings.get("price_premium_monthly_cents", "7900"))

    standard_config = get_class_config("standard") or {}
    premium_config = get_class_config("premium") or {}
    on_demand_config = get_class_config("on_demand") or {}

    plans = [
        PlanInfo(
            tier_key="on_demand",
            display_name="On Demand",
            # ... hardcoded features list ...
        ),
        PlanInfo(
            tier_key="standard",
            # ... hardcoded features list ...
        ),
        PlanInfo(
            tier_key="premium",
            # ... hardcoded features list ...
        ),
    ]
    return PlanPricingResponse(plans=plans, current_tier=current_user.user_class)
```

**Refactor to:** Dynamic iteration over `get_user_classes()` filtering by `has_plan: true`, reading `features:` list from config instead of hardcoding. Keep `on_demand` as special case (no `has_plan` but shown in plan selection).

**Import pattern** (lines 1-30):
```python
import json
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.services.platform_settings import get_all as get_platform_settings
from app.services.user_class import get_class_config
```

**Add import:** `from app.services.user_class import get_user_classes`

---

### `backend/app/config/user_classes.yaml` (EXTEND, config)

**Analog:** Self (current version)

**Current tier structure** (lines 17-24):
```yaml
standard:
    display_name: "Standard"
    credits: 100
    reset_policy: none
    workspace_access: true
    max_active_collections: 5
    has_plan: true
    price_cents: 2900
```

**Extension:** Add `features:` list to each tier with `has_plan: true` (and `on_demand` for plan selection display):
```yaml
standard:
    display_name: "Standard"
    credits: 100
    # ... existing fields ...
    features:
      - "100 credits/month"
      - "Priority support"
      - "Full feature access"
      - "Up to 5 active collections"
```

---

## Shared Patterns

### Password Verification (Backend)
**Source:** `backend/app/routers/admin/credits.py` lines 88-91
**Apply to:** All new pricing mutation endpoints (billing_settings PUT, billing_settings reset, credit_packages PUT, credit_packages reset)
```python
from app.utils.security import verify_password

# Use 403 (not 401) -- admin IS authenticated, just wrong confirmation password
if not verify_password(body.password, current_admin.hashed_password):
    raise HTTPException(status_code=403, detail="Incorrect password")
```

### Dependency Injection (Backend)
**Source:** `backend/app/routers/admin/billing_settings.py` lines 37-40
**Apply to:** All new admin router endpoints
```python
async def endpoint_name(
    admin: CurrentAdmin,       # from app.dependencies
    db: DbSession,             # from app.dependencies
):
```

### TanStack Query Hook (Frontend)
**Source:** `admin-frontend/src/hooks/useBilling.ts` lines 68-80 (query), lines 156-174 (mutation)
**Apply to:** All new hooks (credit packages GET, credit package update, reset mutations)
```typescript
// Query pattern
export function useResourceName() {
  return useQuery<ResponseType>({
    queryKey: ["admin", "resource-name"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/resource-path");
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Failed to fetch");
      }
      return res.json();
    },
  });
}

// Mutation pattern
export function useUpdateResourceName() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RequestType) => {
      const res = await adminApiClient.put("/api/admin/resource-path", payload);
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || "Operation failed");
      }
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "resource-name"] });
    },
  });
}
```

### Toast Feedback (Frontend)
**Source:** `admin-frontend/src/app/(admin)/billing-settings/page.tsx` lines 77-87
**Apply to:** All mutation handlers in billing-settings page
```typescript
try {
  const updated = await mutation.mutateAsync(payload);
  toast.success("Success message");
} catch (e: any) {
  toast.error(e.message);
}
```

### Admin Page Layout (Frontend)
**Source:** `admin-frontend/src/app/(admin)/billing-settings/page.tsx` lines 100-109
**Apply to:** Billing-settings page (already applied, preserve on refactor)
```typescript
<div className="space-y-6">
  <div>
    <h1 className="text-2xl font-bold tracking-tight">Page Title</h1>
    <p className="text-muted-foreground">Page description</p>
  </div>
  <div className="max-w-2xl mx-auto space-y-6">
    {/* Card sections */}
  </div>
</div>
```

### Error Response Handling (Frontend)
**Source:** `admin-frontend/src/lib/admin-api-client.ts` lines 69-76
**Apply to:** All mutation error handling -- must handle 403 specially (not redirect)
```typescript
// 401 triggers auto-redirect to /login (line 71-76 of admin-api-client.ts)
// 403 does NOT redirect -- must be handled by the component as inline error
// For PasswordConfirmDialog: catch 403, extract body.detail, show as error prop
```

### Cache Invalidation (Backend)
**Source:** `backend/app/routers/admin/billing_settings.py` lines 174-176
**Apply to:** All endpoints that modify platform_settings or credit_packages
```python
await db.commit()
invalidate_cache()  # from app.services.platform_settings
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | -- | -- | All files have strong analogs in the existing codebase |

## Metadata

**Analog search scope:** `admin-frontend/src/`, `backend/app/routers/admin/`, `backend/app/schemas/`, `backend/app/services/`, `backend/app/config/`, `frontend/src/`
**Files scanned:** 15 analog files read
**Pattern extraction date:** 2026-04-23
