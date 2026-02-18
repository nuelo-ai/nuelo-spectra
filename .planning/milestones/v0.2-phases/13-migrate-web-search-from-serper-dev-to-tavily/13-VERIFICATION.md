---
phase: 13-migrate-web-search-from-serper-dev-to-tavily
verified: 2026-02-09T21:00:00Z
status: passed
score: 11/11
re_verification: false
---

# Phase 13: Migrate Web Search from Serper.dev to Tavily Verification Report

**Phase Goal:** Replace Serper.dev search provider with Tavily API so the Analyst AI agent receives full page content (not just URL links), enabling higher-quality analysis grounded in actual search result content. Additionally, fix follow-up suggestion chips for MEMORY_SUFFICIENT route responses.

**Verified:** 2026-02-09T21:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

Phase 13 includes two sub-goals:
1. **Primary Goal (13-01):** Migrate from Serper.dev to Tavily API with full page content
2. **Gap Closure Goal (13-02):** Fix MEMORY_SUFFICIENT follow-up suggestions display

### Observable Truths (Plan 13-01: Tavily Migration)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Data Analysis Agent receives Tavily's synthesized answer in its LLM context when web search is used | ✓ VERIFIED | `web_search.py:53` formats output as `"Web search answer for '{query}':\n{result.answer}"`. Flows through `ToolMessage.content` into `search_results_text` (data_analysis.py:185-187), then appended to system prompt in `_generate_analysis_with_search` (data_analysis.py:255-258). Full data flow confirmed. |
| 2 | Search results include source URLs in clickable title + URL format for DataCard display | ✓ VERIFIED | `web_search.py:56-58` formats as `"Sources:\n- {r.title}: {r.url}\n"`. Extraction regex `r"^- (.+?):\s+(https?://\S+)$"` at data_analysis.py:417 successfully parses this format. Pattern compatibility maintained. |
| 3 | GET /search/config returns same response shape using tavily_api_key instead of serper_api_key | ✓ VERIFIED | `search.py:38` checks `configured = bool(settings.tavily_api_key)`. Returns identical schema: `{configured, enabled, daily_quota, used_today, quota_exceeded}` (lines 56-62). API contract preserved. |
| 4 | System gracefully degrades when Tavily API key is missing, quota exceeded, or API unavailable | ✓ VERIFIED | Missing key: `SearchService.from_settings()` returns `None` (search.py:60-61), tool returns "Web search is not configured" (web_search.py:37). API error: caught by `except Exception` (search.py:118-135), returns `SearchResponse(success=False, error=str(e))`, tool returns "Search failed" message (web_search.py:42-44). Quota: handled by existing SearchQuota model (unchanged). |
| 5 | Zero references to Serper.dev remain in the codebase after migration | ✓ VERIFIED | `grep -ri "serper" backend/` returns 0 matches (excluding .pyc files). Serper completely removed from backend codebase. |
| 6 | SEARCH_DEPTH is configurable via .env (basic/advanced) | ✓ VERIFIED | `.env.example:3` has `SEARCH_DEPTH=basic`. config.py:69 defines `search_depth: str = "basic"`. Passed to AsyncTavilyClient at search.py:81 in `search()` method. Configuration chain complete. |
| 7 | Web search queries are logged with credits_used for cost tracking (SEARCH-07) | ✓ VERIFIED | search.py:105 logs `"credits_used": 2 if self.search_depth == "advanced" else 1` in success event JSON. Cost tracking implemented per SEARCH-07 requirement. |

**Score:** 7/7 truths verified for Plan 13-01

### Observable Truths (Plan 13-02: Follow-Up Suggestions Fix)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 8 | MEMORY_SUFFICIENT responses include follow-up suggestion chips | ✓ VERIFIED | Backend: `_build_memory_prompt()` instructs JSON output with "follow_up_suggestions" (data_analysis.py:341-358). Frontend streaming: ChatInterface.tsx:379-380 extracts from da_response event, renders chips at lines 399-413. Frontend persisted: ChatMessage.tsx:161-166 checks for follow_up_suggestions, renders chips at lines 240-252. |
| 9 | Follow-up suggestions display during streaming for MEMORY_SUFFICIENT route | ✓ VERIFIED | ChatInterface.tsx:378-413 extracts `followUpSuggestions` from `analysisEvent?.data?.follow_up_suggestions` and renders chips with "Continue exploring" header when `analysisEvent` exists (stream complete). Chips only appear after streaming completes (`analysisEvent &&` guard at line 399). |
| 10 | Follow-up suggestions display from persisted messages for MEMORY_SUFFICIENT route | ✓ VERIFIED | ChatMessage.tsx:161-166 defines `hasFollowUpSuggestions` check for non-DataCard assistant messages. Lines 240-252 render follow-up chips with identical styling to streaming path. Chips display for persisted messages with `follow_up_suggestions` in metadata_json. |
| 11 | Non-streaming endpoint persists follow_up_suggestions to metadata_json | ✓ VERIFIED | agent_service.py:248 includes `"follow_up_suggestions": result.get("follow_up_suggestions", [])` in metadata_json dict passed to `ChatService.create_message()`. Matches streaming path at line 445. Non-streaming persistence complete. |

**Score:** 4/4 truths verified for Plan 13-02

**Overall Score:** 11/11 truths verified

### Required Artifacts (Plan 13-01)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/services/search.py` | Tavily-backed SearchService with AsyncTavilyClient | ✓ VERIFIED | 136 lines. Imports `AsyncTavilyClient` (L7), instantiates in `__init__` (L45), calls `client.search()` with `include_answer=True` (L79-86). SearchResult has `title` and `url` fields (L13-17). SearchResponse has `answer: str | None` field (L26). Substantive implementation, no stubs. |
| `backend/app/agents/tools/web_search.py` | search_web tool returning Tavily answer + source URLs | ✓ VERIFIED | 67 lines. Formats output as `"Web search answer for '{query}':\n{result.answer}\n\nSources:\n- {title}: {url}\n"` (L52-58). No placeholder returns, full error handling. Substantive implementation. |
| `backend/app/config.py` | tavily_api_key and search_depth settings | ✓ VERIFIED | 92 lines. Defines `tavily_api_key: str = ""` (L68) and `search_depth: str = "basic"` (L69). No `serper_api_key` field exists. Settings class complete. |
| `backend/pyproject.toml` | tavily-python dependency | ✓ VERIFIED | Line 33 contains `"tavily-python>=0.7.0"` in dependencies list. Dependency added. |

### Required Artifacts (Plan 13-02)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/agents/data_analysis.py` | JSON-formatted memory prompt with follow_up_suggestions | ✓ VERIFIED | 423 lines. `_build_memory_prompt()` (L298-358) instructs JSON output with "analysis" and "follow_up_suggestions" keys. JSON schema example at L344-352. Matches data_analysis YAML pattern. |
| `backend/app/services/agent_service.py` | follow_up_suggestions in non-streaming metadata_json | ✓ VERIFIED | Line 248 includes `"follow_up_suggestions": result.get("follow_up_suggestions", [])` in metadata_json for `run_chat_query()`. Matches streaming path. |
| `frontend/src/components/chat/ChatInterface.tsx` | Follow-up chip rendering for MEMORY_SUFFICIENT streaming | ✓ VERIFIED | Lines 378-413 extract `followUpSuggestions` from da_response event and render chips with "Continue exploring" header. Styling matches DataCard chips. |
| `frontend/src/components/chat/ChatMessage.tsx` | Follow-up chip rendering for plain assistant messages | ✓ VERIFIED | Lines 161-166 define `hasFollowUpSuggestions` check. Lines 240-252 render chips for persisted messages with follow_up_suggestions in metadata_json. Independent of DataCard rendering. |

### Key Link Verification (Plan 13-01)

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `search.py` | tavily AsyncTavilyClient | SDK import and search() call | ✓ WIRED | Import at L7: `from tavily import AsyncTavilyClient`. Instantiate at L45: `self.client = AsyncTavilyClient(api_key=api_key)`. Call at L79-86: `await self.client.search(query=query, search_depth=self.search_depth, ..., include_answer=True, ...)`. Full wiring confirmed. |
| `web_search.py` | `search.py` | SearchService.from_settings() factory | ✓ WIRED | Import at L12: `from app.services.search import SearchService`. Factory call at L35: `service = SearchService.from_settings()`. Returns configured client or None. |
| `web_search.py` | `data_analysis.py` | Tool output flows into search_results_text | ✓ WIRED | Tool returns formatted string starting with "Web search answer for" (L53). Captured in ToolMessage.content (data_analysis.py:185), concatenated into search_results_text (L187), appended to system prompt in `_generate_analysis_with_search` (L255-258). Answer injection path complete. |
| `search.py` router | `config.py` | settings.tavily_api_key check | ✓ WIRED | Import at L8: `from app.config import get_settings`. Check at L38: `configured = bool(settings.tavily_api_key)`. Router wired to config. |

### Key Link Verification (Plan 13-02)

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `data_analysis.py` | `_parse_analysis_json` | _build_memory_prompt instructs JSON output | ✓ WIRED | `_build_memory_prompt()` returns prompt with JSON schema including "follow_up_suggestions" key (L341-358). `_parse_analysis_json()` extracts `parsed.get("follow_up_suggestions", [])` (L292). Memory prompt → JSON parser wiring complete. |
| `ChatInterface.tsx` | follow-up chips | Extract from da_response event in memory branch | ✓ WIRED | L379-380: `const followUpSuggestions: string[] | undefined = analysisEvent?.data?.follow_up_suggestions`. L399-413: Conditional render with chips. Streaming path wired. |
| `ChatMessage.tsx` | follow-up chips | Render chips for non-DataCard messages with follow_up_suggestions | ✓ WIRED | L161-166: `hasFollowUpSuggestions` check on metadata_json. L240-252: Conditional render with `onFollowUpClick` handler. Persisted path wired. |

### Requirements Coverage

Phase 13 maintains compatibility with all SEARCH-XX requirements from Phase 11 while upgrading the provider:

| Requirement | Status | Supporting Truths |
|-------------|--------|-------------------|
| SEARCH-01 (web search via API) | ✓ SATISFIED | Truths 1, 2 (Tavily API replaces Serper.dev, provides richer content) |
| SEARCH-02 (agent decides when to search) | ✓ SATISFIED | Unchanged - agent tool-calling logic in data_analysis.py intact (L98-107 binds tools conditionally) |
| SEARCH-03 (sources displayed transparently) | ✓ SATISFIED | Truth 2 (source URLs in "- title: url" format, regex extraction at L417) |
| SEARCH-05 (graceful quota degradation) | ✓ SATISFIED | Truth 4 (quota handled by existing SearchQuota model, quota_exceeded logic in search.py:54) |
| SEARCH-06 (graceful API unavailable degradation) | ✓ SATISFIED | Truth 4 (Exception handling returns success=False, tool shows fallback message) |
| SEARCH-07 (cost tracking logging) | ✓ SATISFIED | Truth 7 (credits_used field in success log at L105) |

No requirements broken or degraded by the migration. Follow-up suggestions fix (13-02) addresses UAT issue from Phase 13 testing.

### Anti-Patterns Found

None detected. Scanned 11 files modified across both plans:

| Pattern | Files Scanned | Matches |
|---------|---------------|---------|
| TODO/FIXME/PLACEHOLDER comments | 11 files | 0 |
| Empty return stubs (return null/{}[]) | 11 files | 0 (empty arrays in error paths are intentional) |
| Console.log-only implementations | 11 files | 0 |
| Orphaned code (exists but not imported) | 11 files | 0 |

All modified files are substantive implementations with proper wiring.

### Commit Verification

All commits from both SUMMARYs verified in git log:

**Plan 13-01 (Tavily Migration):**
- `42872c8` - feat(13-01): rewrite SearchService for Tavily and update config/dependencies
- `5ae3726` - feat(13-01): update tool output format, router key check, remove all Serper references

**Plan 13-02 (Follow-Up Suggestions Fix):**
- `a5193ab` - fix(13-02): fix memory prompt JSON output and non-streaming metadata
- `21d5948` - fix(13-02): add follow-up suggestion chips for MEMORY_SUFFICIENT responses

All 4 commits exist and match SUMMARY descriptions. No orphaned changes.

### Human Verification Required

While automated checks passed, the following runtime tests are recommended:

#### 1. Verify Tavily Answer Injection into Agent Context

**Test:**
1. Set `TAVILY_API_KEY` in `.env` to a valid Tavily API key
2. Run `cd backend && pip install tavily-python` to install the dependency
3. Start backend and upload a dataset
4. Ask a question that triggers web search (e.g., "What is the average industry growth rate for SaaS companies?")
5. Check the agent's response

**Expected:**
- Agent response references web search findings
- Sources section shows clickable URLs
- Response quality higher than with Serper.dev (grounded in actual content, not just links)

**Why human:** Requires runtime environment with Tavily API key and end-to-end agent execution. Automated testing cannot verify LLM response quality improvement.

#### 2. Verify Graceful Degradation

**Test:**
1. Remove `TAVILY_API_KEY` from `.env` (or set to empty string)
2. Ask a question that would normally trigger search
3. Check `/search/config` endpoint response

**Expected:**
- `/search/config` returns `{configured: false, enabled: false, ...}`
- Agent answers without search, no errors
- User sees graceful "search not configured" behavior

**Why human:** Requires runtime testing of error paths with missing configuration.

#### 3. Verify Cost Tracking

**Test:**
1. Set `SEARCH_DEPTH=basic` and perform a search
2. Check backend logs for `credits_used` field
3. Set `SEARCH_DEPTH=advanced` and perform another search
4. Check logs again

**Expected:**
- Basic search logs `"credits_used": 1`
- Advanced search logs `"credits_used": 2`

**Why human:** Requires log inspection during runtime. Automated testing cannot verify log output without running the service.

#### 4. Verify MEMORY_SUFFICIENT Follow-Up Suggestions (End-to-End)

**Test:**
1. Upload a dataset and ask an analysis question
2. Wait for DataCard response with follow-up suggestions
3. Click a follow-up suggestion (triggers MEMORY_SUFFICIENT route on repeat query)
4. Verify follow-up chips appear below the memory response

**Expected:**
- Memory response displays as plain text (no DataCard)
- "Continue exploring" header appears below response
- 2-3 follow-up suggestion chips display with clickable styling
- Chips appear during streaming AND persist after page refresh

**Why human:** Requires full frontend + backend runtime with real LLM to test the Manager Agent routing decision and follow-up rendering. Automated testing cannot verify streaming + persistence + styling in browser.

### Deployment Notes

**User Setup Required for Tavily Migration (13-01):**
1. Run `cd backend && pip install tavily-python` to install new dependency
2. Update `.env` file:
   - Replace `SERPER_API_KEY=...` with `TAVILY_API_KEY=your-tavily-api-key`
   - Add `SEARCH_DEPTH=basic` (or `advanced` for 2x credit cost, higher quality results)
3. Get a Tavily API key from https://tavily.com (free tier: 1000 credits/month)

**User Setup Required for Follow-Up Fix (13-02):**
- No external setup required
- No dependency changes
- Works with existing configuration

---

## Summary

**All 11 must-haves verified.** Phase 13 dual goals fully achieved:

### Primary Goal (13-01): Tavily Migration
- ✓ Tavily API successfully replaces Serper.dev with AsyncTavilyClient
- ✓ Data Analysis Agent receives synthesized answers (not just URL links) in LLM context
- ✓ Source extraction regex compatible with new format
- ✓ Cost tracking via credits_used field (SEARCH-07)
- ✓ Graceful degradation for missing key, quota, and API errors
- ✓ Zero Serper references in backend codebase
- ✓ All configuration migrated to tavily_api_key and search_depth

### Gap Closure Goal (13-02): Follow-Up Suggestions Fix
- ✓ Memory prompt instructs JSON output with "analysis" and "follow_up_suggestions" keys
- ✓ Frontend streaming branch extracts and renders follow-up chips from da_response event
- ✓ Frontend persisted messages render follow-up chips for non-DataCard responses
- ✓ Non-streaming endpoint persists follow_up_suggestions in metadata_json

**Code quality:** No anti-patterns detected. All artifacts substantive and wired. All 4 commits verified.

**Deployment readiness:** Requires `pip install tavily-python` and `.env` update with TAVILY_API_KEY. Documented in 13-01 SUMMARY.

**Ready to proceed** to next phase or v0.2 milestone completion (Phase 12 Production Email is the remaining phase per ROADMAP.md).

---

_Verified: 2026-02-09T21:00:00Z_  
_Verifier: Claude (gsd-verifier)_
