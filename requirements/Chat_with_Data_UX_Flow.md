# Chat with Data - Detailed User Experience Flow

## Document Purpose

This document provides a comprehensive step-by-step user experience flow for the "Chat with Data" feature. It is intended to guide UI/UX designers in creating detailed interface designs and interactions.

---

## 1. Entry Point: Dashboard Screen

### 1.1 Initial State

**Screen:** Main Dashboard

**Elements visible:**
- Navigation sidebar (left)
- Header bar with user profile and notifications
- Main content area displaying available data sources
- Credit balance indicator (top-right corner showing "X credits remaining")

### 1.2 Data Source Selection

**User Action:** User clicks on a data source card (e.g., "Sales Data Q4 2024")

**System Response:**
- Selected data source card highlights with a visual indicator (border glow or checkmark)
- A "Chat with Data" button appears or becomes enabled
- Tooltip displays: "Start analyzing [Data Source Name]"

**Alternative Entry:**
- User can also right-click on data source and select "Chat with Data" from context menu
- Or hover over data source card to reveal quick action buttons

### 1.3 Opening the Chat Interface

**User Action:** User clicks "Chat with Data" button

**System Response:**
- Smooth transition animation (slide-in from right or modal expansion)
- Loading indicator displays: "Preparing your data environment..."
- System loads data schema and metadata in background (2-3 seconds max)

---

## 2. Chat Interface - Main Screen

### 2.1 Interface Layout

**Screen:** Chat with Data Interface

**Layout Structure (recommended: split-panel or full-screen modal):**

```
┌─────────────────────────────────────────────────────────────────┐
│  Header Bar                                                      │
│  [← Back] [Data Source Name] [Credit: XX] [Settings ⚙] [✕ Close]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                          │    │
│  │                    Chat Area                             │    │
│  │              (Conversation History)                      │    │
│  │                                                          │    │
│  │                                                          │    │
│  │                                                          │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 💬 Ask a question about your data...            [Send ➤]│    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  [Suggested Prompts: "Show top 10..." | "Compare..." | "Trend.."]│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Header Bar Elements

| Element | Description | Interaction |
|---------|-------------|-------------|
| Back Arrow | Returns to dashboard | Click to exit (with confirmation if conversation exists) |
| Data Source Name | Shows currently selected data source | Click to view data source details/schema |
| Credit Balance | Displays remaining credits | Hover shows tooltip with subscription details |
| Settings Icon | Access chat preferences | Opens settings dropdown |
| Close Button | Closes the chat interface | Click to exit |

### 2.3 Empty State (First Visit)

**Display Elements:**
- Welcome illustration or icon
- Welcome message: "Start exploring your data"
- Brief description: "Ask questions in natural language to analyze, visualize, and understand your data"
- Suggested starter prompts (3-4 clickable chips):
  - "Show me an overview of this data"
  - "What are the top performing categories?"
  - "Show trends over time"
  - "Compare this month vs last month"

### 2.4 Data Schema Panel (Optional - Collapsible)

**Location:** Left sidebar or expandable panel

**Content:**
- List of available tables/datasets
- Column names with data types
- Sample values preview
- Search/filter functionality

**Purpose:** Helps users understand what data is available for querying

---

## 3. Query Submission Flow

### 3.1 Typing a Query

**User Action:** User clicks on input field and types query

**Input Field Behavior:**
- Placeholder text: "Ask a question about your data..."
- Auto-expand for multi-line input (up to 4 lines visible)
- Character counter appears after 200 characters
- Send button activates when text is entered

**Auto-suggestions (Optional Enhancement):**
- As user types, show contextual suggestions based on:
  - Data column names
  - Previous successful queries
  - Common query patterns

### 3.2 Submitting the Query

**User Action:** User clicks Send button or presses Enter

**Immediate System Response:**
1. Input field clears and disables temporarily
2. User's query appears in chat as a message bubble (right-aligned)
3. Credit deduction indicator flashes: "-1 credit"
4. AI response container appears with typing indicator

---

## 4. Response Generation Flow

### 4.1 Processing Indicator

**Display:** AI message bubble with animated typing dots

**Duration indicators:**
- Simple queries: "Analyzing..." (1-3 seconds)
- Complex queries: "Processing your request..." with subtle progress animation

### 4.2 Script Generation Display (When Applicable)

**Trigger:** When the query requires Python script execution

**Visual Presentation:**

```
┌─────────────────────────────────────────────────────────────┐
│ 🔧 Generating analysis script...                            │
├─────────────────────────────────────────────────────────────┤
│ ```python                                                   │
│ # Streaming code appears line by line                       │
│ import pandas as pd                                         │
│                                                             │
│ df = load_data('sales_q4_2024')                            │
│ result = df.groupby('category').sum()...                   │
│ ```                                                         │
│                                                             │
│ [▓▓▓▓▓▓▓▓░░] Generating...                                 │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Code streams in real-time (typewriter effect)
- Syntax highlighting applied
- Collapsible after completion (default: collapsed)
- "View Script" toggle to show/hide

### 4.3 Script Execution Indicator

**Display:** After script generation completes

```
┌─────────────────────────────────────────────────────────────┐
│ ⚙️ Running analysis...                                      │
│ [▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░] Executing in sandbox                  │
└─────────────────────────────────────────────────────────────┘
```

**States:**
- "Executing in sandbox..."
- "Processing results..."
- "Preparing visualization..." (if applicable)

---

## 5. Data Card Display

### 5.1 Data Card Structure

**Container:** Distinct card component within the chat flow

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 Query Result                                    [•••]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ QUERY BRIEF                                                 │
│ ─────────────────────────────────────────────────────────── │
│ Top 10 products by revenue for each category in Q4 2024    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ DATA TABLE                                                  │
│ ─────────────────────────────────────────────────────────── │
│ ┌──────────┬────────────┬───────────┬──────────┐           │
│ │ Rank     │ Product    │ Category  │ Revenue  │           │
│ ├──────────┼────────────┼───────────┼──────────┤           │
│ │ 1        │ Product A  │ Electronics│ $45,230 │           │
│ │ 2        │ Product B  │ Electronics│ $38,100 │           │
│ │ 3        │ Product C  │ Apparel   │ $32,500  │           │
│ │ ...      │ ...        │ ...       │ ...      │           │
│ └──────────┴────────────┴───────────┴──────────┘           │
│                                                             │
│ Showing 10 of 47 results    [Load More] [View Full Table]  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ EXPLANATION                                                 │
│ ─────────────────────────────────────────────────────────── │
│ Electronics dominates the top positions with 6 out of 10   │
│ spots. Product A leads with $45,230 in revenue,            │
│ representing 12% of total category sales.                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ VISUALIZATION                                               │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│     ████████████████████████████  Product A ($45,230)      │
│     ██████████████████████████    Product B ($38,100)      │
│     ████████████████████          Product C ($32,500)      │
│     ██████████████████            Product D ($31,200)      │
│     ████████████████              Product E ($28,900)      │
│                                                             │
│                              [Expand Chart] [Change Type ▼] │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [💾 Save] [📊 To PowerPoint] [📤 Share ▼]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Data Card Sections Detail

#### Query Brief Section
- **Icon:** 🎯 or similar
- **Content:** AI-generated interpretation of user's query
- **Style:** Slightly emphasized text, 1-2 lines maximum
- **Purpose:** Confirms understanding of user intent

#### Data Table Section
- **Default display:** First 10 rows
- **Features:**
  - Sortable columns (click header to sort)
  - Resizable columns
  - Horizontal scroll for wide tables
  - Row hover highlighting
- **Actions:**
  - "Load More" - loads next 10 rows incrementally
  - "View Full Table" - opens modal with complete dataset

#### Explanation Section
- **Content:** 2-4 sentences summarizing key insights
- **Style:** Regular paragraph text
- **Tone:** Informative, not overly detailed

#### Visualization Section (Conditional)
- **Display condition:** When visual representation adds value
- **Chart types available:**
  - Bar chart (horizontal/vertical)
  - Line chart
  - Pie chart
  - Area chart
  - Scatter plot
- **Interactions:**
  - Hover for tooltips with exact values
  - "Expand Chart" opens fullscreen view
  - "Change Type" dropdown to switch visualization type
  - Download chart as image

### 5.3 Data Card Action Buttons

#### Save Action
**User Action:** Click "Save" button

**System Response:**
1. Modal appears: "Save to Collection"
2. Input field for custom name (pre-filled with query brief)
3. Optional: Select/create collection folder
4. Confirm button

**Success State:**
- Toast notification: "Saved to [Collection Name]"
- Button changes to "Saved ✓" temporarily

#### Generate PowerPoint Action
**User Action:** Click "To PowerPoint" button

**System Response:**
1. Brief loading indicator: "Generating slide..."
2. Preview modal showing slide layout:
   - Title: Query Brief
   - Content: Table (abbreviated if large) + Chart
   - Footer: Data source and timestamp
3. Options:
   - "Download .pptx"
   - "Add to existing presentation" (if applicable)
   - "Customize layout" (advanced)

**Output:** Downloaded .pptx file

#### Share Action
**User Action:** Click "Share" dropdown

**Dropdown Options:**
| Option | Action |
|--------|--------|
| Share via Email | Opens email composer modal with embedded card preview |
| Save as Image | Downloads PNG of the data card |
| Save as PDF | Downloads PDF document with full card content |
| Copy Link | Generates shareable link (if sharing is enabled) |

**Email Sharing Flow:**
1. Modal with recipient email input
2. Optional message field
3. Preview of what will be shared
4. Send button

---

## 6. Conversation Continuation

### 6.1 Follow-up Queries

**Context:** After receiving a Data Card, user can continue the conversation

**Input field re-enables immediately after response completes**

**Contextual Suggestions appear below input:**
- "Drill down into Electronics category"
- "Show this as a trend over time"
- "Compare with Q3 2024"
- "Why is Product A leading?"

### 6.2 Conversation History

**Display:** All messages and Data Cards remain visible in scrollable chat

**Navigation:**
- Smooth scroll through conversation
- "Jump to top" button appears when scrolled down
- Each Data Card is collapsible to reduce clutter

### 6.3 Query Refinement

**Scenario:** User wants to modify previous query

**Options:**
1. Type new query naturally: "Actually, show me top 20 instead"
2. Click "Refine" button on existing Data Card (if implemented)
3. Reference previous results: "From the previous result, filter only Apparel"

---

## 7. Error Handling

### 7.1 Query Processing Errors

**Error Types and Display:**

#### Insufficient Data
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Unable to Complete Query                                 │
├─────────────────────────────────────────────────────────────┤
│ The requested data is not available in this dataset.       │
│                                                             │
│ Available columns: product_name, category, revenue, date   │
│                                                             │
│ Try asking about: revenue trends, category performance,    │
│ product comparisons                                         │
│                                                             │
│ [Suggested: "Show revenue by category"]                    │
└─────────────────────────────────────────────────────────────┘
```

#### Ambiguous Query
```
┌─────────────────────────────────────────────────────────────┐
│ 🤔 Clarification Needed                                     │
├─────────────────────────────────────────────────────────────┤
│ I found multiple interpretations for your query:           │
│                                                             │
│ Did you mean:                                               │
│ ○ Top products by revenue                                  │
│ ○ Top products by units sold                               │
│ ○ Top products by profit margin                            │
│                                                             │
│ [Click an option or type to clarify]                       │
└─────────────────────────────────────────────────────────────┘
```

#### Execution Error
```
┌─────────────────────────────────────────────────────────────┐
│ ❌ Processing Error                                         │
├─────────────────────────────────────────────────────────────┤
│ We encountered an issue while processing your request.     │
│                                                             │
│ [View Technical Details ▼]                                  │
│                                                             │
│ [🔄 Retry] [📝 Rephrase Query] [📞 Contact Support]        │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Credit-Related Scenarios

#### Insufficient Credits
**Trigger:** User attempts query with 0 credits remaining

**Display:**
```
┌─────────────────────────────────────────────────────────────┐
│ 💳 Insufficient Credits                                     │
├─────────────────────────────────────────────────────────────┤
│ You've used all your credits for this month.               │
│                                                             │
│ Credits reset on: [Date]                                   │
│ Or top up now to continue analyzing.                       │
│                                                             │
│ [🛒 Top Up Credits] [📅 View Reset Date]                   │
└─────────────────────────────────────────────────────────────┘
```

#### Low Credit Warning
**Trigger:** Credits fall below threshold (e.g., 5 remaining)

**Display:** Non-intrusive banner above input field
```
⚠️ Low credits: 3 remaining | [Top Up]
```

---

## 8. Additional Interface States

### 8.1 Loading States

| State | Visual | Duration |
|-------|--------|----------|
| Opening chat | Full screen loader with progress | 2-3 seconds |
| Submitting query | Input disabled, send button shows spinner | < 1 second |
| Processing | AI bubble with typing animation | 2-10 seconds |
| Generating script | Streaming code display | 3-15 seconds |
| Executing script | Progress bar in sandbox indicator | 2-20 seconds |
| Rendering results | Data Card skeleton loading | 1-2 seconds |

### 8.2 Empty and Null States

#### No Results Found
```
┌─────────────────────────────────────────────────────────────┐
│ 📭 No Results                                               │
├─────────────────────────────────────────────────────────────┤
│ Your query returned no matching data.                      │
│                                                             │
│ Suggestions:                                                │
│ • Check if the date range includes data                    │
│ • Try broader filter criteria                              │
│ • Verify spelling of category/product names                │
│                                                             │
│ [Show available data ranges]                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Session Management

#### Session Timeout Warning
**Trigger:** 10 minutes of inactivity

**Display:** Toast notification
```
Your session will expire in 5 minutes due to inactivity. [Stay Active]
```

#### Session Expired
**Display:** Modal overlay
```
┌─────────────────────────────────────────────────────────────┐
│ ⏰ Session Expired                                          │
├─────────────────────────────────────────────────────────────┤
│ Your session has timed out for security.                   │
│                                                             │
│ Your conversation history has been saved.                  │
│                                                             │
│ [🔄 Reconnect] [🚪 Return to Dashboard]                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Settings and Preferences

### 9.1 Chat Settings Dropdown

**Access:** Click settings icon in header

**Options:**
| Setting | Description | Default |
|---------|-------------|---------|
| Show generated scripts | Display Python code during processing | On |
| Auto-expand visualizations | Charts expand by default | Off |
| Compact Data Cards | Reduce card padding and spacing | Off |
| Dark mode | Toggle dark/light theme | System |

### 9.2 Data Display Preferences

**Table preferences:**
- Default rows to display: 10 / 25 / 50
- Number formatting: 1,000 vs 1000
- Date format: MM/DD/YYYY vs DD/MM/YYYY

---

## 10. Accessibility Considerations

### 10.1 Keyboard Navigation

| Action | Shortcut |
|--------|----------|
| Focus chat input | `/` or `Ctrl + K` |
| Send message | `Enter` or `Ctrl + Enter` |
| Navigate Data Cards | `Tab` through interactive elements |
| Collapse/Expand sections | `Space` when focused |
| Close modal/dropdown | `Escape` |

### 10.2 Screen Reader Support

- All interactive elements have appropriate ARIA labels
- Data tables include proper header associations
- Charts have text alternatives describing key insights
- Loading states announced to assistive technology

### 10.3 Visual Accessibility

- Minimum contrast ratio of 4.5:1 for text
- Charts use colorblind-friendly palettes
- Focus indicators clearly visible
- Text resizable up to 200% without loss of functionality

---

## 11. Mobile Responsiveness

### 11.1 Layout Adaptations

**Breakpoints:**
- Desktop: > 1024px (full layout as described)
- Tablet: 768px - 1024px (collapsible sidebar)
- Mobile: < 768px (stacked layout, bottom sheet for cards)

### 11.2 Mobile-Specific Interactions

- Data Cards open as bottom sheets
- Tables horizontally scrollable with swipe
- Charts tappable for detail view
- Voice input option for queries

---

## 12. Flow Summary Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Dashboard   │────▶│ Select Data  │────▶│ Open Chat    │
│              │     │   Source     │     │  Interface   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────────────────────────────────────────────────┐
│                    CHAT INTERFACE                         │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  │  ┌─────────────┐    ┌─────────────┐                 │ │
│  │  │ User types  │───▶│  -1 Credit  │                 │ │
│  │  │   query     │    │  deducted   │                 │ │
│  │  └─────────────┘    └──────┬──────┘                 │ │
│  │                            │                         │ │
│  │                            ▼                         │ │
│  │              ┌─────────────────────────┐             │ │
│  │              │   Processing Query      │             │ │
│  │              │  ┌─────────────────┐    │             │ │
│  │              │  │ Generate Script │    │             │ │
│  │              │  │   (if needed)   │    │             │ │
│  │              │  └────────┬────────┘    │             │ │
│  │              │           ▼             │             │ │
│  │              │  ┌─────────────────┐    │             │ │
│  │              │  │Execute in       │    │             │ │
│  │              │  │Sandbox          │    │             │ │
│  │              │  └────────┬────────┘    │             │ │
│  │              └───────────┼─────────────┘             │ │
│  │                          ▼                           │ │
│  │              ┌─────────────────────────┐             │ │
│  │              │     DATA CARD           │             │ │
│  │              │  • Query Brief          │             │ │
│  │              │  • Data Table           │             │ │
│  │              │  • Explanation          │             │ │
│  │              │  • Visualization        │             │ │
│  │              │  ─────────────────────  │             │ │
│  │              │  [Save][PPT][Share]     │             │ │
│  │              └───────────┬─────────────┘             │ │
│  │                          │                           │ │
│  │                          ▼                           │ │
│  │              ┌─────────────────────────┐             │ │
│  │              │ Continue Conversation?  │◀────┐       │ │
│  │              │    [Yes]     [Exit]     │     │       │ │
│  │              └─────┬───────────────────┘     │       │ │
│  │                    │                         │       │ │
│  │                    └─────────────────────────┘       │ │
│  │                                                      │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## Appendix A: Component Specifications

### A.1 Data Card Component Props

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| queryBrief | string | Yes | AI interpretation of query |
| tableData | array | Yes | Array of row objects |
| tableColumns | array | Yes | Column definitions |
| explanation | string | No | Summary text |
| visualization | object | No | Chart configuration |
| timestamp | datetime | Yes | Query execution time |
| queryId | string | Yes | Unique identifier |

### A.2 Credit Display Component

| State | Display | Color |
|-------|---------|-------|
| Sufficient (>10) | "XX credits" | Green |
| Low (5-10) | "XX credits" + warning icon | Yellow |
| Critical (1-4) | "XX credits" + alert | Orange |
| Empty (0) | "No credits" | Red |

---

## Appendix B: Animation Specifications

| Interaction | Animation Type | Duration | Easing |
|-------------|---------------|----------|--------|
| Chat open | Slide in from right | 300ms | ease-out |
| Message appear | Fade + slide up | 200ms | ease-out |
| Data Card expand | Height expansion | 250ms | ease-in-out |
| Button hover | Scale + shadow | 150ms | ease |
| Loading dots | Opacity pulse | 1000ms | linear (loop) |
| Code streaming | Typewriter | 20ms/char | linear |
