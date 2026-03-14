# Phase 51: Frontend Migration - Research

**Researched:** 2026-03-07
**Domain:** Next.js route groups, component migration, Plotly signal charts, unified sidebar
**Confidence:** HIGH

## Summary

Phase 51 migrates the pulse-mockup workspace pages into the main frontend app. The work has three major axes: (1) palette swap from Nord to Hex.tech dark theme in globals.css plus replacing all shared UI components with mockup versions, (2) building a unified sidebar replacing ChatSidebar and creating a `(workspace)` route group, and (3) wiring workspace pages (collections list, collection detail with 4 tabs, detection results with signal split-panel) to live API data via TanStack Query hooks, with Recharts signal charts rewritten in Plotly.

The existing codebase already has ThemeProvider (next-themes) in layout.tsx, TanStack Query in providers.tsx, Zustand stores, Plotly via ChartRenderer, and the (dashboard) route group pattern -- so the migration is adapting established patterns, not introducing new ones. The main risk is regression on existing pages after the UI component swap.

**Primary recommendation:** Structure work as: (Wave 1) palette + shared UI component swap + regression check, (Wave 2) unified sidebar + route groups, (Wave 3) workspace pages with API hooks + Plotly signal charts.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Replace ALL shared UI components with pulse-mockup versions (full UI refresh, not just workspace)
- Plotly everywhere -- no Recharts. Rewrite mockup Recharts signal charts in Plotly
- Build ONE unified sidebar for entire app, replacing ChatSidebar, based on mockup sidebar.tsx
- Both (workspace) and (dashboard) route groups use the unified sidebar
- Chat history list becomes a context section within sidebar (only visible on chat routes)
- Split-panel layout for signals: SignalListPanel (left) + SignalDetailPanel (right)
- Signals sorted by severity (critical > warning > info), highest auto-selected
- Investigation + What-If buttons visible but disabled (opacity-50, tooltip "Coming in a future update")
- TanStack Query hooks for all workspace API calls
- Zustand for client-only workspace state (selected signal, selected files)
- Skeleton loaders for all workspace loading states
- Inline error display with "Try again" retry button
- TanStack Query refetchInterval (~3s) for Pulse detection polling
- Skip v0.9+ components: add-to-collection-modal, investigation-qa-thread, whatif-refinement-chat
- Per-page regression verification after component swap is non-negotiable
- Link nav entries: Files -> /my-files, Settings -> /settings (with API keys tab)
- Admin Panel nav entry only visible to admin users

### Claude's Discretion
- Exact migration order within each plan
- Skeleton loader layout shapes per page
- Plotly configuration details for matching mockup chart aesthetics
- Query key naming conventions for workspace hooks
- Zustand store structure for workspace state

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NAV-01 | Sidebar with Pulse Analysis -> /workspace, Chat, Files, Settings, Admin Panel | Unified sidebar pattern from mockup sidebar.tsx; admin visibility via useAuth role check |
| NAV-02 | Collection Overview tab: stat cards, Run Detection banner, signal previews, file table, activity feed | Mockup components: overview-stat-cards, run-detection-banner, signal-card, file-table, activity-feed; wire to collection detail API |
| NAV-03 | Collection Signals tab: signal cards + "Open Signals View" button | Mockup signal-card component; link to /workspace/collections/[id]/signals |
| NAV-04 | Collection detail header credit usage pill | Badge with Zap icon showing credits used from collection API response |
| SIGNAL-01 | Signal list sorted by severity on Detection Results page | SignalListPanel with severityOrder sorting; signals from GET /collections/{id}/signals |
| SIGNAL-02 | Highest-severity signal auto-selected on page load | Zustand store initializes selectedSignalId to sorted[0].id on data load |
| SIGNAL-03 | Signal detail panel with chart, evidence grid, disabled Investigate/What-If buttons | SignalDetailPanel adapted from mockup; buttons disabled with opacity-50 + tooltip |
| SIGNAL-04 | Signal chart type driven by chartType field via Plotly | New SignalChartRenderer using existing ChartRenderer pattern; map chartType to Plotly trace types |
</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | App router, route groups | Already in use |
| next-themes | 0.4.6 | Dark mode ThemeProvider | Already in layout.tsx |
| @tanstack/react-query | 5.90.20 | Server state, API calls | Already in use |
| zustand | 5.0.11 | Client state (selected signal) | Already in use |
| plotly.js-dist-min | 3.3.1 | Chart rendering | Already in use, ChartRenderer exists |
| lucide-react | 0.563.0 | Icons | Already in use |
| radix-ui | 1.4.3 | UI primitives | Already in use |
| sonner | 2.0.7 | Toast notifications | Already in use |

### Not Needed
| Library | Reason |
|---------|--------|
| recharts | Decision: Plotly everywhere. Do NOT install. Mockup signal-chart.tsx must be rewritten |
| react-plotly.js | ChartRenderer already wraps plotly.js-dist-min directly; no wrapper needed |

**Installation:** No new packages required.

## Architecture Patterns

### Route Group Structure
```
frontend/src/app/
├── (auth)/                    # Login/register (existing)
├── (dashboard)/               # Chat pages (existing, refactored to use unified sidebar)
│   ├── layout.tsx             # Refactored: unified sidebar replaces ChatSidebar
│   ├── dashboard/             # Dashboard page
│   ├── sessions/              # Chat sessions
│   ├── my-files/              # File manager
│   └── settings/              # Settings
├── (workspace)/               # NEW route group
│   ├── layout.tsx             # Auth guard + unified sidebar (no ChatSidebar, no LinkedFilesPanel)
│   └── workspace/
│       ├── page.tsx                           # Collection list
│       └── collections/
│           └── [id]/
│               ├── page.tsx                   # Collection detail (4 tabs)
│               └── signals/
│                   └── page.tsx               # Detection Results (split panel)
├── globals.css
├── layout.tsx                 # Root: ThemeProvider + Providers (unchanged)
└── providers.tsx              # QueryClient + AuthProvider (unchanged)
```

### Pattern 1: Unified Sidebar
**What:** Single sidebar component used by both (dashboard) and (workspace) layouts
**When to use:** All authenticated pages
**Key details:**
- Based on mockup `sidebar.tsx` design with collapsible state
- NAV_ITEMS: Pulse Analysis (/workspace), Chat (/sessions/new), Files (/my-files), Settings (/settings), Admin Panel (external admin-frontend, admin-only)
- Chat history section (ChatList component) rendered conditionally when on chat routes (`pathname.startsWith('/sessions')`)
- User section at bottom (reuse existing UserSection component)
- Active state detection via `usePathname()`
- Admin visibility: check user role from `useAuth()` hook

### Pattern 2: Workspace API Hooks
**What:** TanStack Query hooks for workspace data fetching
**Where:** `frontend/src/hooks/useWorkspace.ts` (or split into useCollections.ts, useSignals.ts)
**Example following existing pattern (from useFileManager.ts):**
```typescript
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useCollections() {
  return useQuery({
    queryKey: ["collections"],
    queryFn: async () => {
      const response = await apiClient.get("/collections/");
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
  });
}

export function useCollectionDetail(id: string) {
  return useQuery({
    queryKey: ["collections", id],
    queryFn: async () => {
      const response = await apiClient.get(`/collections/${id}`);
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!id,
  });
}

export function useCollectionSignals(collectionId: string) {
  return useQuery({
    queryKey: ["collections", collectionId, "signals"],
    queryFn: async () => {
      const response = await apiClient.get(`/collections/${collectionId}/signals`);
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!collectionId,
  });
}

// Pulse detection polling
export function usePulseStatus(collectionId: string, pulseRunId: string | null) {
  return useQuery({
    queryKey: ["collections", collectionId, "pulse", pulseRunId],
    queryFn: async () => {
      const response = await apiClient.get(`/collections/${collectionId}/pulse/${pulseRunId}`);
      if (!response.ok) throw new Error(`Failed: ${response.status}`);
      return response.json();
    },
    enabled: !!pulseRunId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "complete" || status === "failed" ? false : 3000;
    },
  });
}
```

### Pattern 3: Workspace Zustand Store
**What:** Client-only state for workspace UI
```typescript
import { create } from "zustand";

interface WorkspaceState {
  selectedSignalId: string | null;
  setSelectedSignalId: (id: string | null) => void;
  selectedFileIds: string[];
  toggleFileSelection: (id: string) => void;
  clearFileSelection: () => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  selectedSignalId: null,
  setSelectedSignalId: (id) => set({ selectedSignalId: id }),
  selectedFileIds: [],
  toggleFileSelection: (id) => set((s) => ({
    selectedFileIds: s.selectedFileIds.includes(id)
      ? s.selectedFileIds.filter((f) => f !== id)
      : [...s.selectedFileIds, id],
  })),
  clearFileSelection: () => set({ selectedFileIds: [] }),
}));
```

### Pattern 4: Plotly Signal Charts (replacing Recharts)
**What:** Rewrite mockup's Recharts-based SignalChart using existing ChartRenderer
**Key mapping:**
- `chartType: "bar"` -> Plotly `type: "bar"` trace
- `chartType: "line"` -> Plotly `type: "scatter"` with `mode: "lines"` and `fill: "tozeroy"` (area fill to match mockup)
- `chartType: "scatter"` -> Plotly `type: "scatter"` with `mode: "markers"`

**Severity colors for Plotly traces:**
```typescript
const SEVERITY_COLORS = {
  critical: "#ef4444",
  warning: "#f59e0b",
  info: "#22c55e",
};
```

**Approach:** Build a `buildSignalPlotlyJSON(signal)` function that converts signal data + chartType into Plotly JSON string, then pass to ChartRenderer. This reuses ChartRenderer's theme integration, ResizeObserver, and cleanup logic.

### Anti-Patterns to Avoid
- **Installing Recharts:** Decision is Plotly everywhere. Do not add recharts dependency.
- **Separate sidebar per route group:** Build ONE sidebar, share it. Do not duplicate sidebar code.
- **Fetching in components directly:** Always use TanStack Query hooks. No raw fetch() in components.
- **Mock data in production components:** All mockup `MOCK_*` imports must be replaced with API hook data.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chart rendering | Custom SVG/canvas charts | ChartRenderer + Plotly | Already handles theming, resize, cleanup |
| Dark mode | Manual class toggling | next-themes ThemeProvider | Already configured in layout.tsx |
| API state management | useState + useEffect fetch | TanStack Query hooks | Caching, retry, refetching built in |
| UI primitives | Custom button/card/badge | shadcn/ui components (mockup versions) | Consistent design system |
| Sidebar collapse | Custom toggle logic | shadcn SidebarProvider or mockup's collapsed state | Already patterned |

## Common Pitfalls

### Pitfall 1: UI Component Swap Breaking Existing Pages
**What goes wrong:** Replacing shared UI components (button, card, badge, etc.) with mockup versions causes prop/API mismatches on existing pages.
**Why it happens:** Mockup components may have different prop signatures, missing variants, or different className patterns.
**How to avoid:** (1) Diff each mockup component against current version before replacing. (2) After swap, verify every page that uses the component. (3) Keep the same export signatures.
**Warning signs:** TypeScript errors after component replacement, visual regressions on /sessions, /my-files, /settings.

### Pitfall 2: ChatSidebar Removal Breaking Chat Routes
**What goes wrong:** Removing ChatSidebar before the unified sidebar properly renders ChatList on chat routes.
**Why it happens:** ChatList component has dependencies (useChatSessions, sessionStore) that must be preserved.
**How to avoid:** Build unified sidebar with ChatList section first, verify chat routes work, THEN remove ChatSidebar.

### Pitfall 3: Plotly Bundle Size
**What goes wrong:** plotly.js-dist-min is already ~1MB. Adding it to signal pages that render many charts can cause slow initial loads.
**Why it happens:** Plotly is client-side only, large bundle.
**How to avoid:** Already using `plotly.js-dist-min` (minified distribution). Use dynamic import (`next/dynamic`) for signal chart components with `ssr: false`. ChartRenderer already uses this pattern.

### Pitfall 4: Signal Data Shape Mismatch
**What goes wrong:** Mockup uses `Signal` type from mock-data.ts. Real API returns different field names/structure.
**Why it happens:** Backend PulseAgentOutput schema may differ from mockup's Signal type.
**How to avoid:** Define TypeScript types matching actual API response. Check backend signal schema before writing signal components. Key fields: id, title, severity, category, chartType, chartData, description, statisticalEvidence.

### Pitfall 5: Route Group Layout Nesting
**What goes wrong:** (workspace) layout accidentally inherits (dashboard) layout elements or vice versa.
**Why it happens:** Next.js route groups are parallel -- they share root layout but NOT each other's layouts. Confusion arises when moving pages between groups.
**How to avoid:** (workspace)/layout.tsx and (dashboard)/layout.tsx are independent. Both import the unified sidebar but configure it differently (chat context section visibility).

### Pitfall 6: Hex.tech Palette Not Applied to Light Mode
**What goes wrong:** Only dark mode tokens are updated; light mode becomes inconsistent.
**How to avoid:** The success criteria specifies dark mode tokens. Update .dark {} block. Light mode (:root) can remain as-is since app defaults to dark.

## Code Examples

### Hex.tech Dark Palette (from mockup globals.css)
```css
.dark {
  --background: #0a0e1a;
  --foreground: #f8fafc;
  --card: #111827;
  --card-foreground: #f8fafc;
  --popover: #111827;
  --popover-foreground: #f8fafc;
  --primary: #3b82f6;
  --primary-foreground: #ffffff;
  --secondary: #1e293b;
  --secondary-foreground: #f8fafc;
  --muted: #1e293b;
  --muted-foreground: #64748b;
  --accent: #1e293b;
  --accent-foreground: #f8fafc;
  --destructive: #ef4444;
  --border: #1e293b;
  --input: #1e293b;
  --ring: #3b82f6;
  --chart-1: #3b82f6;
  --chart-2: #22c55e;
  --chart-3: #f59e0b;
  --chart-4: #8b5cf6;
  --chart-5: #ef4444;
  --sidebar: #070b14;
  --sidebar-foreground: #f8fafc;
  --sidebar-primary: #3b82f6;
  --sidebar-primary-foreground: #ffffff;
  --sidebar-accent: #111827;
  --sidebar-accent-foreground: #f8fafc;
  --sidebar-border: #1e293b;
  --sidebar-ring: #3b82f6;
  /* Severity tokens (new) */
  --severity-critical: #ef4444;
  --severity-warning: #f59e0b;
  --severity-info: #22c55e;
}
```

### Signal Plotly JSON Builder
```typescript
function buildSignalPlotlyJSON(signal: SignalResponse): string {
  const color = SEVERITY_COLORS[signal.severity];
  const data = signal.chartData; // array of objects
  const keys = Object.keys(data[0] || {});
  const xKey = keys[0];
  const numericKeys = keys.filter(k => typeof data[0][k] === "number");

  let traces: object[];
  switch (signal.chartType) {
    case "line":
      traces = numericKeys.map((key, i) => ({
        type: "scatter",
        mode: "lines",
        x: data.map(d => d[xKey]),
        y: data.map(d => d[key]),
        name: key,
        line: { color: i === 0 ? color : "#64748b", width: i === 0 ? 2 : 1.5, dash: i === 0 ? undefined : "dash" },
        fill: i === 0 ? "tozeroy" : undefined,
        fillcolor: i === 0 ? color + "1a" : undefined,
      }));
      break;
    case "bar":
      traces = numericKeys.map((key, i) => ({
        type: "bar",
        x: data.map(d => d[xKey]),
        y: data.map(d => d[key]),
        name: key,
        marker: { color: i === 0 ? color : "#3b82f6", opacity: 0.85 },
      }));
      break;
    case "scatter":
      traces = [{
        type: "scatter",
        mode: "markers",
        x: data.map(d => d[numericKeys[0]]),
        y: data.map(d => d[numericKeys[1]]),
        marker: { color, opacity: 0.8, size: 8 },
        name: "Data",
      }];
      break;
    default:
      traces = [];
  }

  return JSON.stringify({ data: traces, layout: { height: 300 } });
}
```

### Workspace Layout (skeleton)
```typescript
// frontend/src/app/(workspace)/layout.tsx
"use client";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { UnifiedSidebar } from "@/components/sidebar/UnifiedSidebar";

export default function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) return <LoadingSpinner />;
  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen overflow-hidden w-full">
      <UnifiedSidebar />
      <main className="flex-1 overflow-y-auto overflow-x-hidden">
        {children}
      </main>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Nord palette | Hex.tech palette | Phase 51 | All dark mode colors change |
| ChatSidebar (chat-only) | UnifiedSidebar (all nav) | Phase 51 | Single sidebar for entire app |
| Recharts in mockup | Plotly everywhere | Phase 51 decision | Signal charts use ChartRenderer |
| Route-specific sidebars | Shared sidebar + route group layouts | Phase 51 | Simpler maintenance |

## Open Questions

1. **Backend signal response shape**
   - What we know: PulseAgentOutput has severity (Literal), chartType (Literal), plus chart data
   - What's unclear: Exact JSON shape of API response for GET /collections/{id}/signals -- field names may differ from mockup's Signal type
   - Recommendation: Check backend signal serialization before writing TypeScript types. Look at Phase 49 signal output schema.

2. **Admin Panel link behavior**
   - What we know: Opens admin-frontend (separate app)
   - What's unclear: Is it same-origin or different port/domain? External link vs route?
   - Recommendation: Use `<a href>` with target if external, or router.push if same-origin. Check existing admin routing.

3. **Existing page regression scope**
   - What we know: Pages to verify: /sessions/*, /my-files, /settings, /dashboard
   - What's unclear: How many components actually change behavior vs just styling
   - Recommendation: After UI component swap, do a build + manual check of each page. TypeScript will catch most prop mismatches.

## Sources

### Primary (HIGH confidence)
- Codebase inspection: frontend/src/app/ structure, existing components, hooks, stores
- Codebase inspection: pulse-mockup/src/components/ -- all workspace and UI components
- Codebase inspection: pulse-mockup/src/app/globals.css -- Hex.tech palette tokens
- Codebase inspection: frontend/src/components/chart/ChartRenderer.tsx -- existing Plotly integration

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions (user-locked, 2026-03-07)
- REQUIREMENTS.md (NAV-01 through NAV-04, SIGNAL-01 through SIGNAL-04)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already installed, no new dependencies
- Architecture: HIGH - follows existing route group and hook patterns from codebase
- Pitfalls: HIGH - identified from direct codebase analysis of component interfaces

**Research date:** 2026-03-07
**Valid until:** 2026-04-07 (stable -- no external dependencies changing)
