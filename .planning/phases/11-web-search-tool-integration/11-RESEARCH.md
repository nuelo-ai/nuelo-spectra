# Phase 11: Web Search Tool Integration - Research

**Researched:** 2026-02-08
**Domain:** Serper.dev API integration, LangGraph tool architecture, search UX patterns
**Confidence:** HIGH

## Summary

Phase 11 adds web search capability to the Data Analysis Agent via Serper.dev, enabling benchmarking queries that require external data. The architecture is well-defined by the existing codebase: the Data Analysis Agent (`data_analysis.py`) is the correct integration point since it interprets results and generates the final response. The search is NOT a LangGraph tool binding -- it is a direct `httpx` call within the Data Analysis Agent node, keeping the implementation simple and aligned with the existing graph topology.

The key architectural decision is: **search happens inside the `data_analysis_agent` node, not as a separate graph node or LLM tool call**. The agent receives a `web_search_enabled` flag in state, decides whether search is needed based on the query, calls Serper.dev directly via `httpx` (already a project dependency), and incorporates results into its analysis prompt. Sources are returned as structured data in the response for the frontend to render.

**Primary recommendation:** Build a lightweight `SearchService` class using `httpx.AsyncClient` for Serper.dev API calls, integrate it into the existing `data_analysis_agent` node, add a `web_search_enabled` flag to `ChatAgentState` and `ChatQueryRequest`, and extend `DataCard` with a sources section. No new graph nodes needed. No `langchain-community` dependency needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Dual-gate activation: user must toggle "Search Tool" ON below chat input (per-query, not per-tab) AND agent decides if search is actually needed for the query
- Default toggle state: OFF -- user explicitly activates per message
- Toggle resets to OFF after each query -- user re-enables for next query if desired
- When toggle is ON but agent decides search isn't needed: silent skip (no notification to user)
- Multiple searches allowed per response -- agent can issue up to N searches per query (configurable via env/config, default max: 5)
- Agent formulates search queries autonomously based on query content
- Sources displayed as "Sources" section at the end of the response (not inline citations)
- Each source entry: page title as clickable link + URL (no snippet/excerpt)
- Search activity shown in real-time while searching -- display actual search query text (e.g., "Searching: 'industry revenue benchmarks 2025'...") similar to Perplexity's search transparency
- Search results integrate into DataCard format -- sources section added as part of the DataCard (not separate chat message)
- API failure/timeout: inline notice in response ("Web search unavailable -- answering from available data") then continue with data analysis only
- On search failure: do NOT attempt to answer from LLM knowledge -- just analyze the uploaded data without external comparison
- No API key configured: search toggle appears but is grayed out with tooltip "Search not configured"
- Quota exceeded: toggle auto-disables for the rest of the session with message "Search quota reached"
- Configurable domain blocklist -- admin can block specific domains from search results
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

### Deferred Ideas (OUT OF SCOPE)
- Subscription-tier search quotas (different limits for free vs paid users) -- future subscription/billing phase
- Query safety filter in Manager Agent (block PII extraction, prompt injection) -- noted in STATE.md pending todos
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | >=0.27.0 | Serper.dev API calls (async) | Already in pyproject.toml, async-native, no new dependency |
| langgraph | >=1.0.7 | Workflow orchestration, state management | Already in use, graph topology unchanged |
| langchain-core | >=0.3.0 | Message types, LLM interface | Already in use for all agents |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | (bundled) | Search config models, response schemas | Already used for RoutingDecision, Settings |
| pyyaml | >=6.0.0 | Search config in prompts.yaml | Already used for agent config |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct httpx | langchain-community GoogleSerperAPIWrapper | Would add ~50MB dependency for a 20-line wrapper. langchain-community is NOT installed. |
| Direct httpx | LangChain Tool + bind_tools | Adds complexity, requires ToolNode, changes graph topology. Overkill for single API call. |
| Serper.dev | Tavily API | Tavily is AI-optimized but costs more ($0.50/1k vs $0.30/1k). Serper is locked decision. |

**Installation:**
No new dependencies required. `httpx` is already installed.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
  services/
    search.py              # NEW: SearchService class (Serper.dev API client)
  agents/
    data_analysis.py        # MODIFIED: Add search integration
    state.py                # MODIFIED: Add web_search_enabled, search_sources fields
    config.py               # MODIFIED: Add search config loader
  config/
    prompts.yaml            # MODIFIED: Add search-related prompt sections
    search.yaml             # NEW: Search configuration (blocklist, defaults)
  models/
    search_quota.py         # NEW: SearchQuota model for daily tracking
  routers/
    chat.py                 # MODIFIED: Accept web_search_enabled in request
    search.py               # NEW: Search config endpoint (quota status, toggle availability)
  schemas/
    chat.py                 # MODIFIED: Add web_search_enabled to ChatQueryRequest
frontend/src/
  components/chat/
    ChatInput.tsx            # MODIFIED: Add search toggle below textarea
    DataCard.tsx             # MODIFIED: Add Sources section
    ChatInterface.tsx        # MODIFIED: Handle search streaming events
  hooks/
    useSSEStream.ts          # MODIFIED: Handle search_started events
    useSearchToggle.ts       # NEW: Toggle state + config check hook
  types/
    chat.ts                  # MODIFIED: Add search event types
```

### Pattern 1: Search Service (Direct API Client)
**What:** A lightweight async service class wrapping the Serper.dev API
**When to use:** All search operations go through this service
**Example:**
```python
# backend/app/services/search.py
import httpx
import logging
from dataclasses import dataclass

logger = logging.getLogger("spectra.search")

@dataclass
class SearchResult:
    title: str
    link: str
    position: int

@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult]
    success: bool
    error: str | None = None

class SearchService:
    """Serper.dev search API client."""

    BASE_URL = "https://google.serper.dev/search"

    def __init__(
        self,
        api_key: str,
        num_results: int = 5,
        blocked_domains: list[str] | None = None,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.num_results = num_results
        self.blocked_domains = blocked_domains or []
        self.timeout = timeout

    async def search(self, query: str) -> SearchResponse:
        """Execute a search query against Serper.dev."""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "num": self.num_results,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                data = response.json()

            # Parse organic results
            organic = data.get("organic", [])
            results = []
            for item in organic:
                link = item.get("link", "")
                # Apply domain blocklist
                if any(domain in link for domain in self.blocked_domains):
                    continue
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=link,
                    position=item.get("position", 0),
                ))

            # Log search for debugging and cost tracking (SEARCH-07)
            logger.info({
                "event": "web_search",
                "query": query,
                "results_count": len(results),
                "status": "success",
            })

            return SearchResponse(
                query=query,
                results=results,
                success=True,
            )

        except httpx.TimeoutException:
            logger.warning({"event": "web_search", "query": query, "status": "timeout"})
            return SearchResponse(query=query, results=[], success=False, error="timeout")
        except httpx.HTTPStatusError as e:
            logger.error({"event": "web_search", "query": query, "status": "http_error", "code": e.response.status_code})
            return SearchResponse(query=query, results=[], success=False, error=f"HTTP {e.response.status_code}")
        except Exception as e:
            logger.error({"event": "web_search", "query": query, "status": "error", "error": str(e)})
            return SearchResponse(query=query, results=[], success=False, error=str(e))
```

### Pattern 2: State Extension for Search
**What:** Add search-related fields to ChatAgentState
**When to use:** Passing search flag and results through the graph
**Example:**
```python
# Additions to backend/app/agents/state.py
class ChatAgentState(TypedDict):
    # ... existing fields ...

    web_search_enabled: bool
    """Whether user toggled web search ON for this query."""

    search_sources: list[dict]
    """List of search sources: [{"title": str, "url": str}]"""
```

### Pattern 3: Integration in Data Analysis Agent
**What:** The Data Analysis Agent decides whether to search, executes searches, and incorporates results
**When to use:** When `web_search_enabled` is True in state
**Example:**
```python
# Inside data_analysis_agent() in data_analysis.py
async def data_analysis_agent(state: ChatAgentState) -> dict:
    # ... existing routing check ...

    # Web search integration
    search_sources = []
    search_context = ""
    web_search_enabled = state.get("web_search_enabled", False)

    if web_search_enabled:
        search_service = get_search_service()  # factory function
        if search_service:
            # Ask LLM to formulate search queries
            search_queries = await formulate_search_queries(
                user_query=state["user_query"],
                data_summary=state.get("data_summary", ""),
                llm=llm,
            )

            for query in search_queries:
                writer({"type": "search_started", "message": f"Searching: '{query}'..."})
                result = await search_service.search(query)
                if result.success:
                    for r in result.results:
                        search_sources.append({"title": r.title, "url": r.link})
                    search_context += f"\nSearch results for '{query}':\n"
                    for r in result.results:
                        search_context += f"- {r.title}: {r.link}\n"
                else:
                    # Search failed -- continue without it
                    writer({"type": "search_failed", "message": "Web search unavailable"})

    # Include search context in analysis prompt if available
    if search_context:
        system_prompt += f"\n\n**Web Search Results:**\n{search_context}"
        system_prompt += "\n\nIncorporate relevant web search findings into your analysis."
    elif web_search_enabled:
        system_prompt += "\n\nNote: Web search was requested but unavailable. Answer from available data only."

    # ... existing LLM call and response parsing ...

    return {
        "analysis": analysis,
        "final_response": analysis,
        "follow_up_suggestions": follow_ups,
        "search_sources": search_sources,
        "messages": [AIMessage(content=analysis)],
    }
```

### Pattern 4: Dual-Gate Activation (Frontend)
**What:** Toggle below chat input that enables search per query, resets after send
**When to use:** Every query send
**Example:**
```typescript
// In ChatInput.tsx - add toggle below textarea
import { Globe } from "lucide-react";
import { Switch } from "@/components/ui/switch";

export function ChatInput({ onSend, disabled, initialValue, searchAvailable, searchEnabled, onSearchToggle }) {
  // ... existing state ...

  const handleSend = () => {
    const trimmed = message.trim();
    if (trimmed && !disabled) {
      onSend(trimmed);
      setMessage("");
      // Reset toggle after send
      onSearchToggle?.(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-end gap-3">
        {/* existing textarea and send button */}
      </div>
      {/* Search toggle below input */}
      <div className="flex items-center gap-2 px-1">
        <Switch
          checked={searchEnabled}
          onCheckedChange={onSearchToggle}
          disabled={!searchAvailable || disabled}
          className="scale-75"
        />
        <span className="text-xs text-muted-foreground">
          Search web
        </span>
      </div>
    </div>
  );
}
```

### Pattern 5: Sources Section in DataCard
**What:** Display search sources at the bottom of DataCard
**When to use:** When response includes search_sources in metadata
**Example:**
```typescript
// Addition to DataCard.tsx
{searchSources && searchSources.length > 0 && !isStreaming && (
  <div className="space-y-2 pt-3 border-t border-border/50">
    <h4 className="text-xs font-medium text-muted-foreground">Sources</h4>
    <div className="space-y-1">
      {searchSources.map((source, i) => (
        <a
          key={i}
          href={source.url}
          target="_blank"
          rel="noopener noreferrer"
          className="block text-xs text-primary hover:underline truncate"
        >
          {source.title}
        </a>
      ))}
    </div>
  </div>
)}
```

### Anti-Patterns to Avoid
- **Adding a new LangGraph node for search:** The search is logically part of the Data Analysis Agent's context gathering. A separate node would complicate routing and state management.
- **Using bind_tools/ToolNode:** The existing graph does NOT use LLM tool calling. All nodes are custom functions with Command-based routing. Introducing bind_tools would require a fundamental architectural change.
- **Adding langchain-community as a dependency:** The project deliberately uses only langchain-core plus provider-specific packages. GoogleSerperAPIWrapper from langchain-community is a trivial wrapper around httpx POST; building it directly avoids a heavy dependency.
- **Passing search results through Messages:** Search sources should be in a dedicated state field (`search_sources`), not embedded in AIMessage content. This keeps them structured for frontend rendering.
- **Blocking on search failure:** Never let search failure prevent the analysis from completing. Always degrade gracefully.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP client | Raw socket/urllib | httpx.AsyncClient | Already a dependency, handles timeouts, retries, async natively |
| API rate limiting | Custom rate limiter | Simple counter in DB (SearchQuota model) | App-level quota is a counter, not a rate limiter. DB query is sufficient for 7/day. |
| Search result parsing | Custom HTML scraper | Serper.dev JSON API response | Serper returns structured JSON; no scraping needed |
| Toggle component | Custom toggle from scratch | shadcn/ui Switch component | Already in the project's UI library |

**Key insight:** The Serper.dev API does all the heavy lifting (query -> structured JSON results). Our code only needs to: call the API, filter results, pass to LLM, render sources.

## Common Pitfalls

### Pitfall 1: Search Queries Leaking Sensitive Data
**What goes wrong:** Agent formulates search queries that include raw cell values, user names, or other identifiable data from uploaded files
**Why it happens:** LLM naturally includes specific data in search queries for precision
**How to avoid:** Explicit prompt instruction: "Formulate GENERIC industry/benchmarking queries. NEVER include specific values, names, or identifiable information from the dataset." Add examples of good vs bad queries in the prompt.
**Warning signs:** Search logs showing queries with numeric values, company names, or personal data

### Pitfall 2: Serper API Key Exposed in Frontend
**What goes wrong:** API key sent to frontend or visible in SSE events
**Why it happens:** Accidentally including config details in stream events
**How to avoid:** Search is backend-only. API key never leaves the server. Only search query text and source results are sent to frontend via SSE events.
**Warning signs:** API key appearing in network tab, SSE event payloads, or client-side state

### Pitfall 3: Search Quota Not Counting Failed Searches
**What goes wrong:** Failed/timed-out searches still decrement user quota, or conversely, successful searches don't count toward quota
**Why it happens:** Quota check happens at wrong point in the flow
**How to avoid:** Increment quota count BEFORE the API call (optimistic). If the API call fails, the query was still "used" from the user's perspective. Check quota BEFORE starting any searches in a query.
**Warning signs:** Users running out of quota without seeing results, or quota never decrementing

### Pitfall 4: Race Condition on Toggle Reset
**What goes wrong:** Toggle state is ON when the next query starts because reset hasn't propagated
**Why it happens:** React state update is async; if user types and sends very quickly after a previous query completes
**How to avoid:** Reset toggle in the `handleSend` function BEFORE calling `startStream`, not in a useEffect after stream completes
**Warning signs:** Consecutive queries both having search enabled when user only toggled once

### Pitfall 5: Search Results Dominating LLM Context Window
**What goes wrong:** Including full search result snippets/content fills the LLM context, reducing space for actual data analysis
**Why it happens:** Passing too much search context to the analysis prompt
**How to avoid:** Only pass title + URL (per CONTEXT.md decision -- no snippets). The LLM uses titles/URLs as signals for context, not as source material. Keep search context brief.
**Warning signs:** Analysis responses becoming shorter/lower quality when search is enabled

### Pitfall 6: Multiple Search Queries Serialized Slowly
**What goes wrong:** 5 sequential search queries add 5-10 seconds to response time
**Why it happens:** Each search query waits for the previous one to complete
**How to avoid:** Use `asyncio.gather()` to execute multiple search queries concurrently. Each Serper call takes 1-2s; parallel execution keeps total to ~2s regardless of count.
**Warning signs:** Search-enabled queries taking significantly longer (5x+) than non-search queries

### Pitfall 7: Quota Check Creating DB Session Issues During Stream
**What goes wrong:** Checking/updating quota during stream causes "connection closed" errors
**Why it happens:** The injected DB session times out during long streams (see existing Pitfall 7 in agent_service.py comments)
**How to avoid:** Use a fresh `async_session_maker()` session for quota operations, same pattern as existing stream save logic
**Warning signs:** Intermittent 500 errors on search-enabled queries

### Pitfall 8: Search Toggle State Unclear When Not Configured
**What goes wrong:** Users see a toggle they can't use without understanding why
**Why it happens:** API key not configured, but toggle still appears interactive
**How to avoid:** Check search availability via config endpoint. Show grayed-out toggle with tooltip "Search not configured" when API key is missing. Disable toggle entirely when quota exceeded.
**Warning signs:** User complaints about broken search toggle

## Code Examples

### Serper.dev API Call
```python
# Verified pattern from Serper.dev docs and community examples
import httpx

async def search_serper(query: str, api_key: str, num: int = 5) -> dict:
    """Call Serper.dev search API.

    Endpoint: POST https://google.serper.dev/search
    Auth: X-API-KEY header
    Params: q (query), num (results count), gl (country), hl (language)
    Response: JSON with organic[], knowledgeGraph{}, answerBox{}, peopleAlsoAsk[]
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": num},
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
```

### Serper.dev Response Structure
```json
{
  "searchParameters": {
    "q": "industry revenue benchmarks 2025",
    "type": "search",
    "num": 5
  },
  "organic": [
    {
      "title": "Industry Revenue Benchmarks Report 2025",
      "link": "https://example.com/report",
      "snippet": "Comprehensive analysis of industry revenue...",
      "position": 1
    },
    {
      "title": "Another Result",
      "link": "https://example.com/other",
      "snippet": "More information...",
      "position": 2
    }
  ],
  "knowledgeGraph": { "title": "...", "description": "..." },
  "answerBox": { "answer": "...", "snippet": "..." },
  "peopleAlsoAsk": [{ "question": "...", "snippet": "..." }]
}
```

### Search Query Formulation Strategy
```python
async def formulate_search_queries(
    user_query: str,
    data_summary: str,
    llm,
    max_queries: int = 3,
) -> list[str]:
    """Use LLM to formulate generic search queries from user's data question.

    Rules:
    - Formulate GENERIC benchmarking/industry queries
    - NEVER include specific values, names, or identifiable data
    - Focus on industry standards, benchmarks, averages, trends
    - Return 1-3 search queries as a JSON array
    """
    prompt = f"""Based on this user's data analysis question, formulate 1-{max_queries} web search queries
to find relevant external benchmarks or industry data.

User's question: {user_query}
Data context: {data_summary[:500]}

RULES:
- Create GENERIC search queries (no specific company names, values, or personal data)
- Focus on industry benchmarks, standards, averages, and trends
- Each query should be 3-8 words
- Return ONLY a JSON array of strings, nothing else

Example good queries: ["average SaaS churn rate 2025", "ecommerce revenue benchmarks"]
Example bad queries: ["Acme Corp revenue vs competitors", "john doe salary comparison"]

Return your queries:"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    # Parse JSON array from response
    import json
    try:
        queries = json.loads(response.content.strip())
        return queries[:max_queries]
    except json.JSONDecodeError:
        return []
```

### Daily Quota Tracking (Database Model)
```python
# backend/app/models/search_quota.py
from sqlalchemy import Date, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date
from uuid import UUID
from app.models.base import Base

class SearchQuota(Base):
    """Track daily search usage per user."""
    __tablename__ = "search_quotas"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    search_date: Mapped[date] = mapped_column(Date, primary_key=True)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
```

### SSE Event Types for Search
```python
# New SSE event types emitted by data_analysis_agent during search
# 1. Search query being executed
{"type": "search_started", "message": "Searching: 'industry revenue benchmarks 2025'..."}

# 2. Search completed with results
{"type": "search_completed", "message": "Found 5 results", "sources_count": 5}

# 3. Search failed gracefully
{"type": "search_failed", "message": "Web search unavailable -- answering from available data"}

# 4. Quota exceeded (emitted before search attempt)
{"type": "search_quota_exceeded", "message": "Search quota reached"}
```

### Frontend Search Config Check
```typescript
// New endpoint: GET /search/config
// Returns search availability for current user
interface SearchConfig {
  available: boolean;       // API key configured
  quota_remaining: number;  // searches left today
  quota_limit: number;      // daily limit
  quota_exceeded: boolean;  // true if 0 remaining
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| langchain-community GoogleSerperAPIWrapper | Direct httpx calls | N/A (design choice) | Avoids heavy dependency, same functionality |
| LangGraph ToolNode + bind_tools | Custom node with direct API call | N/A (design choice) | Keeps existing graph architecture clean |
| Inline citations in text | Structured sources section | N/A (user decision) | Cleaner UX, easier to maintain |

**Deprecated/outdated:**
- LangChain's `load_tools(["google-serper"])` pattern requires langchain-community. Not applicable here.
- SerpApi (different service from Serper.dev) -- more expensive, different API. Not what user chose.

## Discretion Recommendations

### Default Results Per Query: 5
**Rationale:** Balances information density with API cost. Serper's default is 10, but for benchmarking context, 5 results provide sufficient signal without wasting quota. Configurable via `SEARCH_NUM_RESULTS` env var.

### Default Domain Blocklist: Empty
**Rationale:** No domains need blocking by default. Admin can configure via `search.yaml` if needed. Common candidates for future blocking: reddit.com (unreliable), quora.com (outdated), pinterest.com (irrelevant).

### Search Query Formulation Strategy
**Rationale:** Use a lightweight LLM call (same provider as data_analysis agent) to convert the user's query + data context into 1-3 generic search queries. This approach:
1. Ensures query sanitization (no raw data values)
2. Produces better search results than raw user queries
3. Allows multiple focused queries per user question
4. Costs minimal tokens (small prompt, short response)

### Toggle UI Design
**Rationale:** A small Switch component with "Search web" label below the chat input textarea, left-aligned. Grayed out with tooltip when unavailable. Inspired by Claude's and Perplexity's search toggles. Uses shadcn/ui Switch (already in project).

### Search Activity Indicator
**Rationale:** Reuse the existing status indicator bar at the bottom of ChatInterface (the one showing "Generating code...", "Validating...", etc.). Add a new status message format: "Searching: 'query text'..." with the same pulsing dot animation. No new animation components needed.

### Sources Section Styling
**Rationale:** Add sources below the follow-up suggestions in DataCard, separated by a border-t. Each source is a clickable link with the page title, using text-xs styling. Compact, non-intrusive, consistent with existing card aesthetics.

## Open Questions

1. **Serper API Response Schema Completeness**
   - What we know: Response includes `organic[]` with `title`, `link`, `snippet`, `position`. Also has `knowledgeGraph`, `answerBox`, `peopleAlsoAsk`.
   - What's unclear: Exact field names for all response variants (news, images). Whether `organic` is always present even on zero results.
   - Recommendation: Build for `organic[]` only (per CONTEXT.md -- we only need title + link). Test with real API key in development. Handle missing `organic` key gracefully.

2. **Concurrent Search Query Limits**
   - What we know: Serper supports 300 queries/second on Ultimate tier. Our max is 5 per query.
   - What's unclear: Whether free/starter tier has lower rate limits that could affect concurrent queries.
   - Recommendation: Use `asyncio.gather()` for parallel execution but add a semaphore (max 3 concurrent) as safety margin. Configurable.

3. **Quota Tracking Granularity**
   - What we know: User decision is 7 searches per day per user. Each search query to Serper counts as 1.
   - What's unclear: Does "7 searches per day" mean 7 Serper API calls, or 7 user queries with search enabled? (A single user query can trigger up to 5 Serper calls.)
   - Recommendation: Count per USER QUERY (not per Serper API call). If user sends 1 query and agent makes 3 Serper calls, that's 1 of 7. This is more user-friendly and aligns with "7 searches per day per user" wording.

## Sources

### Primary (HIGH confidence)
- Serper.dev official site: https://serper.dev/ -- API overview, pricing, free tier (2,500 queries)
- Existing codebase analysis: All agent files, graph.py, state.py, data_analysis.py, config.py, llm_factory.py, chat.py (router + schemas), ChatInterface.tsx, DataCard.tsx, ChatInput.tsx, useSSEStream.ts
- pyproject.toml dependency analysis: httpx already installed, langchain-community NOT installed

### Secondary (MEDIUM confidence)
- Serper API documentation via third-party: https://docs.sim.ai/tools/serper -- endpoint, params, response fields
- Serper API usage example: https://rramos.github.io/2024/06/13/serper/ -- POST format, headers, Python example
- LangChain Serper integration docs: https://docs.langchain.com/oss/python/integrations/providers/google_serper -- GoogleSerperAPIWrapper patterns
- CrewAI Serper docs: https://docs.crewai.com/en/tools/search-research/serperdevtool -- params reference

### Tertiary (LOW confidence)
- Serper response schema details (organic fields): reconstructed from multiple indirect sources, needs validation with real API call
- Serper rate limits by tier: only Ultimate tier (300 qps) documented; free/starter limits unclear

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- httpx already installed, no new dependencies, patterns verified in codebase
- Architecture: HIGH -- integration point (data_analysis_agent) clearly identified, graph topology unchanged, state extension is minimal
- API integration: MEDIUM -- Serper API docs are sparse; endpoint/auth/basic response verified, but full response schema needs real API testing
- Frontend patterns: HIGH -- extending existing DataCard, ChatInput, useSSEStream with small additions
- Quota system: MEDIUM -- database model is straightforward, but quota counting granularity needs confirmation

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days -- Serper API is stable, codebase patterns unlikely to change)
