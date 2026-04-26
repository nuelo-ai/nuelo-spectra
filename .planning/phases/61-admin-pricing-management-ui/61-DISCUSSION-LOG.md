# Phase 61: Admin Pricing Management UI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 61-admin-pricing-management-ui
**Areas discussed:** Admin pricing layout, Config vs DB display, Reset UX and safety, Dynamic plan selection page, Credit package editing UX, Stripe readiness feedback, Backend API contracts

---

## Admin Pricing Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Extend billing-settings page | Add credit packages below existing subscription pricing. Single page. | ✓ |
| Tabs on billing-settings | Add tabs: Subscription Pricing, Credit Packages, Settings. | |
| Separate pages | Keep billing-settings, add new /credit-packages page. | |

**User's choice:** Extend billing-settings page
**Notes:** None

### Page Order

| Option | Description | Selected |
|--------|-------------|----------|
| After subscription pricing | Sub Pricing → Credit Packages → Monetization → Trial Settings | |
| After monetization toggle | Sub Pricing → Monetization → Trial Settings → Credit Packages | |
| You decide | Claude picks | |

**User's choice:** Custom — Monetization Toggle → Subscription Pricing → Credit Packages. User corrected that there is no Trial Settings on this page (confirmed by reading the actual code).

### Page Title

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 'Billing Settings' | Current name, broad enough | ✓ |
| Rename to 'Pricing & Billing' | More descriptive, needs nav update | |

**User's choice:** Keep 'Billing Settings'

---

## Config vs DB Display

| Option | Description | Selected |
|--------|-------------|----------|
| Inline hint under each field | "Default: $29.00" hint under each input | ✓ |
| Side-by-side columns in a table | Table with Config Default, Current Value, Status columns | |
| Editable fields with change indicator | Colored dot/badge on modified fields | |

**User's choice:** Inline hint under each field

### Modified Indicator

| Option | Description | Selected |
|--------|-------------|----------|
| No indicator, just the hint | Hint is enough. Clean UI. | ✓ |
| Amber dot or 'Modified' badge | Visual cue when value differs from default | |

**User's choice:** No indicator, just the hint

---

## Reset UX and Safety

| Option | Description | Selected |
|--------|-------------|----------|
| One reset button per section | Per-section reset at bottom of each card. Granular. | ✓ |
| Single global reset button | One button for all pricing. | |
| Per-field reset icons | Individual reset icon per field. | |

**User's choice:** One reset button per section, with confirmation dialog that explains impact AND requires password re-entry.
**Notes:** User added requirement that ALL pricing changes (edits AND resets) must have the same confirmation + password pattern, not just resets.

### Password Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Inline password field in dialog | Password in the confirmation dialog, sent with request. | ✓ |

**User's choice:** Inline password field in dialog

---

## Dynamic Plan Selection Page

### Plan Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| Config-driven features | Add `features:` list to each tier in user_classes.yaml | ✓ |
| Keep hardcoded features, dynamic pricing only | Backend hardcodes features, reads pricing from DB | |

**User's choice:** Config-driven features
**Notes:** User confirmed understanding that "features" are user-facing plan benefit bullets shown to consumers on the Plan Selection page.

### Billing Page Credit Packages

| Option | Description | Selected |
|--------|-------------|----------|
| Dynamic credit package cards | Cards from database with name, price, credits, Buy button | ✓ |
| Keep current layout, just use DB data | Swap hardcoded values for DB-driven | |

**User's choice:** Dynamic credit package cards

---

## Credit Package Editing UX

| Option | Description | Selected |
|--------|-------------|----------|
| Inline editable card rows | Edit in place, no modal | |
| Click-to-edit modal | Click package to open modal/dialog form | ✓ |
| Expandable accordion rows | Collapsed rows, click to expand | |

**User's choice:** Click-to-edit modal — AND apply the same pattern to subscription pricing editing for consistency (replace current inline inputs)
**Notes:** Credit package cards show full details in view mode: name, price, credits, display_order, active status, Stripe Price ID (read-only). User confirmed Stripe Price ID is never admin-editable.

---

## Stripe Readiness Feedback

| Option | Description | Selected |
|--------|-------------|----------|
| Inline warning on toggle | Warning below toggle when Stripe not ready. Toggle still clickable. | |
| Pre-check before toggle | Disable toggle, show checklist of missing items. Enable when ready. | ✓ |
| Status banner at top of page | Persistent amber banner. | |

**User's choice:** Pre-check with checklist — most informative approach per Claude's recommendation.

---

## Backend API Contracts

### Reset Endpoints

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated reset endpoints | Separate POST endpoints per section | |
| Single reset with scope | One endpoint with scope parameter | |
| You decide | Claude picks | ✓ |

**User's choice:** Claude's discretion

### Credit Package Router

| Option | Description | Selected |
|--------|-------------|----------|
| Extend billing-settings router | Add to existing router | |
| New credit-packages router | Separate router | |
| You decide | Claude picks | ✓ |

**User's choice:** Claude's discretion

### Password API

| Option | Description | Selected |
|--------|-------------|----------|
| Password in each request | Send with save/reset body | ✓ |
| Dedicated verify endpoint | Two-step: verify → token → action | |

**User's choice:** Password in each request — Claude recommended as simpler and more secure (atomic verification, no token replay risk)

---

## Claude's Discretion

- Router organization for credit package endpoints
- Reset endpoint design (dedicated vs scope parameter)
- Modal component implementation details
- API response shapes and error formats
- Impact text wording in confirmation dialogs
- Stripe readiness checklist UI component design

## Deferred Ideas

- Admin creating new credit packages from scratch (out of scope per REQUIREMENTS.md)
- Admin deleting credit packages (deactivate via is_active flag instead)
- Admin-editable feature bullets in UI (features are config-driven)
- Stripe webhook status dashboard
