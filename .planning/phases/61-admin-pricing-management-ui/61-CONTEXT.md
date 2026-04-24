# Phase 61: Admin Pricing Management UI - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin can view, edit, and reset both subscription pricing and credit packages from the admin portal. Public-facing Plan Selection and Billing pages render dynamically from database/config instead of hardcoded values. This phase covers admin UI changes, new backend endpoints, and frontend dynamic rendering.

</domain>

<decisions>
## Implementation Decisions

### Admin Page Layout
- **D-01:** Extend the existing billing-settings page — single page for all pricing management, no separate pages or tabs
- **D-02:** Page section order: Monetization Toggle → Subscription Pricing → Credit Packages → Save Button
- **D-03:** Keep the page title as "Billing Settings" — existing name is broad enough

### Config vs DB Display
- **D-04:** Each editable field shows an inline hint underneath: "Default: $29.00" showing the config-file default value
- **D-05:** No visual indicator (dot/badge) when DB value differs from config default — the inline hint is sufficient

### Editing UX (Subscription and Credit Packages)
- **D-06:** Click-to-edit modal pattern for BOTH subscription pricing and credit packages. The existing inline price inputs for subscription pricing must be replaced with the same click-to-edit modal UX for consistency
- **D-07:** Credit package cards in view mode show full details: name, price, credits, display_order, active status, and Stripe Price ID (read-only/uneditable)
- **D-08:** Edit modal allows changing: name, price, credits, display_order, active status. Stripe Price ID is never editable by admin (auto-created by system)

### Confirmation & Safety
- **D-09:** All pricing changes (subscription edits, credit package edits, AND resets) require a confirmation dialog that: (1) explains the impact of the changes, (2) requires password re-entry to confirm
- **D-10:** The confirmation dialog has an inline password field. Password is sent alongside the save/reset request to the backend, which verifies before executing
- **D-11:** Per-section "Reset to Defaults" buttons — one at the bottom of Subscription Pricing card, one at the bottom of Credit Packages card. Each resets only its section

### Stripe Readiness
- **D-12:** Pre-check approach for the monetization toggle: when Stripe isn't ready, the toggle is disabled with a checklist of missing items shown in the Monetization card (e.g., "Standard plan: missing Stripe Price ID"). Toggle becomes enabled when all checks pass

### Dynamic Plan Selection Page
- **D-13:** Add a `features:` list to each tier in `user_classes.yaml` — config-driven plan benefit bullets instead of hardcoded in Python backend
- **D-14:** The `/subscriptions/plans` endpoint reads tiers with `has_plan: true` from config and builds the response dynamically instead of hardcoding 3 plans
- **D-15:** Plan Selection page (`/settings/plan`) already renders dynamically from API — backend changes are sufficient, no frontend changes needed for plan rendering

### Dynamic Billing Page
- **D-16:** Billing page (`/settings/billing`) shows dynamic credit package cards rendered from the database. Each card shows package name, price, credits, and a "Buy" button. Replaces any hardcoded credit package references

### Backend API Contracts
- **D-17:** Password sent in each save/reset request body (not a separate verify endpoint). Backend verifies atomically with the action. Returns 403 if password wrong (deviation from original 401 — approved by owner because 401 triggers adminApiClient auto-redirect to /login, logging the admin out; 403 matches existing codebase pattern in admin/credits.py)
- **D-18:** Router and endpoint design: Claude's discretion — pick the approach that best fits existing admin API patterns (extend billing-settings vs new router, dedicated reset endpoints vs scope parameter)

### Claude's Discretion
- Exact modal component implementation (reuse existing Dialog from shadcn/ui)
- API response shapes and error formats
- Router organization (extend billing-settings vs new credit-packages router)
- Reset endpoint shape (dedicated per-section vs single with scope param)
- Impact text wording in confirmation dialogs
- Stripe readiness checklist UI component design

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Admin Billing UI (existing)
- `admin-frontend/src/app/(admin)/billing-settings/page.tsx` — Current billing settings page (207 lines). Monetization toggle + subscription pricing inputs. Must be extended with credit packages section and refactored to click-to-edit modal pattern
- `admin-frontend/src/hooks/useBilling.ts` — useBillingSettings and useUpdateBillingSettings hooks
- `admin-frontend/src/app/(admin)/credits/page.tsx` — Existing credits page (may have reusable patterns)

### Backend Billing
- `backend/app/routers/admin/billing_settings.py` — GET/PUT billing settings. Has monetization toggle guard (D-07 from Phase 60). Password verification for pricing changes will be added here
- `backend/app/services/pricing_sync.py` — Phase 60 service: reset_subscription_pricing(), reset_credit_packages(), check_stripe_readiness(). Admin UI calls these
- `backend/app/services/platform_settings.py` — DEFAULTS dict, upsert(), get_all(). Subscription pricing stored as platform_settings keys

### Config & Models
- `backend/app/config/user_classes.yaml` — Tier definitions with has_plan, price_cents, credit_packages section. Will be extended with `features:` list per tier
- `backend/app/models/credit_package.py` — CreditPackage model (name, price_cents, credit_amount, display_order, is_active, stripe_price_id)
- `backend/app/services/user_class.py` — get_user_classes(), get_credit_packages() loaders with TTL cache

### Public Frontend
- `frontend/src/app/(dashboard)/settings/plan/page.tsx` — Plan Selection page (60 lines). Already renders dynamically from API. Backend changes sufficient
- `frontend/src/hooks/usePlanPricing.ts` — PlanInfo interface, usePlanPricing hook hitting /subscriptions/plans
- `backend/app/routers/subscriptions.py` lines 91-152 — GET /plans endpoint. Currently hardcodes 3 plans with hardcoded features. Must be made dynamic
- `frontend/src/app/(dashboard)/settings/billing/page.tsx` — Billing page. Credit packages need to render from database
- `backend/app/routers/credits.py` — Credit packages endpoint serving frontend

### Phase 60 Context
- `.planning/phases/60-config-driven-pricing-startup-sync/60-CONTEXT.md` — Phase 60 decisions (D-01 through D-12) for config structure, startup sync, Stripe provisioning, and reset contracts

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Card`, `CardHeader`, `CardContent`, `CardTitle`, `CardDescription` — shadcn/ui card components used throughout admin-frontend
- `Switch` component — used for monetization toggle
- `Input`, `Label` — form components from shadcn/ui
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription` — shadcn/ui dialog for modals
- `useBillingSettings` / `useUpdateBillingSettings` — TanStack Query hooks for billing data
- `PlanCard` component — frontend plan card renderer (already dynamic)
- `centsToDisplay()` / `displayToCents()` — currency conversion utilities in billing-settings page

### Established Patterns
- Admin pages use `max-w-2xl mx-auto space-y-6` layout with Card-based sections
- TanStack Query for data fetching with `staleTime` configuration
- `toast.success()` / `toast.error()` from Sonner for feedback
- `apiClient` wrapper for authenticated API calls
- Form state managed with useState + isDirty tracking

### Integration Points
- `billing_settings.py` PUT endpoint — already handles monetization toggle guard (Phase 60)
- `pricing_sync.py` — reset functions and readiness check ready to be called from new endpoints
- `user_classes.yaml` — needs `features:` list added per tier
- `/subscriptions/plans` endpoint — needs dynamic tier filtering by `has_plan`

</code_context>

<specifics>
## Specific Ideas

- The confirmation dialog with password re-entry is a shared pattern across all pricing operations (edits AND resets) — implement as a reusable component
- Stripe Price ID is display-only in the UI — never editable, shown for admin reference
- The monetization toggle pre-check should call `check_stripe_readiness()` on page load and update reactively
- Existing subscribers are grandfathered on reset (per Phase 60 D-11) — the impact text in the confirmation dialog should mention this

</specifics>

<deferred>
## Deferred Ideas

- **Admin creating new credit packages from scratch** — out of scope per REQUIREMENTS.md; config-defined packages only
- **Admin deleting credit packages** — deactivate via is_active flag instead; preserves payment history references
- **Admin-editable feature bullet points in UI** — features are config-driven in user_classes.yaml; admin editing would need DB schema changes
- **Stripe webhook status dashboard** — showing webhook delivery history in admin portal

</deferred>

---

*Phase: 61-admin-pricing-management-ui*
*Context gathered: 2026-04-23*
