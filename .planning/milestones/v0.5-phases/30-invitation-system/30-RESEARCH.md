# Phase 30: Invitation System - Research

**Researched:** 2026-02-16
**Domain:** Email invitation system, admin management, token-based registration
**Confidence:** HIGH

## Summary

Phase 30 adds an admin invitation system to Spectra. The existing codebase already provides nearly all the infrastructure needed: the `invitations` table and `Invitation` model already exist (created in the admin portal migration `dfe836ff84e9`), the email service with Jinja2 HTML templates and aiosmtplib is operational (used for password resets), the token hashing pattern (SHA-256 with `secrets.token_urlsafe`) is established, and the platform settings system already has `invite_expiry_days` configured with a default of 7 days.

The primary work is: (1) creating the invitation service layer with create/list/revoke/resend logic, (2) adding an admin invitations router, (3) building the invite email HTML/text templates, (4) creating or modifying the public-facing invite registration endpoint and frontend page, and (5) adding a `max_pending_invites` platform setting. The existing `auth/signup` endpoint already has partial invite token validation code (lines 78-102 in `routers/auth.py`) that validates invite tokens when public signup is disabled.

**Primary recommendation:** Follow existing patterns exactly -- new `routers/admin/invitations.py` router, new `services/admin/invitations.py` service, new `schemas/invitation.py` schemas, new email templates under `templates/email/`, and a dedicated `/auth/invite-register` endpoint for invite-based registration (separate from the existing signup to match the "display name + password only" decision).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Invite email content
- Professional tone -- formal, clean ("You've been invited to join Spectra")
- Minimal content -- just the invite link and expiry date, no platform description or inviter name
- Styled HTML template -- branded header, CTA button for the link, footer (consistent with existing email templates)
- No personal message field -- standard template only, keeps emails consistent

#### Registration experience
- Form fields: display name + password only (email pre-filled and locked from invite token)
- Auto-login after registration -- user lands directly in the main app, no manual login step
- Welcome variant page -- header says "You've been invited to Spectra" to differentiate from public signup
- No email verification required -- the invite link itself proves email ownership

#### Admin invite management
- Single invite at a time -- one email per invite action, no bulk
- Default platform tier -- invited users get the default user class from platform_settings; admin can change tier after registration
- Three invite statuses: Pending, Accepted, Expired (revoked invites become Expired)
- Fresh token on resend -- old token invalidated, new token with full expiry window

#### Edge cases & policies
- Already-registered email: block with error -- "This email is already registered"
- Duplicate pending invite: warning shown to admin, option to resend or cancel
  - Resend cooldown: 10 minutes minimum between resends for same email
  - Resend invalidates previous token (fresh token generated)
- Expired/revoked link: error message -- "This invite has expired. Contact your administrator for a new one."
- Configurable limit on total pending invites (platform setting)

### Claude's Discretion
- HTML email template design details
- Exact invite token format and hashing implementation
- Registration form validation rules
- Default pending invite limit value
- Invite expiry default (7 days per requirements, but configurable)

### Deferred Ideas (OUT OF SCOPE)
- Google OAuth + invite interaction -- when OAuth is added, need to decide: does an invite lock to a specific email, or can the user register with a Google account on a different email? Email binding policy TBD in future OAuth phase.
- Bulk invites (paste/upload multiple emails) -- could be added later if single invite proves insufficient
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INVITE-01 | Admin can invite a user by entering their email address | Admin invitations router + service; check existing user table for duplicates; check pending invites for duplicates |
| INVITE-02 | System generates a unique, time-limited invite link (default 7 days, configurable) | Reuse `email.create_reset_token()` pattern (secrets.token_urlsafe + SHA-256); read `invite_expiry_days` from platform_settings (already exists, default=7) |
| INVITE-03 | Invite email sent via existing SMTP/email service with branded template | New Jinja2 HTML + text templates under `app/templates/email/`; new `send_invite_email()` function in email service; follows existing password_reset email pattern |
| INVITE-04 | Invited user clicks link and sees registration form with pre-filled, locked email | New frontend page at `/invite/[token]`; API endpoint to validate token and return email; email field rendered as read-only |
| INVITE-05 | Invited user completes registration (sets password, name) via separate invite signup endpoint | New `POST /auth/invite-register` endpoint; creates user with default_user_class from platform_settings; auto-login (returns TokenResponse) |
| INVITE-06 | Admin can view list of pending invitations (email, date, expiry, status) | Admin GET `/api/admin/invitations` with status filter and pagination; query Invitation model |
| INVITE-07 | Admin can revoke or resend pending invitations | Revoke: set status to "expired"; Resend: generate fresh token, reset expires_at, send new email; enforce 10-min cooldown |
| INVITE-08 | Invite links are single-use (invalidated after registration, token hashed in DB) | Token hash stored as SHA-256 in `token_hash` column; on registration, set status="accepted" + accepted_at; existing code in auth.py already does partial version of this |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | API framework, admin + public endpoints | Already used throughout |
| SQLAlchemy 2.0 (async) | existing | ORM, Invitation model already exists | Already used throughout |
| aiosmtplib | existing | Async SMTP email delivery | Already used for password reset emails |
| Jinja2 | existing | HTML/text email template rendering | Already configured in email service |
| Pydantic v2 | existing | Request/response schemas | Already used throughout |
| secrets + hashlib | stdlib | Token generation + SHA-256 hashing | Already used in email.py (create_reset_token) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| email-validator | existing | EmailStr validation in Pydantic schemas | Already a dependency |
| Alembic | existing | Database migrations (if schema changes needed) | Only if adding new columns/settings |

### Alternatives Considered
None needed -- all required libraries are already in the project.

**Installation:**
No new dependencies required.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── models/invitation.py          # EXISTS - Invitation model
├── schemas/invitation.py         # NEW - invite request/response schemas
├── services/admin/invitations.py # NEW - invitation business logic
├── services/email.py             # MODIFY - add send_invite_email()
├── routers/admin/invitations.py  # NEW - admin invite management endpoints
├── routers/admin/__init__.py     # MODIFY - register invitations router
├── routers/auth.py               # MODIFY - add /auth/invite-register endpoint
├── templates/email/
│   ├── invite.html               # NEW - branded HTML invite email
│   └── invite.txt                # NEW - plain text invite email
├── services/platform_settings.py # MODIFY - add max_pending_invites default + validation
└── schemas/auth.py               # MODIFY - add InviteRegisterRequest schema
frontend/src/
├── app/(auth)/invite/[token]/page.tsx  # NEW - invite registration page
└── types/auth.ts                       # MODIFY - add invite types
```

### Pattern 1: Token Generation and Hashing (Existing Pattern)
**What:** Generate cryptographic token, store SHA-256 hash in DB, send raw token to user
**When to use:** Any single-use secure link (already used for password resets)
**Example (from existing `app/services/email.py`):**
```python
def create_reset_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash
```
**Recommendation:** Reuse `create_reset_token()` directly for invite tokens. Same security properties needed: cryptographic randomness, SHA-256 hashing, constant-time comparison. Rename to `create_secure_token()` or just reuse as-is since it is a generic token utility.

### Pattern 2: Admin Router with Audit Logging (Existing Pattern)
**What:** Admin endpoint -> service function -> audit log -> commit
**When to use:** All admin mutation endpoints
**Example (from existing `routers/admin/users.py`):**
```python
@router.post("/{user_id}/deactivate", response_model=ActivateDeactivateResponse)
async def deactivate_user_endpoint(
    user_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> ActivateDeactivateResponse:
    try:
        await deactivate_user(db, user_id)
    except ValueError as e:
        # error handling...

    client_ip = request.client.host if request.client else None
    await log_admin_action(db, admin_id=current_admin.id, action="deactivate_user", ...)
    await db.commit()
    return ActivateDeactivateResponse(...)
```

### Pattern 3: Platform Settings with Cache (Existing Pattern)
**What:** Key-value settings in DB with 30s TTL cache, JSON-encoded values
**When to use:** Configurable limits and defaults
**Example:** `invite_expiry_days` already exists in `DEFAULTS` dict. Add `max_pending_invites` in same pattern.

### Pattern 4: Email Sending with Dev Mode Fallback (Existing Pattern)
**What:** Check `is_smtp_configured()`, log to console in dev, send via SMTP in prod
**When to use:** All email sending functions
**Example (from existing `email.py`):**
```python
if not is_smtp_configured(settings):
    logger.info("Invite email (dev mode)", ...)
    return True
# Production: render Jinja2 template, build EmailMessage, send via aiosmtplib
```

### Pattern 5: Separate Invite Registration Endpoint
**What:** New `POST /auth/invite-register` rather than overloading existing signup
**Why:** The existing signup has `invite_token` as an optional field but the CONTEXT decisions require a different form (display name only, no first/last split; pre-filled locked email). A dedicated endpoint is cleaner.
**However:** Note that the existing `SignupRequest` already has `invite_token: str | None = None` and `auth.py` lines 78-102 already validate invite tokens. The planner should decide whether to:
  - (A) Create a completely separate endpoint `/auth/invite-register` with its own schema (cleaner, matches locked decision of "display name + password only")
  - (B) Enhance the existing `/auth/signup` endpoint (less code, but more complex conditional logic)
**Recommendation:** Option A -- separate endpoint. The form fields differ (display name vs first/last), and the flow differs (no email verification, token validation required). Keep the existing partial invite code in signup for backward compatibility or remove it.

### Anti-Patterns to Avoid
- **Storing raw tokens in DB:** Always hash with SHA-256 before storing. Raw token goes only to user via email link.
- **Checking token expiry only in DB query:** Also check programmatically after fetching the row -- defense in depth.
- **Committing before audit log:** Always add audit log entry before `db.commit()` so it is in the same transaction.
- **Sending email inside DB transaction:** Send email after commit to avoid long-held transactions. If email fails, the invite record exists but email wasn't sent -- admin can resend.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secure token generation | Custom random strings | `secrets.token_urlsafe(32)` | Cryptographically secure, URL-safe, 256 bits of entropy |
| Token hashing | Custom hash function | `hashlib.sha256` + `secrets.compare_digest` | Standard, timing-safe |
| Email sending | Custom SMTP code | Existing `aiosmtplib` integration in `email.py` | Already handles TLS, auth, error handling |
| HTML email rendering | String concatenation | Existing Jinja2 `_jinja_env` | Auto-escaping, template inheritance ready |
| Cooldown tracking | DB-based cooldown | In-memory dict with timestamps (like `_reset_cooldowns` in auth.py) | Simple, fast, no DB overhead for rate limiting |

**Key insight:** The entire invitation infrastructure is nearly identical to the password reset flow. Token generation, hashing, email sending, and single-use validation are all established patterns. The main new work is the admin management layer and the invite-specific registration endpoint.

## Common Pitfalls

### Pitfall 1: Race Condition on Invite Acceptance
**What goes wrong:** Two concurrent requests try to register with the same invite token. Both pass validation, both create users.
**Why it happens:** SELECT + UPDATE is not atomic without locking.
**How to avoid:** Use `SELECT ... FOR UPDATE` (pessimistic lock) when validating the invite token during registration, OR rely on the unique email constraint on the users table to fail the second attempt gracefully.
**Warning signs:** Duplicate user creation errors in production logs.

### Pitfall 2: Email Enumeration via Invite Endpoint
**What goes wrong:** Admin invite endpoint reveals whether an email is already registered vs already invited.
**Why it happens:** Different error messages for "already registered" vs "already has pending invite."
**How to avoid:** This is intentional for admins (they need to know). The public-facing endpoints must NOT reveal user existence. The invite-register endpoint should only accept valid tokens, not take email as input (email comes from the token lookup).
**Warning signs:** N/A -- this is by design for admin endpoints.

### Pitfall 3: Stale Expiry After Resend
**What goes wrong:** Old token still works after resend because only a new row was created, old row not invalidated.
**Why it happens:** Forgot to expire/invalidate old invitation record on resend.
**How to avoid:** Per locked decision, resend MUST: (1) set old invitation status to "expired", (2) create new invitation with fresh token and full expiry window. Use a single transaction.
**Warning signs:** Multiple pending invitations for same email.

### Pitfall 4: Missing Platform Setting Registration
**What goes wrong:** `max_pending_invites` not in `DEFAULTS` dict, so `get()` returns `None`.
**Why it happens:** Forgot to add new setting key to `DEFAULTS` and `VALID_KEYS` in platform_settings.py.
**How to avoid:** Add `max_pending_invites` to `DEFAULTS` dict and update `validate_setting()` function in `services/platform_settings.py`. Also add to `SettingsResponse` and `SettingsUpdateRequest` schemas.
**Warning signs:** Setting returns None, no validation on update.

### Pitfall 5: Display Name vs First/Last Name Mismatch
**What goes wrong:** The invite registration form asks for "display name" (single field) but the User model has `first_name` and `last_name` (two fields).
**Why it happens:** Locked decision says "display name + password only" but User model expects first/last.
**How to avoid:** Store display name as `first_name` with `last_name` set to `None`. Or parse if space-separated. Recommend: single field mapped to `first_name`, `last_name = None`. Document this clearly.
**Warning signs:** Empty last_name for all invited users.

## Code Examples

### Invite Service - Create Invitation
```python
# services/admin/invitations.py
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.invitation import Invitation
from app.models.user import User
from app.services.email import create_reset_token
from app.services import platform_settings

async def create_invitation(
    db: AsyncSession,
    email: str,
    admin_id: UUID,
    settings: Settings,
) -> dict:
    """Create a new invitation. Returns dict with invite details + raw token."""

    # Check if email already registered
    existing_user = await db.execute(
        select(User).where(User.email == email)
    )
    if existing_user.scalar_one_or_none():
        raise ValueError("This email is already registered")

    # Check for existing pending invite
    existing_invite = await db.execute(
        select(Invitation).where(
            Invitation.email == email,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.now(timezone.utc),
        )
    )
    pending = existing_invite.scalar_one_or_none()
    if pending:
        raise DuplicateInviteError(email=email, invite_id=pending.id)

    # Check max pending invites limit
    max_pending = await platform_settings.get(db, "max_pending_invites")
    if max_pending:
        count_result = await db.execute(
            select(func.count()).select_from(Invitation).where(
                Invitation.status == "pending",
                Invitation.expires_at > datetime.now(timezone.utc),
            )
        )
        current_count = count_result.scalar()
        if current_count >= max_pending:
            raise ValueError(f"Maximum pending invites ({max_pending}) reached")

    # Generate token
    raw_token, token_hash = create_reset_token()

    # Read expiry from platform settings
    expiry_days = await platform_settings.get(db, "invite_expiry_days")

    invitation = Invitation(
        email=email,
        token_hash=token_hash,
        invited_by=admin_id,
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days),
    )
    db.add(invitation)

    return {
        "invitation": invitation,
        "raw_token": raw_token,
    }
```

### Invite Email Template (HTML)
```html
<!-- templates/email/invite.html -->
<!-- Follow exact same structure as password_reset.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>You've been invited to Spectra</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, ...same as reset...">
  <table role="presentation" width="100%" ...same structure...>
    <!-- Header: Spectra brand, same blue #2563eb -->
    <!-- Body: "You've been invited to join Spectra" -->
    <!-- CTA button: "Accept Invitation" -->
    <!-- Link text fallback -->
    <!-- Expiry notice: "This invitation expires on {{ expiry_date }}" -->
    <!-- No footer text about ignoring (unlike password reset) -->
  </table>
</body>
</html>
```

### Invite Registration Endpoint
```python
# In routers/auth.py
@router.post("/invite-register", response_model=TokenResponse, status_code=201)
async def invite_register(
    body: InviteRegisterRequest,  # token, display_name, password
    db: DbSession,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Register via invite token. No auth required."""
    # Hash token, look up invitation
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()
    result = await db.execute(
        select(Invitation).where(
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.now(timezone.utc),
        ).with_for_update()  # Prevent race condition
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(403, "This invite has expired. Contact your administrator for a new one.")

    # Mark accepted
    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(timezone.utc)

    # Create user (email from invitation, display_name -> first_name)
    # ... create user, auto-login, return tokens
```

### Token Validation Endpoint (for frontend pre-fill)
```python
@router.get("/invite-validate")
async def validate_invite_token(
    token: str,
    db: DbSession,
) -> dict:
    """Validate invite token and return email for pre-fill. Public endpoint."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(
        select(Invitation).where(
            Invitation.token_hash == token_hash,
            Invitation.status == "pending",
            Invitation.expires_at > datetime.now(timezone.utc),
        )
    )
    invitation = result.scalar_one_or_none()
    if not invitation:
        raise HTTPException(400, "This invite has expired. Contact your administrator for a new one.")
    return {"email": invitation.email, "valid": True}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Store raw tokens in DB | Store SHA-256 hash of token | Standard practice | Already implemented in codebase |
| Synchronous SMTP | Async SMTP (aiosmtplib) | Already in place | Non-blocking email delivery |
| Inline HTML strings | Jinja2 templates | Already in place | Maintainable email templates |

**Deprecated/outdated:**
- The partial invite token validation in `routers/auth.py` lines 78-102 was added during the admin portal phase but is incomplete. It validates tokens during signup but does not handle the "display name only" registration form or auto-login properly. This should either be replaced by the dedicated `/auth/invite-register` endpoint or left as a fallback.

## Existing Infrastructure Summary

### Already Exists (No Changes Needed)
1. **`Invitation` model** (`models/invitation.py`) -- complete with id, email, token_hash, invited_by, status, expires_at, accepted_at, created_at
2. **`invitations` table** -- created by migration `dfe836ff84e9` with indexes on email and token_hash (unique)
3. **`invite_expiry_days` platform setting** -- default 7, validated 1-365, in DEFAULTS dict
4. **Token utilities** -- `create_reset_token()` and `verify_token_hash()` in email.py
5. **Email infrastructure** -- aiosmtplib, Jinja2 templates, dev mode fallback
6. **Admin auth dependency** -- `CurrentAdmin` with defense-in-depth
7. **Audit logging** -- `log_admin_action()` utility
8. **`SignupRequest.invite_token`** -- optional field already on schema

### Needs Creation
1. **`schemas/invitation.py`** -- CreateInviteRequest, InviteResponse, InviteListResponse
2. **`schemas/auth.py` addition** -- InviteRegisterRequest (token, display_name, password)
3. **`services/admin/invitations.py`** -- create, list, revoke, resend logic
4. **`routers/admin/invitations.py`** -- admin CRUD endpoints
5. **`routers/auth.py` additions** -- `/invite-validate` GET, `/invite-register` POST
6. **`templates/email/invite.html`** -- branded invite email HTML
7. **`templates/email/invite.txt`** -- plain text invite email
8. **`services/email.py` addition** -- `send_invite_email()` function
9. **`frontend/src/app/(auth)/invite/[token]/page.tsx`** -- invite registration page

### Needs Modification
1. **`services/platform_settings.py`** -- add `max_pending_invites` to DEFAULTS + validate_setting
2. **`schemas/platform_settings.py`** -- add `max_pending_invites` to SettingsResponse + SettingsUpdateRequest
3. **`routers/admin/__init__.py`** -- register invitations router

## Design Decisions (Claude's Discretion)

### Token Format
**Recommendation:** Use `secrets.token_urlsafe(32)` (same as password reset). Produces 43-character URL-safe base64 string with 256 bits of entropy. Hash with SHA-256 for storage. This is already proven in the codebase.

### Default Pending Invite Limit
**Recommendation:** 50 pending invites. Reasonable for single-invite-at-a-time workflow. Configurable via `max_pending_invites` platform setting.

### Registration Form Validation
**Recommendation:**
- Display name: required, 1-100 characters, trimmed
- Password: required, minimum 8 characters (matches existing signup)
- Map display name to `first_name` field on User model, set `last_name = None`

### Invite Expiry
**Recommendation:** 7 days default (already configured in platform_settings). Configurable 1-365 days (already validated).

### HTML Email Template
**Recommendation:** Match existing `password_reset.html` structure exactly:
- Same branded header with blue "Spectra" text (#2563eb)
- Same card layout (560px, white background, border-radius: 8px)
- Subject: "You've been invited to join Spectra"
- Body: brief invitation text, CTA button "Accept Invitation", link fallback, expiry date
- No "if you didn't request this" text (unlike password reset)

## Open Questions

1. **Clean up existing partial invite code in auth.py?**
   - What we know: Lines 78-102 in `routers/auth.py` already validate invite tokens during signup
   - What's unclear: Should this be removed when the dedicated `/invite-register` endpoint is added?
   - Recommendation: Keep it for backward compatibility but route all new invite flows through `/invite-register`. The existing code serves as a safety net if someone bookmarks the old signup URL with an invite token.

2. **Expired invite cleanup**
   - What we know: Invitations with past `expires_at` and status "pending" are effectively expired
   - What's unclear: Should there be a background job to mark them as "expired" status, or just filter by `expires_at` in queries?
   - Recommendation: Filter by `expires_at` in queries (no background job needed). Optionally mark status as "expired" when encountered during list queries for admin UI display clarity.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `backend/app/services/email.py` -- existing token + email patterns
- Codebase inspection: `backend/app/models/invitation.py` -- existing Invitation model
- Codebase inspection: `backend/app/services/platform_settings.py` -- existing invite_expiry_days setting
- Codebase inspection: `backend/app/routers/auth.py` -- existing partial invite token validation
- Codebase inspection: `backend/app/routers/admin/users.py` -- admin router pattern with audit logging
- Codebase inspection: `backend/app/templates/email/password_reset.html` -- email template pattern
- Codebase inspection: `backend/alembic/versions/dfe836ff84e9` -- invitations table schema

### Secondary (MEDIUM confidence)
- Python `secrets` module documentation -- token_urlsafe produces URL-safe base64 with 32 bytes = 256 bits entropy
- SHA-256 hashing with `secrets.compare_digest` -- standard timing-safe comparison

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project, no new dependencies
- Architecture: HIGH -- follows exact existing patterns (admin router, service, schema, email template)
- Pitfalls: HIGH -- identified from existing codebase patterns and common token-based auth issues
- Existing infrastructure: HIGH -- verified by reading actual source code

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable patterns, no external dependency changes)
