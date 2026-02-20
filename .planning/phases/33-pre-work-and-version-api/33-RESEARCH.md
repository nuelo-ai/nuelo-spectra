# Phase 33: Pre-Work and Version API - Research

**Researched:** 2026-02-18
**Domain:** Next.js 16 Docker readiness, proxy configuration, FastAPI version endpoint, React version display
**Confidence:** HIGH

---

## Summary

Phase 33 is a preparatory phase with eight tightly scoped requirements: eliminate two hardcoded `localhost:8000` URLs in the public frontend, add `output: 'standalone'` to both `next.config.ts` files, implement runtime-configurable backend URL proxying, add `/api/health` Next.js route handlers to both frontends, add a `/version` FastAPI endpoint to the backend, and surface the version in both frontend settings pages.

The codebase is already well-structured for these changes. Both frontends use `/api/` as the proxy prefix consistently in their API clients (`api-client.ts`, `admin-api-client.ts`), meaning the two hardcoded URLs are isolated exceptions. The backend already has a `/health` endpoint (returning `status: "healthy"`) that needs adjustment to return `status: "ok"` for the frontend health routes, and the backend `config.py` already exposes `spectra_mode` via `settings.spectra_mode` making the `/version` endpoint implementation straightforward.

**Critical finding:** The prior decisions describe "Runtime `process.env.BACKEND_URL` in rewrites" but in Next.js standalone mode (`node server.js`), `next.config.ts` rewrites are evaluated at build time, NOT at server startup. The values get baked into the standalone output. For true runtime backend URL configuration without image rebuild, `proxy.ts` (Next.js 16's replacement for `middleware.ts`) is the correct mechanism. However, if the team accepts "configure at build time" behavior (which still avoids hardcoding `localhost:8000` in source), `rewrites()` with `process.env.BACKEND_URL` works for local dev (`next start`) and the value defaults correctly. The planner must decide which path to take.

**Primary recommendation:** Use `proxy.ts` for runtime BACKEND_URL (true Docker portability); use `rewrites()` with `process.env.BACKEND_URL` only if local-dev use case is the priority. The health check endpoints should be Next.js App Router route handlers (`app/api/health/route.ts`), not rewrites to the backend.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PRE-01 | No `http://localhost:8000` in `useSSEStream.ts` (line 112) or `register/page.tsx` (line 26) | Confirmed both locations identified; SSE hook needs path change to `/api/chat/sessions/${sessionId}/stream`; register page needs `/api/auth/signup-status` |
| PRE-02 | Both Next.js apps get `output: 'standalone'` in `next.config.ts` | Confirmed pattern: add `output: 'standalone'` to `NextConfig` object |
| PRE-03 | Both Next.js apps read `process.env.BACKEND_URL` in rewrite destinations (defaults to `http://localhost:8000`) | CRITICAL CAVEAT: rewrites in `next.config.ts` are baked at build time in standalone mode; see Architecture Patterns for full analysis |
| PRE-04 | Public frontend exposes `GET /api/health` returning `{status: "ok"}` | Next.js App Router route handler at `src/app/api/health/route.ts` |
| PRE-05 | Admin frontend exposes `GET /api/health` returning `{status: "ok"}` | Next.js App Router route handler at `src/app/api/health/route.ts` |
| VER-01 | Backend `GET /version` returns `{"version": APP_VERSION env var, "environment": SPECTRA_MODE}` with `APP_VERSION` defaulting to `"dev"` | New router in `backend/app/routers/version.py` + include in `main.py` + add `app_version` to `config.py` Settings |
| VER-02 | User sees app version on public frontend settings page, fetched from `GET /api/version` | Add `useAppVersion` hook + render in `AccountInfo.tsx` component |
| VER-03 | Admin sees app version on admin frontend settings page, fetched from `GET /api/version` | Add version card to admin `SettingsForm.tsx` or new `AppVersionCard.tsx` component |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 (in use) | Frontend framework, `output: 'standalone'`, route handlers, proxy.ts | Already in use in both frontends |
| FastAPI | 0.115+ (in use) | Backend REST endpoints | Already in use |
| TanStack Query | 5.90+ (in use) | Data fetching with caching for version display | Already used throughout both frontends |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@tanstack/react-query` | 5.x (in use) | `useQuery` for version fetching | VER-02, VER-03 |
| Pydantic Settings | 2.x (in use) | Backend env var config (`APP_VERSION`) | VER-01 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `next.config.ts` rewrites with `process.env.BACKEND_URL` | `proxy.ts` (NextResponse.rewrite) | `proxy.ts` = true runtime; rewrites = baked at build in standalone mode |
| New `/version` router | Extending `/health` endpoint | Separate router is cleaner, health stays simple, version stays separate |
| `apiClient.get` for version | `fetch` directly | apiClient is consistent with codebase patterns |

---

## Architecture Patterns

### Files to Create/Modify

**Public Frontend (`/frontend`):**
```
src/
├── app/
│   ├── api/
│   │   └── health/
│   │       └── route.ts        # NEW: GET /api/health returns {status:"ok"}
│   ├── (auth)/
│   │   └── register/
│   │       └── page.tsx        # MODIFY: line 26, remove localhost:8000
│   └── (dashboard)/
│       └── settings/
│           └── page.tsx        # No change (uses AccountInfo.tsx)
├── components/
│   └── settings/
│       └── AccountInfo.tsx     # MODIFY: add version display
└── hooks/
    ├── useSSEStream.ts         # MODIFY: line 112, remove localhost:8000
    └── useAppVersion.ts        # NEW: fetch /api/version
next.config.ts                  # MODIFY: add output:standalone, BACKEND_URL in rewrite
```

**Admin Frontend (`/admin-frontend`):**
```
src/
├── app/
│   └── api/
│       └── health/
│           └── route.ts        # NEW: GET /api/health returns {status:"ok"}
└── components/
    └── settings/
        └── SettingsForm.tsx    # MODIFY: add version card at bottom
next.config.ts                  # MODIFY: add output:standalone, BACKEND_URL in rewrite
```

**Backend (`/backend`):**
```
app/
├── config.py                   # MODIFY: add app_version field
├── main.py                     # MODIFY: include version router
└── routers/
    └── version.py              # NEW: GET /version endpoint
```

### Pattern 1: Next.js Standalone Output
**What:** Adding `output: 'standalone'` enables Next.js to produce `.next/standalone/` with only the necessary files for production. The `standalone/server.js` replaces `next start`.
**When to use:** Required for Docker multi-stage builds to reduce image size.

```typescript
// Source: https://nextjs.org/docs/app/api-reference/config/next-config-js/output
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
```

**CAVEAT FOR STANDALONE:** When running `node .next/standalone/server.js`, the `process.env.BACKEND_URL` value is baked at build time. Setting `BACKEND_URL` at container runtime will NOT change the rewrite destination. This behavior is confirmed by multiple Next.js GitHub issues (#21888, #33932, discussion #34894). See Pitfalls section.

### Pattern 2: Next.js Route Handler Health Endpoint
**What:** App Router route handlers in `src/app/api/health/route.ts` respond to HTTP requests directly from Next.js (not proxied to backend).
**When to use:** PRE-04, PRE-05 — health endpoints must be served by the Next.js process itself, not proxied to backend.

```typescript
// Source: https://nextjs.org/docs/app/api-reference/file-conventions/route
// frontend/src/app/api/health/route.ts
import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({ status: "ok" });
}
```

**Important:** The health route must NOT be caught by the rewrites proxy. Since rewrites only apply when the file does not exist on the filesystem, and the route handler creates a real `/api/health` page, this is handled automatically — the route handler takes priority over rewrites.

### Pattern 3: FastAPI Version Endpoint
**What:** A new lightweight router that reads `APP_VERSION` env var (default `"dev"`) and `SPECTRA_MODE` from settings.

```python
# backend/app/routers/version.py
import os
from fastapi import APIRouter

router = APIRouter(tags=["Version"])

@router.get("/version")
async def get_version():
    """Returns the application version and environment mode."""
    return {
        "version": os.getenv("APP_VERSION", "dev"),
        "environment": os.getenv("SPECTRA_MODE", "dev"),
    }
```

**Alternative using Settings:**
```python
from app.config import get_settings

@router.get("/version")
async def get_version():
    settings = get_settings()
    return {
        "version": os.getenv("APP_VERSION", "dev"),
        "environment": settings.spectra_mode,
    }
```

**Note:** `APP_VERSION` should NOT be added to Pydantic Settings if the intent is to default to `"dev"` when unset — it can be read directly with `os.getenv`. Alternatively, add `app_version: str = "dev"` to the Settings class (consistent with existing pattern).

### Pattern 4: TanStack Query Hook for Version
**What:** A `useQuery` hook that fetches `/api/version` from the backend (via proxy).

```typescript
// frontend/src/hooks/useAppVersion.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface AppVersion {
  version: string;
  environment: string;
}

export function useAppVersion() {
  return useQuery<AppVersion>({
    queryKey: ["app", "version"],
    queryFn: async () => {
      const res = await apiClient.get("/version");
      if (!res.ok) throw new Error("Failed to fetch version");
      return res.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - version rarely changes
  });
}
```

**Admin frontend note:** The admin frontend uses `adminApiClient` and path prefix `/api/admin/...` for admin routes. The version endpoint is at `/version` (not under `/api/admin/`). The admin rewrite maps `/api/:path*` → `http://localhost:8000/api/:path*`, so the fetch should be `adminApiClient.get("/api/version")` which proxies to `http://backend:8000/api/version`. Check rewrite mapping carefully.

### Rewrite Path Mapping — Current vs. Target

**Public frontend current:**
```
/api/:path*  →  http://localhost:8000/:path*
```
Example: `/api/auth/login` → `http://localhost:8000/auth/login`

**Public frontend target:**
```
/api/:path*  →  {BACKEND_URL}/:path*  (BACKEND_URL defaults to http://localhost:8000)
```
No path structure change — only the hostname becomes configurable.

**Admin frontend current:**
```
/api/:path*  →  http://localhost:8000/api/:path*
```
Example: `/api/admin/users` → `http://localhost:8000/api/admin/users`

**Admin frontend target:**
```
/api/:path*  →  {BACKEND_URL}/api/:path*  (BACKEND_URL defaults to http://localhost:8000)
```

**Key difference:** Public frontend strips the `/api/` prefix when proxying; admin frontend keeps it. The path structure must remain unchanged.

### Pattern 5: Fix `useSSEStream.ts` Hardcoded URL

Current (line 112):
```typescript
const response = await fetch(`http://localhost:8000/chat/sessions/${sessionId}/stream`, {
```

Target:
```typescript
const response = await fetch(`/api/chat/sessions/${sessionId}/stream`, {
```

The public frontend's rewrite proxies `/api/chat/:path*` → `http://localhost:8000/chat/:path*`, so this correctly reaches the backend.

### Pattern 6: Fix `register/page.tsx` Hardcoded URL

Current (line 26):
```typescript
fetch("http://localhost:8000/auth/signup-status")
```

Target:
```typescript
fetch("/api/auth/signup-status")
```

The public frontend's rewrite proxies `/api/auth/:path*` → `http://localhost:8000/auth/:path*`.

### Anti-Patterns to Avoid
- **Using `NEXT_PUBLIC_BACKEND_URL`:** This is client-side bundled at build time — no better than hardcoding. The phase specifically excludes this approach.
- **Adding `/api/health` to the rewrite rule exclusion list:** Unnecessary because Next.js route handlers take priority over rewrites automatically.
- **Proxying health check to backend:** The health check should be served by the Next.js process itself. A `GET /api/health` should confirm the Next.js process is alive, independent of the backend.
- **Using `middleware.ts` (deprecated):** In Next.js 16, use `proxy.ts`. The file convention is the same but the export function name changes from `middleware` to `proxy`.
- **Hardcoding version in frontend:** The version must be fetched live from the backend so no page rebuild is needed when `APP_VERSION` changes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frontend health endpoint | Express proxy or custom fetch to backend `/health` | Next.js App Router route handler | Simple, native, no dependencies |
| Backend version env reading | Custom env loading code | `os.getenv("APP_VERSION", "dev")` | One-liner, standard Python |
| Frontend version caching | useState + useEffect | TanStack Query `useQuery` | Already used throughout the codebase; handles loading/error states |

---

## Common Pitfalls

### Pitfall 1: process.env in next.config.ts Rewrites is Baked at Build Time in Standalone Mode
**What goes wrong:** Developer adds `process.env.BACKEND_URL ?? "http://localhost:8000"` to rewrite destination, sets `BACKEND_URL=http://backend:8000` at container runtime, but requests still go to `http://localhost:8000`.
**Why it happens:** In `output: 'standalone'` mode, Next.js bakes next.config.ts values (including rewrite destinations) into the standalone build artifacts at build time. The `.next/standalone/server.js` does not re-evaluate `next.config.ts` at startup. This is confirmed by Next.js GitHub issues #21888, #33932, and discussion #34894.
**How to avoid:** For local dev and `next start`, `process.env.BACKEND_URL` in rewrites works fine. For Docker standalone (`node server.js`), use `proxy.ts` with `NextResponse.rewrite()` instead, which IS evaluated at runtime.
**Warning signs:** Backend URL does not change when `BACKEND_URL` env var is changed at container runtime.

**Decision for planner:** The phase's stated goal says "no image rebuild on URL change." For this to actually work in standalone Docker, `proxy.ts` must be used instead of `next.config.ts` rewrites. Using `rewrites()` alone meets the requirement technically (env var replaces hardcode) but not operationally (rebuild still needed for Docker). The planner should note this decision point.

**Practical interim approach (acceptable per prior decisions):** Use `rewrites()` with `process.env.BACKEND_URL ?? "http://localhost:8000"` in `next.config.ts`. This:
- Eliminates hardcoded `localhost:8000` from source code (PRE-03 met)
- Works correctly for local dev without Docker
- For Docker: `BACKEND_URL` must be set at build time (not ideal but acceptable as Phase 33 scope)
- Docker images can be built with the correct URL baked in without source code changes

### Pitfall 2: Health Route Accidentally Proxied to Backend
**What goes wrong:** `/api/health` is created as a Next.js route handler, but if a developer changes the rewrite source pattern to include wildcards that capture it before the filesystem is checked, it could be proxied to the backend instead.
**Why it happens:** Next.js rewrite processing order: redirects → beforeFiles → filesystem (pages, public, route handlers) → afterFiles → fallback. Default `rewrites()` return is checked AFTER filesystem, so route handlers win.
**How to avoid:** Use the default `rewrites()` (not `beforeFiles`). The route handler at `src/app/api/health/route.ts` will be served directly by Next.js without hitting the backend.

### Pitfall 3: Admin Frontend Version Endpoint Path Mismatch
**What goes wrong:** Admin frontend fetches `/api/version` which proxies to `http://backend:8000/api/version`, but the backend `/version` endpoint is mounted at `/version` not `/api/version`.
**Why it happens:** Admin next.config.ts rewrites `/api/:path*` → `http://localhost:8000/api/:path*` (keeps the `/api/` prefix). So `/api/version` → `http://backend/api/version` which is 404.
**How to avoid:** The backend `/version` endpoint must be accessible at `/api/version` (i.e., mounted under `/api/` prefix) OR the admin frontend must fetch `/version` directly (no proxy). Since the admin frontend's proxy keeps the `/api/` prefix, and the backend doesn't have a `/api/version` path, options are:
  - Mount the backend `/version` router under `/api/` prefix in `main.py`, OR
  - Fetch directly from the backend URL in a server component (bypassing proxy), OR
  - Use a different path like `/api/version` in the backend

  **Recommended:** Add a separate route at `/api/version` on the backend that also returns version info, OR mount the version router at both `/version` and `/api/version`.

  **Alternative:** In `main.py`, include the version router twice:
  ```python
  app.include_router(version.router)         # /version
  app.include_router(version.router, prefix="/api")  # /api/version
  ```
  The public frontend fetches `/version` (proxied to `http://backend/version`).
  The admin frontend fetches `/api/version` (proxied to `http://backend/api/version`).

### Pitfall 4: Backend Health Endpoint Response Format Mismatch
**What goes wrong:** The frontend `/api/health` route handlers return `{status:"ok"}` (from Next.js directly), but the backend `/health` endpoint returns `{status:"healthy", version:"0.1.0"}`. If someone uses the backend health route for frontend health checks, they get a different format.
**Why it happens:** Backend and frontend health routes are separate — PRE-04/PRE-05 create Next.js-level health routes, not proxy routes to backend.
**How to avoid:** The backend `/health` endpoint does NOT need to be changed for this phase. The frontend health routes are implemented as standalone Next.js route handlers returning `{status:"ok"}`. These are independent endpoints.

### Pitfall 5: TanStack Query Missing in Admin Frontend for Version Hook
**What goes wrong:** Developer creates a `useAppVersion` hook using `@tanstack/react-query` in admin-frontend but the QueryClient provider is not set up.
**Why it happens:** Need to verify TanStack Query is properly configured in admin-frontend.
**How to avoid:** Check admin-frontend's layout/providers for QueryClientProvider. Admin-frontend already uses `useQuery` in multiple hooks (`useSettings.ts`, `useUsers.ts`, etc.), so QueryClient is confirmed set up.

---

## Code Examples

Verified patterns from official sources and codebase inspection:

### Next.js Standalone + BACKEND_URL Rewrite (public frontend)
```typescript
// frontend/next.config.ts
// Source: https://nextjs.org/docs/app/api-reference/config/next-config-js/output
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL ?? "http://localhost:8000"}/:path*`,
      },
    ];
  },
};

export default nextConfig;
```

### Next.js Health Route Handler
```typescript
// frontend/src/app/api/health/route.ts (same for admin-frontend)
// Source: https://nextjs.org/docs/app/api-reference/file-conventions/route
import { NextResponse } from "next/server";

export function GET() {
  return NextResponse.json({ status: "ok" });
}
```

### FastAPI Version Router
```python
# backend/app/routers/version.py
import os
from fastapi import APIRouter

router = APIRouter(tags=["Version"])

@router.get("/version")
async def get_version():
    """Returns application version and deployment environment."""
    return {
        "version": os.getenv("APP_VERSION", "dev"),
        "environment": os.getenv("SPECTRA_MODE", "dev"),
    }
```

### Register version router in main.py
```python
# backend/app/main.py (addition)
from app.routers import auth, chat, chat_sessions, files, health, search, version

# After health router (health is always available):
app.include_router(health.router)
app.include_router(version.router)  # Always available (all modes)

# Or for dual-path support:
app.include_router(version.router)           # /version
app.include_router(version.router, prefix="/api")  # /api/version
```

### useAppVersion Hook (public frontend)
```typescript
// frontend/src/hooks/useAppVersion.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface AppVersion {
  version: string;
  environment: string;
}

export function useAppVersion() {
  return useQuery<AppVersion>({
    queryKey: ["app", "version"],
    queryFn: async () => {
      const res = await apiClient.get("/version");
      if (!res.ok) throw new Error("Failed to fetch version");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}
```

### AccountInfo.tsx version display (public frontend)
```typescript
// Add to AccountInfo.tsx
import { useAppVersion } from "@/hooks/useAppVersion";

// Inside AccountInfo component:
const { data: versionData } = useAppVersion();

// In JSX, add a new section:
<div className="space-y-2">
  <Label>App Version</Label>
  <p className="text-sm text-muted-foreground">
    {versionData?.version ?? "—"}
  </p>
</div>
```

### Admin frontend version display
```typescript
// admin-frontend: add useAppVersion hook using adminApiClient
import { useQuery } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";

export function useAppVersion() {
  return useQuery({
    queryKey: ["app", "version"],
    queryFn: async () => {
      // Note: adminApiClient proxies /api/:path* → backend/api/:path*
      // So /api/version → backend/api/version (backend must serve at /api/version)
      const res = await adminApiClient.get("/api/version");
      if (!res.ok) throw new Error("Failed to fetch version");
      return res.json();
    },
    staleTime: 5 * 60 * 1000,
  });
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `middleware.ts` + `middleware()` export | `proxy.ts` + `proxy()` export | Next.js 16.0.0 (Oct 2025) | Both apps use 16.1.6; use `proxy.ts` for new proxy files |
| `pages/api/health.ts` | `src/app/api/health/route.ts` | Next.js 13+ (App Router) | Both apps use App Router; use route handlers |
| `serverRuntimeConfig` | Removed in Next.js 16 | Next.js 16 | Do NOT use `serverRuntimeConfig` |
| Global process.env in rewrites | `proxy.ts` with `NextResponse.rewrite()` | Next.js 16 | True runtime env support |

**Deprecated/outdated:**
- `middleware.ts`: Deprecated in Next.js 16, renamed to `proxy.ts`. The `middleware.ts` file still works but shows deprecation warning.
- `serverRuntimeConfig`: Removed entirely in Next.js 16.
- `pages/api/` directory pattern: Both apps use App Router; use `app/api/*/route.ts`.

---

## Open Questions

1. **Should `proxy.ts` or `rewrites()` be used for BACKEND_URL?**
   - What we know: `rewrites()` in `next.config.ts` bakes the URL at build time in standalone mode; `proxy.ts` evaluates at runtime.
   - What's unclear: Phase 33 scope — does "no image rebuild on URL change" mean Docker image rebuild, or just source code change?
   - Recommendation: If Docker portability is critical (different URL per environment), use `proxy.ts`. If local dev + single-environment Docker is acceptable, use `rewrites()` with `process.env.BACKEND_URL` — simpler and meets the letter of PRE-03. **Document the limitation in the plan.**

2. **Should backend `/version` be available at both `/version` and `/api/version`?**
   - What we know: Public frontend proxies `/api/:path*` → `backend/:path*` (strips `/api/`); admin frontend proxies `/api/:path*` → `backend/api/:path*` (keeps `/api/`).
   - What's unclear: Whether the planner expects a single fetch path that works in both frontends.
   - Recommendation: Mount the version router at both paths in `main.py` (one include without prefix, one with `/api` prefix). Zero code duplication, works for both frontends.

3. **Does the `APP_VERSION` env var need to be documented in `.env.example`?**
   - What we know: `.env.example` documents all env vars; `APP_VERSION` is new.
   - Recommendation: Yes, add `APP_VERSION=` to `.env.example` with a comment explaining it defaults to `"dev"`.

---

## Sources

### Primary (HIGH confidence)
- Next.js 16.1.6 official docs (fetched 2026-02-18) — standalone output, route handlers, proxy.ts, rewrites
  - https://nextjs.org/docs/app/api-reference/config/next-config-js/output
  - https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites
  - https://nextjs.org/docs/app/api-reference/file-conventions/proxy
  - https://nextjs.org/docs/app/api-reference/file-conventions/route
  - https://nextjs.org/docs/app/guides/self-hosting
  - https://nextjs.org/blog/next-16
- Codebase inspection (fetched 2026-02-18) — both `next.config.ts` files, all hook files, backend `main.py`, `config.py`, `health.py`

### Secondary (MEDIUM confidence)
- Next.js GitHub issue #21888 — confirms rewrites/next.config.js vars inlined at build time
- Next.js GitHub discussion #33932 — "Rewrites are only configurable at build time"
- Next.js GitHub discussion #34894 — standalone output + serverRuntimeConfig limitations

### Tertiary (LOW confidence)
- Community blog posts on Next.js Docker + standalone — consistent with official docs findings

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Next.js 16.1.6 docs fetched directly; codebase inspected
- Architecture: HIGH — all file locations confirmed by codebase inspection; patterns verified against official docs
- Pitfalls: HIGH — rewrites build-time baking confirmed by multiple official GitHub issues; path mapping verified by reading both `next.config.ts` files
- Version endpoint: HIGH — FastAPI patterns consistent with existing codebase; `spectra_mode` already in settings

**Research date:** 2026-02-18
**Valid until:** 2026-03-18 (stable APIs — Next.js 16.x, FastAPI 0.115+)
