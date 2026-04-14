---
phase: 59-admin-billing-tools
plan: 03
subsystem: frontend
tags: [admin, billing, react, tanstack-query, shadcn, stripe]

# Dependency graph
requires:
  - phase: 59-admin-billing-tools
    plan: 01
    provides: Admin billing API endpoints, billing settings API
provides:
  - UserBillingTab component with subscription card, payment history, Stripe event log
  - ForceSetTierDialog with reason field and Stripe sync warning
  - RefundDialog with credit deduction preview
  - BillingSettingsPage with monetization toggle, trial settings, pricing config
  - useBilling hooks for all billing admin API calls
  - Sidebar Billing section with Billing Settings and Discount Codes links
affects: [59-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TanStack Query hooks in dedicated useBilling.ts file following useUsers.ts pattern
    - Price display as dollars in inputs, stored/sent as cents
    - Client-side pagination with Load More button pattern
    - Proportional credit deduction preview computed on frontend

key-files:
  created:
    - admin-frontend/src/hooks/useBilling.ts
    - admin-frontend/src/components/users/UserBillingTab.tsx
    - admin-frontend/src/components/users/ForceSetTierDialog.tsx
    - admin-frontend/src/components/users/RefundDialog.tsx
    - admin-frontend/src/app/(admin)/billing-settings/page.tsx
  modified:
    - admin-frontend/src/components/users/UserDetailTabs.tsx
    - admin-frontend/src/components/layout/AdminSidebar.tsx

key-decisions:
  - "Billing tab is 6th tab in UserDetailTabs (after API Keys)"
  - "Refund button only shown for succeeded payments with stripe_payment_intent_id"
  - "BillingSettingsPage sends only changed fields via Partial<BillingSettings>"
  - "Credit Packages card is read-only placeholder (managed via DB)"
  - "Sidebar Discount Codes link added now (page created in Plan 04)"

requirements-completed: [ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07]

# Metrics
duration: 4min
completed: 2026-03-24
---

# Phase 59 Plan 03: Admin Billing Frontend Summary

**Admin billing UI with UserBillingTab (subscription card, payment history, Stripe events), ForceSetTierDialog, RefundDialog, BillingSettingsPage, and sidebar nav**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-24T19:13:43Z
- **Completed:** 2026-03-24T19:17:17Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments
- 6 TanStack Query hooks for billing admin API (useUserBillingDetail, useForceSetTier, useAdminCancelSubscription, useRefundPayment, useBillingSettings, useUpdateBillingSettings)
- UserBillingTab with 3 stacked Cards: subscription status with action buttons, payment history table with per-row refund, Stripe event log
- ForceSetTierDialog with tier selector (filters out current tier), mandatory reason field, Stripe sync warning copy
- RefundDialog with pre-filled amount, cents input, proportional credit deduction preview, destructive action button
- BillingSettingsPage with monetization Switch, trial settings, subscription pricing (dollar display / cents storage), save-only-changes
- AdminSidebar updated with Billing section containing Billing Settings and Discount Codes links

## Task Commits

Each task was committed atomically:

1. **Task 1: Billing hooks + UserBillingTab + ForceSetTierDialog + RefundDialog** - `ee1ca5b` (feat)
2. **Task 2: Billing Settings page + sidebar navigation update** - `de989df` (feat)

## Files Created/Modified
- `admin-frontend/src/hooks/useBilling.ts` - 6 TanStack Query hooks for billing admin API
- `admin-frontend/src/components/users/UserBillingTab.tsx` - Billing tab with subscription, payments, Stripe events
- `admin-frontend/src/components/users/ForceSetTierDialog.tsx` - Force set tier dialog with reason and Stripe warning
- `admin-frontend/src/components/users/RefundDialog.tsx` - Refund dialog with credit deduction preview
- `admin-frontend/src/components/users/UserDetailTabs.tsx` - Added Billing tab (6th tab)
- `admin-frontend/src/app/(admin)/billing-settings/page.tsx` - Billing Settings admin page
- `admin-frontend/src/components/layout/AdminSidebar.tsx` - Added Billing section with 2 nav items

## Decisions Made
- Billing tab placed as 6th tab after API Keys in UserDetailTabs
- Refund button only rendered for payments with status "succeeded" and a Stripe payment intent ID
- BillingSettingsPage computes diff and sends only changed fields to PUT endpoint
- Credit Packages card is read-only placeholder directing to DB admin
- Discount Codes sidebar link added proactively (page created in Plan 04) to avoid file conflicts

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all components are wired to real API hooks with proper loading/error/empty states.

## Next Phase Readiness
- Plan 04 (Discount Codes page) can proceed -- sidebar link already in place
- All billing admin API hooks available for reuse

## Self-Check: PASSED

All 7 files verified present. Both task commits (ee1ca5b, de989df) verified in git log.

---
*Phase: 59-admin-billing-tools*
*Completed: 2026-03-24*
