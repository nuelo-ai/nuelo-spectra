---
status: diagnosed
trigger: "P26-T2 — Admin catch-all routes visible in OpenAPI docs in public mode"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — catch-all route registered with @app.api_route without include_in_schema=False, so FastAPI includes it in OpenAPI schema
test: read main.py lines 322-331
expecting: route declaration would have include_in_schema=False if it were meant to be hidden
next_action: DONE — root cause confirmed

## Symptoms

expected: Zero admin routes visible in OpenAPI docs in public mode (SPECTRA_MODE=public)
actual: /api/admin/{path} catch-all routes appear in OpenAPI /docs page, returning "Admin Route Not Found"
errors: no error — routes appear but return wrong response
reproduction: run backend with SPECTRA_MODE=public, visit /docs
started: unknown — may have always been this way

## Eliminated

- hypothesis: catch-all route is registered outside the if mode == "public" block
  evidence: route is inside the if mode == "public" block (lines 323-331) — block is correct
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: backend/app/main.py lines 322-331
  found: "@app.api_route('/api/admin/{path:path}', methods=[...]) async def admin_route_not_found" is defined inside `if mode == 'public'` but WITHOUT `include_in_schema=False`
  implication: FastAPI's default for `include_in_schema` is True, so ANY route registered with @app.api_route or @app.get etc. will appear in /docs unless explicitly set to False

- timestamp: 2026-02-17
  checked: entire backend/app/main.py and backend/app/ for `include_in_schema`
  found: zero occurrences of include_in_schema anywhere in the codebase
  implication: no routes are explicitly excluded from OpenAPI schema — the catch-all is the only case where this matters since all other admin routes are skipped via the `if mode in ("admin", "dev")` gate

## Resolution

root_cause: The catch-all admin route on line 326 of main.py is registered with @app.api_route without include_in_schema=False, causing FastAPI to include it in the OpenAPI schema by default. The SPECTRA_MODE gate correctly prevents the route from doing admin work, but does not prevent its schema advertisement.
fix: Add include_in_schema=False to the @app.api_route decorator on line 326
verification:
files_changed: [backend/app/main.py]
