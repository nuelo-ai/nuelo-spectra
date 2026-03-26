---
phase: 58-billing-ui-subscription-management
plan: 04
subsystem: ui
tags: [react, billing, stripe, tanstack-query, shadcn, subscription, credits]

# Dependency graph
requires:
  - phase: 58-01
    provides: Backend billing API endpoints (cancel, billing-history, credit packages, credit balance)
  - phase: 58-03
    provides: useSubscription hook, useTrialState hook, settings layout
provides:
  - Manage Plan page at /settings/billing with plan status, credit balance, credit packages, billing history
  - Data hooks: useBillingHistory, useCreditPackages
  - Billing UI components: PlanStatusCard, CreditBalanceSection, CreditPackageCard, BillingHistoryTable
  - Post-Stripe redirect toast handling for session_id and topup=success
affects: [58-05, billing-integration, settings-navigation]

# Tech tracking
tech-stack:
  added: []
  patterns: [post-redirect-toast-pattern, section-not-card-pattern, cancel-confirmation-dialog]

key-files:
  created:
    - frontend/src/hooks/useBillingHistory.ts
    - frontend/src/hooks/useCreditPackages.ts
    - frontend/src/hooks/useSubscription.ts
    - frontend/src/hooks/useTrialState.ts
    - frontend/src/components/billing/PlanStatusCard.tsx
    - frontend/src/components/billing/CreditBalanceSection.tsx
    - frontend/src/components/billing/CreditPackageCard.tsx
    - frontend/src/components/billing/BillingHistoryTable.tsx
    - frontend/src/app/(dashboard)/settings/billing/page.tsx
  modified:
    - frontend/src/hooks/useCredits.ts
    - frontend/src/types/auth.ts

key-decisions:
  - "CreditBalanceSection renders as section content within parent Card, not as standalone Card (avoids nested Card nesting)"
  - "useSubscription and useTrialState created as dependency hooks since Plan 03 runs in parallel and may not have committed yet"
  - "UserResponse extended with user_class and trial_expires_at fields (prerequisite for useTrialState)"
  - "Suspense wrapper required for useSearchParams in Next.js App Router client components"

patterns-established:
  - "Post-redirect toast pattern: check searchParams on mount, show toast, router.replace to clean URL, invalidate queries"
  - "Section-not-card pattern: CreditBalanceSection renders within parent Card to avoid double Card nesting"
  - "Cancel confirmation: AlertDialog with destructive action styling and loading spinner"

requirements-completed: [SUB-03, SUB-04, SUB-05, TOPUP-01, TOPUP-02, TOPUP-03, TOPUP-05, BILL-03, BILL-05]

# Metrics
duration: 5min
completed: 2026-03-23
---

# Phase 58 Plan 04: Manage Plan Billing Page Summary

**Complete billing management page at /settings/billing with plan status card, dual credit balance display, credit top-up purchase flow via Stripe, and billing history table with post-redirect toast handling.**

## What Was Built

### Task 1: Data Hooks and Billing Components (1a41224)
- **useBillingHistory**: React Query hook for GET /subscriptions/billing-history with 30s stale time
- **useCreditPackages**: React Query hook for GET /credits/packages with 60s stale time
- **useSubscription**: React Query hook for GET /subscriptions/status (dependency from Plan 03)
- **useTrialState**: Derived hook computing trial status from user data (dependency from Plan 03)
- **useCredits update**: Added purchased_balance and total_balance to CreditBalance interface
- **PlanStatusCard**: Shows plan name, status badge (Active/Cancelled/At Risk/Free Trial/On Demand), next billing date, Change Plan and Cancel Plan buttons with AlertDialog confirmation
- **CreditBalanceSection**: Displays subscription balance (X/allocation), purchased balance, and total; trial users see "Trial credits: X/Y"; on-demand users see purchased only
- **CreditPackageCard**: Inline card with credit amount, price, and Buy Credits button that redirects to Stripe checkout via POST /credits/purchase
- **BillingHistoryTable**: Payment history table with Date/Type/Amount/Status columns, status badges (Paid/Failed/Refunded), empty state, error state with retry

### Task 2: Billing Page with Post-Stripe Redirects (6599791)
- **/settings/billing** page composing all 4 sections in stacked vertical layout (space-y-8)
- Post-Stripe redirect handling: session_id param shows "Subscription activated!" toast, topup=success shows "Credits added!" toast
- Query invalidation on redirect: subscription, credits/balance, auth/me, billing-history
- Buy Credits section hidden for trial users via useTrialState
- Suspense wrapper for useSearchParams compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created dependency hooks (useSubscription, useTrialState) and updated UserResponse type**
- **Found during:** Task 1
- **Issue:** Plan 03 creates useSubscription.ts and useTrialState.ts, but Plan 04 runs in parallel and these files don't exist in the worktree yet. Additionally, UserResponse type was missing user_class and trial_expires_at fields needed by useTrialState.
- **Fix:** Created both hooks matching Plan 03 spec, added user_class and trial_expires_at to UserResponse interface in auth.ts
- **Files modified:** frontend/src/hooks/useSubscription.ts, frontend/src/hooks/useTrialState.ts, frontend/src/types/auth.ts
- **Commit:** 1a41224

## Known Stubs

None - all components are wired to real API hooks with proper data flow.

## Self-Check: PASSED

All 10 created/modified files verified present. Both commit hashes (1a41224, 6599791) verified in git log. TypeScript compiles clean.
