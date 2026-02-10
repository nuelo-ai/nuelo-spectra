# Phase 12: Production Email Infrastructure - Research

**Researched:** 2026-02-09
**Domain:** SMTP email delivery, password reset tokens, HTML email templates
**Confidence:** HIGH

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Email template & branding:**
- HTML email with plain text fallback (multipart MIME)
- Minimal branding -- app name ("Spectra") in header + styled reset button, no logo image, no footer links
- Professional & concise tone -- straight to the point, no casual language
- Personalized greeting using first name: "Hi [First Name],"

**SMTP configuration & fallback:**
- Console logging fallback when SMTP is not configured -- keeps current dev-mode behavior for local development
- Validate SMTP connection at startup -- test connection, log success/failure, but don't block app from starting
- All SMTP settings via environment variables only: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
- Sender address configurable via .env: SMTP_FROM_EMAIL and SMTP_FROM_NAME

**Reset link behavior:**
- 10-minute expiry on reset links
- Single-use links -- invalidated after first successful password change
- Expired/invalid link shows error page with "Request new reset" button (not redirect to login)
- New reset request invalidates all previous unused tokens for that email -- only latest link works

**Security & rate limiting:**
- No email enumeration -- always respond "Check your email" whether account exists or not
- Per-email cooldown: same email can only request reset once per 2 minutes
- Structured JSON logging for all email events (send attempts, successes, failures) -- metadata only, no email content

### Claude's Discretion

- HTML template implementation approach (inline CSS vs template engine)
- Token generation method (JWT vs random token in DB)
- Exact email copy wording
- SMTP connection pooling strategy
- Error page styling

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope

</user_constraints>

## Summary

This phase replaces the existing Mailgun HTTP API-based email service (`backend/app/services/email.py`) with standard SMTP using `aiosmtplib`, and upgrades the password reset flow to use database-backed single-use tokens instead of the current JWT-only approach. The current codebase has a fully functional password reset flow (forgot-password endpoint, reset-password endpoint, JWT-based tokens with 10-minute expiry, frontend pages for both flows), but the email delivery uses `httpx` to call Mailgun's REST API -- which is vendor-locked and not working in production (diagnosed in debug sessions as never successfully sending).

The key architectural change is moving from JWT-based reset tokens (stateless, not single-use, not invalidatable) to database-backed random tokens using `secrets.token_urlsafe()`. This is required by the locked decisions: single-use links (invalidated after password change), and new requests invalidating all previous tokens. JWTs cannot satisfy these requirements without a database lookup anyway, so random tokens stored in a `password_reset_tokens` table are the correct approach. The email template will use Jinja2 (already available as a transitive dependency, v3.1.6) with inline CSS for maximum email client compatibility, loaded via `FileSystemLoader` from a `templates/` directory under the app package.

**Primary recommendation:** Use `aiosmtplib` 5.1.0 for async SMTP, `secrets.token_urlsafe(32)` with a `password_reset_tokens` database table for single-use tokens, Jinja2 `FileSystemLoader` with inline CSS for the HTML template, and a simple in-memory `dict` for the per-email 2-minute cooldown.

## Discretionary Decisions (Claude's Recommendations)

### 1. Token Generation: Database-backed random tokens (not JWT)

**Recommendation:** Use `secrets.token_urlsafe(32)` stored in a `password_reset_tokens` database table.

**Rationale:** The locked decisions require single-use links (invalidated after use) and invalidation of all previous tokens when a new request comes in. JWTs are stateless -- you cannot invalidate a JWT without a server-side store, which defeats their purpose. The current implementation uses JWT tokens (in `backend/app/utils/security.py:154-170`), which already has the 10-minute expiry but cannot enforce single-use or bulk invalidation. Random tokens stored in PostgreSQL satisfy all requirements naturally:
- Single-use: mark token as `used=True` after password change
- Invalidate previous: `UPDATE ... SET is_active=False WHERE email=X` before inserting new token
- Expiry: check `expires_at` timestamp

**Confidence:** HIGH -- this is the standard approach for password reset tokens. Multiple authoritative sources confirm database-backed tokens are preferred for revocable, single-use operations.

### 2. HTML Template: Jinja2 with inline CSS (no template engine like premailer)

**Recommendation:** Use Jinja2 `FileSystemLoader` pointing to `backend/app/templates/email/`, with all CSS written inline in the template file itself (style attributes on HTML elements). Do not add `premailer` as a dependency.

**Rationale:** The email template is a single file with minimal styling (app name header + styled button). Inline CSS is simpler and avoids the complexity of a CSS-to-inline transformation step. Premailer adds a dependency for a problem we do not have -- we only have one template with straightforward styling. Jinja2 is already installed (v3.1.6, transitive dependency of FastAPI/Starlette) and does not need to be added to `pyproject.toml`. The requirement SMTP-04 explicitly calls for Jinja2.

**Confidence:** HIGH -- Jinja2 is the standard Python template engine, already in the environment.

### 3. SMTP Connection Strategy: Connect-per-send (no pooling)

**Recommendation:** Use `aiosmtplib.send()` one-shot coroutine for each email. Do not maintain a persistent SMTP connection or pool.

**Rationale:** Password reset emails are infrequent (perhaps a few per day in a single-developer SaaS). SMTP connection establishment takes ~100-300ms, which is negligible for this use case. `aiosmtplib`'s `send()` coroutine handles the full connect/authenticate/send/disconnect lifecycle in one call. Connection pooling adds complexity (handling disconnects, keepalives, concurrency) with no measurable benefit at this scale. The `aiosmtplib` documentation explicitly notes that SMTP is a sequential protocol and recommends multiple separate connections for high-volume scenarios, not persistent connections.

**Confidence:** HIGH -- verified from aiosmtplib official docs.

### 4. Error Page Styling: Reuse existing auth page card layout

**Recommendation:** The frontend reset-password page already uses the `Card` component from shadcn/ui. Add conditional rendering: when the token is invalid/expired, show an error state within the same card with a "Request new reset" button linking to `/forgot-password`. No new page needed.

**Confidence:** HIGH -- based on direct codebase observation of `frontend/src/app/(auth)/reset-password/page.tsx`.

### 5. Per-Email Cooldown: In-memory dict with TTL

**Recommendation:** Use a simple Python `dict[str, float]` mapping email to last-request-timestamp, stored as a module-level variable in the email service or auth router. Check `time.time() - last_request < 120` before allowing a new reset request. No external dependency (no Redis, no SlowAPI).

**Rationale:** This is a single-server application (single developer, no horizontal scaling). An in-memory dict is the simplest solution. The dict naturally resets on server restart, which is acceptable -- cooldowns are a UX convenience and abuse deterrent, not a security-critical mechanism. If the app scales later, this can be replaced with Redis.

**Confidence:** HIGH -- appropriate for single-server deployment.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| aiosmtplib | >=5.1.0 | Async SMTP client | Only maintained async SMTP library for Python asyncio; Production/Stable status; MIT license |
| jinja2 | 3.1.6 (already installed) | Email HTML templating | Requirement SMTP-04; already a transitive dep of FastAPI; standard Python template engine |
| secrets (stdlib) | Python 3.12 stdlib | Secure token generation | `token_urlsafe(32)` generates 256-bit cryptographically random URL-safe tokens |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| email.message (stdlib) | Python 3.12 stdlib | Multipart MIME construction | Build HTML+plain text alternative messages with `EmailMessage.set_content()` + `add_alternative()` |
| email.mime (stdlib) | Python 3.12 stdlib | MIME message parts | Alternative to `email.message` for multipart construction |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| aiosmtplib | smtplib (stdlib) | smtplib is synchronous -- blocks the event loop in FastAPI async endpoints |
| aiosmtplib | fastapi-mail | fastapi-mail wraps aiosmtplib but adds unnecessary abstraction and config patterns that conflict with our Settings class |
| secrets.token_urlsafe | JWT (current impl) | JWTs cannot be invalidated or made single-use without a DB -- defeats their purpose |
| In-memory cooldown dict | SlowAPI / fastapi-throttle | Adds dependency for a single-endpoint rate limit; overkill for this use case |

**Installation:**
```bash
cd backend && uv add "aiosmtplib>=5.1.0"
```

Note: Jinja2 does NOT need to be added -- it is already installed as a transitive dependency. However, adding `jinja2>=3.1.0` to pyproject.toml explicitly is good practice since we now directly import it.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── config.py              # ADD: SMTP settings (smtp_host, smtp_port, smtp_user, smtp_pass, smtp_from_email, smtp_from_name)
├── main.py                # ADD: SMTP validation in lifespan startup
├── models/
│   ├── __init__.py        # ADD: import PasswordResetToken
│   └── password_reset.py  # NEW: PasswordResetToken SQLAlchemy model
├── services/
│   └── email.py           # REWRITE: Replace Mailgun with aiosmtplib + Jinja2
├── routers/
│   └── auth.py            # MODIFY: forgot_password (cooldown + DB tokens), reset_password (single-use check)
├── templates/
│   └── email/
│       ├── password_reset.html  # NEW: Jinja2 HTML template
│       └── password_reset.txt   # NEW: Jinja2 plain text template
└── utils/
    └── security.py        # MODIFY: Remove JWT password reset functions, add DB token functions
```

### Pattern 1: Database-Backed Reset Tokens
**What:** Store password reset tokens in PostgreSQL with expiry and used/active flags.
**When to use:** Any single-use, revocable token (password reset, email verification, invite links).
**Example:**
```python
# Model: backend/app/models/password_reset.py
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4
import secrets

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_password_reset_tokens_email_active", "email", "is_active"),
    )
```

### Pattern 2: SMTP Email Service with Fallback
**What:** Async SMTP sending with automatic fallback to console logging when not configured.
**When to use:** All email sending operations.
**Example:**
```python
# Service: backend/app/services/email.py
import logging
from email.message import EmailMessage
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import Settings

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
_template_dir = Path(__file__).parent.parent / "templates" / "email"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_template_dir)),
    autoescape=select_autoescape(["html"]),
)


def _is_smtp_configured(settings: Settings) -> bool:
    """Check if SMTP is properly configured (not dev mode)."""
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_pass)


async def send_password_reset_email(
    to_email: str,
    first_name: str | None,
    reset_link: str,
    settings: Settings,
) -> bool:
    """Send password reset email via SMTP, or log to console in dev mode."""
    greeting_name = first_name or "there"

    if not _is_smtp_configured(settings):
        # Dev mode: console logging fallback
        logger.info("=" * 60)
        logger.info("PASSWORD RESET (Dev Mode)")
        logger.info(f"  To: {to_email}")
        logger.info(f"  Link: {reset_link}")
        logger.info(f"  Expires: 10 minutes")
        logger.info("=" * 60)
        return True

    try:
        # Render templates
        html_template = _jinja_env.get_template("password_reset.html")
        text_template = _jinja_env.get_template("password_reset.txt")

        context = {
            "first_name": greeting_name,
            "reset_link": reset_link,
            "expiry_minutes": 10,
        }

        html_body = html_template.render(**context)
        text_body = text_template.render(**context)

        # Build multipart message
        msg = EmailMessage()
        msg["Subject"] = "Spectra - Reset Your Password"
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg.set_content(text_body)
        msg.add_alternative(html_body, subtype="html")

        # Send via SMTP
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_pass,
            start_tls=True,
        )

        logger.info("Password reset email sent", extra={"email": to_email, "event": "email_sent"})
        return True

    except Exception as e:
        logger.error(
            "Failed to send password reset email",
            extra={"email": to_email, "event": "email_failed", "error": str(e)},
        )
        return False
```

### Pattern 3: SMTP Startup Validation (Non-Blocking)
**What:** Test SMTP connectivity during app startup; log result but do not prevent startup.
**When to use:** In the FastAPI lifespan function alongside LLM validation.
**Example:**
```python
# In main.py lifespan function
async def validate_smtp_configuration():
    """Test SMTP connection at startup. Log result, never block startup."""
    smtp_logger = logging.getLogger("spectra.smtp")

    if not _is_smtp_configured(settings):
        smtp_logger.info("SMTP not configured - email will use console logging (dev mode)")
        return

    try:
        smtp_client = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=True,
            timeout=10,
        )
        await smtp_client.connect()
        await smtp_client.login(settings.smtp_user, settings.smtp_pass)
        await smtp_client.quit()
        smtp_logger.info("SMTP connection validated successfully")
    except Exception as e:
        smtp_logger.warning(f"SMTP validation failed: {e}. Emails may fail to send.")
```

### Anti-Patterns to Avoid
- **Persistent SMTP connection stored in app.state:** SMTP connections can timeout, get reset by the server, or fail silently. Connect-per-send is more reliable for low-volume use.
- **Using JWT for single-use tokens:** JWTs are designed to be stateless and verifiable without server state. If you need to invalidate or mark as used, you need DB state anyway -- use a random token instead.
- **Logging email content (HTML body, reset links) in production:** Reset links are security-sensitive. Log metadata only (to_email, event type, success/failure) per the locked decision.
- **Blocking app startup on SMTP failure:** The user explicitly decided SMTP validation should log but not block. The app must start even if SMTP is down.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async SMTP sending | Custom asyncio socket code | `aiosmtplib.send()` | SMTP protocol has EHLO/STARTTLS/AUTH handshake, MIME encoding, error handling |
| HTML email templates | f-string HTML construction | Jinja2 `FileSystemLoader` | Current code uses f-strings (email.py:53-77) -- hard to maintain, no escaping, no separation of concerns |
| Multipart MIME messages | Manual MIME boundary construction | `email.message.EmailMessage` | Python stdlib handles Content-Type headers, boundary generation, character encoding |
| Secure random tokens | `uuid4()` or `random.choice()` | `secrets.token_urlsafe(32)` | `secrets` uses OS-level CSPRNG; `random` is predictable; `uuid4` has less entropy than 256-bit random |
| Token hash comparison | `==` string comparison | `secrets.compare_digest()` | Constant-time comparison prevents timing attacks on token lookup |

**Key insight:** The current email.py is only 103 lines because it uses f-string HTML and Mailgun's HTTP API. The SMTP rewrite will be slightly longer but modular: separate template files, separate token model, separate SMTP sending. This separation makes each piece independently testable.

## Common Pitfalls

### Pitfall 1: SMTP Port/TLS Mismatch
**What goes wrong:** Email sending fails silently or with cryptic SSL errors.
**Why it happens:** Port 465 expects direct TLS (`use_tls=True`), port 587 expects STARTTLS (`start_tls=True`), port 25 expects no encryption. Mixing them up causes connection failures.
**How to avoid:** Document port/TLS combinations in .env.example. Default to port 587 + STARTTLS (the most common production configuration). Use `start_tls=True` as default in the `send()` call.
**Warning signs:** `SMTPConnectError`, `SSLError`, or timeout errors during SMTP validation at startup.

### Pitfall 2: Storing Raw Tokens in Database
**What goes wrong:** If the database is compromised, attacker can use stored tokens to reset any user's password.
**Why it happens:** Developer stores the token as-is in the DB instead of hashing it.
**How to avoid:** Store `hashlib.sha256(token.encode()).hexdigest()` in the DB. Send the raw token in the email. On verification, hash the incoming token and look up the hash. This way, even a DB breach does not expose usable tokens.
**Warning signs:** Token column contains URL-safe base64 strings instead of hex digests.

### Pitfall 3: Race Condition on Token Invalidation
**What goes wrong:** Two simultaneous reset requests for the same email create tokens without properly invalidating each other, or a user clicks an old link while a new one is being generated.
**Why it happens:** Non-atomic read-then-write on the tokens table.
**How to avoid:** Use a single UPDATE statement to invalidate all existing tokens before INSERT of the new one, within the same database transaction. The `forgot_password` endpoint already runs within a DB session transaction.
**Warning signs:** Multiple active tokens for the same email in the database.

### Pitfall 4: Dev Mode Detection After Config Migration
**What goes wrong:** After replacing `EMAIL_SERVICE_API_KEY` with `SMTP_HOST/SMTP_USER/SMTP_PASS`, the dev mode detection logic breaks or behaves unexpectedly.
**Why it happens:** The current email.py has a complex dev-mode check involving `_DEV_PLACEHOLDERS`. The new logic must be clear: SMTP is configured if and only if `smtp_host` AND `smtp_user` AND `smtp_pass` are all non-empty.
**How to avoid:** Simple boolean check: `bool(settings.smtp_host and settings.smtp_user and settings.smtp_pass)`. No placeholder lists.
**Warning signs:** Emails silently falling back to console logging in production, or attempting SMTP sends in development.

### Pitfall 5: Forgetting to Pass first_name to Email Service
**What goes wrong:** The email greeting shows "Hi there," instead of "Hi John," because the user's first_name is not fetched or passed.
**Why it happens:** The current `forgot_password` endpoint queries the user but only passes `user.email` to the email service. The `first_name` must also be passed.
**How to avoid:** Update the `forgot_password` endpoint to pass `user.first_name` to `send_password_reset_email()`.
**Warning signs:** All emails show generic greeting despite users having first names set.

### Pitfall 6: Not Cleaning Up Expired Tokens
**What goes wrong:** The `password_reset_tokens` table grows indefinitely with expired/used tokens.
**Why it happens:** No cleanup mechanism for old tokens.
**How to avoid:** For now, expired tokens are naturally filtered out by the `WHERE expires_at > now() AND is_active AND NOT is_used` query. Add a periodic cleanup later (out of scope for this phase), or rely on the invalidation of old tokens when new ones are created. This is acceptable for a low-volume app.
**Warning signs:** Table size growing without bound (monitor in future phases).

## Code Examples

Verified patterns from official sources:

### Multipart MIME Email with EmailMessage (Python stdlib)
```python
# Source: https://docs.python.org/3/library/email.examples.html
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = "Spectra - Reset Your Password"
msg["From"] = "Spectra <noreply@spectra.app>"
msg["To"] = "user@example.com"

# Plain text first (fallback)
msg.set_content("Hi John,\n\nReset your password: https://app.spectra.com/reset?token=abc123\n\nThis link expires in 10 minutes.")

# HTML alternative (preferred by clients)
msg.add_alternative("""\
<html>
<body>
<h2>Spectra</h2>
<p>Hi John,</p>
<p>Reset your password by clicking the button below:</p>
<a href="https://app.spectra.com/reset?token=abc123"
   style="display:inline-block;padding:12px 24px;background-color:#2563eb;color:white;text-decoration:none;border-radius:6px;font-weight:600;">
   Reset Password
</a>
<p style="margin-top:16px;color:#6b7280;font-size:14px;">This link expires in 10 minutes.</p>
</body>
</html>
""", subtype="html")
```

### Sending with aiosmtplib (one-shot)
```python
# Source: https://aiosmtplib.readthedocs.io/en/latest/usage.html
import aiosmtplib

await aiosmtplib.send(
    msg,
    hostname="smtp.gmail.com",
    port=587,
    username="user@gmail.com",
    password="app-password",
    start_tls=True,  # Port 587 uses STARTTLS
)
```

### SMTP Connection Test
```python
# Source: https://aiosmtplib.readthedocs.io/en/latest/client.html
import aiosmtplib

smtp = aiosmtplib.SMTP(hostname="smtp.example.com", port=587, start_tls=True, timeout=10)
await smtp.connect()
await smtp.login("user", "password")
await smtp.quit()
```

### Secure Token Generation and Hashing
```python
# Source: https://docs.python.org/3/library/secrets.html
import secrets
import hashlib

# Generate token (sent in email)
raw_token = secrets.token_urlsafe(32)  # 256-bit, ~43 chars

# Hash for storage (stored in DB)
token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

# Verification (on reset-password submit)
incoming_hash = hashlib.sha256(incoming_token.encode()).hexdigest()
# Look up: SELECT ... WHERE token_hash = incoming_hash AND is_active AND NOT is_used AND expires_at > now()

# Constant-time comparison (if comparing directly)
secrets.compare_digest(stored_hash, incoming_hash)
```

### Jinja2 FileSystemLoader Setup
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

template_dir = Path(__file__).parent.parent / "templates" / "email"

env = Environment(
    loader=FileSystemLoader(str(template_dir)),
    autoescape=select_autoescape(["html"]),  # Auto-escape HTML templates
)

template = env.get_template("password_reset.html")
html = template.render(first_name="John", reset_link="https://...", expiry_minutes=10)
```

### Alembic Migration for password_reset_tokens
```python
# Example migration structure
def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.UUID(), nullable=False, default=uuid4),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token_hash", sa.String(128), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
    op.create_index("ix_password_reset_tokens_email_active", "password_reset_tokens", ["email", "is_active"])
```

### Settings Configuration Pattern
```python
# Additions to backend/app/config.py Settings class
class Settings(BaseSettings):
    # ... existing settings ...

    # SMTP Email (replaces email_service_api_key and email_from)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from_email: str = "noreply@spectra.app"
    smtp_from_name: str = "Spectra"
```

### .env.example SMTP Configuration
```bash
# SMTP Email Configuration
# Leave SMTP_HOST empty for dev mode (console logging)
# Common configurations:
#   Gmail:     SMTP_HOST=smtp.gmail.com  SMTP_PORT=587
#   SendGrid:  SMTP_HOST=smtp.sendgrid.net  SMTP_PORT=587
#   Mailgun:   SMTP_HOST=smtp.mailgun.org  SMTP_PORT=587
#   AWS SES:   SMTP_HOST=email-smtp.us-east-1.amazonaws.com  SMTP_PORT=587
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM_EMAIL=noreply@spectra.app
SMTP_FROM_NAME=Spectra
```

## State of the Art

| Old Approach (Current) | New Approach (This Phase) | Why Change |
|------------------------|---------------------------|------------|
| Mailgun HTTP API via httpx | Standard SMTP via aiosmtplib | Vendor-neutral, works with any SMTP provider |
| f-string HTML in Python code | Jinja2 templates in separate files | Maintainable, auto-escaped, testable |
| JWT reset tokens (stateless) | DB-backed random tokens (stateful) | Enables single-use, bulk invalidation |
| `_DEV_PLACEHOLDERS` set for detection | Simple `bool(smtp_host and smtp_user and smtp_pass)` | Clear, no edge cases |
| `EMAIL_SERVICE_API_KEY` + `EMAIL_FROM` | `SMTP_HOST/PORT/USER/PASS` + `SMTP_FROM_EMAIL/NAME` | Industry-standard naming |
| No rate limiting on forgot-password | In-memory per-email 2-minute cooldown | Abuse prevention |
| No startup SMTP validation | Non-blocking SMTP connectivity test | Fail-fast awareness |

**Deprecated/outdated (to remove):**
- `email_service_api_key` setting in config.py -- replaced by smtp_* settings
- `email_from` setting in config.py -- replaced by `smtp_from_email` and `smtp_from_name`
- `_DEV_PLACEHOLDERS` set in email.py -- replaced by simple boolean check
- `httpx` import in email.py -- no longer needed for email (still used elsewhere in app)
- `create_password_reset_token()` and `verify_password_reset_token()` in security.py -- replaced by DB token operations

## Existing Code Impact Analysis

### Files to MODIFY
| File | Changes | Risk |
|------|---------|------|
| `backend/app/config.py` | Remove `email_service_api_key`, `email_from`; add `smtp_host`, `smtp_port`, `smtp_user`, `smtp_pass`, `smtp_from_email`, `smtp_from_name` | LOW -- additive, clear mapping |
| `backend/app/main.py` | Add SMTP validation call in lifespan | LOW -- follows existing pattern (LLM validation) |
| `backend/app/routers/auth.py` | Rewrite `forgot_password` (DB tokens, cooldown, pass first_name); rewrite `reset_password` (DB token lookup, single-use) | MEDIUM -- core business logic change |
| `backend/app/services/email.py` | Full rewrite: aiosmtplib + Jinja2 replacing Mailgun + f-strings | MEDIUM -- complete file replacement |
| `backend/app/utils/security.py` | Remove `create_password_reset_token()` and `verify_password_reset_token()` | LOW -- functions being replaced |
| `backend/app/models/__init__.py` | Add PasswordResetToken import | LOW -- one line |
| `backend/alembic/env.py` | Add `password_reset` to model imports | LOW -- one line |
| `backend/.env.example` | Replace email config with SMTP config | LOW -- documentation |
| `backend/pyproject.toml` | Add `aiosmtplib>=5.1.0`, optionally add `jinja2>=3.1.0` | LOW -- dependency addition |
| `frontend/src/app/(auth)/reset-password/page.tsx` | Add error state for expired/invalid token with "Request new reset" button | LOW -- UI state addition |

### Files to CREATE
| File | Purpose |
|------|---------|
| `backend/app/models/password_reset.py` | PasswordResetToken SQLAlchemy model |
| `backend/app/templates/email/password_reset.html` | Jinja2 HTML email template |
| `backend/app/templates/email/password_reset.txt` | Jinja2 plain text email template |
| `backend/alembic/versions/xxx_add_password_reset_tokens.py` | Alembic migration |

## Open Questions

1. **Should we hash tokens with SHA-256 or a stronger algorithm?**
   - What we know: SHA-256 is standard for token hashing (not password hashing). The token has 256 bits of entropy, so brute-force is infeasible regardless of hash speed.
   - What's unclear: Whether the team has a preference for bcrypt/argon2 even for tokens (overkill but possible).
   - Recommendation: Use SHA-256. It is the standard for this use case. Argon2 is for passwords (low entropy, needs slow hash); tokens have high entropy and just need a one-way mapping.

2. **Should the old `email_service_api_key` / `email_from` settings be kept for backward compatibility?**
   - What we know: The .env currently has `EMAIL_SERVICE_API_KEY=` (empty) and `EMAIL_FROM=noreply@spectra.app`. This is a single-developer project.
   - What's unclear: Whether there are other deployment environments that need migration.
   - Recommendation: Remove them cleanly. Add the new SMTP_* vars. Document the migration in the .env.example comments. No backward compatibility layer needed for a single-developer project.

3. **Should the in-memory cooldown dict be persisted or shared?**
   - What we know: Single-server deployment. The cooldown resets on restart.
   - What's unclear: Whether this is a problem in practice (rapid restart + abuse scenario).
   - Recommendation: In-memory is fine. If needed later, move to a simple DB check (last reset request timestamp on the tokens table).

## Sources

### Primary (HIGH confidence)
- aiosmtplib 5.1.0 official docs: https://aiosmtplib.readthedocs.io/en/latest/usage.html -- send() API, SMTP client, multipart messages
- aiosmtplib 5.1.0 API reference: https://aiosmtplib.readthedocs.io/en/latest/reference.html -- full function signatures
- aiosmtplib 5.1.0 client docs: https://aiosmtplib.readthedocs.io/en/latest/client.html -- connection management, async context manager
- Python secrets docs: https://docs.python.org/3/library/secrets.html -- token_urlsafe, compare_digest
- Python email.message docs: https://docs.python.org/3/library/email.message.html -- EmailMessage, multipart
- Jinja2 API docs: https://jinja.palletsprojects.com/en/stable/api/ -- Environment, FileSystemLoader
- Codebase direct inspection: email.py, config.py, auth.py, security.py, user model, frontend pages

### Secondary (MEDIUM confidence)
- aiosmtplib PyPI: https://pypi.org/project/aiosmtplib/ -- version 5.1.0 released 2026-01-25
- aiosmtplib GitHub issues #15: https://github.com/cole/aiosmtplib/issues/15 -- concurrency limitations confirmed

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- aiosmtplib is the only maintained async SMTP library, Jinja2 is already installed, secrets is stdlib
- Architecture: HIGH -- patterns derived from direct codebase analysis + official library docs
- Pitfalls: HIGH -- based on documented issues in codebase debug logs + standard SMTP knowledge
- Discretionary decisions: HIGH -- each recommendation backed by specific requirements analysis

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (30 days -- stable domain, no fast-moving dependencies)
