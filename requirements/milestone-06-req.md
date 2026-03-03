# Milestone v0.6 Requirements: Production Readiness

## Overview
Harden the application for public release. These are the minimum requirements before Spectra can accept real users in production. Assumes v0.5 (Admin Portal) is complete.

---

## 1. Email Verification

- Add `is_verified` boolean field to `users` table (default: `false`)
- On signup, send verification email with unique token link
- User must verify email before accessing the app (redirect to "check your email" page)
- Verification token expires after 24 hours
- "Resend verification email" option on the verification page
- **Exception**: users who register via an admin invite link are auto-verified (email already validated by admin)
- Unverified users cannot log in (return clear error message)

---

## 2. Rate Limiting

- Add `slowapi` middleware to the FastAPI backend
- Rate limits per endpoint category:
  - Login: 5 attempts per minute per IP
  - Signup: 3 attempts per minute per IP
  - Password reset request: 3 per hour per email
  - Chat messages: 30 per minute per user (adjustable via platform settings)
  - File upload: 10 per minute per user
- Return `429 Too Many Requests` with `Retry-After` header
- Rate limits apply to **public mode** endpoints only (admin endpoints are already network-isolated)
- Rate limit thresholds configurable via environment variables

---

## 3. Security Headers

- Add security headers middleware to all responses:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HTTPS only)
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'` (tune as needed for frontend assets)

---

## 4. Global Error Handling

### Backend
- Add global exception handler (`@app.exception_handler(Exception)`)
- Return clean JSON error responses (no Python tracebacks leaked to client)
- Standard error format: `{ "error": "message", "code": "ERROR_CODE" }`
- Log full tracebacks server-side for debugging
- Handle common cases explicitly: 400 (validation), 401 (auth), 403 (forbidden), 404 (not found), 500 (internal)

### Frontend
- Add React error boundary at the app root level
- Fallback UI with "Something went wrong" message and retry option
- Dedicated error pages: 404 (not found), 500 (server error)
- Toast/notification system for API error feedback

---

## 5. Account Deletion

### User Self-Service
- "Delete my account" option in user settings page
- Requires password confirmation before deletion
- Shows warning: "This will permanently delete your account, files, and chat history"
- Soft-delete with 30-day grace period (user can contact support to recover)
- After 30 days, hard-delete all user data (files, chat sessions, messages, credits)

### Admin-Initiated
- Already covered in v0.5 admin portal requirements
- Admin can delete user immediately (hard delete) or deactivate (soft delete)

### Data Cleanup
- On account deletion, remove:
  - User record (soft-delete initially)
  - Uploaded files from storage
  - Chat sessions and messages
  - Credit balance and transaction history
  - Any pending invitations sent to this email

---

## 6. HTTPS / SSL

- All production deployments must be behind HTTPS
- HTTP requests redirect to HTTPS (301)
- SSL termination at reverse proxy level (Traefik, Nginx, or Cloudflare)
- Secure cookies: `Secure`, `HttpOnly`, `SameSite=Lax` flags on auth tokens if using cookies
- HSTS header enforced (covered in section 3)

---

## 7. Error Monitoring (Optional but Recommended)

- Integrate Sentry SDK for both backend (Python) and frontend (Next.js)
- Capture unhandled exceptions with context (user ID, request path, environment)
- Configurable via `SENTRY_DSN` environment variable
- Disabled by default in dev mode
- Source maps uploaded for frontend error readability
