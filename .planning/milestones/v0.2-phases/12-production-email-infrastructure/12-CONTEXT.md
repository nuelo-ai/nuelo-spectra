# Phase 12: Production Email Infrastructure - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace dev-mode console logging with real SMTP email delivery for password reset flow. Professional HTML email templates, production-ready SMTP configuration, and secure reset link handling. No new email-triggered features (e.g., welcome emails, notifications) — only password reset.

</domain>

<decisions>
## Implementation Decisions

### Email template & branding
- HTML email with plain text fallback (multipart MIME)
- Minimal branding — app name ("Spectra") in header + styled reset button, no logo image, no footer links
- Professional & concise tone — straight to the point, no casual language
- Personalized greeting using first name: "Hi [First Name],"

### SMTP configuration & fallback
- Console logging fallback when SMTP is not configured — keeps current dev-mode behavior for local development
- Validate SMTP connection at startup — test connection, log success/failure, but don't block app from starting
- All SMTP settings via environment variables only: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
- Sender address configurable via .env: SMTP_FROM_EMAIL and SMTP_FROM_NAME

### Reset link behavior
- 10-minute expiry on reset links
- Single-use links — invalidated after first successful password change
- Expired/invalid link shows error page with "Request new reset" button (not redirect to login)
- New reset request invalidates all previous unused tokens for that email — only latest link works

### Security & rate limiting
- No email enumeration — always respond "Check your email" whether account exists or not
- Per-email cooldown: same email can only request reset once per 2 minutes
- Structured JSON logging for all email events (send attempts, successes, failures) — metadata only, no email content

### Claude's Discretion
- HTML template implementation approach (inline CSS vs template engine)
- Token generation method (JWT vs random token in DB)
- Exact email copy wording
- SMTP connection pooling strategy
- Error page styling

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-production-email-infrastructure*
*Context gathered: 2026-02-09*
