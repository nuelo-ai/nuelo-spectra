# Phase 6: Frontend UI & Interactive Data Cards - Research

**Researched:** 2026-02-03
**Domain:** Modern Next.js 16 + React 19 streaming chat interface with progressive Data Card rendering
**Confidence:** HIGH

## Summary

This phase builds a polished Next.js web interface featuring real-time chat with streaming AI responses and interactive Data Cards. The research focuses on the modern Next.js 16 + React 19 stack with Server-Sent Events (SSE) for streaming, shadcn/ui for components, and specialized libraries for data tables and state management.

The standard approach uses Next.js 16's App Router with React 19.2 features, EventSource API for SSE streaming, TanStack Table for sortable/filterable data displays, TanStack Query for server state, and Zustand for client-side UI state. The architecture follows server-first principles with careful client/server component boundaries, progressive rendering patterns, and optimistic UI updates.

**Primary recommendation:** Use Next.js 16 App Router with async Request APIs, implement SSE streaming with immediate Response return pattern, leverage shadcn/ui collapsible components for Data Cards, and manage tab state with Zustand while server state stays in TanStack Query.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.x | React framework with App Router | Industry standard for React SSR/SSG, built-in streaming support, React 19.2 integration |
| React | 19.2 | UI library with Server Components | Latest stable with useOptimistic, useActionState, improved streaming |
| shadcn/ui | Latest | Component library | Copy-paste components built on Radix UI, full customization, TypeScript-first |
| TanStack Table | v8+ | Data table component | Headless, supports sorting/filtering/pagination, 100k+ rows performance |
| TanStack Query | v5+ | Server state management | Industry standard for data fetching, caching, and invalidation |
| Zustand | 4.x+ | Client state management | Lightweight (3KB), no boilerplate, perfect for UI state like active tabs |
| Tailwind CSS | 3.x+ | Utility-first CSS | Required by shadcn/ui, gradient support, modern SaaS aesthetics |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-dropzone | 14.x+ | File drag-and-drop | Standard pattern for file uploads with validation |
| react-textarea-autosize | 8.x+ | Auto-expanding textarea | Chat input with shift-enter multiline support |
| papaparse | 5.x+ | CSV parsing/generation | Browser-side CSV export without backend |
| Lucide React | Latest | Icon library | Default icon set for shadcn/ui, tree-shakeable |
| Sonner | Latest | Toast notifications | shadcn/ui ecosystem, minimal API |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TanStack Query | SWR | SWR is lighter but less feature-rich, Query has better cache invalidation |
| Zustand | Jotai/Redux Toolkit | Jotai more atomic, Redux more structure - Zustand hits sweet spot |
| shadcn/ui | MUI/Chakra UI | Full libraries have more components but less customization |
| EventSource SSE | WebSockets | WebSockets bidirectional but more complex, SSE perfect for unidirectional streaming |

**Installation:**
```bash
# Next.js 16 project with shadcn/ui
npx create-next-app@latest --typescript --tailwind
npx shadcn@latest init

# Core dependencies
npm install @tanstack/react-table @tanstack/react-query zustand

# Supporting libraries
npm install react-dropzone react-textarea-autosize papaparse
npm install lucide-react sonner

# Dev dependencies
npm install -D @types/papaparse
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth routes (login, register)
│   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── chat/          # Chat interface with file tabs
│   │   └── settings/      # User settings page
│   └── api/               # API routes for SSE streaming
├── components/            # React components
│   ├── ui/               # shadcn/ui components (owned, editable)
│   ├── chat/             # Chat-specific components
│   │   ├── ChatInput.tsx          # Auto-expanding textarea with shift-enter
│   │   ├── ChatMessage.tsx        # Message bubbles with streaming
│   │   ├── DataCard.tsx           # Progressive rendering card
│   │   ├── TypingIndicator.tsx    # Animated dots
│   │   └── FileTabBar.tsx         # Multi-tab interface
│   ├── file/             # File management components
│   │   ├── FileSidebar.tsx        # File list with info/delete
│   │   ├── FileUploadZone.tsx     # Drag-drop with progress
│   │   └── FileInfoModal.tsx      # Onboarding analysis display
│   └── data/             # Data display components
│       ├── DataTable.tsx          # TanStack Table wrapper
│       └── DownloadButtons.tsx    # CSV/Markdown export
├── lib/                   # Utilities and configurations
│   ├── api-client.ts     # API client with auth headers
│   ├── query-client.ts   # TanStack Query setup
│   └── utils.ts          # shadcn/ui utils (cn helper)
├── hooks/                # Custom React hooks
│   ├── useSSEStream.ts   # EventSource SSE streaming
│   ├── useFileManager.ts # File list and operations
│   └── useTabState.ts    # Active tabs with Zustand
├── stores/               # Zustand stores
│   └── tabStore.ts       # Active file tabs (max 5)
└── types/                # TypeScript types
    ├── chat.ts           # Message, DataCard types
    └── file.ts           # File, UploadStatus types
```

### Pattern 1: Server-First Component Architecture
**What:** Maximize Server Components, mark only interactive parts as Client Components
**When to use:** All pages and layouts by default
**Example:**
```typescript
// app/(dashboard)/chat/page.tsx - SERVER COMPONENT (default)
import { FileManager } from '@/components/file/FileManager'
import { ChatInterface } from '@/components/chat/ChatInterface'

export default async function ChatPage() {
  // Direct database/API calls - no route handler needed
  const files = await db.file.findMany({
    where: { userId: session.user.id }
  })

  return (
    <div className="flex h-screen">
      <FileManager initialFiles={files} /> {/* Client Component */}
      <ChatInterface /> {/* Client Component */}
    </div>
  )
}

// components/chat/ChatInterface.tsx - CLIENT COMPONENT
'use client'

import { useTabState } from '@/hooks/useTabState'
import { ChatInput } from './ChatInput'

export function ChatInterface() {
  const { activeTabs, currentTab } = useTabState()
  // Client-side interactivity here
}
```

### Pattern 2: SSE Streaming with Immediate Response Return
**What:** Return Response immediately to avoid buffering, stream after return
**When to use:** All Server-Sent Events endpoints
**Example:**
```typescript
// app/api/chat/stream/route.ts
import { NextRequest } from 'next/server'

export async function POST(req: NextRequest) {
  const { message, fileId } = await req.json()

  // Create readable stream
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Backend SSE connection
        const eventSource = new EventSource(
          `${process.env.BACKEND_URL}/chat/stream`,
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, fileId })
          }
        )

        eventSource.onmessage = (event) => {
          controller.enqueue(`data: ${event.data}\n\n`)
        }

        eventSource.onerror = () => {
          eventSource.close()
          controller.close()
        }
      } catch (error) {
        controller.error(error)
      }
    }
  })

  // CRITICAL: Return immediately to avoid buffering
  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no', // Disable nginx buffering
    },
  })
}
```

### Pattern 3: Progressive Data Card Rendering
**What:** Sections appear sequentially as SSE events arrive
**When to use:** Data Cards with query brief, table, and explanation
**Example:**
```typescript
// components/chat/DataCard.tsx
'use client'

import { useState } from 'react'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { DataTable } from '@/components/data/DataTable'
import { DownloadButtons } from '@/components/data/DownloadButtons'

interface DataCardProps {
  queryBrief?: string
  tableData?: { columns: string[], rows: any[] }
  explanation?: string
  isStreaming: boolean
}

export function DataCard({ queryBrief, tableData, explanation, isStreaming }: DataCardProps) {
  const [isOpen, setIsOpen] = useState(true)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="border rounded-lg p-4 my-4">
      {/* Section 1: Query Brief - appears first */}
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{queryBrief || 'Processing query...'}</h3>
          <ChevronDownIcon className={isOpen ? 'rotate-180' : ''} />
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent>
        {/* Section 2: Data Table - appears when ready */}
        {tableData && (
          <div className="mt-4">
            <DataTable columns={tableData.columns} data={tableData.rows} />
            <DownloadButtons
              data={tableData}
              format="csv"
              filename={`${queryBrief}-data.csv`}
            />
          </div>
        )}

        {/* Section 3: AI Explanation - streams in last */}
        {explanation && (
          <div className="mt-4 prose">
            <p>{explanation}</p>
            <DownloadButtons
              content={`# ${queryBrief}\n\n${explanation}`}
              format="markdown"
              filename={`${queryBrief}-analysis.md`}
            />
          </div>
        )}

        {isStreaming && !explanation && (
          <div className="mt-4 text-muted-foreground">
            <TypingIndicator />
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  )
}
```

### Pattern 4: Client State Management with Zustand
**What:** Zustand for UI state (active tabs), TanStack Query for server state
**When to use:** Tab management, modal open/close, UI preferences
**Example:**
```typescript
// stores/tabStore.ts
import { create } from 'zustand'

interface FileTab {
  fileId: string
  fileName: string
  isActive: boolean
}

interface TabStore {
  tabs: FileTab[]
  currentTab: string | null
  maxTabs: 5

  openTab: (fileId: string, fileName: string) => void
  closeTab: (fileId: string) => void
  switchTab: (fileId: string) => void
  canOpenTab: () => boolean
}

export const useTabStore = create<TabStore>((set, get) => ({
  tabs: [],
  currentTab: null,
  maxTabs: 5,

  canOpenTab: () => get().tabs.length < get().maxTabs,

  openTab: (fileId, fileName) => {
    const { tabs, maxTabs } = get()

    // Check if already open
    const existingTab = tabs.find(t => t.fileId === fileId)
    if (existingTab) {
      get().switchTab(fileId)
      return
    }

    // Check max tabs
    if (tabs.length >= maxTabs) {
      // Show alert to user
      alert(`Maximum ${maxTabs} tabs allowed. Please close a tab first.`)
      return
    }

    set({
      tabs: [...tabs, { fileId, fileName, isActive: true }],
      currentTab: fileId
    })
  },

  closeTab: (fileId) => {
    const { tabs, currentTab } = get()
    const newTabs = tabs.filter(t => t.fileId !== fileId)

    // Auto-switch to next available tab
    const newCurrentTab = currentTab === fileId
      ? (newTabs[0]?.fileId || null)
      : currentTab

    set({ tabs: newTabs, currentTab: newCurrentTab })
  },

  switchTab: (fileId) => set({ currentTab: fileId })
}))

// Usage in component
'use client'

import { useTabStore } from '@/stores/tabStore'

export function FileTabBar() {
  const { tabs, currentTab, switchTab, closeTab } = useTabStore()

  return (
    <div className="flex gap-2 border-b">
      {tabs.map(tab => (
        <div
          key={tab.fileId}
          className={currentTab === tab.fileId ? 'active' : ''}
          onClick={() => switchTab(tab.fileId)}
        >
          <span>{tab.fileName}</span>
          <button onClick={() => closeTab(tab.fileId)}>×</button>
        </div>
      ))}
    </div>
  )
}
```

### Pattern 5: Auto-Expanding Textarea with Shift-Enter
**What:** Enter sends message, Shift+Enter adds newline, auto-grows vertically
**When to use:** Chat input fields
**Example:**
```typescript
// components/chat/ChatInput.tsx
'use client'

import { useRef, KeyboardEvent } from 'react'
import TextareaAutosize from 'react-textarea-autosize'
import { Button } from '@/components/ui/button'
import { SendIcon } from 'lucide-react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Shift+Enter: allow new line (default behavior)
    if (e.key === 'Enter' && e.shiftKey) {
      return
    }

    // Enter alone: send message
    if (e.key === 'Enter') {
      e.preventDefault()
      const message = textareaRef.current?.value.trim()
      if (message) {
        onSend(message)
        textareaRef.current!.value = ''
      }
    }
  }

  const handleSendClick = () => {
    const message = textareaRef.current?.value.trim()
    if (message) {
      onSend(message)
      textareaRef.current!.value = ''
    }
  }

  return (
    <div className="flex gap-2 items-end">
      <TextareaAutosize
        ref={textareaRef}
        placeholder="Ask about your data..."
        className="flex-1 resize-none rounded-lg border p-3"
        minRows={1}
        maxRows={6}
        onKeyDown={handleKeyDown}
        disabled={disabled}
      />
      <Button
        onClick={handleSendClick}
        disabled={disabled}
        size="icon"
      >
        <SendIcon />
      </Button>
    </div>
  )
}
```

### Pattern 6: Browser-Side File Export (CSV & Markdown)
**What:** Generate and download files without server using Blob API
**When to use:** Export table data as CSV or analysis as Markdown
**Example:**
```typescript
// components/data/DownloadButtons.tsx
'use client'

import { Button } from '@/components/ui/button'
import { DownloadIcon } from 'lucide-react'
import Papa from 'papaparse'

interface DownloadButtonsProps {
  data?: { columns: string[], rows: any[] }
  content?: string
  format: 'csv' | 'markdown'
  filename: string
}

export function DownloadButtons({ data, content, format, filename }: DownloadButtonsProps) {

  const downloadCSV = () => {
    if (!data) return

    // Convert to CSV using papaparse
    const csv = Papa.unparse({
      fields: data.columns,
      data: data.rows
    })

    // Create blob and download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()

    // Cleanup
    URL.revokeObjectURL(url)
  }

  const downloadMarkdown = () => {
    if (!content) return

    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.click()

    URL.revokeObjectURL(url)
  }

  if (format === 'csv') {
    return (
      <Button onClick={downloadCSV} variant="outline" size="sm">
        <DownloadIcon className="mr-2 h-4 w-4" />
        Download CSV
      </Button>
    )
  }

  return (
    <Button onClick={downloadMarkdown} variant="outline" size="sm">
      <DownloadIcon className="mr-2 h-4 w-4" />
      Download Markdown
    </Button>
  )
}
```

### Anti-Patterns to Avoid
- **Fetching data with useEffect in Client Components:** Use Server Components for initial data, TanStack Query for client fetches
- **Marking entire pages as Client Components:** Only interactive parts need 'use client'
- **Creating route handlers for Server Component data:** Call database/API directly in Server Components
- **Not cleaning up EventSource connections:** Always close in useEffect cleanup
- **Manual cache invalidation with strings:** Use TanStack Query's hierarchical query keys
- **Storing server data in Zustand:** Use TanStack Query for server state, Zustand only for UI state
- **Not returning Response immediately for SSE:** Causes buffering issues in Next.js

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Data table sorting/filtering | Custom table logic | TanStack Table | Handles virtualization, pagination, 100k+ rows, accessibility |
| File drag-and-drop | Custom drop zone | react-dropzone | File validation, preview, mobile support, accessibility |
| Textarea auto-resize | Manual height calculation | react-textarea-autosize | Handles edge cases, performance optimized |
| CSV generation | String concatenation | papaparse | Escapes special characters, handles edge cases |
| Toast notifications | Custom notification system | Sonner | Stacking, dismissal, accessibility, animations |
| Collapsible sections | Custom accordion | shadcn/ui Collapsible/Accordion | Keyboard nav, ARIA, animations, controlled state |
| Icon library | SVG imports | Lucide React | Tree-shakeable, consistent design, extensive library |

**Key insight:** Modern React ecosystem has battle-tested solutions for common UI patterns. Custom solutions typically miss accessibility, edge cases, and performance optimizations.

## Common Pitfalls

### Pitfall 1: Client/Server Component Boundary Confusion
**What goes wrong:** Marking components as 'use client' too high in the tree, passing Server Components incorrectly, using browser APIs in Server Components
**Why it happens:** App Router's server-first architecture is a paradigm shift from traditional React
**How to avoid:**
- Default to Server Components, add 'use client' only when needed (hooks, event handlers, browser APIs)
- Place 'use client' as deep as possible in component tree
- Pass Server Components to Client Components as children prop (JSX), not function prop
- Check `typeof window !== 'undefined'` before accessing browser APIs
**Warning signs:**
- Large client bundle size
- Errors about accessing cookies/headers in Client Components
- "localStorage is not defined" errors

### Pitfall 2: EventSource Memory Leaks
**What goes wrong:** EventSource connections remain open after component unmount, causing memory leaks and zombie connections
**Why it happens:** Not returning cleanup function from useEffect
**How to avoid:**
```typescript
useEffect(() => {
  const eventSource = new EventSource('/api/stream')

  eventSource.onmessage = (event) => {
    // Handle event
  }

  // CRITICAL: Cleanup on unmount
  return () => {
    eventSource.close()
  }
}, [])
```
**Warning signs:**
- Network tab shows multiple open connections
- Memory usage grows over time
- React Strict Mode double-mounting causes issues

### Pitfall 3: Next.js 16 Async Request APIs
**What goes wrong:** Accessing `params`, `searchParams`, `cookies()`, `headers()` synchronously throws errors
**Why it happens:** Next.js 16 removed synchronous access to Request APIs
**How to avoid:**
```typescript
// OLD (Next.js 15)
export default function Page({ params, searchParams }) {
  const id = params.id // Synchronous
}

// NEW (Next.js 16) - REQUIRED
export default async function Page({
  params,
  searchParams
}: {
  params: Promise<{ id: string }>,
  searchParams: Promise<{ query: string }>
}) {
  const { id } = await params // Async
  const { query } = await searchParams // Async
}
```
**Warning signs:**
- Build errors about synchronous API access
- TypeScript errors expecting Promise types

### Pitfall 4: SSE Buffering in Next.js
**What goes wrong:** SSE responses don't stream to client, entire response arrives at once
**Why it happens:** Next.js waits for route handler to complete before sending Response
**How to avoid:**
- Return Response immediately
- Start streaming work after return statement
- Include `'X-Accel-Buffering': 'no'` header for nginx compatibility
**Warning signs:**
- No progressive rendering, entire response arrives at end
- Browser network tab shows pending request until completion

### Pitfall 5: TanStack Query Cache Invalidation Mistakes
**What goes wrong:** Mutations succeed but UI doesn't update, or wrong queries invalidate
**Why it happens:** Forgetting to invalidate cache, or using flat query keys without hierarchical structure
**How to avoid:**
```typescript
// BAD: Flat keys, hard to invalidate related queries
['user.files']
['file.details', fileId]

// GOOD: Hierarchical keys, fuzzy matching
['files', 'user', userId]
['files', 'detail', fileId]

// Invalidate all file queries
queryClient.invalidateQueries({ queryKey: ['files'] })

// Invalidate after mutation
const mutation = useMutation({
  mutationFn: deleteFile,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['files'] })
  }
})
```
**Warning signs:**
- Data doesn't refresh after mutations
- Manual page refresh required to see changes

### Pitfall 6: Incorrect State Management Choice
**What goes wrong:** Storing server data in Zustand, or putting UI state in TanStack Query
**Why it happens:** Unclear separation of concerns between client and server state
**How to avoid:**
- TanStack Query: Server data (API responses, lists, details)
- Zustand: UI state (active tabs, modal open/close, theme preferences)
- useState: Component-local state (form inputs, toggles)
**Warning signs:**
- Complex cache invalidation logic in Zustand
- Trying to persist TanStack Query cache across sessions

### Pitfall 7: Missing React 19 Migration Steps
**What goes wrong:** Build errors, type errors, runtime warnings
**Why it happens:** React 19 has breaking changes requiring code updates
**How to avoid:**
- Update TypeScript to 5.1+, set `"jsx": "react-jsx"` in tsconfig.json
- Use named imports: `import { useState } from 'react'`
- Update @types/react and @types/react-dom to latest
- Run `npx @next/codemod@canary upgrade latest` for automated migration
**Warning signs:**
- TypeScript errors about JSX
- Import errors for React hooks

## Code Examples

Verified patterns from official sources:

### EventSource SSE Stream Hook
```typescript
// hooks/useSSEStream.ts
// Pattern: Clean EventSource with proper cleanup
'use client'

import { useEffect, useState } from 'react'

interface UseSSEStreamOptions {
  url: string
  body?: any
  enabled?: boolean
}

export function useSSEStream({ url, body, enabled = true }: UseSSEStreamOptions) {
  const [data, setData] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (!enabled) return

    setIsStreaming(true)

    // For POST requests, use fetch to initiate then read stream
    const controller = new AbortController()

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
      .then(response => {
        if (!response.ok) throw new Error('Stream failed')

        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        function read() {
          reader?.read().then(({ done, value }) => {
            if (done) {
              setIsStreaming(false)
              return
            }

            const chunk = decoder.decode(value)
            const lines = chunk.split('\n')

            lines.forEach(line => {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                setData(prev => prev + data)
              }
            })

            read()
          })
        }

        read()
      })
      .catch(err => {
        setError(err)
        setIsStreaming(false)
      })

    // CRITICAL: Cleanup on unmount
    return () => {
      controller.abort()
    }
  }, [url, body, enabled])

  return { data, isStreaming, error }
}
```

### Typing Indicator Animation
```typescript
// components/chat/TypingIndicator.tsx
// Pattern: Three-dot animation with staggered timing
'use client'

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1">
      <span className="animate-typing-dot animation-delay-0 h-2 w-2 rounded-full bg-muted-foreground" />
      <span className="animate-typing-dot animation-delay-200 h-2 w-2 rounded-full bg-muted-foreground" />
      <span className="animate-typing-dot animation-delay-400 h-2 w-2 rounded-full bg-muted-foreground" />
    </div>
  )
}

// Add to tailwind.config.ts
module.exports = {
  theme: {
    extend: {
      animation: {
        'typing-dot': 'typing 1.4s infinite ease-in-out',
      },
      keyframes: {
        typing: {
          '0%, 60%, 100%': { opacity: '0.3' },
          '30%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [
    function({ addUtilities }) {
      addUtilities({
        '.animation-delay-0': { 'animation-delay': '0s' },
        '.animation-delay-200': { 'animation-delay': '0.2s' },
        '.animation-delay-400': { 'animation-delay': '0.4s' },
      })
    },
  ],
}
```

### TanStack Table with Sorting and Filtering
```typescript
// components/data/DataTable.tsx
// Pattern: Client-side table with sorting/filtering
'use client'

import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
} from '@tanstack/react-table'
import { useState } from 'react'

interface DataTableProps {
  columns: string[]
  data: any[]
}

export function DataTable({ columns, data }: DataTableProps) {
  const [sorting, setSorting] = useState([])
  const [globalFilter, setGlobalFilter] = useState('')

  const tableColumns = columns.map(col => ({
    accessorKey: col,
    header: col,
  }))

  const table = useReactTable({
    data,
    columns: tableColumns,
    state: {
      sorting,
      globalFilter,
    },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: { pageSize: 10 },
    },
  })

  return (
    <div>
      <input
        value={globalFilter}
        onChange={e => setGlobalFilter(e.target.value)}
        placeholder="Search all columns..."
        className="mb-4 rounded border p-2"
      />

      <table className="w-full border-collapse">
        <thead>
          {table.getHeaderGroups().map(headerGroup => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map(header => (
                <th
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler()}
                  className="cursor-pointer border p-2 text-left"
                >
                  {flexRender(header.column.columnDef.header, header.getContext())}
                  {header.column.getIsSorted()
                    ? header.column.getIsSorted() === 'desc' ? ' ↓' : ' ↑'
                    : null
                  }
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id}>
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="border p-2">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="mt-4 flex items-center gap-2">
        <button
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
          className="rounded border px-4 py-2"
        >
          Previous
        </button>
        <span>
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
        </span>
        <button
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
          className="rounded border px-4 py-2"
        >
          Next
        </button>
      </div>
    </div>
  )
}
```

### File Upload with Progress and Stages
```typescript
// components/file/FileUploadZone.tsx
// Pattern: Drag-drop with multi-stage progress
'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadIcon } from 'lucide-react'

const UPLOAD_STAGES = [
  { id: 1, label: 'Uploading...', progress: 33 },
  { id: 2, label: 'Analyzing data...', progress: 66 },
  { id: 3, label: 'Ready!', progress: 100 },
]

export function FileUploadZone() {
  const [uploadStage, setUploadStage] = useState(0)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    // Stage 1: Upload
    setUploadStage(1)
    const formData = new FormData()
    formData.append('file', file)

    const uploadRes = await fetch('/api/files/upload', {
      method: 'POST',
      body: formData,
    })

    const { fileId } = await uploadRes.json()

    // Stage 2: Analysis (SSE stream)
    setUploadStage(2)
    const eventSource = new EventSource(`/api/files/${fileId}/analyze`)

    eventSource.addEventListener('complete', () => {
      setUploadStage(3)
      eventSource.close()

      // Redirect to chat after 1s
      setTimeout(() => {
        window.location.href = `/chat?file=${fileId}`
      }, 1000)
    })
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
    multiple: false,
  })

  const currentStage = UPLOAD_STAGES[uploadStage - 1]

  return (
    <div>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition
          ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
          ${uploadStage > 0 ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        <UploadIcon className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
        <p className="text-lg font-medium">
          {isDragActive ? 'Drop file here...' : 'Drag & drop your file, or click to browse'}
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          Excel (.xlsx, .xls) or CSV files, max 10MB
        </p>
      </div>

      {uploadStage > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">{currentStage?.label}</span>
            <span className="text-sm text-muted-foreground">{currentStage?.progress}%</span>
          </div>
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
              style={{ width: `${currentStage?.progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WebSockets for streaming | Server-Sent Events (SSE) | 2023-2024 | Simpler unidirectional streaming, no connection handshake overhead |
| Redux for all state | TanStack Query + Zustand | 2023-2025 | Separation of server/client state, less boilerplate |
| Pages Router | App Router with Server Components | 2023 (Next.js 13+) | Server-first architecture, streaming support |
| Synchronous Request APIs | Async Request APIs | 2025 (Next.js 16) | Better streaming semantics, required migration |
| useFormState | useActionState | 2024 (React 19) | Renamed hook with same functionality |
| Custom components | Copy-paste components (shadcn/ui) | 2023-2024 | Full ownership and customization |
| Implicit caching | Opt-in caching with "use cache" | 2025 (Next.js 16) | Explicit cache control |

**Deprecated/outdated:**
- **getServerSideProps/getStaticProps**: Replaced by async Server Components with direct data fetching
- **next/head**: Replaced by Metadata API in App Router
- **synchronous params/searchParams**: Must await these in Next.js 16
- **React 18's useFormState**: Renamed to useActionState in React 19

## Open Questions

Things that couldn't be fully resolved:

1. **React 19 Compiler Adoption**
   - What we know: React 19 Compiler is stable in Next.js 16, automatically memoizes components
   - What's unclear: Whether to enable by default for this phase, potential build time impact
   - Recommendation: Start without compiler, enable if performance issues arise (opt-in optimization)

2. **Turbopack Production Readiness**
   - What we know: Turbopack is default bundler in Next.js 16, significant build speed improvements
   - What's unclear: Production deployment edge cases, compatibility with all ecosystem tools
   - Recommendation: Use default Turbopack, have webpack fallback plan if issues arise

3. **Progressive Enhancement vs JavaScript-First**
   - What we know: Next.js 16 emphasizes Server Components for progressive enhancement
   - What's unclear: Whether chat interface should work without JavaScript (non-functional without SSE)
   - Recommendation: Focus on JavaScript-enabled experience, chat inherently requires JS for streaming

## Sources

### Primary (HIGH confidence)
- [Next.js 16 Official Announcement](https://nextjs.org/blog/next-16) - Features, breaking changes, migration guide
- [Next.js 16 Upgrade Guide](https://nextjs.org/docs/app/guides/upgrading/version-16) - Async Request APIs, version requirements
- [React 19 Official Blog](https://react.dev/blog/2024/12/05/react-19) - useActionState, useOptimistic, form Actions
- [shadcn/ui Next.js Installation](https://ui.shadcn.com/docs/installation/next) - Setup and integration
- [TanStack Table Documentation](https://tanstack.com/table/latest) - Sorting, filtering, pagination APIs
- [TanStack Query Guide](https://tanstack.com/query/latest) - Cache invalidation, server state management
- [Zustand GitHub](https://github.com/pmndrs/zustand) - State management patterns

### Secondary (MEDIUM confidence)
- [Next.js App Router Common Mistakes (Vercel Blog)](https://vercel.com/blog/common-mistakes-with-the-next-js-app-router-and-how-to-fix-them) - Client/Server Component boundaries
- [SSE Streaming in Next.js (Medium, Jan 2026)](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996) - Immediate Response return pattern
- [Server-Sent Events in React (OneUpTime, Jan 2026)](https://oneuptime.com/blog/post/2026-01-15-server-sent-events-sse-react/view) - EventSource cleanup patterns
- [React State Management 2026 (Nucamp)](https://www.nucamp.co/blog/state-management-in-2026-redux-context-api-and-modern-patterns) - Modern state management strategy
- [React Optimistic UI (FreeCodeCamp)](https://www.freecodecamp.org/news/how-to-use-the-optimistic-ui-pattern-with-the-useoptimistic-hook-in-react/) - useOptimistic patterns

### Tertiary (LOW confidence)
- [FlowToken LLM Streaming Library](https://github.com/Ephibbs/flowtoken) - Specialized streaming animations (evaluate if needed)
- [React Chat Stream Hook](https://github.com/XD2Sketch/react-chat-stream) - Alternative to custom SSE hook (evaluate vs custom)
- WebSearch results on gradient design trends (aesthetic guidance, not technical requirements)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries officially documented, widely adopted, versions verified
- Architecture: HIGH - Patterns from official Next.js/React docs and Vercel best practices
- Pitfalls: HIGH - Based on official migration guides, GitHub discussions, and recent 2026 articles

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - stack is stable, Next.js 16 and React 19 recently released)
