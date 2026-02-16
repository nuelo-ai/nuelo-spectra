# Phase 29: User Management - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Admin API endpoints for finding, inspecting, and managing any user account on the platform. Includes user listing with search/filter, user detail with activity data, individual account actions (activate/deactivate, password reset, tier change, credit adjustment, delete), and bulk operations on multiple users. The admin frontend UI for these endpoints is Phase 31.

</domain>

<decisions>
## Implementation Decisions

### User listing & search
- Offset-based pagination with classic page numbers (page 1, 2, 3...)
- 20 users per page (fixed default)
- Search uses partial match (ILIKE contains) on email and name fields
- Multiple sort columns supported: signup date, last login, name, credit balance
- Filters: active/inactive status, user class (tier), signup date range

### User detail view
- Summary counts: total files, total sessions, total messages
- Activity timeline computed on-the-fly from existing tables (messages, sessions grouped by month) — important for tracking monthly active user patterns
- Last login timestamp + last message sent tracked for activity visibility
- API shape for detail vs activity endpoints: Claude's discretion (single vs split endpoints based on response size)

### Account actions — Deactivation
- Deactivating a user triggers immediate logout — all tokens invalidated, user kicked out immediately
- Deactivation is a soft flag (user record preserved, can be reactivated)

### Account actions — Deletion
- Hard delete immediately when admin confirms — user and all their data (files, sessions, messages, credits) permanently removed
- Anonymized audit log entry created before deletion (e.g., "deleted_user_123" replaces actual email/name in audit references)
- Deletion confirmation requires a random 6-character alphanumeric challenge code displayed to admin; admin must manually type it to confirm
- Paste disabled on the confirmation text field to ensure deliberate action

### Account actions — Tier change
- Changing a user's tier always resets their credit balance to the new tier's allocation (clean slate)
- This applies to both upgrades and downgrades

### Account actions — Password reset
- Admin triggers password reset which sends a reset email to the user via existing SMTP service
- Admin does not set the password directly

### Bulk operations
- Full bulk actions supported: bulk activate/deactivate, bulk tier change, bulk credit adjustment, bulk delete
- User selection via checkboxes on the user list (manual selection, not filter-based)
- Bulk credit adjustment supports both modes: set exact amount OR add/deduct a delta from current balance
- Bulk delete uses the same 6-char confirmation challenge as individual delete (paste disabled)

### Claude's Discretion
- API endpoint structure (single detail endpoint vs split endpoints for profile/activity)
- Exact query optimization for activity timeline aggregation
- Error response format and validation patterns
- How token invalidation is implemented for immediate logout on deactivation

</decisions>

<specifics>
## Specific Ideas

- Activity timeline is specifically for tracking monthly active users (MAU) — the admin wants to see how active each user has been over time
- Deletion challenge: the random 6-char alphanumeric code approach with paste-disabled input field — same pattern for both individual and bulk delete

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 29-user-management*
*Context gathered: 2026-02-16*
