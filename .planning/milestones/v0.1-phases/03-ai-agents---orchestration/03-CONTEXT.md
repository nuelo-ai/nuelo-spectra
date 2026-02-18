# Phase 3: AI Agents & Orchestration - Context

**Gathered:** 2026-02-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Multi-agent system that analyzes uploaded data files and generates validated Python code for data analysis queries. The system consists of 4 agents:
1. **Onboarding Agent** - Triggered during file upload to profile data structure
2. **Coding Agent** - Generates Python code based on user queries during chat
3. **Code Checker Agent** - Validates generated code for safety and correctness
4. **Data Analysis Agent** - Interprets execution results and generates explanations

Onboarding is a separate flow (file upload), while Coding → Code Checker → Execute → Data Analysis happens during chat queries.

</domain>

<decisions>
## Implementation Decisions

### Agent Collaboration Pattern
- **Onboarding Agent:** Independent agent triggered immediately on file upload (separate from chat flow)
- **Chat agents:** Coding Agent → Code Checker Agent (with retry loop) → Execute → Data Analysis Agent
- **Retry loop:** Code Checker validates generated code; if validation fails, routes back to Coding Agent with feedback
- **Architecture:** Independent orchestration logic/engine with clean API interface separation to enable future flexibility (adding new agents/nodes/tools without breaking the interface)
- **Memory scope:** Memory maintained at chat tab level (per-file isolation)

### Data Understanding Flow
- **Onboarding analysis includes:**
  - Structure & types (column names, data types, row count, missing values - pandas.describe() level)
  - Data quality insights (duplicates, outliers, formatting problems, inconsistent values)
  - Semantic understanding (infer column meanings like 'cust_id' = customer identifier, 'amt' = monetary amount)
  - Sample data preview (first few rows for user verification)

- **User context - two-stage gathering:**
  1. **Pre-processing:** User can provide high-level context during upload (e.g., "Sales data from Q4 2025")
  2. **Post-processing:** After Onboarding summary displayed, user can provide agreement or optional clarification
     - Example: "AI: This is data about sales by region. Is that correct or do you want to add more context?"
     - User can agree without feedback, or add clarification like "Correct but data only for year 2025"

- **Refinement handling (v1):** User feedback appended to Onboarding summary and fed to chat agents
  - Note: v2 will ask user if they want to re-run Onboarding Agent with new input or save as additional context

- **Context visibility:** Onboarding Agent's data summary MUST be included in chat agent context
  - Critical for Coding Agent to know: analysis summary, data structure, column meanings/formats, sample data
  - Without this context, code generation quality suffers

### Code Validation Approach
- **Code Checker validates:**
  - Syntax correctness (Python code parses without errors)
  - Library allowlist (only allowed libraries imported - pandas, numpy, etc. from YAML config)
  - Unsafe operations (file deletion, table drops, network calls, eval(), exec())
  - Logical correctness (code actually answers user's query, not just syntactically valid)

- **Validation failure handling:** Send back to Coding Agent with feedback
  - Code Checker provides specific error details to help Coding Agent regenerate correct code

### Claude's Discretion
- Orchestration pattern choice (sequential vs conditional routing with LangGraph)
- Unsafe operation detection method (AST analysis, RestrictedPython, or pattern matching)
- Validation feedback format (structured error types, natural language, or both)
- Execution vs validation failure retry flow details

</decisions>

<specifics>
## Specific Ideas

- **Architecture principle:** "Independent logic/engine while maintaining the interface/api" - ensures flexibility as business rules may change
- **Memory isolation:** Chat memory at tab level (per-file), not global
- **Two-stage context:** Pre-upload context + post-analysis refinement
- **Context is critical:** Onboarding summary must flow to chat agents for quality code generation

</specifics>

<deferred>
## Deferred Ideas

- v2 feature: Ask user whether to re-run Onboarding Agent with new context or just save as additional context (v1 always appends)

</deferred>

---

*Phase: 03-ai-agents---orchestration*
*Context gathered: 2026-02-03*
