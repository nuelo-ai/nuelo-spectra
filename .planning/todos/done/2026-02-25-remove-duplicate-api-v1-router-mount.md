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

The proposed proxy fix (strip removal) is **not safe** as a simple patch. The public frontend proxy strips `/api` for ALL routes — not just v1. The backend mounts `auth`, `chat`, `files`, `credits`, `search`, `chat_sessions` all without an `/api` prefix.

The correct full solution requires migrating ALL those routers to use an `/api` prefix on the backend:

1. `backend/app/main.py` — add `prefix="/api"` to auth, chat, files, credits, search, chat_sessions routers
2. Verify no backend-internal route references break
3. `frontend/src/app/api/[...slug]/route.ts` — remove the `replace(/^\/api/, "")` strip
4. Then remove the duplicate v1 router mount

This is a planned migration, not a quick patch. Do as a dedicated phase.

## Attempted (v0.7.1 — REVERTED in v0.7.2)

Attempted to remove proxy strip + single v1 mount — broke login and all non-v1 public routes. Reverted immediately.
