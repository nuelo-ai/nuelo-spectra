# Phase 11: Web Search Tool Integration - Context

**Gathered:** 2026-02-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Data Analysis Agent gains web search capability via Serper.dev to answer benchmarking queries requiring external data, with transparent source citations. Search is user-activated per query (toggle below chat input), agent decides whether search is actually needed. This phase covers search execution, result presentation, failure handling, and guardrails. It does NOT cover subscription tiers or advanced query safety filters.

</domain>

<decisions>
## Implementation Decisions

### Search Triggering
- Dual-gate activation: user must toggle "Search Tool" ON below chat input (per-query, not per-tab) AND agent decides if search is actually needed for the query
- Default toggle state: OFF — user explicitly activates per message
- Toggle resets to OFF after each query — user re-enables for next query if desired
- When toggle is ON but agent decides search isn't needed: silent skip (no notification to user)
- Multiple searches allowed per response — agent can issue up to N searches per query (configurable via env/config, default max: 5)
- Agent formulates search queries autonomously based on query content

### Result Presentation
- Sources displayed as "Sources" section at the end of the response (not inline citations)
- Each source entry: page title as clickable link + URL (no snippet/excerpt)
- Search activity shown in real-time while searching — display actual search query text (e.g., "Searching: 'industry revenue benchmarks 2025'...") similar to Perplexity's search transparency
- Search results integrate into DataCard format — sources section added as part of the DataCard (not separate chat message)

### Failure UX
- API failure/timeout: inline notice in response ("Web search unavailable — answering from available data") then continue with data analysis only
- On search failure: do NOT attempt to answer from LLM knowledge — just analyze the uploaded data without external comparison
- No API key configured: search toggle appears but is grayed out with tooltip "Search not configured"
- Quota exceeded: toggle auto-disables for the rest of the session with message "Search quota reached"

### Search Guardrails
- Configurable domain blocklist — admin can block specific domains from search results
- Results per search query: configurable via env/config (Claude picks sensible default)
- Query sanitization: agent must formulate generic search queries, never include raw cell values or identifiable data from uploaded files in search queries
- User-level daily search quota: configurable, default 7 searches per day per user (future subscription tiers will increase this for paid users)
- App-level quota tracking separate from Serper's own plan limits

### Claude's Discretion
- Default number of results per search query
- Default domain blocklist entries (if any)
- Search query formulation strategy (how agent converts user intent to search queries)
- Exact toggle UI component design and positioning
- Search activity animation/indicator design
- How sources section is styled within DataCard

</decisions>

<specifics>
## Specific Ideas

- Toggle UX inspired by Perplexity and Claude's web search toggles — located below chat input
- Search activity display inspired by Perplexity's transparent "Searching: ..." indicators
- User-level quota of 7/day is a placeholder — will be adjusted when subscription plans are implemented (paid users get higher quota)

</specifics>

<deferred>
## Deferred Ideas

- Subscription-tier search quotas (different limits for free vs paid users) — future subscription/billing phase
- Query safety filter in Manager Agent (block PII extraction, prompt injection) — noted in STATE.md pending todos

</deferred>

---

*Phase: 11-web-search-tool-integration*
*Context gathered: 2026-02-08*
