# Phase 28: Platform Config - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Admins can configure platform behavior at runtime — signup mode, default tier, invite expiry, credit policies, cost per message — without redeployment. Tier definitions come from `user_classes.yaml` (read-only); admin can view tiers with user counts and assign/change a user's tier. No admin-editable credit overrides per tier in this phase.

</domain>

<decisions>
## Implementation Decisions

### Settings API design
- Claude's Discretion: API shape (single flat endpoint vs grouped by domain) — pick what fits existing codebase patterns
- Claude's Discretion: Update style (partial vs full object) — pick what works best with key-value table design
- Claude's Discretion: Validation approach — pick safest option for platform config
- Claude's Discretion: Response metadata (values only vs values + last_modified) — pick based on admin frontend needs in Phase 31

### Signup mode behavior
- When signup is disabled, registration page still renders but form is hidden/disabled, replaced with message: "Thank you for your interest. We are currently open for beta test invitees only. Please send us an email as per the contact if you are interested to participate."
- Signup toggle takes effect immediately — no grace period. If someone submits the form after toggle, they get rejected
- Default tier for new signups (public or invite) is configurable in platform settings (not hardcoded to free)

### Tier management flow
- Tier credit allocations are read-only from `user_classes.yaml` — no admin override through platform_settings in this phase
- Admin can view tier summary: tier name, credit allocation (from yaml), and user count per tier
- Admin can assign/change a user's tier
- When admin changes a user's tier, their credit balance resets to the new tier's allocation
- Tier allocation changes (yaml edits) apply to existing users on next scheduled reset only, not immediately
- Individual per-user credit adjustments remain available via Phase 27's admin credit endpoints

### Claude's Discretion
- Settings API shape and update patterns
- Validation strategy
- Response metadata structure
- Cache invalidation approach (30s TTL already decided in architecture)

</decisions>

<specifics>
## Specific Ideas

- Signup disabled message is specific and branded: mentions beta test, invitees only, directs to contact email
- Registration page should feel informative, not like an error — user sees the page with the message, not a redirect

</specifics>

<deferred>
## Deferred Ideas

- Admin-editable credit overrides per tier via platform_settings UI — deferred to future milestone. For now, tier credit allocations can only be changed by editing `user_classes.yaml`

</deferred>

---

*Phase: 28-platform-config*
*Context gathered: 2026-02-16*
