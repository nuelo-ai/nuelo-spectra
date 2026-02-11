# Phase 16: Frontend Restructure (Session-Centric UX) - Research

**Researched:** 2026-02-11
**Domain:** Session-centric navigation with collapsible sidebars, chat history management, and multi-file context display
**Confidence:** HIGH

## Summary

Phase 16 transforms the current file-tab-centric navigation into a session-based chat interface similar to ChatGPT. The research covers three major areas: (1) collapsible sidebar patterns using shadcn/ui Sidebar component, (2) chat session state management with Zustand + TanStack Query, and (3) responsive layout architecture for left sidebar (chat history), main content (active chat), and right sidebar (linked files).

The existing stack (Next.js 16, React 19, shadcn/ui, Zustand, TanStack Query) is well-suited for this restructure. The backend session APIs from Phase 14 provide all necessary endpoints. The key architectural shift is replacing file-based tab store with session-based navigation store, migrating ChatInterface from file-id to session-id, and implementing the official shadcn/ui Sidebar component with "icon" collapsible mode.

**Primary recommendation:** Use shadcn/ui Sidebar component with `collapsible="icon"` mode for left chat history sidebar, maintain existing Zustand pattern for session state with TanStack Query for server-side session data, implement right sidebar as custom collapsible panel (not shadcn Sidebar), and preserve all current ChatInterface logic while updating from file-based to session-based routing.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Left Sidebar Design:**
- Collapsible sidebar with toggle button — when collapsed, shows icons only (New Chat, recent chat icons, My Files)
- Fixed width when expanded (~260-300px, Claude's discretion on exact value)
- Top section: "New Chat" button and "My Files" button grouped together
- Middle section: Flat chronological chat list, most recent first — NO time grouping (Today/Week/Month removed from requirements)
- Bottom section: User profile/avatar with dropdown for Settings, Logout
- Each chat item shows title only (no timestamp, no file count, no preview)
- Active session indicated by highlighted background color
- Hover on chat item reveals three-dot menu with Rename and Delete options
- Delete requires confirmation dialog; Rename is inline edit
- No search/filter for chat history in this phase

**Welcome Screen:**
- Friendly, warm greeting: "Hi [name]! What would you like to analyze today?" style
- Text-only greeting — no logo, no action cards, no quick-start tiles
- Chat input is always active (not disabled) — if user sends a message without a linked file, show a prompt asking them to "Add a file first"
- Query suggestions appear below greeting once first file is linked
- Suggestions refresh when additional files are linked (reflect all currently linked files)
- Initial suggestions disappear after first user message; follow-up suggestions continue to appear on Data Cards as in current flow

**Chat List Display:**
- Flat chronological list, most recent first
- Title-only display per session — compact and clean
- Active session: highlighted background
- Chat list loading strategy: Claude's discretion (load all vs lazy-load based on expected volume)

**Linked Files Right Panel:**
- Collapsible right sidebar panel (not top bar, not header strip)
- Toggle button in the chat header area to show/hide
- Default state: closed (maximizes chat area)
- Each file shows: file name + row/column count + file type icon + (i) info button + remove button
- Clicking (i) opens file context modal (same as current version)
- Remove button unlinks file from chat session with confirmation dialog ("Remove [filename] from this chat?")
- File removal unlinks only — does not delete the file itself

### Claude's Discretion

- Exact sidebar width when expanded (range: 260-300px)
- Chat list loading strategy (all-at-once vs lazy-load)
- Collapsed sidebar icon design
- Transition animations between states
- Exact spacing, typography, and color values
- Mobile/responsive breakpoint behavior

### Deferred Ideas (OUT OF SCOPE)

- Chat history search/filter — future enhancement when chat volume warrants it
- Time-based grouping of chat history (Today, This Week, etc.) — removed from Phase 16, can be reconsidered later

</user_constraints>

## Standard Stack

All components already exist in the project. No new libraries required.

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shadcn/ui Sidebar | Latest | Collapsible sidebar component | Official shadcn component with icon collapse mode, responsive, keyboard shortcuts |
| Zustand | 5.0.11 | Session navigation state | Already used for tab state, lightweight (3KB), perfect for UI state |
| TanStack Query | 5.90.20 | Server state (sessions, messages) | Already used, handles caching/invalidation for session list and messages |
| Next.js | 16.1.6 | Framework with App Router | Current stack, dynamic routes for `/sessions/[id]` |
| React | 19.2.3 | UI library | Current stack |
| Lucide React | 0.563.0 | Icons | Current icon library, used for sidebar icons |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui Dialog | Latest | Confirmation dialogs | Delete session/unlink file confirmations |
| shadcn/ui DropdownMenu | Latest | Chat item context menu | Three-dot menu for Rename/Delete |
| shadcn/ui AlertDialog | Latest | Delete confirmations | Session deletion warnings |
| shadcn/ui Avatar | Latest | User profile display | Bottom sidebar section |

**Installation:**
```bash
# Add shadcn/ui Sidebar component (if not already present)
npx shadcn@latest add sidebar

# All other components already installed in project
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/src/
├── app/
│   └── (dashboard)/
│       ├── layout.tsx                # NEW: Session-aware layout with sidebars
│       ├── page.tsx                  # NEW: Default redirect to /sessions/new
│       ├── sessions/
│       │   ├── new/
│       │   │   └── page.tsx          # NEW: Welcome screen with file linking
│       │   └── [sessionId]/
│       │       └── page.tsx          # NEW: Session chat page
│       └── files/
│           └── page.tsx              # NEW: My Files screen (Phase 17)
│
├── components/
│   ├── sidebar/                      # NEW: Left sidebar components
│   │   ├── ChatSidebar.tsx           # Main left sidebar with shadcn Sidebar
│   │   ├── ChatList.tsx              # Scrollable chat history list
│   │   ├── ChatListItem.tsx          # Individual chat item with context menu
│   │   └── UserSection.tsx           # Bottom profile section
│   │
│   ├── session/                      # NEW: Session-specific components
│   │   ├── WelcomeScreen.tsx         # Greeting + file link prompt
│   │   ├── LinkedFilesPanel.tsx      # Right collapsible panel
│   │   ├── FileCard.tsx              # Individual file card in panel
│   │   └── FileLinkButton.tsx        # Button to open file picker
│   │
│   ├── chat/                         # EXISTING: Mostly preserved
│   │   ├── ChatInterface.tsx         # MODIFIED: session-id instead of file-id
│   │   ├── ChatInput.tsx             # PRESERVED: no changes
│   │   ├── ChatMessage.tsx           # PRESERVED: no changes
│   │   ├── DataCard.tsx              # PRESERVED: no changes
│   │   └── QuerySuggestions.tsx      # MODIFIED: multi-file context
│   │
│   └── file/                         # EXISTING: Moved to My Files screen
│       ├── FileSidebar.tsx           # REMOVED: replaced by ChatSidebar
│       ├── FileUploadZone.tsx        # PRESERVED: used in My Files screen
│       └── FileInfoModal.tsx         # PRESERVED: used in LinkedFilesPanel
│
├── hooks/
│   ├── useChatSessions.ts            # NEW: TanStack Query for session list
│   ├── useCreateSession.ts           # NEW: Mutation for new sessions
│   ├── useDeleteSession.ts           # NEW: Mutation for session deletion
│   ├── useLinkFile.ts                # NEW: Mutation for linking files
│   ├── useUnlinkFile.ts              # NEW: Mutation for unlinking files
│   ├── useChatMessages.ts            # MODIFIED: session-id instead of file-id
│   └── useSSEStream.ts               # MODIFIED: session-id instead of file-id
│
└── stores/
    ├── tabStore.ts                   # REMOVED: replaced by sessionStore
    └── sessionStore.ts               # NEW: Active session, sidebar state
```

### Pattern 1: shadcn/ui Sidebar with Icon Collapse Mode
**What:** Use official shadcn Sidebar component with `collapsible="icon"` for left chat history sidebar
**When to use:** Left sidebar implementation
**Example:**
```typescript
// components/sidebar/ChatSidebar.tsx
'use client'

import { Sidebar, SidebarProvider, SidebarContent, SidebarHeader,
         SidebarFooter, SidebarTrigger, useSidebar } from '@/components/ui/sidebar'
import { Button } from '@/components/ui/button'
import { MessageSquarePlus, FolderOpen } from 'lucide-react'

export function ChatSidebar() {
  const { state } = useSidebar() // "expanded" | "collapsed"

  return (
    <SidebarProvider defaultOpen={true}>
      <Sidebar
        collapsible="icon"  // Collapses to icons only
        className="border-r"
        style={{
          width: state === "expanded" ? "280px" : "60px"
        }}
      >
        {/* Top section: New Chat + My Files buttons */}
        <SidebarHeader className="p-3 border-b space-y-2">
          <Button
            variant="default"
            className="w-full justify-start gap-2"
          >
            <MessageSquarePlus className="h-4 w-4" />
            {state === "expanded" && <span>New Chat</span>}
          </Button>
          <Button
            variant="ghost"
            className="w-full justify-start gap-2"
          >
            <FolderOpen className="h-4 w-4" />
            {state === "expanded" && <span>My Files</span>}
          </Button>
        </SidebarHeader>

        {/* Middle section: Chat history */}
        <SidebarContent>
          <ChatList expanded={state === "expanded"} />
        </SidebarContent>

        {/* Bottom section: User profile */}
        <SidebarFooter className="border-t p-3">
          <UserSection expanded={state === "expanded"} />
        </SidebarFooter>
      </Sidebar>
    </SidebarProvider>
  )
}
```
**Source:** [shadcn/ui Sidebar Documentation](https://ui.shadcn.com/docs/components/radix/sidebar)

### Pattern 2: Session State Management with Zustand + TanStack Query
**What:** Zustand for UI state (active session, sidebar open/closed), TanStack Query for server state (session list, messages)
**When to use:** All session-related state management
**Example:**
```typescript
// stores/sessionStore.ts
import { create } from 'zustand'

interface SessionStore {
  currentSessionId: string | null
  leftSidebarOpen: boolean
  rightSidebarOpen: boolean

  setCurrentSession: (id: string | null) => void
  toggleLeftSidebar: () => void
  toggleRightSidebar: () => void
}

export const useSessionStore = create<SessionStore>((set) => ({
  currentSessionId: null,
  leftSidebarOpen: true,
  rightSidebarOpen: false,  // Default closed per requirements

  setCurrentSession: (id) => set({ currentSessionId: id }),
  toggleLeftSidebar: () => set((state) => ({
    leftSidebarOpen: !state.leftSidebarOpen
  })),
  toggleRightSidebar: () => set((state) => ({
    rightSidebarOpen: !state.rightSidebarOpen
  })),
}))

// hooks/useChatSessions.ts
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useChatSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const res = await apiClient.get('/sessions?limit=50&offset=0')
      if (!res.ok) throw new Error('Failed to load sessions')
      return res.json()
    },
    staleTime: 1000 * 60 * 5,  // 5 minutes
  })
}

// hooks/useCreateSession.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (title: string) => {
      const res = await apiClient.post('/sessions', { title })
      if (!res.ok) throw new Error('Failed to create session')
      return res.json()
    },
    onSuccess: () => {
      // Invalidate session list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    }
  })
}
```
**Source:** [Zustand + React Query State Management](https://medium.com/@freeyeon96/zustand-react-query-new-state-management-7aad6090af56)

### Pattern 3: Inline Rename with Controlled Input
**What:** Three-dot menu reveals Rename option, which triggers inline editing mode
**When to use:** Chat list item rename functionality
**Example:**
```typescript
// components/sidebar/ChatListItem.tsx
'use client'

import { useState, useRef, useEffect } from 'react'
import { MoreVertical, Trash2, Edit2 } from 'lucide-react'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem,
         DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'

export function ChatListItem({ session, isActive, onSelect, onRename, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [title, setTitle] = useState(session.title)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-focus input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleRename = () => {
    if (title.trim() !== session.title) {
      onRename(session.id, title.trim())
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename()
    } else if (e.key === 'Escape') {
      setTitle(session.title)
      setIsEditing(false)
    }
  }

  return (
    <div
      className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
        ${isActive ? 'bg-accent' : 'hover:bg-accent/50'}`}
      onClick={() => !isEditing && onSelect(session.id)}
    >
      {isEditing ? (
        <input
          ref={inputRef}
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onBlur={handleRename}
          onKeyDown={handleKeyDown}
          className="flex-1 bg-transparent border-b focus:outline-none"
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <>
          <span className="flex-1 text-sm truncate">{session.title}</span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100"
                onClick={(e) => e.stopPropagation()}
              >
                <MoreVertical className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setIsEditing(true)}>
                <Edit2 className="mr-2 h-4 w-4" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => onDelete(session.id)}
                className="text-destructive focus:text-destructive"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </>
      )}
    </div>
  )
}
```
**Source:** [React Dropdown onChange Patterns](https://thelinuxcode.com/dropdown-onchange-event-in-react-from-basics-to-production-patterns/)

### Pattern 4: Welcome Screen with Conditional Query Suggestions
**What:** Show warm greeting, display query suggestions only after first file is linked
**When to use:** New session welcome screen
**Example:**
```typescript
// components/session/WelcomeScreen.tsx
'use client'

import { useAuth } from '@/hooks/useAuth'
import { useSessionDetail } from '@/hooks/useChatSessions'
import { QuerySuggestions } from '@/components/chat/QuerySuggestions'
import { FileLinkButton } from './FileLinkButton'
import { ChatInput } from '@/components/chat/ChatInput'

export function WelcomeScreen({ sessionId }) {
  const { user } = useAuth()
  const { data: session } = useSessionDetail(sessionId)

  const hasLinkedFiles = session?.files && session.files.length > 0
  const firstName = user?.first_name || 'there'

  const handleSend = (message: string) => {
    if (!hasLinkedFiles) {
      // Show prompt instead of sending
      toast.error('Please add a file first to start analyzing')
      return
    }
    // Proceed with sending message
    startChat(message)
  }

  return (
    <div className="flex flex-col items-center justify-center h-full px-8">
      <div className="max-w-2xl w-full space-y-6">
        {/* Warm greeting - text only */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-semibold">
            Hi {firstName}! What would you like to analyze today?
          </h1>
        </div>

        {/* File link prompt */}
        {!hasLinkedFiles && (
          <div className="flex justify-center">
            <FileLinkButton sessionId={sessionId} />
          </div>
        )}

        {/* Query suggestions appear after first file linked */}
        {hasLinkedFiles && session.query_suggestions && (
          <QuerySuggestions
            categories={session.query_suggestions.categories}
            onSelect={handleSend}
            autoSend={true}
          />
        )}

        {/* Chat input always active */}
        <div className="mt-8">
          <ChatInput
            onSend={handleSend}
            disabled={false}  // Always active
            placeholder={
              hasLinkedFiles
                ? "Ask a question about your data..."
                : "Add a file first to start analyzing"
            }
          />
        </div>
      </div>
    </div>
  )
}
```
**Source:** [Chat App Empty State Best Practices](https://www.eleken.co/blog-posts/empty-state-ux)

### Pattern 5: Right Collapsible Panel (Custom Implementation)
**What:** Custom collapsible right sidebar (NOT shadcn Sidebar) for linked files with toggle in chat header
**When to use:** Linked files display panel
**Example:**
```typescript
// components/session/LinkedFilesPanel.tsx
'use client'

import { useState } from 'react'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { FileCard } from './FileCard'
import { useSessionStore } from '@/stores/sessionStore'

export function LinkedFilesPanel({ sessionId, files }) {
  const { rightSidebarOpen, toggleRightSidebar } = useSessionStore()

  return (
    <>
      {/* Toggle button in chat header - rendered by parent */}

      {/* Collapsible panel */}
      <div
        className={`
          border-l bg-background transition-all duration-300 ease-in-out
          ${rightSidebarOpen ? 'w-80' : 'w-0'}
        `}
        style={{
          overflow: rightSidebarOpen ? 'visible' : 'hidden',
          opacity: rightSidebarOpen ? 1 : 0
        }}
      >
        {rightSidebarOpen && (
          <div className="h-full flex flex-col">
            {/* Panel header */}
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-semibold">Linked Files ({files.length})</h3>
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleRightSidebar}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            {/* File list */}
            <ScrollArea className="flex-1">
              <div className="p-4 space-y-3">
                {files.map((file) => (
                  <FileCard
                    key={file.id}
                    file={file}
                    sessionId={sessionId}
                  />
                ))}
              </div>
            </ScrollArea>
          </div>
        )}
      </div>
    </>
  )
}

// components/session/FileCard.tsx
export function FileCard({ file, sessionId }) {
  const [showInfoModal, setShowInfoModal] = useState(false)
  const { mutate: unlinkFile } = useUnlinkFile()

  const handleUnlink = () => {
    if (confirm(`Remove ${file.original_filename} from this chat?`)) {
      unlinkFile({ sessionId, fileId: file.id })
    }
  }

  return (
    <div className="p-3 border rounded-lg space-y-2">
      <div className="flex items-center gap-2">
        <FileSpreadsheet className="h-4 w-4 text-primary" />
        <span className="flex-1 text-sm font-medium truncate">
          {file.original_filename}
        </span>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => setShowInfoModal(true)}
        >
          <Info className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 hover:text-destructive"
          onClick={handleUnlink}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>
      <div className="text-xs text-muted-foreground">
        {file.row_count} rows × {file.column_count} columns
      </div>

      {showInfoModal && (
        <FileInfoModal
          fileId={file.id}
          onClose={() => setShowInfoModal(false)}
        />
      )}
    </div>
  )
}
```

### Pattern 6: Migrating ChatInterface from File-ID to Session-ID
**What:** Update existing ChatInterface to work with session-id while preserving all logic
**When to use:** Adapting existing chat components to session-based architecture
**Example:**
```typescript
// Before (file-based):
// app/(dashboard)/dashboard/page.tsx
export default function DashboardPage() {
  const { tabs, currentTabId } = useTabStore()
  const currentTab = tabs.find((tab) => tab.fileId === currentTabId)

  return currentTab ? (
    <ChatInterface
      fileId={currentTab.fileId}
      fileName={currentTab.fileName}
    />
  ) : (
    <EmptyState />
  )
}

// After (session-based):
// app/(dashboard)/sessions/[sessionId]/page.tsx
export default function SessionPage({ params }) {
  const { data: session } = useSessionDetail(params.sessionId)

  return session ? (
    <ChatInterface
      sessionId={session.id}
      sessionTitle={session.title}
      linkedFiles={session.files}
    />
  ) : (
    <LoadingState />
  )
}

// components/chat/ChatInterface.tsx - Updated
interface ChatInterfaceProps {
  sessionId: string          // Changed from fileId
  sessionTitle: string        // Changed from fileName
  linkedFiles: FileBasicInfo[] // New prop
}

export function ChatInterface({ sessionId, sessionTitle, linkedFiles }: ChatInterfaceProps) {
  // Replace all fileId references with sessionId
  const { data: chatData, isLoading, refetch } = useChatMessages(sessionId)  // Updated
  const { startStream } = useSSEStream()

  const handleSend = async (message: string) => {
    await startStream(sessionId, message, searchToggle.enabled)  // Updated
  }

  // Rest of component logic remains the same
  // All existing features preserved: streaming, DataCards, suggestions, etc.
}
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Collapsible sidebar | Custom sidebar with state management | shadcn/ui Sidebar component | Handles responsive behavior, keyboard shortcuts (Cmd+B), mobile/desktop states, accessibility out of the box |
| Chat session caching | Manual localStorage/sessionStorage | TanStack Query with staleTime | Automatic cache invalidation, deduplication, background refetch, optimistic updates |
| Inline editing UI | Custom contentEditable div | Controlled input with focus/blur handlers | Better accessibility, form validation, keyboard navigation (Enter/Escape) |
| Confirmation dialogs | Custom modal state management | shadcn/ui AlertDialog | Accessible, keyboard navigation, focus trap, ESC to close |
| Virtual scrolling for chat list | Custom intersection observer | Start with simple scrolling | Only needed for 1000+ chats; premature optimization for expected volume |

**Key insight:** The shadcn/ui ecosystem already provides all necessary components. The session API from Phase 14 handles server state. Focus on composition, not custom implementation.

## Common Pitfalls

### Pitfall 1: Mixing File-Based and Session-Based Routing
**What goes wrong:** Existing file-tab URLs (`/dashboard?file=abc`) conflict with new session URLs (`/sessions/xyz`)
**Why it happens:** Incremental migration leaves both navigation systems active
**How to avoid:**
- Remove file-based routing completely in single PR
- Create migration that moves existing chat history to sessions
- Add redirect from old `/dashboard` to `/sessions/new`
**Warning signs:** 404 errors when clicking chat history, duplicate chat interfaces, URL params not matching state

### Pitfall 2: Not Invalidating Session List After Mutations
**What goes wrong:** Creating/deleting sessions doesn't update the sidebar chat list
**Why it happens:** TanStack Query cache not invalidated after mutations
**How to avoid:** Always use `queryClient.invalidateQueries({ queryKey: ['sessions'] })` in mutation `onSuccess` callbacks
**Warning signs:** New sessions not appearing, deleted sessions still visible, stale session titles

### Pitfall 3: Right Sidebar State Conflicts with Content Reflow
**What goes wrong:** Chat messages jump/reflow when right sidebar opens/closes
**Why it happens:** Main content area width changes, causing message re-wrap
**How to avoid:**
- Use CSS transitions for smooth width changes
- Default right sidebar to closed state (per requirements)
- Apply `transition-all duration-300` to main content area
**Warning signs:** Janky animations, messages jumping during sidebar toggle, scroll position lost

### Pitfall 4: Session-ID Not Available on Initial Render
**What goes wrong:** `useChatMessages(sessionId)` fires before session detail loads, causing 404
**Why it happens:** Race condition between session detail fetch and messages fetch
**How to avoid:**
- Conditionally render ChatInterface only after session detail loads
- Use TanStack Query's `enabled` option: `enabled: !!sessionId`
**Warning signs:** Flash of error state, 404 requests in network tab, console errors about undefined sessionId

### Pitfall 5: Overloading Chat List with Metadata
**What goes wrong:** Chat list loads slowly, sidebar feels sluggish
**Why it happens:** Fetching full session detail (with files, message counts) for every list item
**How to avoid:**
- Use list endpoint that returns title + id only
- Fetch session detail only when session is opened
- Per requirements: "Each chat item shows title only (no timestamp, no file count, no preview)"
**Warning signs:** Slow sidebar render, N+1 query problem, high network traffic on page load

### Pitfall 6: Welcome Screen Query Suggestions Not Updating
**What goes wrong:** Query suggestions don't refresh when additional files are linked
**Why it happens:** Welcome screen component doesn't re-fetch session detail when files array changes
**How to avoid:**
- Use TanStack Query's `refetchOnMount` and `refetchOnWindowFocus`
- Invalidate session detail query when linking/unlinking files
- Watch `session.files.length` in useEffect to trigger suggestion refresh
**Warning signs:** Stale suggestions, suggestions only reflect first file, new files ignored

### Pitfall 7: Inline Rename Loses Focus on Re-render
**What goes wrong:** Typing in rename input causes blur/unfocus
**Why it happens:** Parent component re-renders, recreating input element
**How to avoid:**
- Use local state for editing mode within ChatListItem component
- Don't lift editing state to parent
- Use `useRef` for input and `useEffect` for auto-focus
**Warning signs:** Input loses focus while typing, can't complete rename, characters dropped

## Code Examples

Verified patterns from official sources and existing codebase:

### Session List Query with Optimistic Updates
```typescript
// hooks/useChatSessions.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useChatSessions() {
  return useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const res = await apiClient.get('/sessions?limit=50&offset=0')
      if (!res.ok) throw new Error('Failed to load sessions')
      const data = await res.json()
      return data.sessions  // Array of ChatSessionResponse
    },
    staleTime: 1000 * 60 * 5,  // 5 minutes
    gcTime: 1000 * 60 * 30,    // 30 minutes
  })
}

export function useUpdateSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ sessionId, title }: { sessionId: string, title: string }) => {
      const res = await apiClient.patch(`/sessions/${sessionId}`, { title })
      if (!res.ok) throw new Error('Failed to update session')
      return res.json()
    },
    onMutate: async ({ sessionId, title }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['sessions'] })

      // Snapshot previous value
      const previousSessions = queryClient.getQueryData(['sessions'])

      // Optimistically update
      queryClient.setQueryData(['sessions'], (old: any) =>
        old.map((s: any) => s.id === sessionId ? { ...s, title } : s)
      )

      return { previousSessions }
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousSessions) {
        queryClient.setQueryData(['sessions'], context.previousSessions)
      }
    },
    onSettled: () => {
      // Refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['sessions'] })
    }
  })
}
```
**Source:** [TanStack Query Caching Guide](https://tanstack.com/query/latest/docs/framework/react/guides/caching)

### Chat List with Lazy Loading Strategy
```typescript
// components/sidebar/ChatList.tsx
'use client'

import { useChatSessions } from '@/hooks/useChatSessions'
import { ChatListItem } from './ChatListItem'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Loader2 } from 'lucide-react'

export function ChatList({ expanded }: { expanded: boolean }) {
  const { data: sessions, isLoading, error } = useChatSessions()
  const { currentSessionId, setCurrentSession } = useSessionStore()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-sm text-destructive text-center">
        Failed to load chat history
      </div>
    )
  }

  // Decision: Load all sessions at once (expected volume < 100)
  // If volume exceeds 500, switch to infinite scroll with Intersection Observer
  return (
    <ScrollArea className="flex-1">
      <div className="p-2 space-y-1">
        {sessions?.map((session) => (
          <ChatListItem
            key={session.id}
            session={session}
            isActive={session.id === currentSessionId}
            expanded={expanded}
            onSelect={setCurrentSession}
          />
        ))}
      </div>
    </ScrollArea>
  )
}
```

### Responsive Layout with Three Columns
```typescript
// app/(dashboard)/layout.tsx
'use client'

import { ChatSidebar } from '@/components/sidebar/ChatSidebar'
import { LinkedFilesPanel } from '@/components/session/LinkedFilesPanel'
import { useSessionStore } from '@/stores/sessionStore'
import { useSessionDetail } from '@/hooks/useChatSessions'

export default function DashboardLayout({ children }) {
  const { currentSessionId, rightSidebarOpen } = useSessionStore()
  const { data: session } = useSessionDetail(currentSessionId)

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left sidebar - collapsible with shadcn/ui */}
      <ChatSidebar />

      {/* Main content area - dynamic width based on right sidebar state */}
      <main
        className="flex-1 overflow-hidden transition-all duration-300"
        style={{
          marginRight: rightSidebarOpen ? '320px' : '0'
        }}
      >
        {children}
      </main>

      {/* Right sidebar - custom collapsible panel, fixed position */}
      <div
        className="fixed right-0 top-0 h-screen"
        style={{ width: rightSidebarOpen ? '320px' : '0' }}
      >
        {currentSessionId && (
          <LinkedFilesPanel
            sessionId={currentSessionId}
            files={session?.files || []}
          />
        )}
      </div>
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| File-based tabs with max 5 limit | Session-based navigation with unlimited history | Phase 16 | Users can maintain multiple ongoing conversations without tab limits |
| Top header tab bar | Left sidebar chat list | Phase 16 | Matches modern chat UX patterns (ChatGPT, Claude), more screen space for content |
| File sidebar for navigation | File sidebar for management (My Files screen) | Phase 16 | Clearer separation: sessions for chat, files for management |
| Single file per tab | Multiple files per session | Phase 14 → Phase 16 | Multi-file analysis support with session context |
| localStorage for tab state | Zustand + TanStack Query | Phase 16 | Server-synced state, survives page refresh, multi-device support |

**Deprecated/outdated:**
- `useTabStore`: Replaced by `useSessionStore` (session-centric, no tab limit)
- File-based routing (`/dashboard?file=xyz`): Replaced by `/sessions/:sessionId`
- Tab close confirmation: Replaced by session deletion confirmation (more appropriate for persistent conversations)
- FileSidebar component: Moved to My Files screen, no longer in main layout

## Open Questions

1. **Chat List Pagination Strategy**
   - What we know: Backend supports limit/offset pagination, typical user has < 100 sessions
   - What's unclear: When to switch from load-all to lazy-load (performance threshold)
   - Recommendation: Start with load-all (limit=50), monitor performance, switch to infinite scroll if > 200 sessions becomes common

2. **Session Title Auto-Generation**
   - What we know: Backend creates sessions with default title "New Chat"
   - What's unclear: Should frontend auto-generate titles from first message or first linked file?
   - Recommendation: Keep default "New Chat", require manual rename (per requirements: "Rename is inline edit"). Phase 17+ could add auto-title feature.

3. **Mobile Breakpoint Behavior**
   - What we know: User specified "Mobile/responsive breakpoint behavior" as Claude's discretion
   - What's unclear: Should mobile show offcanvas overlay or bottom sheet for chat list?
   - Recommendation: Use shadcn Sidebar's built-in mobile detection (`isMobile`), default to offcanvas overlay on mobile (< 768px)

4. **Query Suggestion Refresh Logic**
   - What we know: "Suggestions refresh when additional files are linked (reflect all currently linked files)"
   - What's unclear: How to aggregate suggestions from multiple files with different contexts
   - Recommendation: Backend Phase 15 ContextAssembler already handles multi-file metadata; query frontend `/sessions/:id` endpoint to get refreshed suggestions after file link mutation

5. **Welcome Screen Persistence**
   - What we know: Welcome screen shows for new sessions before first message
   - What's unclear: Should welcome screen reappear when all messages are deleted from session?
   - Recommendation: No - welcome screen only for truly new sessions. Empty sessions show standard empty state with previous context visible.

## Sources

### Primary (HIGH confidence)
- [shadcn/ui Sidebar Component Documentation](https://ui.shadcn.com/docs/components/radix/sidebar) - Official component API and patterns
- [TanStack Query Caching Guide](https://tanstack.com/query/latest/docs/framework/react/guides/caching) - Caching strategies and configuration
- Backend Phase 14 `/sessions` API endpoints (verified in codebase) - Session CRUD operations
- Existing frontend stack (package.json, components) - Current architecture and patterns

### Secondary (MEDIUM confidence)
- [Zustand + React Query State Management](https://medium.com/@freeyeon96/zustand-react-query-new-state-management-7aad6090af56) - Hybrid state management patterns
- [React Dropdown onChange Patterns](https://thelinuxcode.com/dropdown-onchange-event-in-react-from-basics-to-production-patterns/) - Inline editing best practices
- [Chat App Empty State Best Practices](https://www.eleken.co/blog-posts/empty-state-ux) - Welcome screen design patterns
- [Next.js Collapsible Sidebar Pattern](https://reacthustle.com/blog/nextjs-react-responsive-collapsible-sidebar-tailwind) - Responsive sidebar implementation

### Tertiary (LOW confidence)
- [React Chat History List Optimization](https://blog.logrocket.com/react-infinite-scroll/) - Infinite scroll vs pagination tradeoffs
- [State Management in 2026](https://www.nucamp.co/blog/state-management-in-2026-redux-context-api-and-modern-patterns) - Modern state management trends

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed, official documentation verified
- Architecture: HIGH - Existing codebase patterns + official shadcn/ui patterns + verified backend APIs
- Pitfalls: MEDIUM-HIGH - Based on common React/Next.js migration issues and TanStack Query caching gotchas

**Research date:** 2026-02-11
**Valid until:** 2026-04-11 (60 days - stable frontend ecosystem, core libraries mature)
