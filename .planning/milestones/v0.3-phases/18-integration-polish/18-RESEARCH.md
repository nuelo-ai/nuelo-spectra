# Phase 18: Integration & Polish - Research

**Researched:** 2026-02-11
**Domain:** Form validation UX, session constraints, LLM-based title generation, theme management, session persistence
**Confidence:** HIGH

## Summary

Phase 18 integrates and polishes all v0.3 features (Phases 14-17) with proper constraints and visual refinements. This is NOT a new-feature phase — it enforces file-required validation, implements auto-generated session titles, adds light/dark theme support, and verifies session persistence. The project has strong foundations: next-themes (already installed), sonner toasts, Zustand for state, TanStack Query for data persistence, and complete session/file APIs from Phase 14-17.

The research reveals this is primarily an integration and validation challenge. Key implementation areas: (1) ChatInput validation with dual feedback (toast + inline warning), (2) file unlinking prevention (disable when count = 1), (3) LLM-based title generation after first AI response with manual-rename lock, (4) next-themes ThemeProvider integration with system preference detection, (5) theme persistence using localStorage (matches existing patterns). All backend APIs are ready — focus is on frontend validation, UX polish, and state coordination.

Critical finding: next-themes is already installed (v0.4.6) and partially integrated (used in sonner.tsx). ThemeProvider needs to be added to root layout with suppressHydrationWarning. Sonner already theme-aware. LocalStorage is appropriate for theme persistence (no cross-device sync needed, SSR-compatible with next-themes).

**Primary recommendation:** Build on existing validation patterns. Use sonner for immediate feedback, React state for persistent inline warnings. Prevent unlinking last file with disabled state + warning toast. Generate titles via LLM call after first response completes, store user_modified flag to prevent overwrites. Wrap app in ThemeProvider, add toggle to user menu dropdown, persist to localStorage via next-themes default behavior.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### File requirement UX
- Input field stays enabled (user can type), but sending is blocked when no files are linked
- On send attempt without files: toast notification for immediate feedback + inline warning below input that persists until a file is linked
- Prevent removing the last file from a session — show warning: "At least one file must be linked" when user tries to unlink the only remaining file
- WelcomeScreen stays as-is — file requirement only enforced on message send, not preemptively on the welcome screen

#### Session title generation
- Use LLM to generate session titles — send first user message to LLM with a title-generation prompt
- Title is generated after the first AI response completes (more context available for meaningful title)
- Sidebar shows "Untitled" as placeholder until the LLM-generated title arrives
- Manual rename locks the title — auto-generation never overwrites a user-set title

#### Dark mode design
- Toggle located inside user profile/menu dropdown — not in sidebar or navbar directly
- System preference detection: default to OS/system theme on first visit, user can override
- Two options only: Light / Dark (no explicit "System" option — system preference used only for initial default)
- Theme preference persistence: Claude's Discretion (localStorage vs backend based on existing patterns)
- **UI directive:** Use `/frontend-design` skill for all UI work in this phase

#### Session persistence & login behavior
- On login: always start with a new empty session — previous sessions accessible from sidebar history
- Sessions must survive page refresh and re-login with all messages and linked files intact

### Claude's Discretion
- Sidebar session item design (title + time vs title + file count)
- Session limit strategy (unlimited vs soft limit with cleanup)
- Theme persistence mechanism (localStorage vs backend user profile)
- Loading/transition animations during theme switch
- Dark mode color palette specifics

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope

</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next-themes | 0.4.6 | Theme management for Next.js | Already installed, perfect Next.js dark mode in 2 lines, supports system preference, no flash, localStorage by default |
| sonner | 2.0.7 | Toast notifications | Already in use, theme-aware (already uses next-themes), supports action buttons for inline decisions |
| @tanstack/react-query | 5.90.20 | Server state & cache | Already in use, session persistence via cache, automatic refetching after mutations |
| zustand | 5.0.11 | Client state management | Already in use (sessionStore), persist middleware available for theme if needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-textarea-autosize | 8.5.9 | Auto-expanding input | Already in ChatInput, validation warnings will appear below this |
| lucide-react | 0.563.0 | Icon library | Moon/Sun icons for theme toggle, AlertCircle for warnings |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| next-themes | Custom localStorage | next-themes handles SSR hydration, system preference, no-flash correctly. Custom implementation error-prone. |
| localStorage for theme | Backend user profile | localStorage simpler, instant (no API call), works without login. Backend enables cross-device sync but adds complexity. User decision: localStorage. |
| LLM title generation | Client-side text truncation | LLM generates meaningful titles (context-aware). Truncation loses semantic meaning. User decision: use LLM. |

**Installation:**
No new dependencies required — all needed libraries already installed.

## Architecture Patterns

### Pattern 1: File Requirement Validation (Dual Feedback)
**What:** Block message sending when no files linked, provide immediate + persistent feedback
**When to use:** Form validation that requires user action before proceeding

**Implementation:**
```typescript
// In ChatInput.tsx
const [noFilesWarning, setNoFilesWarning] = useState(false);

const handleSend = () => {
  if (linkedFileIds.length === 0) {
    // Immediate feedback: toast
    toast.error("Link at least one file before chatting");
    // Persistent feedback: inline warning
    setNoFilesWarning(true);
    return;
  }

  setNoFilesWarning(false);
  onSend(message);
};

// Clear warning when files are linked
useEffect(() => {
  if (linkedFileIds.length > 0) {
    setNoFilesWarning(false);
  }
}, [linkedFileIds]);

// UI: Show warning below input
{noFilesWarning && (
  <div className="flex items-center gap-2 text-sm text-destructive mt-2">
    <AlertCircle className="h-4 w-4" />
    <span>Link at least one file to start chatting</span>
  </div>
)}
```

**Why this pattern:**
- Toast provides immediate attention-grabbing feedback
- Inline warning persists until user resolves the issue
- Matches ChatGPT UX: type freely, guided to add context
- Source: User decision + Sonner action patterns

### Pattern 2: Prevent Last Item Removal
**What:** Disable unlink action when only one file remains in session
**When to use:** Enforcing minimum item constraints in lists

**Implementation:**
```typescript
// In FileLinkingDropdown or unlink handler
const canUnlink = linkedFileIds.length > 1;

const handleUnlink = (fileId: string) => {
  if (!canUnlink) {
    toast.warning("At least one file must be linked to the session");
    return;
  }

  unlinkFile({ sessionId, fileId });
};

// UI: Disable unlink button when count = 1
<Button
  disabled={!canUnlink}
  onClick={() => handleUnlink(file.id)}
  title={!canUnlink ? "Cannot remove last file" : "Unlink file"}
>
  <X className="h-4 w-4" />
</Button>
```

**Why this pattern:**
- Preventive (disabled state) better than reactive (error after attempt)
- Toast explains WHY action is blocked
- Tooltip provides passive discovery
- Source: Standard React validation pattern + Sonner toast

### Pattern 3: LLM Title Generation with Lock
**What:** Generate session title via LLM after first response, prevent overwrite on manual rename
**When to use:** Smart defaults that respect user customization

**Implementation:**
```typescript
// Backend: Add user_modified boolean to ChatSession model
// Migration: ALTER TABLE chat_sessions ADD COLUMN user_modified BOOLEAN DEFAULT FALSE;

// Frontend: After first AI response completes
useEffect(() => {
  const shouldGenerateTitle =
    messages.length === 2 && // First user message + first AI response
    sessionDetail?.title === "Untitled" &&
    !sessionDetail?.user_modified;

  if (shouldGenerateTitle) {
    generateTitle({
      sessionId,
      userMessage: messages[0].content
    });
  }
}, [messages, sessionDetail]);

// API endpoint: POST /sessions/{sessionId}/generate-title
// - Calls LLM with prompt: "Generate a concise title (max 70 chars) for this conversation: {userMessage}"
// - Updates session.title only if user_modified = false
// - Returns updated session

// Manual rename: PATCH /sessions/{sessionId}
// - Sets user_modified = true on title update
// - Prevents future auto-generation
```

**Why this pattern:**
- Generated after response = more context than just first message
- user_modified flag prevents overwriting user intent
- 70 char limit follows ChatGPT convention
- Sidebar shows "Untitled" during generation (no loading spinner needed)
- Source: ChatGPT behavior analysis + LLM best practices

### Pattern 4: Theme Management with next-themes
**What:** System preference detection + user override with localStorage persistence
**When to use:** Theme switching in Next.js apps (SSR-compatible)

**Implementation:**
```typescript
// app/layout.tsx
import { ThemeProvider } from "next-themes";

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}

// components/UserMenu.tsx (dropdown)
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return (
    <DropdownMenuItem onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      <span>{theme === "dark" ? "Light" : "Dark"} mode</span>
    </DropdownMenuItem>
  );
}
```

**Why this pattern:**
- suppressHydrationWarning on html prevents Next.js hydration errors
- defaultTheme="system" respects OS preference on first visit
- enableSystem allows detecting system changes
- disableTransitionOnChange prevents jarring CSS transitions
- mounted check prevents SSR/client mismatch
- localStorage used automatically by next-themes (no manual setup)
- Source: next-themes official docs + shadcn/ui dark mode guide

### Pattern 5: Session Persistence Verification
**What:** Sessions survive page refresh and re-login via TanStack Query cache + database
**When to use:** Already implemented — verification tasks only

**Current implementation:**
- TanStack Query caches session list and detail (`queryKey: ["sessions"]`)
- Session data persists in PostgreSQL (ChatSession model)
- Messages linked via session_id foreign key (cascade preserved)
- Files linked via session_files M2M table (cascade preserved)

**Verification checklist:**
1. Create session, send messages, link files
2. Hard refresh (Cmd+R) → session data reloads from server
3. Logout + login → new session created (per user requirement)
4. Navigate to previous session from sidebar → messages + files intact
5. Close browser, reopen app → query refetches from server

**Why this works:**
- TanStack Query handles cache + refetch automatically
- Database foreign keys preserve relationships
- No additional implementation needed — verify only

### Anti-Patterns to Avoid
- **Blocking input on no files:** Input should stay enabled, only send is blocked. Allows users to compose messages while adding files.
- **Hiding "Untitled" with loading spinner:** Sidebar should show placeholder text, not spinner. Title generation is background task.
- **Hardcoded file limits:** Always fetch from config endpoint. Limits may change per deployment.
- **Theme in global state:** Use next-themes hook, not Zustand. Avoids SSR issues and duplicate state.
- **Manual localStorage for theme:** next-themes handles this automatically with proper SSR hydration.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Theme switching with SSR | Custom localStorage + manual class toggle | next-themes | Handles no-flash, hydration, system preference, storage automatically. Custom implementation has edge cases. |
| Toast notifications | Custom toast manager | sonner | Already integrated, theme-aware, action buttons supported, accessible. |
| Form validation state | Custom error state management | React state + useEffect | Simple validation doesn't need library. Inline warnings + toast sufficient. |
| LLM title generation | Client-side text analysis/truncation | Backend LLM call | LLM understands context, generates semantic titles. Truncation loses meaning. |
| Query persistence | Manual localStorage sync | TanStack Query cache | Query cache handles staleness, refetching, invalidation. Manual sync error-prone. |

**Key insight:** This phase integrates existing tools, not new libraries. The stack is complete — focus is on validation logic, state coordination, and UX polish.

## Common Pitfalls

### Pitfall 1: Theme Flash on Page Load
**What goes wrong:** Users see wrong theme briefly during page load (flash of unstyled content)
**Why it happens:** Theme class applied after JavaScript loads, server renders default theme
**How to avoid:** Use next-themes with suppressHydrationWarning on html tag + defaultTheme="system"
**Warning signs:** Brief white flash on dark mode reload, or vice versa
**Source:** next-themes GitHub issues + shadcn/ui documentation

### Pitfall 2: Validation State Not Clearing
**What goes wrong:** Inline warning persists after user links a file
**Why it happens:** Missing useEffect dependency or state update trigger
**How to avoid:** useEffect with linkedFileIds dependency, clear warning when length > 0
**Warning signs:** User adds file but warning doesn't disappear
**Source:** React hooks best practices

### Pitfall 3: Title Generation Race Condition
**What goes wrong:** Title generated multiple times, or overwrites user rename
**Why it happens:** Missing user_modified check or multiple triggers firing
**How to avoid:** Check messages.length === 2 AND title === "Untitled" AND !user_modified before calling API
**Warning signs:** Title flips back to auto-generated after user renames
**Source:** Standard flag pattern for user overrides

### Pitfall 4: SSR Hydration Mismatch with Theme
**What goes wrong:** "Text content does not match server-rendered HTML" error
**Why it happens:** Theme-dependent content rendered differently on server vs client
**How to avoid:** Use mounted check before rendering theme-dependent UI, or use next-themes' useTheme with conditional rendering
**Warning signs:** Console warnings about hydration mismatch, theme toggle not appearing
**Source:** Next.js + next-themes documentation

### Pitfall 5: Unlinking Last File Without Validation
**What goes wrong:** Session ends up with 0 files, breaks chat functionality
**Why it happens:** Missing length check before unlink mutation
**How to avoid:** Disable unlink UI when linkedFileIds.length === 1, show toast on attempt
**Warning signs:** Session with no files, chat input shows persistent warning
**Source:** User decision + validation best practices

### Pitfall 6: Hardcoded "Untitled" String
**What goes wrong:** Title generation checks break if placeholder text changes
**Why it happens:** Magic string comparison instead of explicit flag
**How to avoid:** Use user_modified flag as source of truth, not title comparison
**Warning signs:** Title generation doesn't trigger after changing default title text
**Source:** Database-driven state management best practices

## Code Examples

Verified patterns from existing codebase and official sources:

### File Requirement Check (ChatInput)
```typescript
// Based on: Existing ChatInput.tsx + user requirements
interface ChatInputProps {
  linkedFileIds: string[]; // New prop
  // ... existing props
}

export function ChatInput({ linkedFileIds, onSend, ...props }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [noFilesWarning, setNoFilesWarning] = useState(false);

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed) return;

    // File requirement validation
    if (linkedFileIds.length === 0) {
      toast.error("Link at least one file before chatting");
      setNoFilesWarning(true);
      return;
    }

    setNoFilesWarning(false);
    onSend(trimmed);
    setMessage("");
  };

  // Auto-clear warning when files are linked
  useEffect(() => {
    if (linkedFileIds.length > 0) {
      setNoFilesWarning(false);
    }
  }, [linkedFileIds]);

  return (
    <div className="space-y-2">
      {/* Existing textarea + send button */}
      <div className="flex items-end gap-3">
        <TextareaAutosize {...props} />
        <Button onClick={handleSend}>Send</Button>
      </div>

      {/* Inline warning */}
      {noFilesWarning && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>Link at least one file to start chatting</span>
        </div>
      )}

      {/* Existing toolbar */}
    </div>
  );
}
```

### Prevent Last File Unlink
```typescript
// Based on: Existing useUnlinkFile + validation pattern
function FileLinkingDropdown({ sessionId, linkedFileIds }: Props) {
  const { mutate: unlinkFile } = useUnlinkFile();

  const handleUnlink = (fileId: string) => {
    // Prevent unlinking last file
    if (linkedFileIds.length <= 1) {
      toast.warning("At least one file must be linked to the session");
      return;
    }

    unlinkFile(
      { sessionId, fileId },
      {
        onSuccess: () => toast.success("File unlinked"),
        onError: (error) => toast.error(error.message),
      }
    );
  };

  return (
    <DropdownMenuContent>
      {linkedFileIds.map((file) => (
        <div key={file.id} className="flex items-center justify-between">
          <span>{file.name}</span>
          <Button
            variant="ghost"
            size="sm"
            disabled={linkedFileIds.length === 1}
            onClick={() => handleUnlink(file.id)}
            title={
              linkedFileIds.length === 1
                ? "Cannot remove last file"
                : "Unlink file"
            }
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </DropdownMenuContent>
  );
}
```

### Theme Provider Integration
```typescript
// Source: next-themes official docs + shadcn/ui
// app/layout.tsx
import { ThemeProvider } from "next-themes";

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Providers>{children}</Providers>
        </ThemeProvider>
      </body>
    </html>
  );
}
```

### Theme Toggle Component
```typescript
// Source: next-themes docs + shadcn/ui patterns
// components/ThemeToggle.tsx
"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  return (
    <DropdownMenuItem onClick={toggleTheme}>
      {theme === "dark" ? (
        <>
          <Sun className="h-4 w-4 mr-2" />
          <span>Light mode</span>
        </>
      ) : (
        <>
          <Moon className="h-4 w-4 mr-2" />
          <span>Dark mode</span>
        </>
      )}
    </DropdownMenuItem>
  );
}
```

### LLM Title Generation Hook
```typescript
// New hook for title generation
// hooks/useGenerateTitle.ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export function useGenerateTitle() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      sessionId,
      userMessage,
    }: {
      sessionId: string;
      userMessage: string;
    }) => {
      const response = await apiClient.post(
        `/sessions/${sessionId}/generate-title`,
        { user_message: userMessage }
      );
      if (!response.ok) {
        throw new Error("Failed to generate title");
      }
      return response.json();
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      queryClient.invalidateQueries({
        queryKey: ["sessions", variables.sessionId],
      });
    },
  });
}

// Usage in ChatInterface.tsx
const { mutate: generateTitle } = useGenerateTitle();

useEffect(() => {
  const shouldGenerate =
    messages.length === 2 && // First exchange complete
    sessionDetail?.title === "Untitled" &&
    !sessionDetail?.user_modified;

  if (shouldGenerate) {
    generateTitle({
      sessionId,
      userMessage: messages[0].content,
    });
  }
}, [messages, sessionDetail]);
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom theme toggle with localStorage | next-themes library | Became standard ~2022 | Eliminates SSR flash, handles system preference, localStorage automatic |
| react-toastify | sonner | Rising in 2024-2025 | Cleaner API, better animations, theme integration, action buttons |
| Manual form validation | Controlled inputs + useEffect | React 16.8+ (hooks) | Simpler state management, easier to reason about |
| Hardcoded config values | Backend config endpoints | Phase 14 | Dynamic limits, easier deployment changes |
| File-based chat | Session-based chat | Phase 14-16 | Multi-file support, better conversation management |

**Deprecated/outdated:**
- ThemeProvider from styled-components: Replaced by next-themes for Next.js apps
- Manual class toggling for dark mode: next-themes handles this automatically
- Context API for theme: next-themes uses React Context internally, no need to build custom

**Current as of 2026-02:**
- next-themes v0.4.6 is current stable (released 2024)
- sonner v2.0.7 is latest (released late 2025)
- TanStack Query v5 is current major version
- Zustand v5.0.11 includes critical persist middleware fix (Jan 2026)

## Open Questions

1. **Session title generation timing**
   - What we know: Generate after first AI response for more context
   - What's unclear: Should we retry on failure? Should there be a fallback to first message truncation?
   - Recommendation: Fail silently (leave "Untitled"), user can rename manually. Log errors for monitoring.

2. **Theme transition animations**
   - What we know: next-themes supports disableTransitionOnChange to prevent CSS transitions
   - What's unclear: User wants smooth transitions or instant switch?
   - Recommendation: Start with disableTransitionOnChange=true (instant), gather feedback. Smooth transitions can cause jarring layout shifts.

3. **Session limit enforcement**
   - What we know: Backend has configurable session limits
   - What's unclear: Should we prevent creation at limit or show warning and allow?
   - Recommendation: Check during research if limit exists in config. If yes, show warning before creation. If no limit configured, allow unlimited.

4. **Sidebar session item design**
   - What we know: Show title, need secondary metadata
   - What's unclear: Title + time OR title + file count?
   - Recommendation: Title + relative time ("2m ago", "yesterday") — matches ChatGPT/Julius.ai patterns. File count less useful for scanning history.

## Sources

### Primary (HIGH confidence)
- **Next.js Dark Mode Implementation**: [GitHub - pacocoursey/next-themes](https://github.com/pacocoursey/next-themes) - Official next-themes repository
- **shadcn/ui Dark Mode Guide**: [Next.js Dark Mode - shadcn/ui](https://ui.shadcn.com/docs/dark-mode/next) - Reference implementation
- **Sonner Documentation**: [shadcn/ui Sonner](https://ui.shadcn.com/docs/components/radix/sonner) - Toast notifications with action buttons
- **TanStack Query Persistence**: [persistQueryClient - TanStack Query](https://tanstack.com/query/v4/docs/framework/react/plugins/persistQueryClient) - Cache persistence patterns
- **Zustand Persist Middleware**: [persist - Zustand](https://zustand.docs.pmnd.rs/middlewares/persist) - State persistence with localStorage
- Existing codebase: ChatInput.tsx, ChatInterface.tsx, useSessionMutations.ts, sessionStore.ts, providers.tsx
- Phase 17 RESEARCH.md - File management patterns and validation
- Backend models: ChatSession, session_files association table

### Secondary (MEDIUM confidence)
- **Form Validation Patterns**: [React Form Validation - react.wiki](https://react.wiki/hooks/form-validation/) - Controlled input validation
- **Theme Persistence Best Practices**: [Persisting React State in LocalStorage](https://www.ignek.com/blog/persisting-react-state-in-localstorage) - When to use localStorage vs backend
- **Sonner Modern Patterns**: [Sonner: Modern Toast Notifications - Stackademic](https://medium.com/@rivainasution/shadcn-ui-react-series-part-19-sonner-modern-toast-notifications-done-right-903757c5681f) - 2026 toast patterns
- **Button Disabled State Patterns**: [Disable Submit Button Until Valid - CoreUI](https://coreui.io/answers/how-to-disable-submit-button-in-react-until-form-is-valid/) - Form validation UX

### Tertiary (LOW confidence)
- **LLM Best Practices**: [My LLM Coding Workflow - Addy Osmani](https://addyo.substack.com/p/my-llm-coding-workflow-going-into) - General LLM guidance, not specific to title generation
- **ChatGPT Title Generation**: [OpenAI Community - Title Generator](https://community.openai.com/t/prompt-to-get-chatgpt-api-to-write-concise-chat-titles-as-it-does-in-chatgpt-chat-application/85644) - Community discussion, not official docs

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** - All libraries already installed and in use, versions verified
- Architecture patterns: **HIGH** - Built on existing codebase patterns, next-themes is well-documented
- Validation UX: **HIGH** - User requirements explicit, patterns verified in existing code
- LLM title generation: **MEDIUM** - Implementation straightforward, but prompt optimization may need iteration
- Theme implementation: **HIGH** - next-themes is standard solution, already partially integrated
- Session persistence: **HIGH** - Already implemented via TanStack Query + database, verification only

**Research date:** 2026-02-11
**Valid until:** 2026-03-15 (30 days - stable technologies, unlikely to change)

**Technology stability:**
- next-themes: Mature library (v0.4.6), stable API
- sonner: Stable v2.0 release, active maintenance
- TanStack Query v5: Current major version, stable
- Zustand v5: Recent critical fix (Jan 2026), stable
- Validation patterns: Fundamental React patterns, not version-dependent
