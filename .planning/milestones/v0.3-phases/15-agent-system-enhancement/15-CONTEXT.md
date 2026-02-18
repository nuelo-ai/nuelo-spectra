# Phase 15: Agent System Enhancement (Multi-File Support) - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

AI agents can perform cross-file analysis across all linked files in a single query. This phase delivers the Context Assembler service, multi-file code generation, and Manager Agent routing updates. Frontend changes, file management UI, and session navigation are separate phases (16-18).

</domain>

<decisions>
## Implementation Decisions

### Context Assembly
- Full data profile per file (column types, sample values, statistics, row count) — maximum accuracy
- Progressive reduction when over token budget: full profile → drop sample values → drop statistics → keep column names + types as minimum
- Standalone ContextAssembler service — takes file IDs, returns assembled multi-file context with token management
- Detect shared column names across linked files and include join hints (e.g., "Possible join: sales.customer_id <-> customers.id")
- Join hints are surfaced to the user for clarification before the agent acts on them — prevents wrong assumptions about relationships

### File Limits
- Default max: 5 files per session OR 50MB total combined file size (whichever triggers first)
- Max file count is configurable via YAML config, with an absolute ceiling of 10 files
- This supersedes the Phase 14 hard-coded 10-file limit — now configurable with a lower default

### File Relevance
- Agent always receives context (metadata) for ALL linked files in the session — full picture for every query
- Generated code only loads files that are needed for the specific query — selective DataFrame loading for execution efficiency
- When a file is added mid-conversation, agent auto-acknowledges with a brief summary (e.g., "Now I can also work with customers.csv — 5 columns, 1,200 rows")
- If user references a file not linked to the session, agent explains "That file isn't part of this session" — no suggestion to link (file management is UI phase scope)

### Manager Agent Routing
- Past analysis results stay valid when files change — only trigger NEW_ANALYSIS if the query involves changed files
- Cross-file queries can use MEMORY_SUFFICIENT if the same files were analyzed together before — consistent with existing routing
- Manager Agent's system prompt updated with explicit list of linked files and their names — better routing decisions
- If any referenced file has an error (corrupted/unreadable), fail the whole query with clear explanation of which file has the problem — no partial results

### Claude's Discretion
- DataFrame naming convention (from filename, sanitized, etc.)
- Token budget size and reduction thresholds
- Exact format of the assembled multi-file context string
- Join hint detection algorithm
- Auto-acknowledge message format and detail level

</decisions>

<specifics>
## Specific Ideas

- Success criteria requires named DataFrames (df_sales, df_customers) not generic df — naming approach is Claude's discretion but must be descriptive
- E2B sandbox must handle up to 5 files without memory overflow
- Context Assembler must work within token budget (progressive reduction is the strategy)
- Join hints should feel like suggestions, not assertions — user confirms before agent uses them for cross-file operations

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 15-agent-system-enhancement*
*Context gathered: 2026-02-11*
