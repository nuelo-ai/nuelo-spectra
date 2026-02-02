# Frontend UI Stack Research

**Domain:** AI-Powered Data Analytics Platform (Frontend)
**Researched:** 2026-02-02
**Confidence:** HIGH

## Recommended Stack for Interactive Data Cards

### Overview

This stack is optimized for building interactive Data Cards with streaming AI responses, sortable tables, visualizations, and polished animations in Next.js 15. All components are vendor-neutral, open source, and deploy anywhere.

---

## 1. UI Component Library

### **RECOMMENDED: shadcn/ui + Radix UI**

**Version:** Latest (updated monthly)

**Rationale:**
- **Copy-paste architecture** - components live in your codebase, not node_modules
- **Full code ownership** - customize without fighting framework opinions
- Built on **Radix UI primitives** for accessibility (WCAG 2.1 compliant)
- **Zero-runtime CSS** with Tailwind integration
- **104,000+ GitHub stars** (January 2026), 560,000+ weekly npm downloads
- Perfect for **custom Data Card designs** - no Material Design constraints
- **Excellent TypeScript support** out of the box
- **Next.js 15 compatible** - works with App Router and Server Components

**Installation:**
```bash
npx shadcn@latest init
npx shadcn@latest add button card table dialog skeleton tabs
```

**Why Not Material UI or Chakra UI?**
- Runtime CSS-in-JS (Emotion) causes performance issues with React 19 concurrent rendering
- Less customizable without fighting Material Design opinions
- Heavier bundle sizes and hydration costs

**Example Data Card Component:**
```tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export function DataCard({ title, isLoading, children }) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? <Skeleton className="h-48" /> : children}
      </CardContent>
    </Card>
  )
}
```

---

## 2. Data Table Library

### **RECOMMENDED: TanStack Table v8**

**Package:** `@tanstack/react-table`
**Version:** 8.21.3+

**Rationale:**
- **Headless architecture** - complete UI control for custom Data Card tables
- **First-class TypeScript support** - built with TypeScript for type safety
- Handles **10,000+ rows efficiently** with virtualization
- Lightweight and flexible for sortable, filterable, expandable tables
- **MIT license** - no licensing costs
- Works perfectly with shadcn/ui table components

**Installation:**
```bash
npm i @tanstack/react-table
npm i @tanstack/react-virtual  # for large datasets
```

**Integration with shadcn/ui:**
```bash
npx shadcn@latest add table
```

**Example Usage:**
```tsx
import { useReactTable, getCoreRowModel, getSortedRowModel } from '@tanstack/react-table'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"

export function DataTable({ data, columns }) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map(headerGroup => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map(header => (
              <TableHead key={header.id}>
                {header.column.columnDef.header}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map(row => (
          <TableRow key={row.id}>
            {row.getVisibleCells().map(cell => (
              <TableCell key={cell.id}>
                {cell.renderValue()}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

**When to Use AG Grid Instead:**
- Enterprise apps with 100,000+ rows requiring pivot tables
- Need Excel-style features out-of-the-box
- Budget allows for AG Grid Enterprise license ($1000+/developer)

---

## 3. Styling Framework

### **RECOMMENDED: Tailwind CSS**

**Rationale:**
- **Zero-runtime cost** - critical for Server Components performance
- **Industry standard** for Next.js projects in 2026
- Perfect integration with shadcn/ui architecture
- Forces design system consistency via `tailwind.config.js` tokens
- Tree-shakable and optimized for production builds
- Fastest development speed for component-based architecture

**Installation:**
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**What to AVOID:**
- ❌ **styled-components & Emotion** - runtime CSS-in-JS causes performance issues
- Runtime style generation adds unacceptable cost in React concurrent rendering
- CSS-in-JS recalculates styles every render frame

**Alternative (specific cases only):**
- **CSS Modules** - for scoped CSS without runtime cost when Tailwind doesn't fit

---

## 4. Animation Library

### **RECOMMENDED: Framer Motion**

**Package:** `framer-motion`
**Version:** 11.x+

**Rationale:**
- **Most intuitive API** for declarative animations
- Hardware-accelerated animations for smooth 60fps
- Perfect for Data Card animations (expand/collapse, loading states, transitions)
- Rich feature set: layout animations, gestures, drag-and-drop, shared transitions
- Optimized for React concurrent mode and hooks
- LazyMotion feature for code-splitting animation features (reduces bundle size)

**Installation:**
```bash
npm i framer-motion
```

**Example Data Card Animation:**
```tsx
import { motion, AnimatePresence } from 'framer-motion'

export function AnimatedDataCard({ isVisible, children }) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="rounded-lg border bg-card"
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  )
}
```

**When to Use React Spring Instead:**
- Need physics-based spring animations with precise control
- Performance-critical mobile applications
- Complex interactive features requiring fine-tuned animation properties

---

## 5. Chart/Visualization Library

### **RECOMMENDED: Recharts (Frontend) + Hybrid Approach**

**Package:** `recharts`
**Version:** 2.12.0+

**Rationale:**
- **Best React integration** - declarative, component-based API
- Smooth integration with React state and hooks
- Good performance for datasets under 5,000 points (typical for Data Cards)
- Responsive and works well with Tailwind CSS styling
- Smaller learning curve than D3.js
- Built on D3 under the hood but with React-friendly API

**Installation:**
```bash
npm i recharts
```

**Example Usage:**
```tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export function DataVisualization({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#8884d8" />
      </LineChart>
    </ResponsiveContainer>
  )
}
```

### **Hybrid Backend/Frontend Strategy:**

**For Static/Complex Charts (Backend):**
- Generate with matplotlib/plotly on FastAPI backend
- Serve as optimized images (PNG/WebP) or static SVG
- Cache aggressively
- **Pros:** Faster initial load, no frontend processing, consistent rendering

**For Interactive/Real-time Charts (Frontend):**
- Use Recharts on Next.js frontend
- Stream data via SSE (Server-Sent Events)
- Update charts in real-time as data arrives
- **Pros:** Interactivity, hover tooltips, zoom, live updates

**Best Practice:** Use backend-generated images for initial page load, lazy-load interactive Recharts for user interactions.

**Alternative Chart Libraries:**

| Library | Use When | Pros | Cons |
|---------|----------|------|------|
| **Chart.js** | Simple, standard charts (bar, line, pie) | Excellent performance (10k+ points), canvas-based | Less React-friendly |
| **D3.js** | Highly custom, complex visualizations | Complete control over SVG/Canvas | Steep learning curve, large bundle (200KB+) |
| **Victory** | Need consistent API across web/mobile | Cross-platform support | Larger bundle than Recharts |

---

## 6. State Management

### **RECOMMENDED: Zustand**

**Package:** `zustand`
**Version:** 4.5.0+

**Rationale:**
- **Minimal boilerplate** - simplest API among modern state managers
- Tiny bundle size (~3KB minified)
- Perfect for streaming AI responses and Data Card state
- No Provider wrapper needed
- Excellent TypeScript support
- 30%+ year-over-year growth, appears in ~40% of projects (2026)
- Fast, predictable performance

**Installation:**
```bash
npm i zustand
```

**Example for Data Card State:**
```tsx
import { create } from 'zustand'

interface DataCardStore {
  cards: DataCard[]
  activeCardId: string | null
  addCard: (card: DataCard) => void
  updateCard: (id: string, data: Partial<DataCard>) => void
  setActiveCard: (id: string) => void
}

export const useDataCardStore = create<DataCardStore>((set) => ({
  cards: [],
  activeCardId: null,
  addCard: (card) => set((state) => ({
    cards: [...state.cards, card]
  })),
  updateCard: (id, data) => set((state) => ({
    cards: state.cards.map(c => c.id === id ? { ...c, ...data } : c)
  })),
  setActiveCard: (id) => set({ activeCardId: id })
}))
```

**For Server Data:** Use **TanStack Query (React Query)** for server state, caching, and data fetching:
```bash
npm i @tanstack/react-query
```

**When to Use Alternatives:**
- **React Context** - For simple, low-frequency state (theme, auth status)
- **Jotai** - For complex, atomic state relationships with interdependencies

---

## 7. AI Streaming (Vendor-Neutral SSE)

### **RECOMMENDED: Native Server-Sent Events (SSE)**

**Rationale:**
- **Zero vendor lock-in** - standard HTTP protocol
- **No external SDK needed** - native browser EventSource API
- Works perfectly with FastAPI backend + LangChain
- Built-in automatic reconnection in browsers
- Simple, maintainable code
- Deploy anywhere (Docker, AWS, GCP, bare metal)

### Backend Implementation (FastAPI + LangChain)

```python
# backend/api/chat.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain.chat_models import ChatOpenAI
import json
import asyncio

app = FastAPI()

async def generate_ai_stream(user_message: str):
    """
    Generator function for streaming AI responses using LangChain
    """
    llm = ChatOpenAI(model="gpt-4", streaming=True, temperature=0.7)

    # Stream tokens from LangChain
    async for token in llm.astream(user_message):
        # Format as SSE (Server-Sent Events)
        yield f"data: {json.dumps({'token': token.content})}\n\n"
        await asyncio.sleep(0)  # Allow other tasks to run

    # Send completion signal
    yield f"data: {json.dumps({'done': True})}\n\n"

@app.post("/api/chat/stream")
async def stream_chat(request: dict):
    """
    SSE endpoint for streaming AI responses
    """
    user_message = request.get("message", "")

    return StreamingResponse(
        generate_ai_stream(user_message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
```

### Frontend Implementation (Next.js)

**Custom Hook:**
```typescript
// frontend/hooks/useAIStream.ts
import { useState, useCallback } from 'react'

interface UseAIStreamReturn {
  response: string
  isStreaming: boolean
  error: string | null
  streamMessage: (message: string) => Promise<void>
  reset: () => void
}

export function useAIStream(): UseAIStreamReturn {
  const [response, setResponse] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const streamMessage = useCallback(async (message: string) => {
    setIsStreaming(true)
    setResponse('')
    setError(null)

    try {
      const res = await fetch('http://localhost:8000/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message }),
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const reader = res.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        // Decode the SSE chunk
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.done) {
              setIsStreaming(false)
              break
            }

            if (data.token) {
              setResponse(prev => prev + data.token)
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setIsStreaming(false)
    }
  }, [])

  const reset = useCallback(() => {
    setResponse('')
    setError(null)
    setIsStreaming(false)
  }, [])

  return { response, isStreaming, error, streamMessage, reset }
}
```

**Usage in Component:**
```tsx
// frontend/components/ChatInterface.tsx
'use client'

import { useState } from 'react'
import { useAIStream } from '@/hooks/useAIStream'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const { response, isStreaming, error, streamMessage } = useAIStream()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return

    await streamMessage(input)
    setInput('')
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-6">
          {response && (
            <div className="prose prose-sm">
              {response}
              {isStreaming && <span className="animate-pulse">▋</span>}
            </div>
          )}
          {error && (
            <div className="text-destructive text-sm">{error}</div>
          )}
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your data..."
          disabled={isStreaming}
        />
        <Button type="submit" disabled={isStreaming}>
          {isStreaming ? 'Streaming...' : 'Send'}
        </Button>
      </form>
    </div>
  )
}
```

**CORS Configuration (Backend):**
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Complete Stack Summary

```json
{
  "dependencies": {
    "next": "^15.x",
    "react": "^19.x",
    "react-dom": "^19.x",

    "// UI Components": "",
    "@radix-ui/react-dialog": "latest",
    "@radix-ui/react-dropdown-menu": "latest",
    "@radix-ui/react-tabs": "latest",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0",

    "// Data Tables": "",
    "@tanstack/react-table": "^8.21.3",
    "@tanstack/react-virtual": "^3.x",

    "// Styling": "",
    "tailwindcss": "^3.4.0",
    "tailwindcss-animate": "^1.0.7",

    "// Animations": "",
    "framer-motion": "^11.x",

    "// Charts": "",
    "recharts": "^2.12.0",

    "// State Management": "",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.x"
  },
  "devDependencies": {
    "@types/react": "^19.x",
    "@types/node": "^20.x",
    "typescript": "^5.x",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

**Note:** No Vercel AI SDK needed. All streaming handled via native SSE.

---

## Integration Patterns

### 1. Complete Data Card with Streaming + Table + Chart

```tsx
'use client'

import { useState } from 'react'
import { useAIStream } from '@/hooks/useAIStream'
import { useReactTable, getCoreRowModel } from '@tanstack/react-table'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { motion } from 'framer-motion'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/table'

export function DataCard({ query }: { query: string }) {
  const { response, isStreaming } = useAIStream()
  const [tableData, setTableData] = useState([])

  const table = useReactTable({
    data: tableData,
    columns,
    getCoreRowModel: getCoreRowModel(),
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>{query}</CardTitle>
        </CardHeader>
        <CardContent>
          {/* AI Explanation */}
          <div className="prose prose-sm mb-4">
            {response}
            {isStreaming && <span className="animate-pulse">▋</span>}
          </div>

          {/* Data Table */}
          <div className="rounded-md border mb-4">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map(headerGroup => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map(header => (
                      <TableHead key={header.id}>
                        {header.column.columnDef.header}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map(row => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map(cell => (
                      <TableCell key={cell.id}>
                        {cell.renderValue()}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Chart */}
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tableData}>
              <Line type="monotone" dataKey="value" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </motion.div>
  )
}
```

### 2. Server Components + Client Islands Pattern

```tsx
// app/dashboard/page.tsx (Server Component)
export default async function DashboardPage() {
  const initialData = await fetchInitialData()

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Dashboard</h1>

      {/* Server Component - Static Content */}
      <StaticHeader data={initialData} />

      {/* Client Component - Interactive Features */}
      <DataCardClient initialData={initialData} />
    </div>
  )
}

// components/DataCardClient.tsx
'use client'

import { useAIStream } from '@/hooks/useAIStream'
import { useDataCardStore } from '@/store/data-card-store'

export function DataCardClient({ initialData }) {
  const { response, streamMessage } = useAIStream()
  const { cards, addCard } = useDataCardStore()

  // Interactive features: streaming, animations, state
  return (
    <div className="space-y-4">
      {cards.map(card => (
        <DataCard key={card.id} {...card} />
      ))}
    </div>
  )
}
```

### 3. State Architecture

```
┌─────────────────────────────────────┐
│     Server Components (RSC)         │
│  - Initial data fetching            │
│  - SEO content                      │
│  - Static elements                  │
└───────────────┬─────────────────────┘
                │ props
                ▼
┌─────────────────────────────────────┐
│   Client Components ('use client')  │
├─────────────────────────────────────┤
│  Zustand: UI state, filters         │
│  React Query: Server data cache     │
│  useAIStream: AI streaming (SSE)    │
│  useState: Local component state    │
└─────────────────────────────────────┘
                │
                │ SSE/HTTP
                ▼
┌─────────────────────────────────────┐
│   FastAPI Backend                   │
│  - LangChain agents                 │
│  - StreamingResponse                │
│  - PostgreSQL                       │
└─────────────────────────────────────┘
```

---

## What to AVOID

### ❌ Runtime CSS-in-JS
- **styled-components, Emotion** - Performance issues with Server Components
- Recalculates styles on every render in concurrent mode
- Community moving toward zero-runtime solutions

### ❌ Deprecated Packages
- **react-table v7** - Use @tanstack/react-table v8 instead
- **next/legacy/image** - Use next/image (current version)
- **getServerSideProps / getStaticProps** - Next.js 15 uses App Router

### ❌ Context for High-Frequency Updates
- Causes unnecessary re-renders
- Use Zustand or Jotai for frequently changing state

### ❌ Client-Side Data Fetching Without Caching
- Always use React Query/TanStack Query for server data
- Implements proper caching, revalidation, deduplication

### ❌ External SDKs for Streaming
- No Vercel AI SDK needed with FastAPI backend
- Native SSE is simpler, more maintainable, zero dependencies

---

## Deployment Considerations

### Docker Multi-Container Setup

```yaml
# docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/spectra
    depends_on:
      - db

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=spectra
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
```

### Environment Variables

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Backend (.env):**
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/spectra
OPENAI_API_KEY=your_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

---

## Sources

**UI Component Libraries:**
- [shadcn/ui Installation - Next.js](https://ui.shadcn.com/docs/installation/next)
- [Material UI vs Shadcn: UI library war](https://codeparrot.ai/blogs/material-ui-vs-shadcn)
- [Building Better UIs: Why ShadCN and Radix Are Worth Your Attention](https://dev.to/lovestaco/building-better-uis-why-shadcn-and-radix-are-worth-your-attention-4fen)

**Data Tables:**
- [TanStack Table vs AG Grid: Complete Comparison (2025)](https://www.simple-table.com/blog/tanstack-table-vs-ag-grid-comparison)
- [TanStack Table Installation](https://tanstack.com/table/v8/docs/installation)

**Styling:**
- [Styling Strategies in Next.js 2025: CSS Modules vs Tailwind CSS 4 vs CSS‑in‑JS](https://medium.com/@sureshdotariya/styling-strategies-in-next-js-2025-css-modules-vs-tailwind-css-4-vs-css-in-js-c63107ba533c)
- [Why We're Breaking Up with CSS-in-JS](https://dev.to/srmagura/why-were-breaking-up-wiht-css-in-js-4g9b)

**Animations:**
- [React Spring or Framer Motion: Which is Better?](https://www.angularminds.com/blog/react-spring-or-framer-motion)
- [Comparing the best React animation libraries for 2026](https://blog.logrocket.com/best-react-animation-libraries/)

**Charts:**
- [Best React chart libraries (2025 update)](https://blog.logrocket.com/best-react-chart-libraries-2025/)
- [Recharts vs D3.js: A Comprehensive Comparison](https://solutions.lykdat.com/blog/recharts-vs-d3-js/)

**State Management:**
- [State Management in 2025: When to Use Context, Redux, Zustand, or Jotai](https://dev.to/hijazi313/state-management-in-2025-when-to-use-context-redux-zustand-or-jotai-2d2k)
- [React State Management in 2025: Zustand vs. Redux vs. Jotai vs. Context](https://www.meerako.com/blogs/react-state-management-zustand-vs-redux-vs-context-2025)

**SSE Streaming:**
- [Using Server-Sent Events (SSE) to stream LLM responses in Next.js](https://upstash.com/blog/sse-streaming-llm-responses)
- [Streaming APIs with FastAPI and Next.js - Part 1](https://sahansera.dev/streaming-apis-python-nextjs-part1/)
- [Stream OpenAI respond through FastAPI to Next.js](https://medium.com/@timnirmal/stream-openai-respond-through-fastapi-to-next-js-f5395f69687c)
- [SSE vs WebSockets: Comparing Real-Time Communication Protocols](https://softwaremill.com/sse-vs-websockets-comparing-real-time-communication-protocols/)

---

**Frontend UI Stack for Spectra**
**Researched:** 2026-02-02
**Confidence:** HIGH - All technologies verified with 2026 documentation, vendor-neutral, production-ready
