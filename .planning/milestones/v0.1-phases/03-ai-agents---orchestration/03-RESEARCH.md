# Phase 3: AI Agents & Orchestration - Research

**Researched:** 2026-02-03
**Domain:** Multi-agent orchestration with LangGraph for data analysis code generation
**Confidence:** HIGH

## Summary

This phase implements a 4-agent system (Onboarding, Coding, Code Checker, Data Analysis) orchestrated with LangGraph to generate and validate Python code for data analysis queries. The standard approach uses LangGraph 1.0 (latest LTS release: 1.0.7) with conditional routing, retry loops, and thread-scoped state management. Code validation uses AST analysis with library whitelists rather than language-level sandboxing, which is fundamentally insecure in Python.

Key architecture decisions are already locked in (see CONTEXT.md): 4 specific agents with defined collaboration patterns, retry loops for validation failures, per-chat-tab memory isolation, and YAML-based configuration for prompts and allowlists. Research focuses on the implementation details marked as "Claude's Discretion": orchestration patterns, AST validation methods, and retry flow mechanics.

The ecosystem is mature as of 2026. LangGraph 1.0 is production-ready with LTS support, LangSmith provides integrated observability with zero-code tracing, and AST-based validation is the proven standard for detecting hallucinated pandas functions (87.6% recall per recent 2026 research). Recent CVE-2026-0863 reinforces that language-level sandboxing is insufficient - validation must use AST + OS-level isolation.

**Primary recommendation:** Use LangGraph 1.0 with conditional routing (not sequential chains), AST-based validation with library allowlists in YAML, bounded retry loops with hard max_steps=3, PostgreSQL checkpointer for production thread isolation, and LangSmith observability from day one.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| langgraph | 1.0.7 | Multi-agent orchestration framework | LTS release (v1.0), production-ready, fastest framework with lowest latency in 2026 benchmarks, powers agents at Uber/LinkedIn/Klarna |
| langchain-core | 0.3+ | Foundation for LangChain ecosystem | Required dependency for LangGraph, provides base abstractions |
| langsmith | Latest | Agent observability & tracing | Zero-code integration with LangGraph, automatic trace capture for all LLM calls/tool invocations |
| pyyaml | 6.0+ | YAML configuration parsing | Standard for prompt/config management, supports comments and multi-line strings |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langgraph-checkpoint-postgres | 2.0+ | PostgreSQL persistence for state | Production deployments requiring thread isolation and durability |
| langgraph-checkpoint-sqlite | 2.0+ | SQLite persistence for state | Local development and testing (NOT production) |
| pandas | 2.0+ | Data analysis library | Already in project; needed for Onboarding Agent data profiling |
| pydantic | 2.0+ | State schema validation | Define typed state objects for LangGraph agents |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LangGraph | LangChain LCEL chains | Chains lack conditional routing and retry loops; not suitable for multi-agent validation workflows |
| PostgreSQL checkpointer | Redis checkpointer | Redis supports TTL expiration but PostgreSQL integrates better with existing FastAPI/SQLAlchemy stack |
| AST validation | RestrictedPython | RestrictedPython more complex (full AST transformation), AST visitor pattern sufficient for allowlist checking |
| LangSmith | Langfuse | Both viable; LangSmith has tighter LangGraph integration with zero-code setup |

**Installation:**
```bash
pip install langgraph==1.0.7 langgraph-checkpoint-postgres langsmith pyyaml
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── agents/
│   ├── __init__.py
│   ├── state.py              # Pydantic state schemas
│   ├── onboarding.py          # Onboarding Agent (independent)
│   ├── coding.py              # Coding Agent
│   ├── code_checker.py        # Code Checker Agent + AST validator
│   ├── data_analysis.py       # Data Analysis Agent
│   └── graph.py               # LangGraph workflow assembly
├── config/
│   ├── prompts.yaml           # Agent system prompts
│   └── allowlist.yaml         # Allowed libraries/functions
└── services/
    └── agent_service.py       # Service layer for graph invocation
```

### Pattern 1: Conditional Routing with Command Objects
**What:** Nodes return `Command[Literal["node1", "node2"]]` to declare routing destinations, making control flow explicit and type-safe.

**When to use:** For validation loops where Code Checker must route to either "execute" or "retry_coding" based on validation results.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph
from langgraph.types import Command
from typing import Literal

def code_checker_node(state: AppState) -> Command[Literal["execute", "retry_coding"]]:
    """Validate generated code and route based on result."""
    validation = validate_code(state["generated_code"])

    if validation.is_valid:
        return Command(goto="execute", update={"validation_status": "passed"})
    else:
        return Command(
            goto="retry_coding",
            update={
                "validation_errors": validation.errors,
                "error_count": state.get("error_count", 0) + 1
            }
        )
```

### Pattern 2: Bounded Retry Loops with Hard Stops
**What:** Use max_steps counter in state to prevent infinite retry loops. Circuit breaker halts execution after N attempts.

**When to use:** Always, for any retry mechanism. Default to max_steps=3 (prevents runaway costs).

**Example:**
```python
# Source: https://dev.to/aiengineering/a-beginners-guide-to-handling-errors-in-langgraph-with-retry-policies-h22
from typing import TypedDict

class AppState(TypedDict):
    error_count: int
    max_steps: int
    # ... other fields

def should_retry(state: AppState) -> Literal["halt", "continue"]:
    """Check if retry should continue or halt."""
    if state.get("error_count", 0) >= state.get("max_steps", 3):
        return "halt"
    return "continue"

# In graph construction
graph.add_conditional_edges(
    "code_checker",
    should_retry,
    {"continue": "coding_agent", "halt": "report_error"}
)
```

### Pattern 3: Thread-Scoped State Isolation
**What:** Use LangGraph checkpointers with thread_id to maintain per-conversation memory. Each file upload gets unique thread_id.

**When to use:** Always. Prevents state bleed between chat tabs and enables concurrent user sessions.

**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/memory
from langgraph.checkpoint.postgres import PostgresSaver

# Initialize checkpointer (call .setup() once)
checkpointer = PostgresSaver.from_conn_string(postgres_url)
await checkpointer.setup()  # Creates required tables

# Compile graph with checkpointer
graph = StateGraph(AppState)
# ... add nodes ...
app = graph.compile(checkpointer=checkpointer)

# Invoke with unique thread_id per chat tab
config = {"configurable": {"thread_id": f"file_{file_id}_user_{user_id}"}}
result = await app.ainvoke({"user_query": query}, config)
```

### Pattern 4: AST-Based Code Validation
**What:** Use Python's `ast` module with `NodeVisitor` pattern to detect disallowed imports and function calls. Safer than execution or regex.

**When to use:** For Code Checker validation. Validates syntax, library allowlist, and detects unsafe operations (eval, exec, file ops).

**Example:**
```python
# Source: https://docs.python.org/3/library/ast.html + https://arxiv.org/abs/2601.19106
import ast
from typing import Set, List

class CodeValidator(ast.NodeVisitor):
    """Validate generated code against allowlist."""

    def __init__(self, allowed_modules: Set[str], allowed_functions: Set[str]):
        self.allowed_modules = allowed_modules
        self.allowed_functions = allowed_functions
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import):
        """Check import statements."""
        for alias in node.names:
            if alias.name not in self.allowed_modules:
                self.errors.append(f"Disallowed import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Check from...import statements."""
        if node.module not in self.allowed_modules:
            self.errors.append(f"Disallowed module: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Check for dangerous function calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__"}:
                self.errors.append(f"Unsafe function: {node.func.id}")
        self.generic_visit(node)

def validate_code(code: str, allowlist: dict) -> ValidationResult:
    """Validate Python code using AST analysis."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return ValidationResult(is_valid=False, errors=[f"Syntax error: {e}"])

    validator = CodeValidator(
        allowed_modules=set(allowlist["modules"]),
        allowed_functions=set(allowlist["functions"])
    )
    validator.visit(tree)

    return ValidationResult(
        is_valid=len(validator.errors) == 0,
        errors=validator.errors
    )
```

### Pattern 5: YAML Configuration for Prompts
**What:** Store agent system prompts and allowlists in YAML files for iteration without code changes.

**When to use:** Always. Enables prompt engineering iterations by non-developers.

**Example:**
```yaml
# Source: https://empathyfirstmedia.com/yaml-files-ai-agents/
# config/prompts.yaml
agents:
  onboarding:
    system_prompt: |
      You are a Data Onboarding Agent. Analyze the uploaded dataset and provide:
      1. Structure (columns, types, row count)
      2. Data quality issues (missing values, duplicates, outliers)
      3. Semantic understanding (infer column meanings)
      4. Sample data preview

      Be concise but thorough. Flag any quality concerns.

  coding:
    system_prompt: |
      You are a Python Coding Agent. Generate pandas code to answer the user's query.

      Context available:
      - Dataset structure: {data_summary}
      - User context: {user_context}

      Requirements:
      - Use ONLY pandas and numpy
      - Store final result in variable 'result'
      - Handle missing values gracefully
      - No file I/O or network calls

# config/allowlist.yaml
allowed_libraries:
  - pandas
  - numpy
  - datetime
  - math

unsafe_operations:
  - eval
  - exec
  - __import__
  - open
  - compile
```

### Pattern 6: LangSmith Integration for Observability
**What:** Enable zero-code tracing with environment variables. Captures all LLM calls, tool invocations, and intermediate states.

**When to use:** From day one. Critical for debugging multi-agent workflows and monitoring token costs.

**Example:**
```python
# Source: https://docs.langchain.com/langsmith/env-var
# Set environment variables (or in .env file)
import os

os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGSMITH_API_KEY"] = "your-api-key"
os.environ["LANGSMITH_PROJECT"] = "spectra-agents"

# No code changes needed - LangGraph automatically traces
# View traces at: https://smith.langchain.com/
```

### Anti-Patterns to Avoid
- **Sequential chains without conditional routing:** LangChain LCEL chains can't handle retry loops. Use LangGraph conditional edges.
- **Language-level Python sandboxing:** RestrictedPython and similar tools are fundamentally insecure (CVE-2026-0863). Use AST validation + OS-level isolation (Phase 5).
- **Unbounded retry loops:** Always add max_steps counter. Default to 3 retries to prevent infinite loops and runaway costs.
- **Global/shared state across conversations:** Always use thread-scoped checkpointers with unique thread_id per chat tab.
- **SQLite checkpointer in production:** Async SQLite has poor write performance. Use PostgreSQL for production.
- **Formatting prompts in state:** Store raw data in state, format prompts inside nodes. Enables flexibility for different formatting needs.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-agent orchestration | Custom agent router with if/else | LangGraph conditional edges | Handles state persistence, retry loops, observability, and complex routing patterns out of the box |
| Code validation | Regex pattern matching | Python `ast` module + NodeVisitor | Regex misses edge cases; AST understands syntax and semantics. Recent research shows 87.6% recall for hallucination detection. |
| Agent tracing/debugging | Custom logging | LangSmith observability | Zero-code integration, captures full reasoning traces, visualizes graphs, tracks token costs automatically |
| Prompt management | Hardcoded strings in code | YAML configuration files | Enables iteration without redeployment, supports comments/documentation, non-developers can tune prompts |
| State persistence | In-memory dicts | LangGraph checkpointers (PostgreSQL) | Handles concurrency, thread isolation, durability, and resumption automatically |
| Retry policies | Manual try/except loops | LangGraph retry policies + bounded loops | Built-in exponential backoff, error categorization, and max attempt limits |
| Pandas function validation | Manual function name checking | AST-based library introspection | Recent 2026 research achieves 100% precision detecting hallucinated pandas functions via AST + dynamic KB |

**Key insight:** Multi-agent orchestration has dozens of edge cases (retry loops, state management, concurrent access, error handling, observability). LangGraph is the production-tested solution used by enterprises. Building custom orchestration is a 2-4 week rabbit hole that will still miss edge cases.

## Common Pitfalls

### Pitfall 1: Infinite Retry Loops
**What goes wrong:** Code Checker finds error → routes to Coding Agent → generates similar bad code → infinite loop. Costs spiral, latency explodes, user waits forever.

**Why it happens:** No circuit breaker on retry count. LangGraph's default `recursion_limit=25` eventually triggers, but that's 25+ expensive LLM calls.

**How to avoid:**
1. Add `error_count` and `max_steps` to state schema
2. Increment `error_count` in Code Checker node before retry
3. Add conditional edge checking `error_count >= max_steps` (default: 3)
4. Route to "halt" node that returns error message to user

**Warning signs:**
- LangGraph raises `GraphRecursionError: Recursion limit of 25 reached`
- Token costs spike unexpectedly
- Single user query takes >30 seconds

### Pitfall 2: LLM Hallucinated Pandas Functions
**What goes wrong:** Coding Agent generates code like `pd.read_exel()` (typo) or `df.dropna_missing()` (non-existent function). Code Checker must catch these before execution.

**Why it happens:** LLMs trained on code may misremember function names or invent plausible-sounding functions.

**How to avoid:**
1. Use AST analysis to extract all function calls
2. Validate against dynamically-built KB of actual pandas/numpy functions (introspection)
3. Recent 2026 research shows 87.6% recall with AST + library introspection
4. Return specific error to Coding Agent: "Function 'dropna_missing' does not exist in pandas. Did you mean 'dropna'?"

**Warning signs:**
- Code execution fails with `AttributeError: 'DataFrame' object has no attribute 'X'`
- Many retry loops without resolution
- Validation passes but execution fails

### Pitfall 3: State Bleed Across Chat Tabs
**What goes wrong:** User uploads File A in Tab 1, uploads File B in Tab 2. Tab 1 queries accidentally see File B's context or vice versa.

**Why it happens:** Sharing thread_id across files or using global state without isolation.

**How to avoid:**
1. Generate unique thread_id per file: `f"file_{file_id}_user_{user_id}"`
2. Pass thread_id in config for every graph invocation
3. PostgreSQL checkpointer automatically isolates by thread_id
4. Never share state objects between invocations

**Warning signs:**
- User reports "AI used wrong dataset"
- Onboarding summary appears in wrong chat tab
- Queries reference columns that don't exist in current file

### Pitfall 4: Token Cost Blowup
**What goes wrong:** 4-agent system with retry loops consumes 5-10x more tokens than expected. Monthly bill explodes.

**Why it happens:** Each agent makes LLM calls, retry loops multiply costs, Onboarding analysis can be verbose, Data Analysis Agent interprets results (more tokens).

**How to avoid:**
1. Set max_tokens caps on each agent (Onboarding: 1000, Coding: 500, Code Checker: 200, Data Analysis: 800)
2. Monitor token usage from day one with LangSmith
3. Set cost alerts at 50%, 80%, 100% of budget
4. Use bounded retry loops (max_steps=3) to limit runaway costs
5. Optimize prompts: "Be concise" in system prompts

**Warning signs:**
- LangSmith shows single query using >5000 tokens
- Monthly token usage 10x higher than projected
- Retry loops consuming majority of tokens

### Pitfall 5: SQLite Checkpointer in Production
**What goes wrong:** High concurrent load causes write bottlenecks. Users experience slow responses or timeout errors.

**Why it happens:** SQLite's single-writer limitation. AsyncSqliteSaver not recommended for production (per LangGraph docs).

**How to avoid:**
1. Use PostgreSQL checkpointer for production (already have PostgreSQL in stack)
2. Call `checkpointer.setup()` once during app startup to create tables
3. SQLite checkpointer OK for local dev/testing only

**Warning signs:**
- Concurrent requests fail with database lock errors
- Latency spikes under load
- Checkpointer writes block graph execution

### Pitfall 6: Onboarding Context Not Flowing to Chat Agents
**What goes wrong:** Coding Agent generates code for wrong column names or incorrect data types. User asks "What's the average sales?" but code references non-existent 'revenue' column.

**Why it happens:** Onboarding summary stored separately and not included in chat agent context.

**How to avoid:**
1. Store Onboarding summary in file metadata (database table)
2. Load summary when initializing chat agent state
3. Include in Coding Agent system prompt via template: `{data_summary}`
4. Critical info: column names, types, sample values, semantic meanings

**Warning signs:**
- Generated code references columns that don't exist
- Data type mismatches (treating string as numeric)
- User says "AI doesn't understand my data"

### Pitfall 7: No Logical Correctness Check
**What goes wrong:** Code Checker validates syntax and libraries but misses logical errors. User asks "What's the max sales?" and code returns `df['sales'].min()`.

**Why it happens:** AST validation only checks syntax and allowlists, not semantic correctness.

**How to avoid:**
1. Add LLM-based logical validation in Code Checker
2. Pass user query + generated code to LLM: "Does this code answer the user's question?"
3. Check for obvious mismatches (max vs min, sum vs count)
4. Return specific feedback: "Code calculates minimum but query asks for maximum"

**Warning signs:**
- Users report "wrong answers"
- Code executes successfully but results don't match query intent
- Validation passes but user rejects result

## Code Examples

Verified patterns from official sources:

### Complete LangGraph Multi-Agent Setup
```python
# Source: https://www.blog.langchain.com/langgraph-multi-agent-workflows/
from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, Literal
from langgraph.types import Command

class AgentState(TypedDict):
    file_id: str
    user_query: str
    data_summary: str
    user_context: str
    generated_code: str
    validation_errors: list[str]
    error_count: int
    max_steps: int
    execution_result: str
    analysis: str

# Agent nodes
def coding_agent(state: AgentState) -> AgentState:
    """Generate Python code based on query."""
    # LLM call to generate code
    code = generate_code(state["user_query"], state["data_summary"])
    return {"generated_code": code}

def code_checker(state: AgentState) -> Command[Literal["execute", "retry_coding", "halt"]]:
    """Validate code and route."""
    errors = validate_with_ast(state["generated_code"])
    error_count = state.get("error_count", 0)

    if not errors:
        return Command(goto="execute", update={"validation_errors": []})

    if error_count >= state.get("max_steps", 3):
        return Command(goto="halt", update={"validation_errors": errors})

    return Command(
        goto="retry_coding",
        update={
            "validation_errors": errors,
            "error_count": error_count + 1
        }
    )

def execute_code(state: AgentState) -> AgentState:
    """Execute validated code (will be sandboxed in Phase 5)."""
    result = execute_in_sandbox(state["generated_code"], state["file_id"])
    return {"execution_result": result}

def data_analysis_agent(state: AgentState) -> AgentState:
    """Interpret results and generate explanation."""
    analysis = interpret_results(
        state["user_query"],
        state["execution_result"]
    )
    return {"analysis": analysis}

# Build graph
def build_chat_graph(postgres_url: str):
    # Initialize checkpointer
    checkpointer = PostgresSaver.from_conn_string(postgres_url)

    # Create graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("coding_agent", coding_agent)
    graph.add_node("code_checker", code_checker)
    graph.add_node("execute", execute_code)
    graph.add_node("data_analysis", data_analysis_agent)

    # Define edges
    graph.add_edge("coding_agent", "code_checker")
    # code_checker has conditional routing via Command return
    graph.add_edge("execute", "data_analysis")

    # Set entry point
    graph.set_entry_point("coding_agent")
    graph.set_finish_point("data_analysis")

    # Compile with checkpointer
    return graph.compile(checkpointer=checkpointer)

# Usage
app = build_chat_graph(postgres_url)
config = {"configurable": {"thread_id": f"file_{file_id}"}}
result = await app.ainvoke({
    "user_query": "What's the average sales?",
    "data_summary": onboarding_summary,
    "max_steps": 3
}, config)
```

### Pandas Data Profiling for Onboarding Agent
```python
# Source: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.describe.html
import pandas as pd

def profile_dataframe(df: pd.DataFrame) -> dict:
    """Generate comprehensive data profile."""
    profile = {
        "shape": {
            "rows": len(df),
            "columns": len(df.columns)
        },
        "columns": {},
        "quality_issues": []
    }

    # Column-level analysis
    for col in df.columns:
        profile["columns"][col] = {
            "dtype": str(df[col].dtype),
            "missing_count": df[col].isna().sum(),
            "missing_pct": (df[col].isna().sum() / len(df)) * 100,
            "unique_count": df[col].nunique()
        }

        # Numeric column stats
        if pd.api.types.is_numeric_dtype(df[col]):
            stats = df[col].describe()
            profile["columns"][col].update({
                "mean": stats["mean"],
                "std": stats["std"],
                "min": stats["min"],
                "max": stats["max"],
                "q25": stats["25%"],
                "q50": stats["50%"],
                "q75": stats["75%"]
            })

    # Quality issues
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        profile["quality_issues"].append(
            f"{duplicates} duplicate rows found ({duplicates/len(df)*100:.1f}%)"
        )

    for col in df.columns:
        missing_pct = (df[col].isna().sum() / len(df)) * 100
        if missing_pct > 10:
            profile["quality_issues"].append(
                f"Column '{col}' has {missing_pct:.1f}% missing values"
            )

    return profile
```

### Loading YAML Configuration
```python
# Source: https://empathyfirstmedia.com/yaml-files-ai-agents/
import yaml
from pathlib import Path

def load_agent_config():
    """Load prompts and allowlist from YAML."""
    config_dir = Path(__file__).parent.parent / "config"

    with open(config_dir / "prompts.yaml") as f:
        prompts = yaml.safe_load(f)

    with open(config_dir / "allowlist.yaml") as f:
        allowlist = yaml.safe_load(f)

    return prompts, allowlist

# Usage
prompts, allowlist = load_agent_config()
system_prompt = prompts["agents"]["coding"]["system_prompt"]
allowed_libs = allowlist["allowed_libraries"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LangChain LCEL chains | LangGraph conditional routing | v0.1 → v1.0 (2024-2025) | Chains can't handle retry loops or complex routing; graphs enable production agentic workflows |
| RestrictedPython sandboxing | AST validation + OS isolation | 2025-2026 security research | Language-level sandboxing fundamentally insecure (CVE-2026-0863); AST + containers/gVisor required |
| Regex code validation | AST-based library introspection | January 2026 research | AST analysis achieves 87.6% recall detecting hallucinations vs <50% for regex |
| Manual retry logic | Bounded retry policies | LangGraph 0.2+ (2024) | Built-in retry policies with max attempts prevent infinite loops |
| SQLite for all use cases | PostgreSQL for production | LangGraph docs (2025) | AsyncSqliteSaver explicitly not recommended for production workloads |
| Custom tracing/logging | LangSmith zero-code observability | LangSmith 1.0 (2024) | No code changes needed; automatic capture of all agent interactions |

**Deprecated/outdated:**
- **LangChain agents (AgentExecutor):** Replaced by LangGraph for production agentic systems. AgentExecutor lacks state management and conditional routing.
- **In-memory state only:** Pre-checkpointer era. Modern apps need persistence for resumption and thread isolation.
- **Language-level Python sandboxing (RestrictedPython, PyPy sandbox):** Recent CVEs prove these are bypassable. AST validation + OS-level isolation is current standard.
- **Single-agent workflows for complex tasks:** 2026 consensus: multi-agent with specialized roles outperforms single mega-agent for high-value tasks.

## Open Questions

Things that couldn't be fully resolved:

1. **LLM-based logical correctness validation performance**
   - What we know: AST handles syntax/allowlists; logical errors require LLM judgment
   - What's unclear: Best prompt design for logical validation; false positive rate
   - Recommendation: Implement AST validation first (high confidence), add LLM logical check as enhancement with monitoring

2. **Optimal max_steps value for retry loops**
   - What we know: Default 3 recommended; prevents runaway costs
   - What's unclear: May need tuning based on real user queries (complex queries may need 5?)
   - Recommendation: Start with 3, monitor via LangSmith, adjust if legitimate queries consistently hit limit

3. **Onboarding Agent verbosity vs token costs**
   - What we know: Comprehensive analysis improves Coding Agent quality
   - What's unclear: Trade-off point between detail and token cost
   - Recommendation: Start with full profiling (structure + quality + semantics), add max_tokens=1000 cap, iterate based on cost metrics

4. **Two-stage user context handling (pre + post processing)**
   - What we know: User can provide context during upload and after Onboarding summary
   - What's unclear: Best UX pattern for prompting post-processing feedback
   - Recommendation: Display Onboarding summary with explicit prompt: "Is this correct? Add any clarifications." Store refinements as appended context (v1 approach per CONTEXT.md).

## Sources

### Primary (HIGH confidence)
- [LangGraph official documentation - Thinking in LangGraph](https://docs.langchain.com/oss/python/langgraph/thinking-in-langgraph) - Core concepts, state management, error handling
- [LangGraph multi-agent workflows blog](https://www.blog.langchain.com/langgraph-multi-agent-workflows/) - Multi-agent patterns
- [Python ast module documentation](https://docs.python.org/3/library/ast.html) - AST parsing, NodeVisitor patterns
- [LangGraph memory documentation](https://docs.langchain.com/oss/python/langgraph/memory) - Thread-scoped state, checkpointers
- [LangSmith environment variables](https://docs.langchain.com/langsmith/env-var) - Zero-code tracing setup
- [LangGraph PyPI](https://pypi.org/project/langgraph/) - Current version 1.0.7
- [LangGraph checkpointer-postgres PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/) - Production persistence
- [LangGraph RECURSION_LIMIT docs](https://docs.langchain.com/oss/python/langgraph/errors/GRAPH_RECURSION_LIMIT) - Circuit breaker mechanism

### Secondary (MEDIUM confidence)
- [LangGraph 2026 updates - AgentFrameworkHub](https://www.agentframeworkhub.com/blog/langgraph-news-updates-2026) - 2026 roadmap and features
- [LangGraph conditional edges tutorial](https://dev.to/jamesli/advanced-langgraph-implementing-conditional-edges-and-tool-calling-agents-3pdn) - Conditional routing patterns
- [LangGraph retry policies guide](https://dev.to/aiengineering/a-beginners-guide-to-handling-errors-in-langgraph-with-retry-policies-h22) - Bounded retry implementation
- [LangGraph best practices - Swarnendu De](https://www.swarnendu.de/blog/langgraph-best-practices/) - Production patterns
- [Multi-agent orchestration guide 2025 - Latenode](https://latenode.com/blog/ai-frameworks-technical-infrastructure/langgraph-multi-agent-orchestration/langgraph-multi-agent-orchestration-complete-framework-guide-architecture-analysis-2025) - Architecture analysis
- [When to build multi-agent systems - LangChain blog](https://www.blog.langchain.com/how-and-when-to-build-multi-agent-systems/) - Use case guidelines
- [LangSmith observability overview](https://www.langchain.com/langsmith/observability) - Tracing capabilities
- [LangGraph with MongoDB memory](https://www.mongodb.com/company/blog/product-release-announcements/powering-long-term-memory-for-agents-langgraph) - Thread-scoped memory patterns
- [Python sandbox security - Two Six Technologies](https://twosixtech.com/blog/hijacking-the-ast-to-safely-handle-untrusted-python/) - AST-based security
- [Setting up secure Python sandbox - dida.do](https://dida.do/blog/setting-up-a-secure-python-sandbox-for-llm-agents) - OS-level isolation best practices
- [Code execution sandbox comparison 2026 - Northflank](https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents) - gVisor, containers, security
- [YAML for AI agents - Empathy First Media](https://empathyfirstmedia.com/yaml-files-ai-agents/) - Configuration management
- [Pandas DataFrame.describe documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.describe.html) - Data profiling method
- [Pandas missing data guide](https://pandas.pydata.org/docs/user_guide/missing_data.html) - Handling missing values
- [LangSmith cost tracking](https://docs.langchain.com/langsmith/cost-tracking) - Token usage monitoring
- [Langfuse token tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking) - Alternative observability

### Tertiary (LOW confidence - marked for validation)
- [Detecting hallucinations in LLM code via AST - arXiv 2601.19106](https://arxiv.org/abs/2601.19106) - Recent 2026 research, 87.6% recall claim, needs production validation
- [AI agent production costs 2026 - AgentFrameworkHub](https://www.agentframeworkhub.com/blog/ai-agent-production-costs-2026) - Cost estimates, needs validation against actual usage
- [RestrictedPython documentation](https://restrictedpython.readthedocs.io/) - Alternative approach, but deprecated for security per research

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - LangGraph 1.0 is LTS with production deployments; PyPI versions verified
- Architecture patterns: HIGH - Official LangGraph docs + established patterns from production systems
- Code validation (AST): MEDIUM-HIGH - Official Python docs (HIGH) + 2026 research paper (needs prod validation, marked MEDIUM)
- Pitfalls: MEDIUM-HIGH - Combination of official docs warnings + community-reported issues
- OS-level sandboxing: MEDIUM - Recent CVEs validate approach but Phase 5 implementation details TBD

**Research date:** 2026-02-03
**Valid until:** 2026-03-05 (30 days - LangGraph relatively stable with LTS v1.0)

**Note on confidence:** AST validation for hallucinated functions has strong research backing (January 2026 paper with 87.6% recall) but is cutting-edge. Recommend implementing with monitoring to validate performance in production. All other recommendations are production-proven patterns.
