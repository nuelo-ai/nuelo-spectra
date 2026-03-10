# Phase 54: Pulse Analysis Fixes - Research

**Researched:** 2026-03-10
**Domain:** Next.js frontend — Pulse workspace UI (credit tracking, responsive layout, Chat bridge, timestamp formatting)
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PULSE-01 | Credits Used card shows actual cumulative credits spent (not hardcoded "5") | Backend has `credit_cost` per `PulseRun`; need sum query in `CollectionService` and `credits_used` field added to `CollectionDetailResponse` |
| PULSE-02 | Signal View is mobile responsive — detail panel accessible on small screens | `signals/page.tsx` uses fixed `w-[350px]` side-by-side layout; needs conditional show/hide or tab-style panel switching on mobile |
| PULSE-03 | "Chat with Spectra" button between Analysis and Statistical Evidence on Signal View, opens new Chat session with collection files pre-linked | Pattern exists in `my-files/page.tsx`: create session → link files → navigate. Collection files available via `useCollectionFiles` in parent page |
| PULSE-04 | Activity history entries show date AND time | `activity-feed.tsx` `formatTimestamp` uses `toLocaleDateString` only; fix to include hour/minute |
| PULSE-05 | Files added list entries show date AND time | `file-table.tsx` `formatDate` uses `toLocaleDateString` only; fix to include hour/minute. Same issue in `UserFileTable.formatDate` in `collections/[id]/page.tsx` |
</phase_requirements>

---

## Summary

Phase 54 fixes five data-accuracy and UX gaps in the Pulse Analysis workspace. All five requirements are purely frontend changes with one small backend addition (PULSE-01 requires a new `credits_used` aggregate field from the server).

**PULSE-01 (Credits Used):** The `OverviewStatCards` component receives `creditsUsed={creditCosts?.pulse_run ?? 0}` — a static platform config value (cost per run), not actual cumulative spend. The fix requires: (a) adding a `credits_used` subquery to `CollectionService.get_collection_detail` that sums `credit_cost` across all completed `PulseRun` rows for the collection, (b) exposing `credits_used: float` in `CollectionDetailResponse`, and (c) updating the frontend to read `collection?.credits_used ?? 0`.

**PULSE-02 (Mobile Signal View):** `signals/page.tsx` renders `SignalListPanel` (fixed `w-[350px]`) and `SignalDetailPanel` side-by-side with no breakpoint logic. On small screens the detail panel is hidden behind the list. The fix is a mobile-view state toggle: show list by default, clicking a signal shows the detail panel, a back button returns to the list.

**PULSE-03 (Chat Bridge):** The same create-session → link-files → navigate pattern used in `my-files/page.tsx` can be applied in `SignalDetailPanel`. The component currently lacks access to the collection's file IDs; these must be passed as a prop from the parent (`signals/page.tsx` already fetches collection detail, which gives the collection ID; `useCollectionFiles(id)` provides the file list). The button renders between the Analysis section and the Statistical Evidence card.

**PULSE-04 and PULSE-05 (Timestamps):** Two isolated `formatTimestamp`/`formatDate` functions each use `toLocaleDateString` without time options. The fix adds `hour: "2-digit"` and `minute: "2-digit"` (or equivalent) to the same options object. Three locations must be updated: `activity-feed.tsx`, `file-table.tsx`, and the inline `formatDate` inside `UserFileTable` in `collections/[id]/page.tsx`.

**Primary recommendation:** Implement in two logical waves — Wave 1: backend credits field (PULSE-01) + timestamp fixes (PULSE-04, PULSE-05); Wave 2: mobile Signal View (PULSE-02) + Chat bridge button (PULSE-03).

---

## Standard Stack

### Core (already in use — no new dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 14+ (App Router) | Frontend routing and pages | Project standard |
| React | 18 | Component model | Project standard |
| TanStack Query | 5 | Data fetching, cache invalidation | Project standard |
| Tailwind CSS | 3 | Responsive utility classes (`sm:`, `md:` breakpoints) | Project standard |
| shadcn/ui | latest | UI primitives (Button, ScrollArea, etc.) | Project standard |
| SQLAlchemy (async) | 2.x | Backend ORM queries | Project standard |
| Pydantic v2 | 2.x | Backend response schemas | Project standard |

### No new dependencies required
All five fixes use existing tools. PULSE-02 mobile layout uses Tailwind breakpoint utilities already in the project. PULSE-03 reuses existing `useCreateSession`, `useLinkFile`, and `useCollectionFiles` hooks.

---

## Architecture Patterns

### Recommended Project Structure (no changes)
All changes are edits to existing files:
```
backend/app/
├── services/collection.py       # Add credits_used subquery
├── schemas/collection.py        # Add credits_used field
├── routers/collections.py       # Pass credits_used in response
frontend/src/
├── components/workspace/
│   ├── activity-feed.tsx        # Fix formatTimestamp (PULSE-04)
│   ├── file-table.tsx           # Fix formatDate (PULSE-05)
│   ├── signal-detail-panel.tsx  # Add Chat bridge button (PULSE-03)
│   ├── signal-list-panel.tsx    # Mobile visibility prop (PULSE-02)
│   └── overview-stat-cards.tsx  # (no change needed — receives prop)
├── app/(workspace)/workspace/collections/
│   ├── [id]/page.tsx            # Pass credits_used; fix UserFileTable.formatDate (PULSE-05)
│   └── [id]/signals/page.tsx   # Mobile state, pass collection files to SignalDetailPanel (PULSE-02, PULSE-03)
└── types/workspace.ts           # Add credits_used to CollectionDetail
```

### Pattern 1: Backend Aggregate Subquery (PULSE-01)
**What:** Add a `func.coalesce(func.sum(...), 0)` subquery on `PulseRun.credit_cost` filtered by `collection_id` and `status == "completed"`.
**When to use:** Anytime a collection-level stat needs aggregating from child rows.
**Example:**
```python
# In CollectionService.get_collection_detail
from app.models.pulse_run import PulseRun as PulseRunModel

credits_used_sq = (
    select(func.coalesce(func.sum(PulseRunModel.credit_cost), 0))
    .where(
        PulseRunModel.collection_id == Collection.id,
        PulseRunModel.status == "completed",
    )
    .correlate(Collection)
    .scalar_subquery()
    .label("credits_used")
)
# Add to SELECT and return in dict
```

### Pattern 2: Mobile Panel Toggle (PULSE-02)
**What:** Use a boolean state `showDetail` in `signals/page.tsx` (or the component) that controls which panel is visible on mobile (`sm:` and below). On desktop both panels show side by side.
**When to use:** Any two-panel layout that needs single-panel mobile view.
**Example:**
```tsx
// In signals/page.tsx
const [showDetail, setShowDetail] = useState(false);

// On mobile: show list or detail (not both)
// On desktop: show both side-by-side (unchanged)
<div className="flex flex-1 overflow-hidden">
  {/* List panel: hidden on mobile when detail is shown */}
  <div className={cn(
    "w-[350px] shrink-0 border-r border-border flex flex-col h-full bg-card/50",
    showDetail ? "hidden sm:flex" : "flex"
  )}>
    <SignalListPanel
      signals={sortedSignals}
      selectedId={selectedSignalId}
      onSelect={(id) => { setSelectedSignalId(id); setShowDetail(true); }}
    />
  </div>
  {/* Detail panel: hidden on mobile when list is shown */}
  <div className={cn(
    "flex-1 overflow-hidden",
    showDetail ? "flex" : "hidden sm:flex"
  )}>
    <SignalDetailPanel
      signal={selectedSignal}
      onBack={() => setShowDetail(false)}   // new prop
      collectionFiles={collectionFiles}     // new prop for PULSE-03
      collectionId={id}                    // new prop for PULSE-03
    />
  </div>
</div>
```

### Pattern 3: Chat Bridge Button (PULSE-03)
**What:** Button in `SignalDetailPanel` between Analysis and Statistical Evidence sections. On click: create session → link each collection file → navigate to `/sessions/{id}`.
**When to use:** Any "bridge to Chat with pre-linked files" action.
**Example (mirrors `my-files/page.tsx` pattern):**
```tsx
// SignalDetailPanel (new props: collectionFiles, collectionId)
import { useCreateSession } from "@/hooks/useSessionMutations";
import { useLinkFile } from "@/hooks/useSessionMutations";
import { useRouter } from "next/navigation";
import { MessageSquare, Loader2 } from "lucide-react";

const router = useRouter();
const createSession = useCreateSession();
const linkFile = useLinkFile();
const [isBridging, setIsBridging] = useState(false);

const handleChatBridge = async () => {
  setIsBridging(true);
  try {
    const session = await createSession.mutateAsync("New Chat");
    await Promise.all(
      collectionFiles.map((f) =>
        linkFile.mutateAsync({ sessionId: session.id, fileId: f.file_id })
      )
    );
    router.push(`/sessions/${session.id}`);
  } catch {
    toast.error("Failed to open Chat. Please try again.");
  } finally {
    setIsBridging(false);
  }
};
```

### Pattern 4: Datetime Formatting (PULSE-04, PULSE-05)
**What:** Add `hour` and `minute` to existing `Intl.DateTimeFormat` options.
**When to use:** Any timestamp that must show date and time.
**Example:**
```typescript
// Before (date only):
return date.toLocaleDateString("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
});

// After (date + time):
return date.toLocaleString("en-US", {
  month: "short",
  day: "numeric",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});
// Output example: "Mar 10, 2026, 02:34 PM"
```

### Anti-Patterns to Avoid
- **Passing `creditCosts?.pulse_run` as "credits used":** This is the cost per run, not actual spend. Fix: use the new `collection?.credits_used` field from the API.
- **Hardcoding `window.screen.width` for mobile detection:** Use Tailwind breakpoint classes. The project already uses `use-mobile.ts` hook (`useIsMobile`) if programmatic detection is needed.
- **Fetching collection files inside `SignalDetailPanel`:** The parent page already has access — pass as a prop to avoid duplicate fetches.
- **Linking files sequentially (one-by-one await) for Chat bridge:** Use `Promise.all` for parallel linking to minimize latency.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mobile breakpoints | Custom JS resize listener | Tailwind `sm:` / `md:` utilities | Already in project, SSR-safe |
| Date+time formatting | Custom date library | `toLocaleString` with Intl options | Native, no dependency |
| Session creation + file linking | Custom API calls | `useCreateSession` + `useLinkFile` hooks | Already exist with cache invalidation |
| Credit aggregation | Frontend sum of pulse runs array | Backend aggregate subquery | Single source of truth; no extra API call needed |

---

## Common Pitfalls

### Pitfall 1: Credits Not Including Failed Runs
**What goes wrong:** Summing all `PulseRun.credit_cost` rows includes runs that failed (credits may or may not have been deducted).
**Why it happens:** The `status` field on `PulseRun` is `pending`, `running`, `completed`, or `failed`.
**How to avoid:** Filter `WHERE status = 'completed'` in the subquery — consistent with when credit deduction is confirmed in `scheduler.py` line 149.
**Warning signs:** Credits Used showing higher than expected.

### Pitfall 2: `setShowDetail(true)` without resetting on signal list navigation
**What goes wrong:** On mobile, selecting a different signal from the detail view back-navigates to list but the state remains stuck.
**Why it happens:** The back button sets `showDetail(false)`, but navigating within the list does not reset it if detail is already shown.
**How to avoid:** The `onSelect` handler in `SignalListPanel` always sets `showDetail(true)` — this is correct. The back button is the only exit. No special reset needed.

### Pitfall 3: `useLinkFile` mutation called on all collection files simultaneously hitting race conditions
**What goes wrong:** Rapid `POST /sessions/{id}/files` calls may hit DB constraints if backend is not idempotent.
**Why it happens:** The backend returns 409 for already-linked files (handled by `useLinkFilesToCollection` with 409 → success). The session mutations `useLinkFile` does NOT have this guard.
**How to avoid:** The Chat bridge creates a brand new session (no pre-existing file links), so 409 conflicts are impossible. `Promise.all` is safe.

### Pitfall 4: `credits_used` showing `0` for collections with no completed runs
**What goes wrong:** `func.coalesce(func.sum(...), 0)` returns 0 when no rows match — correct. But the Pydantic schema must declare `credits_used: float` (not `int`) to avoid truncation.
**How to avoid:** Use `float` in both the SQLAlchemy model and Pydantic schema.

### Pitfall 5: Timestamp locale inconsistency between `toLocaleDateString` and `toLocaleString`
**What goes wrong:** Switching from `toLocaleDateString` to `toLocaleString` with the same options object produces the same result because both APIs share the same Intl options. The key difference is adding `hour`/`minute` keys.
**How to avoid:** Use `toLocaleString` (not `toLocaleDateString`) when including time options — `toLocaleDateString` ignores time-related options in all browsers.

---

## Code Examples

Verified patterns from codebase inspection:

### Collection Service Subquery (existing pattern from `file_count_sq`)
```python
# Source: backend/app/services/collection.py lines 104-127
# Credits subquery follows the same correlation pattern:
credits_used_sq = (
    select(func.coalesce(func.sum(PulseRunModel.credit_cost), 0.0))
    .where(
        PulseRunModel.collection_id == Collection.id,
        PulseRunModel.status == "completed",
    )
    .correlate(Collection)
    .scalar_subquery()
    .label("credits_used")
)
```

### CollectionDetailResponse schema addition
```python
# Source: backend/app/schemas/collection.py
class CollectionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ... existing fields ...
    credits_used: float = 0.0   # NEW
```

### Frontend TypeScript type addition
```typescript
// Source: frontend/src/types/workspace.ts
export interface CollectionDetail extends CollectionListItem {
  report_count: number;
  credits_used: number;  // NEW
}
```

### Timestamp fix (applies to activity-feed.tsx and file-table.tsx)
```typescript
// Source: inspected from activity-feed.tsx formatTimestamp and file-table.tsx formatDate
// Change toLocaleDateString → toLocaleString and add hour/minute:
function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
```

### Chat Bridge — session creation and file linking pattern
```typescript
// Source: frontend/src/app/(dashboard)/my-files/page.tsx lines 61-76
// Pattern: create session → link files (Promise.all for collection files) → navigate
const session = await createSession.mutateAsync("New Chat");
await Promise.all(
  collectionFiles.map((f) =>
    linkFile.mutateAsync({ sessionId: session.id, fileId: f.file_id })
  )
);
router.push(`/sessions/${session.id}`);
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Credits shown as cost-per-run config value | Credits shown as actual cumulative spend | This phase | Accurate data; matches user expectation |
| Date-only timestamps | Date + time timestamps | This phase | Activity history entries are unambiguous |
| Desktop-only Signal View layout | Responsive Signal View | This phase | Mobile users can access Signal details |

---

## Open Questions

1. **Should `credits_used` filter only `completed` runs or also include `failed` runs?**
   - What we know: Credit deduction happens in `scheduler.py` after run completion (line 149). Failed runs presumably had credits deducted before failure.
   - What's unclear: Whether the `scheduler.py` refund logic on failure (`test_orphan_refund.py` exists) means failed runs should be excluded.
   - Recommendation: Filter `status == "completed"` for the initial fix. If orphan refund logic means failed credits are returned, the sum of completed runs is the true cost. Planner should verify with scheduler.py logic.

2. **Chat Bridge: should it navigate immediately or open in a new tab?**
   - What we know: The existing `my-files/page.tsx` Chat bridge navigates in the same tab (`router.push`).
   - Recommendation: Use the same `router.push` pattern for consistency.

3. **Mobile back button placement in Signal View**
   - What we know: The header strip already contains `SidebarTrigger` and an `ArrowLeft` back link to the collection.
   - Recommendation: Add a separate "Back to Signals" button in the detail panel header area that only renders on mobile (`sm:hidden`). Alternatively, repurpose the existing ArrowLeft. Planner decides.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio |
| Config file | backend/pyproject.toml |
| Quick run command | `cd backend && python -m pytest tests/test_collections.py -x -q` |
| Full suite command | `cd backend && python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PULSE-01 | `credits_used` field returned by GET /collections/{id} | unit (backend) | `cd backend && python -m pytest tests/test_collections.py -x -q -k "credits"` | ❌ Wave 0 — add test to `test_collections.py` |
| PULSE-02 | Mobile layout — panel visibility logic | manual visual | N/A — CSS class logic | manual only |
| PULSE-03 | Chat bridge creates session, links files, navigates | manual visual | N/A — integration flow | manual only |
| PULSE-04 | Activity timestamps include time component | unit (frontend, manual) | manual visual inspection | manual only |
| PULSE-05 | File added timestamps include time component | unit (frontend, manual) | manual visual inspection | manual only |

### Sampling Rate
- **Per task commit:** `cd backend && python -m pytest tests/test_collections.py -x -q`
- **Per wave merge:** `cd backend && python -m pytest tests/ -x -q`
- **Phase gate:** Backend tests green + manual visual check of all 5 requirements before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_collections.py` — add test for `credits_used` aggregate field in GET /collections/{id} response (REQ PULSE-01)

---

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `backend/app/services/collection.py` — confirmed no `credits_used` aggregate exists
- Codebase inspection: `backend/app/schemas/collection.py` — confirmed `credits_used` absent from `CollectionDetailResponse`
- Codebase inspection: `backend/app/models/pulse_run.py` — confirmed `credit_cost: Mapped[float]` and `status` fields exist on `PulseRun`
- Codebase inspection: `frontend/src/app/(workspace)/workspace/collections/[id]/page.tsx` line 310 — confirmed `creditsUsed={creditCosts?.pulse_run ?? 0}` is cost-per-run not actual spend
- Codebase inspection: `frontend/src/app/(workspace)/workspace/collections/[id]/signals/page.tsx` — confirmed fixed `w-[350px]` side-by-side layout, no mobile breakpoint
- Codebase inspection: `frontend/src/components/workspace/signal-detail-panel.tsx` — confirmed no Chat bridge button; Analysis and Statistical Evidence sections identified at lines 90-135
- Codebase inspection: `frontend/src/components/workspace/activity-feed.tsx` — confirmed `toLocaleDateString` (date only) at line 18-23
- Codebase inspection: `frontend/src/components/workspace/file-table.tsx` — confirmed `toLocaleDateString` (date only) at line 19-25
- Codebase inspection: `frontend/src/app/(dashboard)/my-files/page.tsx` lines 61-76 — confirmed Chat session + file link + navigate pattern

### Secondary (MEDIUM confidence)
- MDN Web API: `toLocaleString` with Intl.DateTimeFormatOptions supports `hour`/`minute` keys alongside `month`/`day`/`year` — standard web platform behavior

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all existing project libraries, no new dependencies
- Architecture: HIGH — patterns verified directly in codebase; parallel patterns confirmed in `my-files/page.tsx`
- Pitfalls: HIGH — root causes identified from direct code inspection
- PULSE-01 backend scope: HIGH — `credit_cost` field on `PulseRun` confirmed; subquery pattern mirrors existing file/signal/report subqueries

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable codebase — no fast-moving dependencies)
