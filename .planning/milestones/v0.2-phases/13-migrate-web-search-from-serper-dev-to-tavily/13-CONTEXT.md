# Phase 13: Migrate Web Search from Serper.dev to Tavily - Context

**Gathered:** 2026-02-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the Serper.dev search provider with Tavily API in the existing web search infrastructure (built in Phase 11). The core motivation: Serper.dev only returns URL links, while Tavily returns synthesized answers with full context — enabling the Analyst AI agent to produce richer, more informed analysis grounded in actual search content.

</domain>

<decisions>
## Implementation Decisions

### Content handling
- Use Tavily's synthesized **answer** (not raw_content or short snippets)
- Tavily returns only 3 results (not 5+) — keep it focused
- Agent receives: Tavily's synthesized answer + source URLs only (no individual snippets)
- **Critical:** The Analyst agent must incorporate Tavily's answer into its analysis context — this is the primary value of the migration. The agent should have more info/context to build better answers for users
- Tavily answer is fed into the agent's LLM context, not displayed separately in the UI

### Search configuration
- All Tavily settings in `.env` only (no search.yaml changes for provider-specific config)
- `TAVILY_API_KEY` in .env (replaces SERPER_API_KEY)
- `SEARCH_DEPTH` configurable in .env (basic/advanced) — admin can set depth
- `topic` parameter fixed to "general" (not configurable)
- Daily quota system stays the same: default 7/day per user, configurable as current setup
- GET /search/config endpoint response shape unchanged — frontend doesn't need to know provider changed

### Source display in UI
- DataCard sources section stays as-is: clickable page title + URL links
- No relevance scores shown to users
- No "Web Context" section — Tavily answer is internal to agent, not user-facing
- UI changes are minimal to none for this migration

### Serper.dev cleanup
- Full removal of all Serper.dev code, config references, and SERPER_API_KEY
- Clean break — no fallback provider pattern
- .env.example updated to show TAVILY_API_KEY instead of SERPER_API_KEY

### Claude's Discretion
- Whether to use tavily-python SDK or raw HTTP calls (httpx) — pick based on code simplicity and reliability
- Test strategy: rewrite vs mock-swap — pick based on ensuring reliable test coverage
- Internal implementation details of how Tavily answer gets injected into agent context

</decisions>

<specifics>
## Specific Ideas

- The whole point of this migration is giving the Analyst agent more context to work with — Tavily's synthesized answer should be treated as the primary search input to the agent, not just metadata
- search_depth=advanced should be the setting admins reach for when they want deeper analysis quality
- This should be a clean swap — the user experience stays the same, but the AI analysis quality improves because the agent has real content to work with

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-migrate-web-search-from-serper-dev-to-tavily*
*Context gathered: 2026-02-09*
