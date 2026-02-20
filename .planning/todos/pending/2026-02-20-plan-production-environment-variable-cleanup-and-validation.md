---
created: 2026-02-20T02:30:20.848Z
title: Plan production environment variable cleanup and validation
area: deployment
files:
  - backend/app/config.py
  - .env.docker.example
  - backend/.env.example
  - DEPLOYMENT.md
  - compose.yaml
  - backend/app/routers/admin/invitations.py:92
  - backend/app/services/admin/users.py:431
  - backend/app/routers/auth.py:297
---

## Problem

Production has two backend deployments (public + admin) with separate environment variables. Discovered that the admin backend had `FRONTEND_URL` empty, causing invite email links to default to `http://localhost:3000` — broken in production. The public backend had it set correctly to `https://spectra.nuelo.ai`.

This highlights a broader risk: environment variables can silently fall back to dev defaults (`config.py` defaults like `http://localhost:3000`) without any warning, leading to broken features that only surface when users hit them. There's no validation that critical env vars are set in production mode, and no way to catch conflicting or missing values across the two deployments.

Key concerns:
- `FRONTEND_URL` used for email links (invite, password reset) — must match actual frontend domain
- `CORS_ORIGINS` must align with `FRONTEND_URL` and `ADMIN_CORS_ORIGIN`
- SMTP settings all-or-nothing (partial config = silent dev mode fallback)
- Two deployments (public/admin) share the same Settings class but need different values for some vars — easy to miss one
- `.env.docker.example` exists but no runtime check that production values are sane

## Solution

1. **Startup validation**: Add a `validate_production_settings()` check in `main.py` that runs when `SPECTRA_MODE != dev`. Should warn/fail on:
   - `FRONTEND_URL` still contains `localhost`
   - `SECRET_KEY` is the default dev key
   - SMTP partially configured (some vars set, others empty)
   - `CORS_ORIGINS` doesn't include `FRONTEND_URL`
   - `DATABASE_URL` points to localhost in production

2. **Health endpoint enhancement**: Extend `GET /health` or add `GET /health/config` (admin-only) that reports which critical settings are set vs defaulted — without exposing values.

3. **Env var audit**: Review all defaults in `config.py` and `.env.docker.example` to ensure no dev defaults can silently break production features. Document which vars are required per deployment type (public vs admin).

4. **Consider**: A shared env var checklist or pre-deploy script that validates both deployments have consistent/correct values.
