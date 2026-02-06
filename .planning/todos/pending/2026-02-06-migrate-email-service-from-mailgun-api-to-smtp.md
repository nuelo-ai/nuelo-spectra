---
created: 2026-02-06T10:28
title: Migrate email service from Mailgun API to standard SMTP
area: api
files:
  - backend/app/services/email.py:44-102
  - backend/app/config.py:23-25
  - backend/.env.example:14-16
---

## Problem

Current email service implementation uses Mailgun-specific HTTP API (lines 44-102 in email.py). This creates vendor lock-in and non-standard configuration:
- Uses `EMAIL_SERVICE_API_KEY` for Mailgun API authentication
- Hardcoded Mailgun API endpoint (`https://api.mailgun.net/v3/{domain}/messages`)
- HTTP POST request with API key auth instead of standard SMTP protocol

Standard SMTP configuration would:
- Work with any email provider (Gmail, SendGrid, AWS SES, self-hosted)
- Use industry-standard env vars (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
- Simplify deployment and provider switching
- Support both development (local SMTP servers like MailHog) and production seamlessly

## Solution

Replace Mailgun API implementation with standard SMTP using Python's `aiosmtplib` library:

1. **Add dependency**: `aiosmtplib>=3.0.0` to backend/pyproject.toml
2. **Update config.py Settings**:
   - Replace `email_service_api_key: str` with standard SMTP fields:
     - `smtp_host: str = "localhost"` (default for dev)
     - `smtp_port: int = 1025` (MailHog default)
     - `smtp_user: str = ""`
     - `smtp_password: str = ""`
     - `smtp_use_tls: bool = False`
     - `smtp_use_ssl: bool = False`
3. **Update email.py**:
   - Import `aiosmtplib` and `email.message.EmailMessage`
   - Detect dev mode by empty `smtp_user` instead of API key check
   - Replace `httpx.AsyncClient().post()` with `aiosmtplib.send()` using SMTP configuration
   - Keep HTML email template and logging structure
4. **Update .env.example**:
   - Remove `EMAIL_SERVICE_API_KEY`
   - Add SMTP configuration block with comments for common providers (Mailgun SMTP, Gmail, SendGrid)
5. **Update README.md**: Update email configuration section with SMTP examples

**Dev mode**: Use MailHog (`docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog`) or log to console if no SMTP configured
**Prod mode**: Configure actual SMTP credentials (Mailgun SMTP, AWS SES SMTP, etc.)

**Breaking change**: Yes - requires env var migration for existing deployments
**Migration path**: Document Mailgun API → Mailgun SMTP credential conversion in PR/changelog
