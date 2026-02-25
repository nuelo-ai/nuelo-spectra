---
created: 2026-02-25T00:51:35.070Z
title: Remove duplicate API v1 router mount
area: api
files:
  - backend/app/main.py:408-409
  - backend/app/routers/api_v1/__init__.py
---

## Problem

The API v1 router is mounted twice in main.py, creating duplicate endpoints visible in `/docs`:

```python
app.include_router(api_v1_router)                    # /v1/* — public frontend proxy strips /api
app.include_router(api_v1_router, prefix="/api")     # /api/v1/* — direct access and admin frontend
```

This was a workaround from Phase 39 UAT gap closure because the public frontend proxy strips the `/api` prefix from paths before forwarding to the backend. The result is every API endpoint appearing twice in FastAPI's OpenAPI docs and swagger UI.

## Solution

Fix the frontend proxy to preserve the `/api` prefix, then mount the router only once at `/api/v1`. This affects:

1. `frontend/src/app/api/[...slug]/route.ts` — adjust proxy path rewriting
2. `admin-frontend/src/app/api/[...slug]/route.ts` — same adjustment
3. `backend/app/main.py` — remove the duplicate `include_router` call, keep only `/api/v1`
4. Update any frontend API client base URLs if they reference `/v1/` directly

Target: v0.7.1 patch release.
