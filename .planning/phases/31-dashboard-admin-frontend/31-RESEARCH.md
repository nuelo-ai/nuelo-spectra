# Phase 31: Dashboard & Admin Frontend - Research

**Researched:** 2026-02-16
**Domain:** Next.js admin dashboard application, Recharts, admin API integration
**Confidence:** HIGH

## Summary

Phase 31 builds a separate Next.js application (`admin-frontend/`) providing a visual admin interface for all backend admin APIs built in Phases 26-30. The project already has a mature public frontend (`frontend/`) using Next.js 16.1.6, TanStack Query v5, Zustand v5, shadcn/ui (new-york style), and Tailwind CSS v4 -- the admin frontend mirrors this exact stack with the addition of Recharts for dashboard charts.

A critical finding: **the backend has NO dashboard metrics endpoint**. All DASH-01 through DASH-07 requirements need a new aggregation endpoint (e.g., `GET /api/admin/dashboard`) that queries total users, signups over time, sessions, files, messages, and credit summaries. Similarly, there is **no audit log listing endpoint** -- only a `log_admin_action` writer exists. Both backend endpoints must be created as part of this phase to support the frontend.

The admin auth flow is distinct from the public auth: admin login returns only an `access_token` (no refresh token), session uses sliding window via `AdminTokenReissueMiddleware` that reissues tokens in the `X-Admin-Token` response header, and the admin timeout is 30 minutes by default. The admin frontend API client must intercept this header on every response and update the stored token.

**Primary recommendation:** Scaffold `admin-frontend/` as a standalone Next.js app on port 3001, reusing the same toolchain and shadcn/ui components. Create 2 new backend endpoints (dashboard metrics + audit log listing), then build the admin API client with X-Admin-Token interception, admin auth context, and all pages: login, dashboard, users list, user detail (tabbed), invitations, credits, settings, and audit log.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Dashboard layout
- Hero section: row of 6 metric cards at the top (total users, active today, new signups, total sessions, messages sent, credit balance)
- Below cards: 2 trend charts side-by-side (signups over time on left, messages over time on right), equal width
- Below charts: credit section with credit distribution by tier (pie/bar chart) + low-credit users table
- Dashboard is a single-page overview -- admin sees the full platform health at a glance

#### Navigation & pages
- Fixed left sidebar with icons + labels, collapsible to icon-only
- Pages grouped into sections:
  - **Overview:** Dashboard
  - **People:** Users, Invitations
  - **Platform:** Credits, Settings, Audit Log
- User detail view: separate page at `/users/:id` (not slide-over panel)
- User detail page uses tabbed sections: Overview | Credits | Activity | Sessions

#### Data tables & actions
- Comfortable row spacing (medium density) with avatar + name in first column
- Row-level actions via three-dot dropdown menu at end of each row
- Bulk operations supported: checkbox column on left, bulk action bar appears at top when rows selected (activate, deactivate, tier change, credit adjust, delete)
- Search bar at top with filter dropdowns (status, tier, date range) shown as removable chips when active

#### Confirmation patterns
- Destructive actions (delete user, bulk delete): 6-character alphanumeric challenge code with paste disabled on confirmation input (per Phase 29 context)
- Less severe actions (deactivate, revoke invite): standard confirm modal

#### Visual style
- Theme: follows public Spectra frontend pattern -- system preference as default, overridable with user preference (dark/light toggle)
- Visual mood: professional & structured (clear section dividers, color badges, status indicators -- Stripe dashboard style)
- Distinct admin look: different accent color/styling from public frontend to visually separate admin from consumer app
- **MANDATORY: Use `/frontend-design` skill for all layout and design implementation** -- distinctive, production-grade design quality required

### Claude's Discretion
- Specific accent color palette for admin portal
- Exact sidebar width and collapse breakpoint
- Chart time range selectors (7d/30d/90d)
- Loading states and skeleton patterns
- Toast notification style for action confirmations
- Responsive behavior (if any -- may be desktop-only)
- Audit log page layout and filtering

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DASH-01 | Dashboard shows total registered users (active vs inactive count) | New `GET /api/admin/dashboard` endpoint needed; query `users` table with `COUNT` and `is_active` grouping |
| DASH-02 | Dashboard shows new user signups (today / this week / this month) | Same dashboard endpoint; `COUNT` with `created_at` date range filters |
| DASH-03 | Dashboard shows total chat sessions created (platform-wide) | Same dashboard endpoint; `COUNT` on `chat_sessions` table |
| DASH-04 | Dashboard shows total files uploaded (platform-wide) | Same dashboard endpoint; `COUNT` on `files` table |
| DASH-05 | Dashboard shows total messages sent (platform-wide) | Same dashboard endpoint; `COUNT` on `chat_messages` table |
| DASH-06 | Dashboard shows credit consumption summary (total used / total remaining) | Same dashboard endpoint; aggregate from `user_credits` table or `credit_transactions`; existing `CreditService.get_credit_distribution` partially covers this |
| DASH-07 | Dashboard displays trend charts for signups over time and messages over time (Recharts) | Same dashboard endpoint returns time-series arrays; Recharts `LineChart` or `AreaChart` renders them |
| ARCH-06 | Separate `admin-frontend/` Next.js application | Scaffold with `npx create-next-app@latest admin-frontend` matching frontend stack |
| ARCH-07 | Admin frontend uses same stack as public frontend | Next.js 16.x, TanStack Query v5, Zustand v5, shadcn/ui, Recharts (new addition) |
| ARCH-09 | Local dev runs 3 processes (backend:8000, frontend:3000, admin:3001) | `next dev --port 3001` in admin-frontend package.json |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 16.1.6 | React framework with App Router | Matches existing frontend exactly |
| react / react-dom | 19.2.3 | UI library | Matches existing frontend |
| @tanstack/react-query | ^5.90.20 | Server state management | Matches existing frontend |
| @tanstack/react-table | ^8.21.3 | Headless table with sorting/filtering/pagination | Matches existing frontend, used for user/invitation/audit tables |
| zustand | ^5.0.11 | Client state management | Matches existing frontend |
| recharts | ^2.x (latest 2.x) | Chart library for dashboard visualizations | Specified in requirements; React-native chart library with LineChart, AreaChart, PieChart, BarChart |
| radix-ui | ^1.4.3 | Headless UI primitives (via shadcn/ui) | Matches existing frontend |
| lucide-react | ^0.563.0 | Icon library | Matches existing frontend |
| next-themes | ^0.4.6 | Theme management (dark/light/system) | Matches existing frontend |
| sonner | ^2.0.7 | Toast notifications | Matches existing frontend |
| tailwindcss | ^4 | Utility-first CSS | Matches existing frontend |
| class-variance-authority | ^0.7.1 | Component variant management | Matches existing frontend (shadcn/ui dependency) |
| clsx | ^2.1.1 | Conditional className utility | Matches existing frontend |
| tailwind-merge | ^3.4.0 | Tailwind class deduplication | Matches existing frontend |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tw-animate-css | ^1.4.0 | Tailwind animation utilities | Matches existing frontend |
| @tailwindcss/postcss | ^4 | PostCSS plugin for Tailwind v4 | Build toolchain |

### Alternatives Considered
None -- stack is locked per ARCH-07 and user decisions. Recharts is the only new library vs. the public frontend (which uses Plotly for data visualization, but Recharts is specified for admin dashboard).

**Installation:**
```bash
cd admin-frontend
npm install next@16.1.6 react@19.2.3 react-dom@19.2.3 \
  @tanstack/react-query@^5.90.20 @tanstack/react-table@^8.21.3 \
  zustand@^5.0.11 recharts@^2 \
  radix-ui@^1.4.3 lucide-react@^0.563.0 next-themes@^0.4.6 \
  sonner@^2.0.7 class-variance-authority@^0.7.1 clsx@^2.1.1 \
  tailwind-merge@^3.4.0 tw-animate-css@^1.4.0

npm install -D tailwindcss@^4 @tailwindcss/postcss@^4 \
  @types/node@^20 @types/react@^19 @types/react-dom@^19 \
  typescript@^5 eslint@^9 eslint-config-next@16.1.6
```

## Architecture Patterns

### Recommended Project Structure
```
admin-frontend/
├── components.json          # shadcn/ui config (new-york style, neutral base)
├── eslint.config.mjs        # ESLint config (copy from frontend)
├── next.config.ts           # Rewrites /api/* -> localhost:8000/*
├── package.json             # dev script: next dev --port 3001
├── postcss.config.mjs       # Tailwind v4 PostCSS plugin
├── tsconfig.json            # Same as frontend
├── public/                  # Static assets
└── src/
    ├── app/
    │   ├── globals.css      # Tailwind + admin theme variables (different accent)
    │   ├── layout.tsx       # Root layout with ThemeProvider + Providers
    │   ├── page.tsx         # Redirect to /login or /dashboard
    │   ├── (auth)/
    │   │   ├── layout.tsx   # Centered auth layout
    │   │   └── login/
    │   │       └── page.tsx # Admin login page
    │   └── (admin)/
    │       ├── layout.tsx   # Admin shell: sidebar + main content area
    │       ├── dashboard/
    │       │   └── page.tsx # Dashboard with metrics + charts
    │       ├── users/
    │       │   ├── page.tsx          # User list with search/filter/bulk actions
    │       │   └── [userId]/
    │       │       └── page.tsx      # User detail (tabbed: Overview|Credits|Activity|Sessions)
    │       ├── invitations/
    │       │   └── page.tsx          # Invitation list with create/revoke/resend
    │       ├── credits/
    │       │   └── page.tsx          # Credit management overview
    │       ├── settings/
    │       │   └── page.tsx          # Platform settings form
    │       └── audit-log/
    │           └── page.tsx          # Audit log viewer with filters
    ├── components/
    │   ├── ui/              # shadcn/ui primitives (init fresh for admin)
    │   ├── dashboard/       # MetricCard, TrendChart, CreditDistribution, LowCreditTable
    │   ├── users/           # UserTable, UserFilters, BulkActionBar, UserDetailTabs
    │   ├── invitations/     # InvitationTable, CreateInviteDialog
    │   ├── credits/         # CreditDistributionChart, TransactionHistory
    │   ├── settings/        # SettingsForm
    │   ├── audit/           # AuditLogTable, AuditLogFilters
    │   ├── layout/          # AdminSidebar, AdminHeader, SidebarNavItem
    │   └── shared/          # ConfirmModal, ChallengeCodeDialog, StatusBadge, DataTableShell
    ├── hooks/
    │   ├── useAdminAuth.tsx          # Admin auth context (login, logout, token management)
    │   ├── useDashboard.ts           # TanStack Query hook for dashboard metrics
    │   ├── useUsers.ts               # TanStack Query hooks for user CRUD
    │   ├── useInvitations.ts         # TanStack Query hooks for invitations
    │   ├── useCredits.ts             # TanStack Query hooks for credit operations
    │   ├── useSettings.ts            # TanStack Query hooks for platform settings
    │   └── useAuditLog.ts            # TanStack Query hooks for audit log
    ├── lib/
    │   ├── admin-api-client.ts       # Fetch wrapper with X-Admin-Token interception
    │   ├── query-client.ts           # TanStack Query client config
    │   └── utils.ts                  # cn() and shared utilities
    ├── stores/
    │   └── sidebarStore.ts           # Sidebar collapse state (Zustand)
    └── types/
        ├── admin-auth.ts             # Admin login/token types
        ├── dashboard.ts              # Dashboard metrics types
        ├── user.ts                   # User list/detail types
        ├── invitation.ts             # Invitation types
        ├── credit.ts                 # Credit types
        ├── settings.ts               # Platform settings types
        └── audit.ts                  # Audit log types
```

### Pattern 1: Admin API Client with X-Admin-Token Interception
**What:** Unlike the public frontend which uses access + refresh tokens, the admin frontend uses a single access token with sliding window reissue. The backend's `AdminTokenReissueMiddleware` returns a fresh token in the `X-Admin-Token` response header on every successful admin API call.
**When to use:** Every admin API call except login.
**Example:**
```typescript
// admin-api-client.ts
const ADMIN_TOKEN_KEY = "spectra_admin_token";

export function setAdminToken(token: string): void {
  localStorage.setItem(ADMIN_TOKEN_KEY, token);
}

export function getAdminToken(): string | null {
  return typeof window !== "undefined"
    ? localStorage.getItem(ADMIN_TOKEN_KEY)
    : null;
}

export function clearAdminToken(): void {
  localStorage.removeItem(ADMIN_TOKEN_KEY);
}

async function fetchWithAdminAuth(
  path: string,
  options: RequestInit
): Promise<Response> {
  const token = getAdminToken();
  const headers = new Headers(options.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`http://localhost:8000${path}`, {
    ...options,
    headers,
  });

  // Intercept X-Admin-Token for sliding window session renewal
  const newToken = response.headers.get("X-Admin-Token");
  if (newToken) {
    setAdminToken(newToken);
  }

  // If 401, redirect to login (session expired)
  if (response.status === 401) {
    clearAdminToken();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return response;
}

export const adminApiClient = {
  async get(path: string): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
  },
  async post(path: string, body?: any): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  },
  async patch(path: string, body: any): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },
  async put(path: string, body: any): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  },
  async delete(path: string, body?: any): Promise<Response> {
    return fetchWithAdminAuth(path, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  },
};
```

### Pattern 2: Admin Auth Context (No Refresh Token)
**What:** Admin auth is simpler than public auth -- login returns only `access_token` (no `refresh_token`). Session continuity relies on sliding window token reissue via `X-Admin-Token` header intercepted by the API client.
**When to use:** Admin login page and protected route guard.
**Example:**
```typescript
// useAdminAuth.tsx
interface AdminAuthContextType {
  user: AdminUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// Login calls POST /api/admin/auth/login
// Response: { access_token: string, token_type: "bearer" }
// Store token via setAdminToken(), then GET /auth/me to load user
// Note: admin /auth/me endpoint needs to verify is_admin claim
```

### Pattern 3: Dashboard Metrics Hook with TanStack Query
**What:** Single query hook that fetches all dashboard data from one aggregation endpoint.
**When to use:** Dashboard page.
**Example:**
```typescript
// useDashboard.ts
export function useDashboardMetrics() {
  return useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: async () => {
      const res = await adminApiClient.get("/api/admin/dashboard");
      if (!res.ok) throw new Error("Failed to fetch dashboard");
      return res.json();
    },
    staleTime: 30 * 1000, // 30 seconds - dashboard data refreshes frequently
    refetchInterval: 60 * 1000, // Auto-refresh every 60 seconds
  });
}
```

### Pattern 4: Recharts Line/Area Chart for Time Series
**What:** Recharts provides declarative chart components that integrate naturally with React.
**When to use:** Signups over time and messages over time trend charts.
**Example:**
```typescript
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";

// data format: [{ date: "2026-01-15", count: 12 }, ...]
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip />
    <Line type="monotone" dataKey="count" stroke="#8884d8" />
  </LineChart>
</ResponsiveContainer>
```

### Pattern 5: Next.js API Rewrites for Admin Backend
**What:** The admin frontend proxies `/api/*` to the backend at `localhost:8000` via Next.js rewrites, same pattern as the public frontend.
**When to use:** `next.config.ts`.
**Example:**
```typescript
// next.config.ts
const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};
```
Note: Admin routes are mounted at `/api/admin/*` on the backend, so `adminApiClient.get("/api/admin/dashboard")` will be rewritten to `http://localhost:8000/api/admin/dashboard`.

### Pattern 6: Bulk Operations with Checkbox Selection
**What:** TanStack Table supports row selection via `getRowModel` with checkbox column. When rows are selected, a bulk action bar appears at the top of the table.
**When to use:** User list page for bulk activate/deactivate/tier-change/credit-adjust/delete.
**Example:**
```typescript
// Column definition with checkbox
const columns: ColumnDef<UserSummary>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={table.getIsAllPageRowsSelected()}
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
      />
    ),
    enableSorting: false,
  },
  // ... other columns
];

const table = useReactTable({
  data,
  columns,
  enableRowSelection: true,
  state: { rowSelection },
  onRowSelectionChange: setRowSelection,
  // ...
});
```

### Anti-Patterns to Avoid
- **Sharing code between frontend/ and admin-frontend/ via symlinks or workspace:** These are separate apps. Copy shared utilities (cn(), query-client config) -- don't symlink. Maintaining separation is intentional per ARCH-06.
- **Using public frontend's refresh token flow:** Admin auth has NO refresh token. Don't try to implement token refresh -- the sliding window `X-Admin-Token` header handles session continuity.
- **Fetching dashboard metrics with multiple parallel queries:** Use a single aggregation endpoint to avoid N+1 API calls on dashboard load.
- **Client-side pagination for admin tables:** Use server-side pagination -- the backend already supports `page` and `per_page` parameters on list endpoints.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data tables with sort/filter/pagination | Custom table logic | @tanstack/react-table v8 | Already used in public frontend; handles all table state |
| Chart rendering | Canvas/SVG charts from scratch | Recharts v2 | Declarative React charts with built-in responsiveness, tooltips, legends |
| Theme management | Custom theme toggle | next-themes | Already proven in public frontend; handles system preference + local storage |
| Toast notifications | Custom notification system | sonner | Already used in public frontend |
| UI primitives (dialog, dropdown, checkbox) | Custom components | shadcn/ui via Radix primitives | Already used in public frontend; accessible by default |
| Sidebar collapse behavior | Custom sidebar state | Zustand store + CSS transitions | Simple state management; shadcn Sidebar component available as reference |

**Key insight:** This phase is a frontend integration effort, not a library-building effort. Every UI primitive needed already exists in the public frontend's component library. The work is: scaffold the app, create the admin-specific API client and auth flow, build the page layouts, and wire up data fetching.

## Common Pitfalls

### Pitfall 1: Missing Backend Endpoints
**What goes wrong:** Frontend tries to fetch dashboard metrics or audit logs, but no backend endpoint exists.
**Why it happens:** Phases 26-30 built admin CRUD endpoints but NOT aggregation/dashboard endpoints.
**How to avoid:** Create `GET /api/admin/dashboard` (metrics aggregation) and `GET /api/admin/audit-log` (paginated audit log listing) endpoints BEFORE building the frontend pages that consume them.
**Warning signs:** 404 errors on dashboard load; empty audit log page.

### Pitfall 2: X-Admin-Token Header Not Intercepted
**What goes wrong:** Admin session expires after 30 minutes even during active use because the sliding window token reissue is ignored.
**Why it happens:** The API client doesn't read the `X-Admin-Token` response header, so the token never gets refreshed.
**How to avoid:** Every response from the admin API client must check `response.headers.get("X-Admin-Token")` and update localStorage.
**Warning signs:** Admin gets logged out after exactly `admin_session_timeout_minutes` regardless of activity.

### Pitfall 3: CORS Header Exposure
**What goes wrong:** `X-Admin-Token` header is not readable from JavaScript because it's not in the CORS `expose_headers`.
**Why it happens:** Default CORS only exposes standard headers.
**How to avoid:** Backend already has `expose_headers=["X-Admin-Token"]` in CORS config (verified in `main.py`). Ensure the admin frontend origin (`http://localhost:3001`) is in the CORS allowed origins -- backend already adds `admin_cors_origin` when in `admin` or `dev` mode.
**Warning signs:** `response.headers.get("X-Admin-Token")` returns `null` even though backend is sending it.

### Pitfall 4: Admin Login Response Shape Differs from Public
**What goes wrong:** Code expects `refresh_token` in admin login response.
**Why it happens:** Copy-pasting from public frontend's auth hook.
**How to avoid:** Admin login returns `{ access_token, token_type }` only (see `AdminLoginResponse` schema). No refresh token. The auth hook must NOT look for or store a refresh token.
**Warning signs:** "Cannot read property 'refresh_token' of undefined" errors on login.

### Pitfall 5: Forgetting `--port 3001` in Dev Script
**What goes wrong:** Admin frontend starts on port 3000, conflicting with public frontend.
**Why it happens:** Default Next.js dev port is 3000.
**How to avoid:** Set `"dev": "next dev --port 3001"` in admin-frontend's `package.json`.
**Warning signs:** "Port 3000 is already in use" error.

### Pitfall 6: Challenge Code Paste Prevention
**What goes wrong:** Users paste challenge codes into confirmation input, bypassing the security intent.
**Why it happens:** Default HTML input allows paste.
**How to avoid:** Add `onPaste={(e) => e.preventDefault()}` on challenge code confirmation inputs for destructive actions (delete user, bulk delete).
**Warning signs:** Security review flags that paste is allowed on challenge code inputs.

### Pitfall 7: shadcn/ui Component Initialization
**What goes wrong:** Components reference `@/components/ui/button` but the file doesn't exist.
**Why it happens:** shadcn/ui components must be explicitly added via CLI (`npx shadcn@latest add button`).
**How to avoid:** After scaffolding the admin-frontend, run `npx shadcn@latest init` (with same config as frontend: new-york style, neutral base, CSS variables) then add all needed components.
**Warning signs:** Module not found errors for ui/ components.

## Code Examples

### Backend: Dashboard Metrics Endpoint (to be created)
```python
# backend/app/routers/admin/dashboard.py
"""Admin dashboard metrics endpoint."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select, and_

from app.dependencies import CurrentAdmin, DbSession
from app.models.user import User
from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage
from app.models.file import File

router = APIRouter(prefix="/dashboard", tags=["admin-dashboard"])


@router.get("")
async def get_dashboard_metrics(
    db: DbSession,
    current_admin: CurrentAdmin,
    days: int = Query(default=30, ge=7, le=90),
) -> dict:
    """Aggregate platform metrics for dashboard (DASH-01 through DASH-07)."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # DASH-01: Total users (active vs inactive)
    user_counts = await db.execute(
        select(User.is_active, func.count(User.id)).group_by(User.is_active)
    )
    active_map = {row[0]: row[1] for row in user_counts.all()}
    total_users = sum(active_map.values())
    active_users = active_map.get(True, 0)
    inactive_users = active_map.get(False, 0)

    # DASH-02: Signups today / this week / this month
    # ... (similar COUNT queries with date filters)

    # DASH-03-05: Total sessions, files, messages
    # ... (COUNT queries on respective tables)

    # DASH-07: Time series for signups and messages
    cutoff = now - timedelta(days=days)
    signup_series = await db.execute(
        select(
            func.date_trunc("day", User.created_at).label("date"),
            func.count(User.id).label("count"),
        )
        .where(User.created_at >= cutoff)
        .group_by("date")
        .order_by("date")
    )
    # ... similar for messages

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "signups_today": ...,
        "signups_this_week": ...,
        "signups_this_month": ...,
        "total_sessions": ...,
        "total_files": ...,
        "total_messages": ...,
        "credit_summary": { "total_used": ..., "total_remaining": ... },
        "signup_trend": [{"date": "2026-02-01", "count": 5}, ...],
        "message_trend": [{"date": "2026-02-01", "count": 42}, ...],
    }
```

### Backend: Audit Log Listing Endpoint (to be created)
```python
# Add to backend/app/routers/admin/ -- a new audit.py router
@router.get("")
async def list_audit_logs(
    db: DbSession,
    current_admin: CurrentAdmin,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    action: str | None = Query(default=None),
    admin_id: UUID | None = Query(default=None),
    target_type: str | None = Query(default=None),
) -> dict:
    """List audit log entries with filtering and pagination."""
    # Query AdminAuditLog with optional filters, ordered by created_at DESC
    ...
```

### Frontend: Admin Theme (Different Accent from Public)
```css
/* globals.css for admin-frontend -- distinct accent color */
:root {
  /* Same neutral base as public frontend */
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  /* Admin-specific: use an indigo/blue accent instead of neutral */
  --primary: oklch(0.45 0.2 260);        /* Indigo-ish */
  --primary-foreground: oklch(0.985 0 0);
  /* ... rest similar to public frontend but with admin accent */
}

.dark {
  /* Nord-based dark theme like public frontend, but admin accent */
  --background: #2E3440;
  --primary: #81A1C1;  /* Nord Frost blue -- distinct from public's neutral */
  /* ... */
}
```

### Frontend: MetricCard Component
```typescript
// components/dashboard/MetricCard.tsx
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: { value: number; isPositive: boolean };
}

export function MetricCard({ title, value, subtitle, icon, trend }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {subtitle && (
              <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
            )}
          </div>
          <div className="text-muted-foreground">{icon}</div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### Frontend: Challenge Code Dialog
```typescript
// components/shared/ChallengeCodeDialog.tsx
// Implements the 6-char alphanumeric challenge code confirmation
// with paste disabled on the input field
<Input
  value={inputCode}
  onChange={(e) => setInputCode(e.target.value.toUpperCase())}
  onPaste={(e) => e.preventDefault()}
  maxLength={6}
  placeholder="Enter code"
  className="font-mono tracking-widest text-center"
/>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Recharts 1.x with class components | Recharts 2.x with function components | 2023 | Use v2 API; ResponsiveContainer, composable chart components |
| Next.js Pages Router | Next.js App Router (16.x) | 2023-2024 | Use app/ directory, layouts, server components where appropriate |
| shadcn/ui `npx shadcn-ui@latest` | `npx shadcn@latest` | 2024 | CLI package renamed; use `shadcn` not `shadcn-ui` |
| Tailwind CSS v3 with `tailwind.config.js` | Tailwind CSS v4 with CSS-based config | 2025 | Use `@import "tailwindcss"` in CSS, `@tailwindcss/postcss` plugin |

**Deprecated/outdated:**
- Recharts 1.x: Use 2.x for React 18/19 compatibility
- `npx shadcn-ui@latest`: Use `npx shadcn@latest` (package renamed)

## Open Questions

1. **Dashboard metrics backend endpoint does not exist yet**
   - What we know: All DASH-01 through DASH-07 require aggregated metrics that don't currently have an API endpoint
   - What's unclear: Exact query performance for large datasets (should be fine with proper indexing)
   - Recommendation: Create `GET /api/admin/dashboard` with a `days` query param for trend time range. This is blocking for the dashboard frontend.

2. **Audit log listing endpoint does not exist yet**
   - What we know: `log_admin_action()` writes to `admin_audit_log` table, but there's no read endpoint
   - What's unclear: Whether audit log should support full-text search on `details` JSONB field
   - Recommendation: Create `GET /api/admin/audit-log` with pagination + filters (action, admin_id, target_type, date range). Start simple; can add JSONB search later.

3. **Admin `/auth/me` endpoint**
   - What we know: The public frontend uses `GET /auth/me` to verify the logged-in user. The admin frontend needs a similar endpoint that verifies the admin JWT (with `is_admin` claim).
   - What's unclear: Whether to reuse `GET /auth/me` with admin token detection or create `GET /api/admin/auth/me`
   - Recommendation: Create `GET /api/admin/auth/me` that uses `CurrentAdmin` dependency. This ensures the admin check is enforced.

4. **Active users "today" metric (DASH-01 context)**
   - What we know: The dashboard hero row specifies "active today" as a metric card. The `last_login_at` field on the User model could approximate this.
   - What's unclear: Whether "active today" means users who logged in today or users who sent messages today
   - Recommendation: Use `last_login_at >= today_start` as the definition. Simple and sufficient for MVP.

## Sources

### Primary (HIGH confidence)
- **Codebase analysis** -- Read all admin backend routers (`backend/app/routers/admin/`), schemas, dependencies, middleware, and config
- **Codebase analysis** -- Read public frontend structure (`frontend/src/`), package.json, globals.css, components.json, api-client.ts, useAuth.tsx, providers.tsx, layout.tsx, next.config.ts
- **Backend main.py** -- Verified SPECTRA_MODE handling, CORS config with admin_cors_origin, X-Admin-Token expose header, admin route prefix `/api/admin`
- **AdminTokenReissueMiddleware** -- Verified sliding window token reissue via X-Admin-Token response header
- **AdminLoginResponse schema** -- Verified: `access_token` + `token_type` only (no refresh_token)

### Secondary (MEDIUM confidence)
- **Recharts 2.x API** -- Based on training data and Recharts documentation patterns; LineChart/AreaChart/BarChart/PieChart with ResponsiveContainer are standard
- **Next.js 16.x** -- Project uses 16.1.6; App Router patterns are stable and well-documented
- **shadcn/ui CLI** -- `npx shadcn@latest init` and `npx shadcn@latest add` commands based on current naming

### Tertiary (LOW confidence)
- None -- all findings are either code-verified or from well-established libraries

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are locked and version-pinned by the existing public frontend
- Architecture: HIGH -- project structure mirrors public frontend; admin API patterns are fully documented in backend code
- Backend gaps: HIGH -- verified through exhaustive search that dashboard metrics and audit log listing endpoints do NOT exist
- Pitfalls: HIGH -- identified from actual code analysis (token flow, CORS headers, schema shapes)

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable stack, all code-verified)
