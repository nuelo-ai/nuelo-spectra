# Phase 39: API Key Management UI + Deployment Mode - Research

**Researched:** 2026-02-24
**Domain:** Frontend UI (React/Next.js), Admin backend (FastAPI), Deployment (Dokploy)
**Confidence:** HIGH

## Summary

Phase 39 builds on the API key infrastructure completed in Phase 38 (model, service, endpoints, basic frontend UI). The work divides into four streams: (1) enhancing the existing public frontend `ApiKeySection` to show additional columns (credit usage, last used), (2) adding admin backend endpoints for managing any user's API keys, (3) building an admin frontend "API Keys" tab in the existing `UserDetailTabs` component, and (4) configuring the `SPECTRA_MODE=api` backend as a deployable standalone Dokploy service with a dedicated health endpoint.

The codebase is well-structured. Phase 38 already established the `ApiKeyService`, `ApiKey` model, Pydantic schemas, and frontend hooks. The admin side follows a clear pattern: admin router under `/api/admin/users/{user_id}/`, `CurrentAdmin` dependency for auth, `UserDetailTabs` for the tabbed UI in the user detail page. The deployment follows documented Dokploy conventions with 4 existing services.

**Primary recommendation:** Follow existing patterns exactly -- extend `ApiKeyService` with admin methods (list-for-any-user, create-for-user, revoke-for-user), add admin router endpoints mirroring the Phase 38 `/v1/keys` pattern but under `/api/admin/users/{user_id}/api-keys`, add a new tab to `UserDetailTabs`, enhance the existing public `ApiKeySection`, and document the 5th Dokploy Application configuration in `DEPLOYMENT.md`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Create key flow: user enters a required name -> modal dialog displays the full key once with copy button and "won't be shown again" warning -> user must explicitly dismiss
- Key list shows per row: name, key prefix (sk-...xxxx), created date, last used timestamp, total credit usage
- All users see last used and credit usage for their own keys (not admin-only)
- Revoke flow: click revoke -> confirmation dialog showing key name -> confirm to revoke
- Key name is required when creating (e.g., "Production server", "CI pipeline")
- Admin key management lives inside the user detail panel in User Management (not a separate tab)
- Admin clicks a user -> sees their details -> API Keys section within that view
- Admin sees all keys for a user: active and revoked, with visual status (revoked keys dimmed/struck-through with revocation date)
- Keys created by admin show a "Created by admin" badge/tag for transparency
- Admin can create and revoke keys on behalf of any user
- Admin uses the same confirmation dialog flow when revoking (no streamlined bypass)
- New "API Keys" tab added as the 5th tab (last position): Overview | Credit | Activity | Session | API Keys
- API Keys tab uses the same card/section style as existing tabs (consistent spacing, typography, containers)
- API Keys tab is visible to all users (no gating by role or feature flag)
- API service uses subdomain pattern: api.spectra.domain (not path-based)
- Dedicated GET /api/v1/health endpoint returning 200 + JSON with service status and DB connectivity
- In SPECTRA_MODE=api, only mount /api/v1/ routes + health check -- no static files, no WebSocket, no frontend routes, no non-API backend routes
- Dokploy Application settings documented (not a separate docker-compose file) -- matches how existing 4 services are configured

### Claude's Discretion
- Exact modal/dialog component implementation (reuse existing UI library patterns)
- Loading states and error handling within the API Keys tab
- Health check response schema details
- Exact styling of "Created by admin" badge
- How revoked keys are visually distinguished (dimmed, struck-through, or grayed)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APIKEY-06 | Admin can view API keys for all users from User Management | Admin backend endpoint `GET /api/admin/users/{user_id}/api-keys` + new "API Keys" tab in `UserDetailTabs` |
| APIKEY-07 | Admin can create API keys on behalf of any user | Admin backend endpoint `POST /api/admin/users/{user_id}/api-keys` + create dialog in admin tab with "Created by admin" tracking |
| APIKEY-08 | Admin can revoke any user's API keys | Admin backend endpoint `DELETE /api/admin/users/{user_id}/api-keys/{key_id}` + revoke confirmation dialog |
| APIINFRA-03 | API service is deployable as a 5th Dokploy service with its own public HTTPS domain | Dedicated `/api/v1/health` endpoint, mode-aware route mounting already works, DEPLOYMENT.md section for 5th service |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Admin API endpoints | Already used for all backend routes |
| SQLAlchemy | 2.0+ | Database queries (ApiKey model) | Already used project-wide |
| React/Next.js | 15.x | Frontend UI components | Already used in both frontends |
| TanStack Query | 5.x | Data fetching hooks | Already used in both frontends |
| shadcn/ui | latest | UI component library | Already used in both frontends |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.x | Request/response schemas | Admin API key schemas |
| sonner | latest | Toast notifications | Success/error feedback |
| lucide-react | latest | Icons (Key, Plus, Trash2, Shield) | UI icons |

### Alternatives Considered
None -- all libraries are already in the project. No new dependencies needed.

## Architecture Patterns

### Recommended Project Structure
```
Backend additions:
backend/app/routers/admin/api_keys.py     # Admin API key management endpoints
backend/app/schemas/api_key.py             # Extend with admin-specific schemas
backend/app/services/api_key.py            # Extend with admin methods

Frontend (public) modifications:
frontend/src/components/settings/ApiKeySection.tsx  # Enhance with credit usage column
frontend/src/hooks/useApiKeys.ts                     # Update types if schema changes

Admin frontend additions:
admin-frontend/src/components/users/UserApiKeysTab.tsx  # New tab component
admin-frontend/src/hooks/useApiKeys.ts                   # Admin API key hooks
admin-frontend/src/types/api-key.ts                      # TypeScript types

Backend deployment:
backend/app/routers/api_v1/health.py       # Dedicated /api/v1/health endpoint
```

### Pattern 1: Admin Endpoint Pattern (following existing users.py)
**What:** Admin endpoints use `CurrentAdmin` dependency, are mounted under `/api/admin/`, and follow the existing CRUD patterns in `backend/app/routers/admin/users.py`.
**When to use:** All admin API key management endpoints.
**Example:**
```python
# backend/app/routers/admin/api_keys.py
from app.dependencies import CurrentAdmin, DbSession

router = APIRouter(prefix="/users/{user_id}/api-keys", tags=["admin-api-keys"])

@router.get("", response_model=list[AdminApiKeyListItem])
async def list_user_api_keys(
    user_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    return await ApiKeyService.list_for_user(db, user_id)
```

### Pattern 2: Admin Frontend Tab Pattern (following UserDetailTabs.tsx)
**What:** The admin `UserDetailTabs` component uses shadcn/ui `Tabs` with separate tab components. Add "API Keys" as the 5th tab.
**When to use:** The admin user detail page.
**Example:**
```tsx
// In UserDetailTabs.tsx
<TabsTrigger value="api-keys">API Keys</TabsTrigger>
<TabsContent value="api-keys" className="mt-4">
  <ApiKeysTab user={user} />
</TabsContent>
```

### Pattern 3: ApiKeyService Extension for Admin
**What:** Add static methods to `ApiKeyService` for admin operations. Admin create needs `created_by_admin` tracking. Admin revoke does NOT check `user_id` match (admin can revoke any key).
**When to use:** Admin API key endpoints.
**Example:**
```python
@staticmethod
async def admin_revoke(db: AsyncSession, key_id: UUID) -> bool:
    """Admin revoke -- no user_id check (admin can revoke any key)."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return False
    api_key.is_active = False
    await db.flush()
    return True
```

### Pattern 4: Mode-Aware Health Endpoint
**What:** A dedicated `/api/v1/health` endpoint that checks DB connectivity, separate from the existing `/health` endpoint. Mounted only in `api` and `dev` modes via the existing `api_v1_router`.
**When to use:** The API service deployment health check.
**Example:**
```python
# backend/app/routers/api_v1/health.py
@router.get("/health")
async def api_health(db: DbSession):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "spectra-api",
        "database": db_status,
    }
```

### Anti-Patterns to Avoid
- **Separate admin API key service class:** Don't create `AdminApiKeyService`. Extend the existing `ApiKeyService` with admin-specific static methods.
- **Separate frontend ApiKeySection for admin:** The admin uses a completely different component (`UserApiKeysTab`) since it operates on any user, not the current user.
- **Mounting admin key endpoints outside the admin router:** Must be under `/api/admin/` via `admin_router` for authentication and CORS consistency.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal dialogs | Custom modal | shadcn/ui `Dialog` and `AlertDialog` | Already used in `ApiKeySection.tsx` and `UserDetailTabs.tsx` |
| Toast notifications | Custom notification system | `sonner` toast | Already used project-wide |
| Data fetching | Custom fetch logic | TanStack Query mutations/queries | Already used in both frontends |
| Admin auth | Custom admin check | `CurrentAdmin` dependency | Already handles JWT verification, admin role check |
| Form state | Form library | `useState` hooks | Consistent with all existing settings components |

**Key insight:** Every UI component and backend pattern needed already exists in the codebase. This phase is about composition and extension, not introducing anything new.

## Common Pitfalls

### Pitfall 1: Missing "created_by_admin" Tracking
**What goes wrong:** Admin creates keys on behalf of users but there's no way to distinguish admin-created keys from user-created keys.
**Why it happens:** The `ApiKey` model doesn't have a `created_by` field.
**How to avoid:** Add `created_by_admin_id: UUID | None` column to the `ApiKey` model (nullable -- NULL means self-created). Requires an Alembic migration.
**Warning signs:** No "Created by admin" badge can be displayed without this field.

### Pitfall 2: Admin Revoke Without user_id Verification
**What goes wrong:** Reusing the existing `ApiKeyService.revoke()` which checks `user_id` match.
**Why it happens:** The existing revoke method enforces ownership (user can only revoke their own keys).
**How to avoid:** Create a separate `admin_revoke(db, key_id)` method that does NOT filter by `user_id`, or add an optional `skip_user_check` parameter.
**Warning signs:** Admin revoke returns 404 when trying to revoke another user's key.

### Pitfall 3: Credit Usage Not in ApiKey Model
**What goes wrong:** The CONTEXT requires showing "total credit usage" per key. This data does not currently exist.
**Why it happens:** Phase 38 built the key infrastructure without credit tracking per key (that's Phase 40: APISEC-03/04).
**How to avoid:** Two options: (a) add a `total_credits_used` field to `ApiKey` now (denormalized counter, updated when credit deduction happens in Phase 40), or (b) show the column as "0.0" or "--" now and populate it in Phase 40 when API usage tracking is implemented.
**Warning signs:** Frontend expects a `credit_usage` field that the backend schema doesn't return.

### Pitfall 4: Settings Page Tab Confusion
**What goes wrong:** Trying to convert the public Settings page to a tabbed layout when it currently uses stacked sections.
**Why it happens:** The CONTEXT mentions "5th tab" but the public Settings page currently has 4 stacked Card components (ProfileForm, PasswordForm, AccountInfo, ApiKeySection), not tabs.
**How to avoid:** The "5th tab" language in CONTEXT refers to the fact that ApiKeySection is the 5th logical section. The existing `ApiKeySection` component from Phase 38 is already rendered on the Settings page. Enhance it in-place with the additional columns (credit usage, last used). Do NOT refactor the Settings page to use tabs.
**Warning signs:** Unnecessary refactoring of the entire Settings page layout.

### Pitfall 5: Forgetting to Register Admin API Keys Router
**What goes wrong:** New `admin/api_keys.py` router not included in `admin_router` in `__init__.py`.
**Why it happens:** Easy to create the file but forget to register it.
**How to avoid:** Add `from app.routers.admin import api_keys as admin_api_keys` and `admin_router.include_router(admin_api_keys.router)` in `backend/app/routers/admin/__init__.py`.
**Warning signs:** Admin key endpoints return 404.

### Pitfall 6: API Mode Health Check vs Existing Health Check
**What goes wrong:** Confusing the existing `GET /health` endpoint with the new `GET /api/v1/health` endpoint.
**Why it happens:** Both serve health check purposes but at different paths.
**How to avoid:** The existing `/health` is a basic "is the server running" check (no DB probe). The new `/api/v1/health` should include DB connectivity for the API service. Dokploy's HEALTHCHECK in the Dockerfile can use `/health` (fast, no DB), while the API service domain health monitoring uses `/api/v1/health` (includes DB check).
**Warning signs:** Health check flapping because DB check adds latency.

### Pitfall 7: SPECTRA_MODE=api Still Mounting Non-API Routes
**What goes wrong:** The `api` mode mounts routes that shouldn't exist (auth, files, chat, admin).
**Why it happens:** The mode-aware routing in `main.py` already handles this correctly (api mode only mounts `api_v1_router`), but the lifespan function runs LLM validation and scheduler setup that may not be needed.
**How to avoid:** Review `main.py` lifespan function. LLM validation IS needed (API mode runs analysis queries). Scheduler should NOT run in API mode (`ENABLE_SCHEDULER=false`). The existing `settings.enable_scheduler` toggle handles this.
**Warning signs:** API service startup fails because scheduler-related env vars are missing.

## Code Examples

### Admin API Key Endpoints (backend pattern)
```python
# backend/app/routers/admin/api_keys.py
from uuid import UUID
from fastapi import APIRouter, HTTPException, Request
from app.dependencies import CurrentAdmin, DbSession
from app.services.api_key import ApiKeyService
from app.services.admin.audit import log_admin_action
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, AdminApiKeyListItem

router = APIRouter(prefix="/users/{user_id}/api-keys", tags=["admin-api-keys"])

@router.get("", response_model=list[AdminApiKeyListItem])
async def list_user_api_keys(
    user_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """List all API keys for a specific user (admin view)."""
    return await ApiKeyService.list_for_user(db, user_id)

@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_user_api_key(
    user_id: UUID,
    body: ApiKeyCreateRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Create an API key on behalf of a user (admin)."""
    api_key, full_key = await ApiKeyService.create(
        db, user_id, body.name, body.description,
        created_by_admin_id=current_admin.id,
    )
    await log_admin_action(
        db, admin_id=current_admin.id,
        action="create_api_key", target_type="api_key",
        target_id=str(api_key.id),
        details={"user_id": str(user_id), "key_name": body.name},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return ApiKeyCreateResponse(
        id=api_key.id, name=api_key.name,
        key_prefix=api_key.key_prefix, full_key=full_key,
        created_at=api_key.created_at,
    )

@router.delete("/{key_id}", status_code=204)
async def revoke_user_api_key(
    user_id: UUID,
    key_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
):
    """Revoke an API key for a user (admin)."""
    revoked = await ApiKeyService.admin_revoke(db, key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
    await log_admin_action(
        db, admin_id=current_admin.id,
        action="revoke_api_key", target_type="api_key",
        target_id=str(key_id),
        details={"user_id": str(user_id)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
```

### Admin Frontend API Key Hooks Pattern
```typescript
// admin-frontend/src/hooks/useApiKeys.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApiClient } from "@/lib/admin-api-client";
import { toast } from "sonner";

export function useUserApiKeys(userId: string | undefined) {
  return useQuery({
    queryKey: ["admin", "users", userId, "api-keys"],
    queryFn: async () => {
      const res = await adminApiClient.get(`/api/admin/users/${userId}/api-keys`);
      if (!res.ok) throw new Error("Failed to fetch API keys");
      return res.json();
    },
    enabled: !!userId,
  });
}

export function useCreateUserApiKey(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: { name: string; description?: string }) => {
      const res = await adminApiClient.post(`/api/admin/users/${userId}/api-keys`, data);
      if (!res.ok) throw new Error("Failed to create API key");
      return res.json();
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users", userId, "api-keys"] });
      toast.success("API key created");
    },
  });
}

export function useRevokeUserApiKey(userId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (keyId: string) => {
      const res = await adminApiClient.delete(`/api/admin/users/${userId}/api-keys/${keyId}`);
      if (!res.ok) throw new Error("Failed to revoke API key");
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin", "users", userId, "api-keys"] });
      toast.success("API key revoked");
    },
  });
}
```

### API v1 Health Endpoint with DB Check
```python
# backend/app/routers/api_v1/health.py
from fastapi import APIRouter
from sqlalchemy import text
from app.dependencies import DbSession
from app.config import get_settings

router = APIRouter(tags=["API v1 Health"])

@router.get("/health")
async def api_v1_health(db: DbSession):
    settings = get_settings()
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    status = "healthy" if db_status == "connected" else "degraded"
    return {
        "status": status,
        "service": "spectra-api",
        "version": settings.app_version,
        "database": db_status,
    }
```

### ApiKey Model Migration (add created_by_admin_id)
```python
# Alembic migration
def upgrade():
    op.add_column('api_keys', sa.Column(
        'created_by_admin_id', sa.UUID(), nullable=True,
        comment='Admin who created this key on behalf of user (NULL = self-created)'
    ))
    op.create_foreign_key(
        'fk_api_keys_created_by_admin',
        'api_keys', 'users',
        ['created_by_admin_id'], ['id'],
        ondelete='SET NULL'
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stacked sections on Settings page | Still stacked sections | Current | ApiKeySection is already the 4th section -- enhance in-place |
| 4 Dokploy services | Adding 5th for API | This phase | Same Dockerfile.backend, different SPECTRA_MODE and domain |

## Open Questions

1. **Credit usage per API key**
   - What we know: CONTEXT requires "total credit usage" column per key. Phase 40 implements credit deduction (APISEC-03/04).
   - What's unclear: Should Phase 39 add the `total_credits_used` column to `ApiKey` now (to display 0.0), or defer it entirely to Phase 40?
   - Recommendation: Add the column now with default 0.0 and display it. Phase 40 will populate it when credit deduction is implemented. This avoids a UI gap.

2. **Revocation date display**
   - What we know: CONTEXT says admin sees revoked keys with "revocation date". The `ApiKey` model has no `revoked_at` column.
   - What's unclear: Should we add a `revoked_at` timestamp column?
   - Recommendation: Add `revoked_at: DateTime | None` column. Set it when `is_active` transitions to False. Cleaner than deriving from audit logs.

3. **API mode lifespan considerations**
   - What we know: `SPECTRA_MODE=api` will run the same `main.py` lifespan (LLM validation, SMTP check, checkpointer setup).
   - What's unclear: Should API mode skip SMTP validation and scheduler? The scheduler is already toggled by `ENABLE_SCHEDULER`.
   - Recommendation: Set `ENABLE_SCHEDULER=false` for the API service. LLM validation and checkpointer are needed (API mode will serve analysis queries in Phase 40). SMTP validation can remain (harmless if not configured).

## Sources

### Primary (HIGH confidence)
- Existing codebase: `backend/app/models/api_key.py`, `backend/app/services/api_key.py`, `backend/app/routers/api_v1/api_keys.py` -- Phase 38 implementation
- Existing codebase: `backend/app/routers/admin/users.py` -- Admin endpoint patterns
- Existing codebase: `admin-frontend/src/components/users/UserDetailTabs.tsx` -- Admin tab UI patterns
- Existing codebase: `frontend/src/components/settings/ApiKeySection.tsx` -- Public frontend API key UI
- Existing codebase: `backend/app/main.py` -- Mode-aware route mounting
- Existing codebase: `DEPLOYMENT.md` -- Dokploy deployment patterns for all 4 services
- Existing codebase: `compose.yaml` -- Docker Compose local dev setup

### Secondary (MEDIUM confidence)
- CONTEXT.md user decisions -- locked decisions for UI/UX flow

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in use, no new dependencies
- Architecture: HIGH - All patterns established in prior phases, pure extension
- Pitfalls: HIGH - Identified from direct codebase analysis (missing columns, auth patterns)

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable -- no external dependency changes)
