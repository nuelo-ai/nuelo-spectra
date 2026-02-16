# Phase 30: Invitation System - Context

**Gathered:** 2026-02-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Admins can invite users via email with time-limited single-use links. Invited users can register even when public signup is disabled. Covers: invite creation, email delivery, invite registration flow, invite management (view/revoke/resend). Does NOT cover: Google OAuth integration, bulk invites, or onboarding flows beyond registration.

</domain>

<decisions>
## Implementation Decisions

### Invite email content
- Professional tone — formal, clean ("You've been invited to join Spectra")
- Minimal content — just the invite link and expiry date, no platform description or inviter name
- Styled HTML template — branded header, CTA button for the link, footer (consistent with existing email templates)
- No personal message field — standard template only, keeps emails consistent

### Registration experience
- Form fields: display name + password only (email pre-filled and locked from invite token)
- Auto-login after registration — user lands directly in the main app, no manual login step
- Welcome variant page — header says "You've been invited to Spectra" to differentiate from public signup
- No email verification required — the invite link itself proves email ownership

### Admin invite management
- Single invite at a time — one email per invite action, no bulk
- Default platform tier — invited users get the default user class from platform_settings; admin can change tier after registration
- Three invite statuses: Pending, Accepted, Expired (revoked invites become Expired)
- Fresh token on resend — old token invalidated, new token with full expiry window

### Edge cases & policies
- Already-registered email: block with error — "This email is already registered"
- Duplicate pending invite: warning shown to admin, option to resend or cancel
  - Resend cooldown: 10 minutes minimum between resends for same email
  - Resend invalidates previous token (fresh token generated)
- Expired/revoked link: error message — "This invite has expired. Contact your administrator for a new one."
- Configurable limit on total pending invites (platform setting)

### Claude's Discretion
- HTML email template design details
- Exact invite token format and hashing implementation
- Registration form validation rules
- Default pending invite limit value
- Invite expiry default (7 days per requirements, but configurable)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- Google OAuth + invite interaction — when OAuth is added, need to decide: does an invite lock to a specific email, or can the user register with a Google account on a different email? Email binding policy TBD in future OAuth phase.
- Bulk invites (paste/upload multiple emails) — could be added later if single invite proves insufficient

</deferred>

---

*Phase: 30-invitation-system*
*Context gathered: 2026-02-16*
