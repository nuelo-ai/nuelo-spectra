# Milestone v0.9 — Collections + Report Export

## Overview

This milestone adds the **Collections output layer** — auto-saving all analysis progress and compiling it into downloadable reports (Markdown + PDF). One Collection can produce **many reports** from different investigation paths. Also introduces the **Chat → Collection bridge**, allowing users to add data cards from Chat sessions into a Collection workspace.

## 1. Report System

### 1.1 Multi-Report Architecture
- One Collection can have many Reports (not just one)
- Report types: `pulse_summary`, `investigation`, `scenario`, `chat_compilation`
- Each report has: title, type, markdown content, source references (which signals/investigations/scenarios it was built from)
- Reports are independently downloadable

### 1.2 Auto-Save & Report Compilation
- All analysis progress auto-saves to the Collection throughout the process
- Pulse results auto-compile into a `pulse_summary` report
- User can trigger "Compile Report" at any point to snapshot current state
- Report compiles the full journey: Signals, any investigation steps, charts, scenario results

### 1.3 Report Quality
- Structured markdown: executive summary, findings sections, charts embedded, methodology notes
- Clean heading hierarchy — suitable for sharing with stakeholders
- Chart rendering within reports (inline visualizations)
- Professional formatting — not a developer markdown dump

### 1.4 Export Formats
- **Markdown download** — primary format, preserves all content
- **PDF download** — polished layout with proper typography, chart rendering, page breaks
- PDF generation pipeline (WeasyPrint or equivalent)

## 2. Collections UI

### 2.1 Collections List View
- List all Collections for the user
- Search by name/description
- Filter by status (active, archived)
- Sort by date, name, signal count
- Show report count per Collection

### 2.2 Collection Detail View
- Overview: name, description, data sources, creation date
- Signals tab: all Pulse findings
- Reports tab: list of all generated reports with type badges
- Timeline of activity within the Collection

## 3. Chat → Collection Bridge

### 3.1 Add Data Card to Collection
- From an existing Chat session, user can select a data card (chart, table, analysis)
- "Add to Collection" action — choose existing Collection or create new
- Chat item is saved with reference to source chat session and data card
- Chat-originated items can be compiled into a `chat_compilation` report

### 3.2 Chat Item Model
- Links to: collection_id, chat_session_id, data_card_id
- Stores: title, content snapshot (chart config or table data), timestamp
- Immutable snapshot — changes in chat don't affect the Collection copy

## 4. Backend Requirements

### 4.1 Report API
- CRUD endpoints for Reports within a Collection
- Report compilation endpoint (triggers markdown generation)
- PDF generation endpoint
- Export/download endpoints (markdown file, PDF file)

### 4.2 Chat Bridge API
- Endpoint to add a data card from Chat to a Collection
- Endpoint to list chat items within a Collection

## 5. Out of Scope
- Guided Q&A investigation (v0.10)
- Simulation / what-if (v1.0)
- Shared/team Collections (backlog)
- PPT/slides export (backlog)
- Shareable report links (backlog)

## 6. Success Criteria
- Generate 3 sample reports from real analysis sessions → reports are "would share with my boss" quality
- Auto-save works: close browser mid-analysis → return → all progress intact
- PDF export produces clean, professional output with charts rendered
- One Collection can hold multiple reports of different types
- Chat → Collection bridge works: add data card from chat → appears in Collection → compilable into report
