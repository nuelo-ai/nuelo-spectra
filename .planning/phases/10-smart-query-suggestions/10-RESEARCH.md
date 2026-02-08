# Phase 10: Smart Query Suggestions - Research

**Researched:** 2026-02-08
**Domain:** LLM-generated suggestions, database schema extension, React empty-state UX, SSE streaming extension
**Confidence:** HIGH

## Summary

Phase 10 adds intelligent, LLM-generated query suggestions at two touchpoints: (1) initial suggestions displayed on empty chat state, generated during onboarding, and (2) follow-up suggestions appended to Data Cards, generated during the Data Analysis Agent response. The implementation spans backend (extending the Onboarding Agent prompt, adding a new `query_suggestions` column to the `files` table, extending the Data Analysis Agent to produce follow-up suggestions) and frontend (new `QuerySuggestions` component replacing the current empty state, follow-up chips at the bottom of `DataCard`, configurable auto-send vs populate-input behavior).

The codebase is well-structured for this feature. The Onboarding Agent already has a dedicated `generate_summary()` method that calls the LLM with data profile JSON -- extending this prompt to also return structured suggestions is straightforward. The `File` model already stores `data_summary` as a Text column; a parallel `query_suggestions` JSON column follows the same pattern. On the frontend, the `ChatInterface` component has a clean `showEmptyState` conditional (line 202-280 in ChatInterface.tsx) that is the exact insertion point for suggestion chips.

**Primary recommendation:** Extend the existing onboarding LLM call to return both summary and structured suggestions in a single response (JSON-structured output), add a `query_suggestions` JSON column to the `files` table, create a new `QuerySuggestions` frontend component rendered in the empty chat state, and extend the Data Analysis Agent prompt to include 2-3 follow-up suggestions in its response.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- LLM-generated from the data profile (columns, types, stats) -- not template-based
- Use real column names but wrap in natural language that explains intent
- Mix of simple and advanced suggestions -- cover beginners and power users
- 5-6 initial suggestions total
- LLM decides categories based on what makes sense for each specific dataset (not fixed General/Benchmarking/Trend)
- Categories shown as grouped headers above chips
- Clickable chips/pills style (compact rounded buttons)
- Grouped under category headers (not flat)
- Centered in empty chat area (like ChatGPT's suggestion layout)
- Generic greeting above chips: "What would you like to know about your data?"
- No loading skeleton needed -- suggestions are pre-generated at upload time
- Generated during onboarding (same LLM call as data summary -- extend onboarding prompt)
- Stored in database alongside data_summary for instant loading
- Shown on empty chat state (zero messages in tab)
- No refresh/regenerate option -- generated once at upload
- Default: auto-send immediately on click (zero friction to first result)
- Configurable in global YAML settings to instead populate chat input for editing before send
- After clicking one suggestion, all remaining chips fade out with animation
- No loading state for suggestions -- already in DB when chat opens
- 2-3 follow-up suggestions shown at bottom of each Data Card
- Based on the analysis just completed (query + result -> natural next steps)
- Same chip/pill visual style as initial suggestions for consistency
- Generated during Data Analysis Agent response (same LLM call, included in stream)
- Clicking a follow-up auto-sends (same behavior as initial suggestions, respects YAML config)

### Claude's Discretion
- Exact category names and distribution of suggestions per category (LLM decides per dataset)

### Deferred Ideas (OUT OF SCOPE)
- Show suggestions in Data Summary panel (info icon on sidebar) -- surface stored suggestions alongside the data profile for re-discovery after initial chat
- Suggestion quality feedback (thumbs up/down) -- could improve generation over time
</user_constraints>

## Standard Stack

### Core (already in codebase)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLAlchemy | (existing) | Database model for `query_suggestions` column | Already used for File model |
| Alembic | (existing) | Database migration for new column | Already used for schema changes |
| FastAPI | (existing) | API endpoint for serving suggestions | Already used for all endpoints |
| Pydantic | (existing) | Response schema for suggestions | Already used for all schemas |
| LangChain | (existing) | LLM invocation for suggestion generation | Already used for all agents |
| React/Next.js | 19/16 | Frontend component for suggestion UI | Already the frontend framework |
| TanStack Query | 5.x | Data fetching for suggestions | Already used for file/chat data |
| shadcn/ui | (existing) | Badge component for chip styling | Already used throughout UI |
| Zustand | 5.x | Tab store already manages chat state | Already used for tab management |
| Tailwind CSS | 4.x | Styling for chips, animations | Already used for all styling |

### No New Dependencies Required
This phase requires zero new library installations. Everything is built using the existing stack.

## Architecture Patterns

### Backend: Suggestion Data Flow

```
Upload File
    |
    v
Onboarding Agent (extended prompt)
    |
    +-- data_summary (Text, existing)
    +-- query_suggestions (JSON, NEW)
    |       {
    |         "categories": [
    |           {
    |             "name": "Revenue Insights",
    |             "suggestions": [
    |               "See how **Revenue** breaks down across different **Region** categories",
    |               "Find the top 10 products by **Total Sales**"
    |             ]
    |           },
    |           ...
    |         ]
    |       }
    |
    v
Stored in files table -> Served via GET /files/{id}/summary (extended)
```

### Backend: Follow-up Suggestion Data Flow

```
User Query -> Agent Pipeline -> Data Analysis Agent (extended prompt)
    |
    v
SSE Stream includes follow_up_suggestions in response metadata
    {
      "analysis": "...",
      "follow_up_suggestions": [
        "Now filter these results to show only Q4 2025",
        "Compare these totals across different **Region** values"
      ]
    }
    |
    v
Frontend extracts from stream events + persisted in chat_messages.metadata_json
```

### Recommended Project Structure (changes only)

```
backend/
  app/
    agents/
      onboarding.py          # MODIFY: extend prompt for suggestions
      data_analysis.py        # MODIFY: extend prompt for follow-ups
    config/
      prompts.yaml            # MODIFY: add suggestion instructions to prompts
    models/
      file.py                 # MODIFY: add query_suggestions column
    schemas/
      file.py                 # MODIFY: add query_suggestions to response schemas
    routers/
      files.py                # MODIFY: include suggestions in summary endpoint
    config.py                 # MODIFY: add suggestion_auto_send setting

  alembic/
    versions/
      xxx_add_query_suggestions.py  # NEW: migration

frontend/
  src/
    components/
      chat/
        QuerySuggestions.tsx   # NEW: suggestion chips component
        ChatInterface.tsx      # MODIFY: render QuerySuggestions in empty state
        DataCard.tsx           # MODIFY: add follow-up chips at bottom
    types/
      file.ts                 # MODIFY: add query_suggestions to types
      chat.ts                 # MODIFY: add follow_up_suggestions to stream events
    hooks/
      useFileManager.ts       # Already has useFileSummary -- will carry suggestions
```

### Pattern 1: Extending Onboarding Prompt for Structured JSON Output
**What:** Modify the onboarding prompt to return both data_summary and query_suggestions in a structured JSON format, then parse and store separately.
**When to use:** When you need the LLM to generate multiple distinct outputs from the same context.
**Implementation approach:**

The current `OnboardingAgent.generate_summary()` returns a plain text summary. The modification needs to:
1. Update the system prompt to request JSON-structured output with `summary` and `suggestions` fields
2. Parse the JSON response in `generate_summary()`
3. Return both values via `OnboardingResult`
4. Save `query_suggestions` alongside `data_summary` in `run_onboarding()`

**Critical detail:** The existing `OnboardingResult` dataclass needs a new `query_suggestions` field. The `run_onboarding()` function in `agent_service.py` already saves `data_summary` to the file record -- add `query_suggestions` in the same commit.

### Pattern 2: Extending Data Analysis Agent for Follow-up Suggestions
**What:** Modify the Data Analysis Agent prompt to include 2-3 follow-up suggestions at the end of its response in a structured format.
**When to use:** When generating contextual next-step recommendations based on completed analysis.
**Implementation approach:**

The Data Analysis Agent's standard mode (not MEMORY_SUFFICIENT) already receives `user_query`, `executed_code`, and `execution_result`. The prompt extension asks for follow-up suggestions. Two approaches:

Option A (Recommended): Include follow-up suggestions as a structured JSON block at the end of the analysis text, delimited by a marker like `<!-- FOLLOW_UP_SUGGESTIONS -->`. Parse server-side before streaming.

Option B: Request the LLM to return a JSON object with `analysis` and `follow_up_suggestions` fields. This requires changing the response parsing but gives cleaner separation.

**Recommendation:** Option B is cleaner. Modify the prompt to return JSON with both `analysis` and `follow_up_suggestions` keys. Parse in the `data_analysis_agent` function. Include `follow_up_suggestions` in the state update so it flows through the stream events.

### Pattern 3: YAML-Configurable Behavior Toggle
**What:** A global setting in `prompts.yaml` (or `config.py` via `.env`) that controls whether clicking a suggestion auto-sends or populates the input.
**When to use:** When behavior needs to be configurable without code changes.
**Implementation approach:**

Add to `config.py`:
```python
# Suggestions
suggestion_auto_send: bool = True  # False = populate input instead
```

Serve this setting to the frontend via a new lightweight endpoint or include it in an existing config endpoint. The frontend reads this setting once and passes it to `QuerySuggestions` as a prop.

**Alternative:** Store in `prompts.yaml` under a `suggestions` key and add a new getter in `config.py`. This keeps it with the other agent configuration.

### Pattern 4: Fade-Out Animation After Selection
**What:** When a user clicks one suggestion, remaining chips fade out with animation before disappearing.
**When to use:** For visual polish indicating suggestions are consumed.
**Implementation approach:**

```tsx
const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);

// When a chip is clicked:
setSelectedSuggestion(text);
// After animation delay:
setTimeout(() => setShowSuggestions(false), 300);
```

Use Tailwind's `transition-opacity duration-300` with conditional `opacity-0` class on unselected chips. The selected chip could briefly highlight before all fade.

### Anti-Patterns to Avoid
- **Separate LLM call for suggestions:** The decision is locked -- suggestions must be generated in the same call as data summary. A separate call wastes tokens and adds latency.
- **Template-based suggestions:** The decision is locked -- suggestions must be LLM-generated from the data profile, not canned templates.
- **Client-side suggestion generation:** Suggestions are pre-generated at upload time and stored in the database. Do not generate them on the frontend.
- **Hard-coding category names:** Categories are LLM-determined per dataset. Do not use fixed "General Analysis / Benchmarking / Trend" labels (the CONTEXT.md overrides the original REQUIREMENTS.md on this point).
- **Loading skeletons for suggestions:** Decision explicitly says no loading skeleton needed since suggestions are pre-generated at upload time.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chip/pill UI component | Custom CSS button styling | shadcn `Badge` with `cursor-pointer` + click handler | Badge already has the rounded pill aesthetic, just needs interactivity |
| Fade animation | Manual DOM manipulation | Tailwind `transition-opacity duration-300` + conditional classes | CSS transitions are more performant than JS animations |
| JSON parsing from LLM | Regex-based text extraction | Request JSON output + `json.loads()` with fallback | LLMs with structured output requests are reliable; regex breaks on edge cases |
| Category grouping | Manual array grouping | Array.reduce or Object.groupBy (or LLM returns pre-grouped) | LLM should return pre-grouped structure, no client-side grouping needed |

**Key insight:** The hardest part of this feature is prompt engineering, not code. The actual code changes are mechanical (add column, extend prompt, parse JSON, render chips). Getting the LLM to generate genuinely useful, well-categorized suggestions from a data profile is the creative challenge.

## Common Pitfalls

### Pitfall 1: LLM Returns Malformed JSON
**What goes wrong:** The onboarding LLM call returns text that isn't valid JSON, or returns JSON with unexpected structure.
**Why it happens:** LLMs can be unreliable with strict JSON formatting, especially with older or smaller models.
**How to avoid:**
1. Use a clear system prompt with exact JSON schema and example
2. Parse with `json.loads()` inside a try/except
3. On parse failure, fall back to generating suggestions in a separate call, or store empty suggestions and let the chat work without them
4. Consider using `response_format={"type": "json_object"}` if supported by the provider (Anthropic does not natively support this, but structured output via prompt engineering works well with Claude)
**Warning signs:** `json.JSONDecodeError` in onboarding logs; suggestions not appearing in frontend.

### Pitfall 2: Suggestions Not Available When Chat Opens
**What goes wrong:** The empty chat state checks for suggestions, but they aren't in the database yet because onboarding is still running in the background.
**Why it happens:** The upload endpoint triggers onboarding as a background task (`asyncio.create_task`). The frontend may open the chat tab before onboarding completes.
**How to avoid:** This is already handled by the existing pattern -- `useFileSummary` polls every 3 seconds until `data_summary` is available. Since suggestions are stored alongside the summary, they'll arrive at the same time. The empty chat state should check for suggestions and show the default "Ask a question" text if not yet available (which it already does). No special handling needed.
**Warning signs:** N/A -- the existing polling pattern handles this.

### Pitfall 3: Category Names vs Requirements Mismatch
**What goes wrong:** The REQUIREMENTS.md says categories should be "General Analysis (2), Benchmarking (2), Trend/Predictive (2)" but the CONTEXT.md says "LLM decides categories based on what makes sense for each specific dataset."
**Why it happens:** The discuss phase refined the original requirements.
**How to avoid:** CONTEXT.md takes precedence. The LLM decides category names and distribution. The prompt should say "organize into 2-4 meaningful categories" rather than prescribing specific category names. The validation should check that the response has grouped suggestions, not that specific category names exist.
**Warning signs:** Hardcoded category checks in tests.

### Pitfall 4: Follow-up Suggestions Breaking the Stream
**What goes wrong:** Adding `follow_up_suggestions` to the Data Analysis Agent's response changes the stream event structure, breaking the frontend parser.
**Why it happens:** The frontend's `useSSEStream` and `ChatInterface` parse specific fields from `node_complete` events.
**How to avoid:**
1. Add `follow_up_suggestions` as an additional field in the `data_analysis` node's state update
2. The `node_complete` event in `agent_service.py` line 384-388 filters to specific keys -- add `follow_up_suggestions` to the allowlist
3. Frontend's stream event handling extracts the new field from the data_analysis node_complete event
**Warning signs:** Follow-up suggestions appearing in console logs but not rendering.

### Pitfall 5: Auto-Send Creates Race Condition with Suggestion Fade
**What goes wrong:** Clicking a suggestion immediately sends it and starts streaming, but the fade animation hasn't completed. The streaming DataCard appears while chips are still animating.
**Why it happens:** Auto-send fires immediately on click; fade animation takes 300ms.
**How to avoid:** Fire the `handleSend` immediately on click (user expects instant response). Run the fade animation concurrently but don't wait for it. The streaming UI will naturally push the suggestions area out of view as the DataCard appears. Consider: once streaming starts (`isStreaming=true`), hide suggestions entirely regardless of animation state.
**Warning signs:** Visual jank with overlapping animations.

### Pitfall 6: Existing Data Files Have No Suggestions
**What goes wrong:** Files uploaded before Phase 10 have `query_suggestions = NULL` in the database. The frontend crashes or shows broken UI.
**Why it happens:** New column added with migration, existing rows have NULL.
**How to avoid:**
1. Make `query_suggestions` nullable (which it should be)
2. Frontend checks `if (suggestions && suggestions.categories.length > 0)` before rendering
3. Fall back to existing empty state if no suggestions
4. Users can re-upload files to get suggestions (no regeneration needed for MVP per decision)
**Warning signs:** `TypeError: Cannot read property 'categories' of null` in frontend console.

### Pitfall 7: Suggestion Text Too Long for Chip Display
**What goes wrong:** LLM generates verbose suggestions that wrap to multiple lines, breaking the chip/pill visual design.
**Why it happens:** Without length constraints in the prompt, the LLM may generate paragraph-length suggestions.
**How to avoid:**
1. Add explicit instruction in the prompt: "Each suggestion should be 8-15 words maximum"
2. Frontend truncation with ellipsis as a safety net (`truncate` Tailwind class)
3. Show full text in tooltip on hover
**Warning signs:** Chips that are wider than the container or wrap to multiple lines.

### Pitfall 8: Onboarding Prompt Becomes Too Long
**What goes wrong:** Adding suggestion generation instructions to the onboarding prompt pushes it beyond comfortable limits, increasing token usage and potentially reducing quality.
**Why it happens:** The existing prompt is already 7 items long. Adding detailed suggestion instructions could make it unfocused.
**How to avoid:** Keep suggestion instructions concise. The prompt should specify the output format (JSON with summary and suggestions keys) and a brief instruction about suggestion quality. The example JSON in the prompt is more effective than verbose instructions. Current `max_tokens: 1500` may need to increase to `2500-3000` to accommodate the additional JSON output.
**Warning signs:** Truncated JSON responses; suggestions cut off mid-sentence.

## Code Examples

### Example 1: Extended Onboarding Prompt (prompts.yaml)
```yaml
onboarding:
  provider: anthropic
  model: claude-sonnet-4-20250514
  temperature: 0.0
  max_tokens: 3000  # Increased from 1500
  system_prompt: |
    You are a Data Onboarding Agent for Spectra analytics platform.
    Analyze the uploaded dataset and return a JSON response with two sections.

    Return ONLY valid JSON in this exact format:
    {
      "summary": "Your comprehensive data summary here...",
      "suggestions": {
        "categories": [
          {
            "name": "Category Name",
            "suggestions": [
              "Natural language suggestion using **ColumnName** with intent",
              "Another suggestion"
            ]
          }
        ]
      }
    }

    SUMMARY SECTION:
    1. Structure & Types: Column names, data types, row count, missing values
    2. Data Quality: Duplicates, outliers, formatting issues
    3. Semantic Understanding: Infer what each column represents
    4. Sample Preview: Show first 3 rows formatted as a table

    SUGGESTIONS SECTION:
    - Generate 5-6 query suggestions organized into 2-4 categories
    - Categories should be meaningful for THIS specific dataset
    - Use real column names wrapped in **bold** within natural language
    - Mix simple questions (beginners) and advanced analysis (power users)
    - Each suggestion: 8-15 words, explains intent not just operation
    - Feel like a knowledgeable analyst looking at the data for the first time

    If user provided context, incorporate it into both summary and suggestions.
```

### Example 2: File Model Extension (models/file.py)
```python
# Add to File model
query_suggestions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

### Example 3: OnboardingResult Extension (agents/onboarding.py)
```python
@dataclass
class OnboardingResult:
    data_summary: str
    data_profile: dict
    sample_data: str
    query_suggestions: dict | None = None  # NEW
```

### Example 4: Parse JSON from LLM Response (agents/onboarding.py)
```python
async def generate_summary(self, profile: dict, user_context: str) -> tuple[str, dict | None]:
    # ... existing LLM setup ...
    response = await asyncio.to_thread(llm.invoke, messages)

    # Parse JSON response
    try:
        parsed = json.loads(response.content)
        summary = parsed.get("summary", response.content)
        suggestions = parsed.get("suggestions", None)
    except json.JSONDecodeError:
        # Fallback: treat entire response as summary, no suggestions
        summary = response.content
        suggestions = None

    return summary, suggestions
```

### Example 5: FileSummaryResponse Extension (schemas/file.py)
```python
class FileSummaryResponse(BaseModel):
    data_summary: str | None
    user_context: str | None
    query_suggestions: dict | None = None  # NEW
```

### Example 6: QuerySuggestions Component (frontend)
```tsx
interface SuggestionCategory {
  name: string;
  suggestions: string[];
}

interface QuerySuggestionsProps {
  categories: SuggestionCategory[];
  onSelect: (suggestion: string) => void;
  autoSend?: boolean;
}

function QuerySuggestions({ categories, onSelect, autoSend = true }: QuerySuggestionsProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [visible, setVisible] = useState(true);

  const handleClick = (suggestion: string) => {
    setSelected(suggestion);
    onSelect(suggestion);
    // Fade out remaining chips
    setTimeout(() => setVisible(false), 300);
  };

  if (!visible) return null;

  return (
    <div className="flex flex-col items-center gap-6 max-w-lg mx-auto">
      <p className="text-muted-foreground text-lg font-medium">
        What would you like to know about your data?
      </p>
      {categories.map((category) => (
        <div key={category.name} className="w-full space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground text-center">
            {category.name}
          </h3>
          <div className="flex flex-wrap justify-center gap-2">
            {category.suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleClick(suggestion)}
                className={`
                  px-4 py-2 rounded-full border text-sm
                  hover:bg-accent hover:border-primary/30
                  transition-all duration-300
                  ${selected && selected !== suggestion ? 'opacity-0' : 'opacity-100'}
                  ${selected === suggestion ? 'bg-primary text-primary-foreground' : 'bg-background'}
                `}
              >
                <ReactMarkdown components={{ p: ({children}) => <>{children}</> }}>
                  {suggestion}
                </ReactMarkdown>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Example 7: Follow-up Suggestions in Data Analysis Agent
```python
# In data_analysis_agent(), standard mode section:
system_prompt = system_prompt_template.format(
    user_query=state["user_query"],
    executed_code=state.get("generated_code", "No code available"),
    execution_result=state.get("execution_result", "No result available")
)

# LLM returns JSON with both analysis and follow_up_suggestions
response = await llm.ainvoke(messages)

try:
    parsed = json.loads(response.content)
    analysis = parsed.get("analysis", response.content)
    follow_ups = parsed.get("follow_up_suggestions", [])
except json.JSONDecodeError:
    analysis = response.content
    follow_ups = []

return {
    "analysis": analysis,
    "final_response": analysis,
    "follow_up_suggestions": follow_ups,  # NEW - flows through stream
    "messages": [AIMessage(content=analysis)],
}
```

### Example 8: Follow-up Chips in DataCard
```tsx
// At the bottom of DataCard, after the Analysis section:
{followUpSuggestions && followUpSuggestions.length > 0 && !isStreaming && (
  <div className="space-y-2 pt-2 border-t">
    <h4 className="text-sm font-medium text-muted-foreground">Continue exploring</h4>
    <div className="flex flex-wrap gap-2">
      {followUpSuggestions.map((suggestion) => (
        <button
          key={suggestion}
          onClick={() => onFollowUpClick?.(suggestion)}
          className="px-3 py-1.5 rounded-full border text-xs
            hover:bg-accent hover:border-primary/30 transition-all duration-200"
        >
          {suggestion}
        </button>
      ))}
    </div>
  </div>
)}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded template suggestions | LLM-generated from data profile | This phase | Suggestions are relevant to actual data |
| Separate API call for suggestions | Same LLM call as data summary | This phase | No extra latency or token cost |
| Fixed category names | LLM-determined categories | This phase (CONTEXT.md override) | Better categorization per dataset |

**Note on REQUIREMENTS.md vs CONTEXT.md:** The original SUGGEST-02 requirement specifies "3 categories: General Analysis (2), Benchmarking (2), Trend/Predictive (2)". The CONTEXT.md discussion explicitly overrides this to "LLM decides categories based on what makes sense for each specific dataset." CONTEXT.md decisions take precedence.

## Key Integration Points

### 1. Database Migration
- Add `query_suggestions` JSON column to `files` table (nullable)
- Use Alembic: `alembic revision --autogenerate -m "add_query_suggestions_to_files"`
- Run: `alembic upgrade head`

### 2. Onboarding Agent Changes
- Modify `generate_summary()` to return both summary and suggestions
- Modify `OnboardingResult` to carry suggestions
- Modify `run_onboarding()` in `agent_service.py` to save suggestions to file record
- Increase `max_tokens` from 1500 to ~3000

### 3. File API Changes
- Extend `FileSummaryResponse` to include `query_suggestions`
- The existing `GET /files/{id}/summary` endpoint automatically picks up new fields

### 4. Frontend Empty State
- Replace the existing empty state in `ChatInterface.tsx` (lines 264-280) with `QuerySuggestions` component
- Component fetches suggestions from the same `useFileSummary` hook (already polls for data_summary)
- When suggestion clicked: call `handleSend(suggestion)` if auto-send, or `setMessage(suggestion)` for input population

### 5. Data Analysis Agent Changes
- Extend prompt to request follow-up suggestions
- Parse response to extract follow-up suggestions
- Add `follow_up_suggestions` to state return dict
- Add `follow_up_suggestions` to the stream event allowlist in `agent_service.py`

### 6. DataCard Changes
- Accept new `followUpSuggestions` prop
- Render follow-up chips at the bottom
- Handle click to send query (same path as initial suggestions)

### 7. ChatMessage Metadata Storage
- Follow-up suggestions are persisted in `chat_messages.metadata_json` alongside existing fields
- This allows follow-up chips to appear on re-rendered messages (page refresh)

### 8. YAML Configuration
- Add `suggestion_auto_send: true` to settings (or `prompts.yaml` under a `suggestions` key)
- Serve to frontend via a config endpoint or inline in file summary response

## Open Questions

1. **Should the auto-send config be served from backend or hardcoded frontend-side initially?**
   - What we know: The decision says "configurable in global YAML settings"
   - What's unclear: Whether to build a full config endpoint or just add it to an existing response
   - Recommendation: Add it to the `/files/{id}/summary` response as `suggestion_config: {auto_send: true}` for simplicity. Can be promoted to a dedicated config endpoint later.

2. **How to handle follow-up suggestions for MEMORY_SUFFICIENT route?**
   - What we know: Follow-up suggestions are generated during Data Analysis Agent response. Memory route also goes through Data Analysis Agent.
   - What's unclear: Should memory-route responses also get follow-up suggestions?
   - Recommendation: Yes, include follow-up suggestions for memory route too. The context is available. But they render as plain text message, not DataCard -- so follow-up chips need to work in both ChatMessage and DataCard contexts.

3. **Should existing files get suggestions via re-onboarding?**
   - What we know: Decision says "generated once at upload, no refresh option"
   - What's unclear: How to handle files already uploaded before Phase 10
   - Recommendation: No automatic back-fill. Existing files show the current empty state (no suggestions). Users can re-upload if they want suggestions. This avoids triggering LLM calls for all existing files.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `backend/app/agents/onboarding.py` -- current onboarding flow and LLM invocation pattern
- Codebase analysis: `backend/app/models/file.py` -- current File model structure (data_summary Text column pattern)
- Codebase analysis: `backend/app/config/prompts.yaml` -- current agent prompt structure and configuration
- Codebase analysis: `backend/app/services/agent_service.py` -- current `run_onboarding()` flow and `run_chat_query_stream()` event structure
- Codebase analysis: `frontend/src/components/chat/ChatInterface.tsx` -- current empty state and streaming UI
- Codebase analysis: `frontend/src/components/chat/DataCard.tsx` -- current DataCard structure
- Codebase analysis: `frontend/src/hooks/useFileManager.ts` -- existing `useFileSummary` polling pattern
- Codebase analysis: `backend/app/agents/data_analysis.py` -- current Data Analysis Agent structure
- Codebase analysis: `backend/app/agents/state.py` -- current ChatAgentState TypedDict
- Codebase analysis: `backend/alembic/` -- existing migration infrastructure

### Secondary (MEDIUM confidence)
- CONTEXT.md discussion decisions -- LLM-decided categories, auto-send behavior, fade animation
- REQUIREMENTS.md SUGGEST-01 through SUGGEST-06 -- formal requirement definitions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, all changes use existing patterns
- Architecture: HIGH - Clear integration points, well-understood codebase patterns
- Pitfalls: HIGH - Identified from direct codebase analysis (nullable columns, background onboarding, stream event allowlist)
- Prompt engineering: MEDIUM - LLM JSON output reliability varies; needs fallback handling

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (stable codebase, no external dependency changes expected)
