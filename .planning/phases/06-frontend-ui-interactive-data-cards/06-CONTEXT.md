# Phase 6: Frontend UI & Interactive Data Cards - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a polished Next.js web interface where users upload Excel/CSV files, chat with AI about their data in real-time, and view streaming analysis results as interactive Data Cards. Each file has its own chat tab with independent history. Users can download results as CSV/Markdown and manage their profile in settings.

Scope: Frontend UI implementation only. Backend APIs (auth, file upload, streaming, agents, sandbox) are complete from Phases 1-5.

</domain>

<decisions>
## Implementation Decisions

### Layout & Navigation

**File Management:**
- Sidebar + multi-tab hybrid architecture
- Left sidebar displays list of all uploaded files (name + icon only, minimal)
- Clicking a file opens a new chat tab on the right
- Maximum 5 active tabs at a time
- If user tries to open 6th tab: show alert asking to close tabs first before proceeding
- Clicking a file that already has an active tab: switch to existing tab (no duplicates)
- Tabs do NOT persist across browser sessions (start fresh each visit)

**File Information Display:**
- Info icon (ⓘ) next to each filename in sidebar
- Clicking info icon opens modal dialog (center of screen) showing onboarding analysis
- Modal displays the AI's data summary from initial upload

**File Deletion:**
- Delete button/icon in sidebar for each file
- Confirmation: modal dialog warning "Delete [filename]? This will remove all chat history."
- When file is deleted: auto-switch to next available tab (or empty state if no tabs)

### Data Card Design

**Card Placement & Structure:**
- Data Cards appear inline with chat messages (like ChatGPT code blocks)
- Vertical stack layout with 3 sections (top to bottom):
  1. Query Brief (top)
  2. Data Table (middle)
  3. AI Explanation (bottom)

**Progressive Rendering:**
- Sections appear sequentially as they complete during streaming:
  1. Query Brief appears first
  2. Data Table appears when ready
  3. AI Explanation streams in last
- Progressive reveal gives immediate feedback to users

**Multiple Cards:**
- Cards are collapsible
- Older cards can collapse to show just Query Brief (click to expand full card again)
- Reduces visual clutter when chat history has many results

**Download Functionality:**
- CSV download button: located within Data Table section (contextual)
- Markdown download button: located within AI Explanation section (contextual)
- Downloads include: CSV table export, Markdown report with query + analysis

### Chat Experience

**File Upload:**
- Drag-and-drop zone + click to browse (standard pattern)
- Upload progress: progress bar with stage indicators
  - Stages: "Uploading... → Analyzing data... → Ready!"
  - Shows current stage with visual progress feedback

**Chat Input:**
- Industry standard pattern (ChatGPT/Claude/Gemini behavior):
  - **Enter** key sends message
  - **Shift+Enter** creates new line (multi-line input)
  - Textarea auto-expands vertically as user types
  - Send button always visible as alternative to Enter

**Streaming & Loading:**
- While waiting for first AI response: typing indicator (animated dots "...")
- Text streaming animation: character-by-character (match ChatGPT feel)
- Frontend animates text from backend event chunks character-by-character for smooth effect

**Error Handling:**
- Errors during AI responses: display error message in chat flow
- Error message format: "Something went wrong. Please try again."
- Error appears as message within chat, not toast notification

### Visual Polish

**Design Aesthetic:**
- Modern & vibrant style
- Colorful accents, gradients, engaging visuals
- Inspired by modern SaaS apps (not minimal/flat, not overly technical)

**Animations:**
- Subtle & smooth transitions
- Gentle fades, slides, ease-in-out timing
- Polished but not distracting (avoid bounce/playful effects)

**Color Scheme:**
- Light mode only (focus on MVP delivery)
- Dark mode deferred to post-v1.0

### Claude's Discretion

- Chat message visual style (bubbles vs full-width with avatar)
- Loading state design patterns (skeleton screens, spinners, progress indicators - may vary by context)
- Settings page layout and interaction patterns (profile editing, password change, account info display)
- Exact spacing, typography, and component styling within design aesthetic guidelines
- Data table interaction details (sorting, filtering, pagination for large results)

</decisions>

<specifics>
## Specific Ideas

**Reference Examples:**
- "Match ChatGPT feel" for streaming text animation and input behavior
- Modern & vibrant aesthetic inspired by contemporary SaaS applications

**Technical Stack (from ROADMAP.md):**
- Next.js 16 with App Router and React 19
- shadcn/ui components for consistent design system
- TanStack Table for sortable/filterable data tables
- TanStack Query for server state management
- Zustand for client state (current file tab, UI state)
- EventSource API for SSE streaming from Next.js API routes

</specifics>

<deferred>
## Deferred Ideas

- Dark mode support — post-v1.0 feature
- Tab persistence across sessions — post-v1.0 enhancement
- More than 5 active tabs — keep simple for MVP

</deferred>

---

*Phase: 06-frontend-ui-interactive-data-cards*
*Context gathered: 2026-02-03*
