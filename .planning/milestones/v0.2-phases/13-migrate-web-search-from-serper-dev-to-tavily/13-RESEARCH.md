# Phase 13: Migrate Web Search from Serper.dev to Tavily - Research

**Researched:** 2026-02-09
**Domain:** Search API migration (Serper.dev -> Tavily), Python async HTTP, LangGraph tool-calling
**Confidence:** HIGH

## Summary

This phase is a clean API provider swap within an existing, well-structured web search infrastructure built in Phase 11. The current implementation uses `SearchService` (in `backend/app/services/search.py`) with httpx to call Serper.dev, returning `SearchResult` dataclasses containing only title, link, and position. The `search_web` tool (in `backend/app/agents/tools/web_search.py`) formats these as `"- {title}: {url}\n"` lines, which the Data Analysis Agent receives as tool output. The key value of this migration is that Tavily returns a synthesized `answer` field -- an LLM-generated summary of search results -- that gives the agent much richer context than bare URL links.

The migration touches 6 backend files and 0 frontend files. The `SearchService` class gets rewritten to call Tavily's `/search` endpoint. The `SearchResult`/`SearchResponse` dataclasses gain an `answer` field. The `search_web` tool returns the Tavily answer + source URLs instead of just titles and URLs. The `_generate_analysis_with_search` function in `data_analysis.py` already injects search results text into the agent's prompt context -- Tavily's synthesized answer flows through this existing path. The `GET /search/config` endpoint swaps its `serper_api_key` check for `tavily_api_key`. Settings in `config.py` swap `serper_api_key` for `tavily_api_key` and add `search_depth`. No database migrations are needed (search_quotas table is provider-agnostic). No frontend changes are needed (SearchSource shape stays `{title, url}`).

**Primary recommendation:** Use the `tavily-python` SDK's `AsyncTavilyClient` for the HTTP layer -- it already uses httpx internally, handles auth/errors/retries, and matches the project's async architecture. Set `include_answer=True` and `max_results=3` as the core configuration.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Use Tavily's synthesized **answer** (not raw_content or short snippets)
- Tavily returns only 3 results (not 5+) -- keep it focused
- Agent receives: Tavily's synthesized answer + source URLs only (no individual snippets)
- The Analyst agent must incorporate Tavily's answer into its analysis context -- this is the primary value of the migration
- Tavily answer is fed into the agent's LLM context, not displayed separately in the UI
- All Tavily settings in `.env` only (no search.yaml changes for provider-specific config)
- `TAVILY_API_KEY` in .env (replaces SERPER_API_KEY)
- `SEARCH_DEPTH` configurable in .env (basic/advanced) -- admin can set depth
- `topic` parameter fixed to "general" (not configurable)
- Daily quota system stays the same: default 7/day per user, configurable as current setup
- GET /search/config endpoint response shape unchanged -- frontend does not need to know provider changed
- DataCard sources section stays as-is: clickable page title + URL links
- No relevance scores shown to users
- No "Web Context" section -- Tavily answer is internal to agent, not user-facing
- UI changes are minimal to none for this migration
- Full removal of all Serper.dev code, config references, and SERPER_API_KEY
- Clean break -- no fallback provider pattern
- .env.example updated to show TAVILY_API_KEY instead of SERPER_API_KEY

### Claude's Discretion
- Whether to use tavily-python SDK or raw HTTP calls (httpx) -- pick based on code simplicity and reliability
- Test strategy: rewrite vs mock-swap -- pick based on ensuring reliable test coverage
- Internal implementation details of how Tavily answer gets injected into agent context

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tavily-python | 0.7.21 | Tavily API client with AsyncTavilyClient | Official SDK, uses httpx internally, handles auth/errors/retries, async-native |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | >=0.27.0 (already installed) | HTTP transport (used by tavily-python internally) | Already a project dependency, no additional install needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tavily-python SDK | Raw httpx calls | Raw httpx is simpler (fewer deps), but SDK handles Bearer auth, error mapping, retry logic, and parameter validation. SDK adds ~1 dependency but saves ~30 lines of boilerplate. |

**Recommendation:** Use `tavily-python` SDK. Rationale:
1. `AsyncTavilyClient` uses httpx internally (same transport the project already depends on)
2. SDK handles error mapping (429 -> rate limit, 401 -> auth error, 432 -> plan limit) with clear exception types
3. SDK manages the `Authorization: Bearer {api_key}` header pattern (Tavily uses Bearer auth, not X-API-KEY like Serper)
4. SDK uses a persistent `httpx.AsyncClient` with connection pooling
5. The project already has SDK dependencies (langchain-anthropic, e2b-code-interpreter) -- adding one more is consistent

**Installation:**
```bash
pip install tavily-python
```

Add to `pyproject.toml` dependencies:
```
"tavily-python>=0.7.0",
```

## Architecture Patterns

### Current Architecture (What Exists)

```
backend/app/
  services/
    search.py           # SearchService (Serper.dev client) -- REWRITE
  agents/
    tools/
      web_search.py     # search_web @tool -- MODIFY (return format)
      __init__.py        # Tool registry -- NO CHANGE
    data_analysis.py     # da_with_tools_node, da_response_node -- MODIFY (answer injection)
    state.py             # ChatAgentState -- NO CHANGE
    graph.py             # LangGraph workflow -- NO CHANGE
  config.py              # Settings (serper_api_key) -- MODIFY (swap env vars)
  config/
    search.yaml          # Feature defaults -- NO CHANGE (per user decision)
  routers/
    search.py            # GET /search/config -- MODIFY (key check)
  models/
    search_quota.py      # SearchQuota model -- NO CHANGE
```

### Pattern 1: SearchService Rewrite with AsyncTavilyClient
**What:** Replace the Serper.dev `SearchService` with a Tavily-backed implementation using `AsyncTavilyClient`
**When to use:** This is the core migration pattern

**Key changes to SearchService:**

Current `SearchResult` has: `title`, `link`, `position`
New `SearchResult` needs: `title`, `url`, `score` (internal only, not displayed)
New `SearchResponse` needs: `answer` field (Tavily's synthesized answer)

Current flow:
```
SearchService.search(query) -> POST to google.serper.dev/search
  -> parse organic[] -> return [SearchResult(title, link, position)]
```

New flow:
```
SearchService.search(query) -> AsyncTavilyClient.search(query, include_answer=True, max_results=3)
  -> extract response["answer"], response["results"] -> return SearchResponse(answer, results)
```

**Critical design detail:** The `SearchResponse.answer` field is the primary value. The `results` list provides source URLs for citation. The `answer` is what gets injected into the Data Analysis Agent's LLM context.

### Pattern 2: Tavily Answer Injection into Agent Context
**What:** Feed Tavily's synthesized answer into the Data Analysis Agent's fresh LLM call
**When to use:** When search was used and `da_response_node` generates the final analysis

The existing code path already handles this well. In `data_analysis.py`:

1. `search_web` tool returns formatted text (currently: `"- Title: URL\n"` lines)
2. `da_response_node` extracts `search_results_text` from `ToolMessage.content`
3. `_generate_analysis_with_search()` appends search results to the system prompt:
   ```python
   system_prompt += f"""
   **Web Search Results (incorporate relevant findings and cite sources):**
   {search_results_text}"""
   ```

**The migration change:** Instead of returning just title/URL lines from `search_web`, return:
```
Web search answer for '{query}':
{tavily_answer}

Sources:
- {title1}: {url1}
- {title2}: {url2}
- {title3}: {url3}
```

This means the Tavily synthesized answer flows naturally through the existing `search_results_text` -> `_generate_analysis_with_search()` -> LLM context path. No structural changes to `da_response_node` are needed.

### Pattern 3: Source Extraction Compatibility
**What:** Ensure `_extract_sources_from_tool_response()` still works
**When to use:** Source parsing from tool output

The current regex in `data_analysis.py`:
```python
pattern = re.compile(r"^- (.+?):\s+(https?://\S+)$", re.MULTILINE)
```

This pattern matches `"- Title: https://url"` lines. As long as the new tool output format keeps sources in this exact format, the extraction works without changes. The Tavily answer text goes above the sources block and does not match this pattern (it contains no lines starting with `- ` followed by a URL).

### Anti-Patterns to Avoid
- **Creating a provider abstraction layer:** User explicitly decided "clean break, no fallback provider pattern." Do NOT build a `SearchProvider` base class or adapter pattern. Just rewrite `SearchService` directly.
- **Storing Tavily answer in state:** The answer is ephemeral -- it flows through the tool output into the LLM context. Do NOT add an `answer` field to `ChatAgentState`. The tool output mechanism handles this.
- **Displaying Tavily answer in UI:** User explicitly decided "Tavily answer is internal to agent, not user-facing." The answer appears only in the agent's LLM context, never in SSE events or frontend rendering.
- **Changing search.yaml:** User decided all Tavily settings go in `.env` only. `search.yaml` keeps its existing provider-agnostic settings (enabled, max_searches_per_query, daily_quota_per_user, timeout_seconds).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tavily HTTP client | Custom httpx client with Bearer auth, error handling, parameter validation | `tavily-python` AsyncTavilyClient | Handles auth headers, error codes (429/401/432), parameter filtering, connection pooling |
| Tavily error mapping | Custom exception classes for each HTTP status | SDK's built-in exceptions | SDK maps 429->rate limit, 401->auth error, 432->plan limit automatically |
| Async HTTP transport | Building async httpx session management | SDK's internal `httpx.AsyncClient` | SDK manages persistent async client with proper cleanup |

**Key insight:** The tavily-python SDK is thin (single file), uses httpx (already in the project), and handles the exact boilerplate you'd otherwise write. The "raw httpx" alternative saves one dependency but costs ~30 lines of auth/error/parameter handling code that the SDK already tests.

## Common Pitfalls

### Pitfall 1: Forgetting include_answer=True
**What goes wrong:** Tavily returns results without the synthesized answer field by default. The `answer` key is only present when `include_answer` is set to `True`, `"basic"`, or `"advanced"`.
**Why it happens:** `include_answer` defaults to `False` in the API. Easy to miss because other parameters like `query` and `max_results` are more prominent.
**How to avoid:** Always pass `include_answer=True` in the `search()` call. Validate in tests that the response contains an `answer` key.
**Warning signs:** `response["answer"]` is `None` or missing.

### Pitfall 2: Tavily answer is None on Failure
**What goes wrong:** Even with `include_answer=True`, the `answer` field can be `None` if Tavily's LLM fails to generate one (rare but possible).
**Why it happens:** The answer is generated by an LLM on Tavily's side, which can occasionally fail.
**How to avoid:** Always have a fallback: if `answer` is `None`, fall back to concatenating `result["content"]` snippets (Tavily always returns content snippets in results).
**Warning signs:** Agent response quality drops because it received no search context.

### Pitfall 3: search_depth Credit Cost
**What goes wrong:** `search_depth="advanced"` costs 2 credits per search instead of 1 for `"basic"`. With 7 searches/day quota, this can hit Tavily's free tier (1000 credits/month) faster.
**Why it happens:** Admin sets `SEARCH_DEPTH=advanced` without understanding credit implications.
**How to avoid:** Document in `.env.example` that advanced uses 2x credits. Default to `"basic"`.
**Warning signs:** 432 (Plan Limit) errors from Tavily.

### Pitfall 4: Breaking Source URL Extraction Regex
**What goes wrong:** If the tool output format changes, `_extract_sources_from_tool_response()` stops finding sources, and the DataCard shows no source links.
**Why it happens:** The regex `r"^- (.+?):\s+(https?://\S+)$"` is format-sensitive. If Tavily answer text contains lines starting with `"- "` followed by a URL, false matches could occur.
**How to avoid:** Keep sources in a clearly delimited section. Ensure Tavily answer text (which can contain markdown with bullet points) does not have lines matching the exact `"- Title: https://url"` pattern. Test with real Tavily responses.
**Warning signs:** Incorrect or missing sources in DataCard.

### Pitfall 5: Not Cleaning Up All Serper References
**What goes wrong:** Stale `serper_api_key` references in code cause confusion or silent failures.
**Why it happens:** Serper is referenced in: `config.py`, `services/search.py`, `routers/search.py`, `.env.example`, docstrings, and comments in `agent_service.py`.
**How to avoid:** After migration, grep for `serper` (case-insensitive) across the entire codebase. Should return zero hits.
**Warning signs:** `grep -ri serper backend/` returns results after migration.

### Pitfall 6: AsyncTavilyClient Lifecycle
**What goes wrong:** Creating a new `AsyncTavilyClient` per search call wastes connection pooling benefits and may leak connections.
**Why it happens:** Current `SearchService.search()` creates a new `httpx.AsyncClient()` per call (line 86 of search.py). Replicating this pattern with `AsyncTavilyClient` would be wasteful since the SDK creates a persistent client internally.
**How to avoid:** Instantiate `AsyncTavilyClient` once in `SearchService.__init__()` or use the SDK's stateless pattern where it manages its own client lifecycle. The SDK's `AsyncTavilyClient` creates a persistent `httpx.AsyncClient` in `__init__`, so instantiating per-call is fine for correctness but suboptimal. The `SearchService.from_settings()` factory pattern can cache or create fresh -- either works since the SDK handles pooling internally.
**Warning signs:** High connection count or slow search times.

## Code Examples

### Example 1: Rewritten SearchService with AsyncTavilyClient

```python
"""Web search service using Tavily API."""

import json
import logging
from dataclasses import dataclass, field

from tavily import AsyncTavilyClient

logger = logging.getLogger("spectra.search")


@dataclass
class SearchResult:
    """A single search result from Tavily."""

    title: str
    url: str


@dataclass
class SearchResponse:
    """Response from a web search query."""

    query: str
    results: list[SearchResult]
    answer: str | None
    success: bool
    error: str | None = None


class SearchService:
    """Tavily search API client.

    Provides async web search via Tavily Search API.
    Returns synthesized answer + source URLs for agent context.
    """

    def __init__(
        self,
        api_key: str,
        max_results: int = 3,
        search_depth: str = "basic",
        timeout: float = 10.0,
    ):
        self.client = AsyncTavilyClient(api_key=api_key)
        self.max_results = max_results
        self.search_depth = search_depth
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "SearchService | None":
        """Create SearchService from app settings.

        Returns None if tavily_api_key is not configured.
        """
        from app.config import get_settings

        settings = get_settings()
        api_key = settings.tavily_api_key
        if not api_key:
            return None
        return cls(
            api_key=api_key,
            max_results=settings.search_num_results,
            search_depth=settings.search_depth,
            timeout=settings.search_timeout,
        )

    async def search(self, query: str) -> SearchResponse:
        """Execute a search query against Tavily."""
        try:
            response = await self.client.search(
                query=query,
                search_depth=self.search_depth,
                topic="general",
                max_results=self.max_results,
                include_answer=True,
                timeout=self.timeout,
            )

            answer = response.get("answer")
            raw_results = response.get("results", [])
            results = [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                )
                for r in raw_results
            ]

            logger.info(
                json.dumps({
                    "event": "web_search",
                    "query": query,
                    "results_count": len(results),
                    "has_answer": answer is not None,
                    "status": "success",
                })
            )

            return SearchResponse(
                query=query,
                results=results,
                answer=answer,
                success=True,
            )

        except Exception as e:
            logger.error(
                json.dumps({
                    "event": "web_search",
                    "query": query,
                    "status": "error",
                    "error": str(e),
                })
            )
            return SearchResponse(
                query=query,
                results=[],
                answer=None,
                success=False,
                error=str(e),
            )
```

Source: Tavily Python SDK reference (https://docs.tavily.com/sdk/python/reference) and Tavily API reference (https://docs.tavily.com/documentation/api-reference/endpoint/search)

### Example 2: Updated search_web Tool Output Format

```python
@tool
async def search_web(query: str) -> str:
    """Search the web for information using Tavily Search.
    ...
    """
    writer = get_stream_writer()
    writer({"type": "search_started", "message": f"Searching: '{query}'..."})

    service = SearchService.from_settings()
    if service is None:
        return "Web search is not configured. Answer from available data only."

    result = await service.search(query)

    if not result.success:
        writer({"type": "search_failed", "message": "Web search unavailable"})
        return f"Search failed ({result.error}). Answer from available data only."

    if not result.results and not result.answer:
        return "No relevant search results found."

    # Format: Tavily answer first (primary value), then source URLs
    formatted = ""
    if result.answer:
        formatted += f"Web search answer for '{query}':\n{result.answer}\n\n"

    if result.results:
        formatted += "Sources:\n"
        for r in result.results:
            formatted += f"- {r.title}: {r.url}\n"

    writer({
        "type": "search_completed",
        "message": f"Found {len(result.results)} results",
        "sources_count": len(result.results),
    })

    return formatted
```

Source: Existing `search_web` tool pattern in `backend/app/agents/tools/web_search.py`

### Example 3: Settings Changes in config.py

```python
# Web Search (in Settings class)
tavily_api_key: str = ""
search_depth: str = "basic"         # "basic" (1 credit) or "advanced" (2 credits)
search_max_per_query: int = 5
search_daily_quota: int = 7
search_num_results: int = 3         # Default changed from 5 to 3
search_timeout: float = 10.0
```

### Example 4: Updated /search/config Endpoint

```python
# In routers/search.py
settings = get_settings()
configured = bool(settings.tavily_api_key)  # Was: settings.serper_api_key
```

Response shape stays identical: `{configured, enabled, daily_quota, used_today, quota_exceeded}`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Serper.dev returns URL links only | Tavily returns synthesized answer + URLs | This migration | Agent gets actual content context, not just links |
| `include_answer` was basic only | `include_answer` supports `"basic"` and `"advanced"` modes | Tavily API 2025+ | `"advanced"` gives more detailed answers, costs same credits |
| Tavily `search_depth` had 2 options | Now has 4: `"fast"`, `"ultra-fast"`, `"basic"`, `"advanced"` | Late 2025 | More granularity, but user decision locks us to basic/advanced only |

**Note:** The Tavily API `topic` parameter also supports `"finance"` in addition to `"general"` and `"news"`, but user decision fixes this to `"general"`.

## Detailed File Change Map

### Files to MODIFY:

1. **`backend/app/services/search.py`** -- Full rewrite
   - Remove: `SearchResult.position`, Serper URL, httpx direct usage, `X-API-KEY` header, `organic[]` parsing, `blocked_domains` filtering
   - Add: `AsyncTavilyClient`, `SearchResponse.answer`, `include_answer=True`, `search_depth` parameter
   - Keep: Error handling structure (timeout, HTTP error, generic), logging pattern, `from_settings()` factory

2. **`backend/app/agents/tools/web_search.py`** -- Modify return format
   - Change: Return Tavily answer + source URLs instead of just title/URL lines
   - Keep: SSE events (search_started, search_completed, search_failed), `from_settings()` call

3. **`backend/app/config.py`** -- Swap env vars
   - Remove: `serper_api_key: str = ""`
   - Add: `tavily_api_key: str = ""`, `search_depth: str = "basic"`
   - Change: `search_num_results` default from 5 to 3

4. **`backend/app/routers/search.py`** -- Swap key check
   - Change: `settings.serper_api_key` -> `settings.tavily_api_key`

5. **`backend/.env.example`** -- Update documentation
   - Remove: `SERPER_API_KEY`
   - Add: `TAVILY_API_KEY`, `SEARCH_DEPTH`

6. **`backend/pyproject.toml`** -- Add dependency
   - Add: `"tavily-python>=0.7.0"`

### Files that NEED NO CHANGES:
- `backend/app/agents/data_analysis.py` -- Tavily answer flows through existing `search_results_text` path
- `backend/app/agents/state.py` -- `ChatAgentState` shape unchanged
- `backend/app/agents/graph.py` -- Graph structure unchanged
- `backend/app/agents/tools/__init__.py` -- Still exports `search_web`
- `backend/app/models/search_quota.py` -- Provider-agnostic
- `backend/app/services/agent_service.py` -- `_track_search_quota` unchanged, quota comments mention "Serper" but are just comments
- `backend/app/schemas/chat.py` -- Stream event types unchanged
- `backend/app/config/search.yaml` -- Per user decision, no changes
- All frontend files -- Per user decision, no UI changes

### Files to CHECK for stale references:
- `backend/app/services/agent_service.py` -- Comments say "Track search quota per user query (not per Serper API call)" -- update comment text
- `backend/app/agents/tools/web_search.py` -- Module docstring mentions "Serper.dev API calls" -- update docstring

## Tavily API Quick Reference

### Authentication
```
Authorization: Bearer tvly-YOUR_API_KEY
```
(Different from Serper's `X-API-KEY` header)

### Search Endpoint
```
POST https://api.tavily.com/search
```

### Key Parameters for This Migration
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `query` | from user | Required |
| `include_answer` | `True` | Core value of migration -- synthesized answer for agent context |
| `max_results` | 3 | User decision: focused results |
| `search_depth` | from `SEARCH_DEPTH` env var | Admin-configurable: "basic" (1 credit) or "advanced" (2 credits) |
| `topic` | `"general"` | User decision: fixed |
| `timeout` | from `search_timeout` setting | Existing timeout setting |

### Response Structure (relevant fields)
```json
{
  "query": "string",
  "answer": "LLM-synthesized answer string (only when include_answer=True)",
  "results": [
    {
      "title": "Page Title",
      "url": "https://example.com/page",
      "content": "Short snippet (always present)",
      "score": 0.95
    }
  ],
  "response_time": 1.23
}
```

### Credit Costs
- `search_depth="basic"`: 1 credit per search
- `search_depth="advanced"`: 2 credits per search
- `include_answer`: No additional credit cost
- Free tier: 1,000 credits/month

### Error Codes
| Code | Meaning | How to Handle |
|------|---------|---------------|
| 401 | Invalid API key | Return `SearchResponse(success=False, error="unauthorized")` |
| 429 | Rate limited | Return `SearchResponse(success=False, error="rate_limited")` |
| 432 | Plan limit exceeded | Return `SearchResponse(success=False, error="plan_limit")` |

## Claude's Discretion: Recommendations

### SDK vs Raw httpx: Use tavily-python SDK

**Decision:** Use `tavily-python` SDK with `AsyncTavilyClient`

**Rationale:**
1. The SDK is thin and uses httpx internally -- same transport the project already depends on
2. Handles Bearer auth headers, error code mapping, parameter validation
3. The `AsyncTavilyClient` creates a persistent `httpx.AsyncClient` with connection pooling
4. Saves ~30 lines of boilerplate (auth headers, payload construction, error mapping)
5. Consistent with project patterns (already uses langchain-anthropic, e2b-code-interpreter SDKs)
6. One-liner search call: `await client.search(query, include_answer=True, max_results=3)`

### Test Strategy: Mock-swap with SDK response fixtures

**Decision:** Mock the `AsyncTavilyClient.search` method in tests, not the HTTP layer

**Rationale:**
1. Mocking at the SDK level is simpler and more stable than mocking httpx responses
2. Create fixtures that mirror real Tavily response structures (with answer field)
3. Test `SearchService.search()` with mocked `AsyncTavilyClient.search()` return values
4. Test `search_web` tool with mocked `SearchService.from_settings()` return values
5. Test error paths: API key not configured, timeout, HTTP errors, missing answer
6. No existing search-specific tests to rewrite (current test files: test_code_checker.py, test_llm_providers.py, test_routing.py -- none test search)

### Answer Injection: Use existing search_results_text path

**Decision:** Return Tavily answer as part of the tool output string, flowing through the existing `_generate_analysis_with_search()` path

**Rationale:**
1. The existing architecture already handles this: `ToolMessage.content` -> `search_results_text` -> system prompt injection
2. No need to add new state fields or modify `da_response_node` logic
3. The Tavily answer appears first in the tool output, followed by source URLs in the existing `"- Title: URL"` format
4. `_extract_sources_from_tool_response()` regex continues to work because the answer text and sources are in separate sections

## Open Questions

1. **AsyncTavilyClient cleanup on shutdown**
   - What we know: The SDK creates an internal `httpx.AsyncClient`. It likely needs explicit cleanup on app shutdown.
   - What's unclear: Whether the SDK exposes a `close()` or `__aexit__` method for cleanup
   - Recommendation: Check if `AsyncTavilyClient` has a close method. If not, instantiating per-call (current Serper pattern) avoids the cleanup issue at the cost of no connection pooling. Given the low search volume (7/day/user), per-call instantiation is acceptable.

2. **Tavily answer quality with basic vs advanced depth**
   - What we know: `include_answer=True` returns a quick answer; `include_answer="advanced"` returns a more detailed one. `search_depth` affects result quality separately.
   - What's unclear: Whether `include_answer=True` (basic) is sufficient quality for the agent context, or if `"advanced"` should be default
   - Recommendation: Start with `include_answer=True` (basic answer) and `search_depth="basic"`. Let the admin escalate via `SEARCH_DEPTH` env var. The answer quality difference can be evaluated post-migration.

## Sources

### Primary (HIGH confidence)
- [Tavily Search API Reference](https://docs.tavily.com/documentation/api-reference/endpoint/search) -- Complete request/response schema, parameters, error codes
- [Tavily Python SDK Reference](https://docs.tavily.com/sdk/python/reference) -- AsyncTavilyClient API, method signatures
- [Tavily API Credits](https://docs.tavily.com/documentation/api-credits) -- Credit costs per search depth
- [tavily-python GitHub (async_tavily.py)](https://github.com/tavily-ai/tavily-python/blob/master/tavily/async_tavily.py) -- AsyncTavilyClient uses httpx internally
- [tavily-python PyPI](https://pypi.org/project/tavily-python/) -- Version 0.7.21, released 2026-01-30
- Existing codebase: `backend/app/services/search.py`, `backend/app/agents/tools/web_search.py`, `backend/app/agents/data_analysis.py`, `backend/app/config.py`, `backend/app/routers/search.py`

### Secondary (MEDIUM confidence)
- [Tavily Query Parameter Optimization](https://help.tavily.com/articles/7879881576-optimizing-your-query-parameters) -- Best practices for search_depth and max_results

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- tavily-python is the official SDK, well-documented, verified via PyPI and GitHub
- Architecture: HIGH -- existing codebase is fully mapped, change surface is small and well-defined
- Pitfalls: HIGH -- error handling, answer field behavior, and credit costs verified via official docs

**Research date:** 2026-02-09
**Valid until:** 2026-03-09 (stable API, monthly SDK releases)
