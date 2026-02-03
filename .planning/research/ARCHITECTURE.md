# Architecture Research

**Domain:** AI-Powered Data Analytics Platform
**Researched:** 2026-02-02
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Frontend (Next.js)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ File Upload  │  │ File Tabs    │  │ Chat UI      │  │ Data Cards   │   │
│  │ Component    │  │ Management   │  │ (Streaming)  │  │ (Interactive)│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
│         └─────────────────┴─────────────────┴─────────────────┘            │
│                                     │                                       │
│                          SSE (Server-Sent Events)                           │
│                                     │                                       │
├─────────────────────────────────────┼───────────────────────────────────────┤
│                         Backend API (FastAPI)                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    API Layer (Route Handlers)                         │ │
│  │  /upload  /chat/stream  /files  /auth  /settings                      │ │
│  └───────────────────────┬───────────────────────────────────────────────┘ │
│                          │                                                  │
│  ┌───────────────────────┴───────────────────────────────────────────────┐ │
│  │                  AI Agent Orchestration (LangGraph)                    │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐              │ │
│  │  │Onboarding│→ │  Coding  │→ │   Code   │→ │   Data   │              │ │
│  │  │  Agent   │  │  Agent   │  │ Checker  │  │ Analysis │              │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘              │ │
│  └───────────────────────┬───────────────────────────────────────────────┘ │
│                          │                                                  │
│  ┌───────────────────────┴───────────────────────────────────────────────┐ │
│  │                    Sandbox Execution Layer                            │ │
│  │              Docker Container + gVisor + RestrictedPython             │ │
│  └───────────────────────┬───────────────────────────────────────────────┘ │
│                          │                                                  │
├──────────────────────────┼──────────────────────────────────────────────────┤
│                    Data & Storage Layer                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐               │
│  │  PostgreSQL    │  │  File Storage  │  │  LangSmith     │               │
│  │  (asyncpg)     │  │  (Local FS)    │  │  (Tracing)     │               │
│  │                │  │                │  │                │               │
│  │ • Users        │  │ /uploads/      │  │ • Agent traces │               │
│  │ • Files Meta   │  │   user_id/     │  │ • Token usage  │               │
│  │ • Chat History │  │     file_id/   │  │ • Debugging    │               │
│  └────────────────┘  └────────────────┘  └────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Next.js Frontend** | User interface, SSE streaming client, file upload UI, Data Cards rendering | React components, App Router, Route Handlers for SSE proxy |
| **FastAPI Backend** | API endpoints, authentication, file handling, agent orchestration, SSE streaming | Python async endpoints, StreamingResponse, LangChain integration |
| **AI Agent Orchestrator** | Multi-agent workflow coordination, state management, agent handoffs | LangGraph with shared state, supervisor or handoff pattern |
| **Onboarding Agent** | Analyzes uploaded file structure, generates metadata, suggests initial queries | LLM + pandas schema inspection, writes to PostgreSQL |
| **Coding Agent** | Generates Python code from natural language queries | LLM + prompt template, outputs executable Python scripts |
| **Code Checker Agent** | Validates generated code for safety and correctness | RestrictedPython AST validation + custom rules, rejects unsafe code |
| **Data Analysis Agent** | Interprets execution results, generates natural language explanations | LLM + execution results, produces Data Card content |
| **Sandbox Executor** | Secure Python code execution in isolated environment | Docker container with gVisor runtime, resource limits, network isolation |
| **PostgreSQL Database** | Persistent storage for users, file metadata, chat history per file | asyncpg driver, SQLAlchemy ORM (optional), relational schema |
| **Local File Storage** | Uploaded file persistence, organized by user and file ID | Filesystem at `/uploads/user_id/file_id/`, segregated by user |
| **LangSmith** | Agent execution tracing, debugging, token usage monitoring | Automatic tracing via environment variable, no code changes |

## Recommended Project Structure

```
spectra-project/
├── frontend/                    # Next.js application
│   ├── app/                     # App Router
│   │   ├── api/                 # API routes (SSE proxy)
│   │   │   └── chat/
│   │   │       └── route.ts     # SSE streaming endpoint
│   │   ├── auth/                # Authentication pages
│   │   ├── dashboard/           # Main app pages
│   │   └── layout.tsx           # Root layout
│   ├── components/              # React components
│   │   ├── FileUpload.tsx       # File upload component
│   │   ├── FileTabs.tsx         # Tabbed file interface
│   │   ├── ChatInterface.tsx    # Chat UI with streaming
│   │   └── DataCard.tsx         # Interactive Data Card
│   └── package.json
│
├── backend/                     # FastAPI application
│   ├── main.py                  # FastAPI app entry point
│   ├── routers/                 # API route handlers
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── files.py             # File upload/management
│   │   ├── chat.py              # Chat streaming endpoint
│   │   └── settings.py          # User settings
│   ├── agents/                  # AI agent implementations
│   │   ├── orchestrator.py      # LangGraph multi-agent workflow
│   │   ├── onboarding.py        # Onboarding Agent
│   │   ├── coding.py            # Coding Agent
│   │   ├── code_checker.py      # Code Checker Agent
│   │   └── data_analysis.py     # Data Analysis Agent
│   ├── sandbox/                 # Code execution sandbox
│   │   ├── executor.py          # Sandbox interface
│   │   └── validator.py         # RestrictedPython validation
│   ├── database/                # Database layer
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── database.py          # Database connection
│   │   └── schemas.py           # Pydantic schemas
│   ├── storage/                 # File storage handling
│   │   └── file_manager.py      # Upload/download logic
│   └── requirements.txt
│
├── docker/                      # Docker configurations
│   ├── Dockerfile.frontend      # Next.js container
│   ├── Dockerfile.backend       # FastAPI container
│   ├── Dockerfile.sandbox       # Sandbox runtime container
│   └── gvisor-runtime.json      # gVisor runtime config
│
├── docker-compose.yml           # Multi-service orchestration
├── .env                         # Environment variables
└── README.md
```

### Structure Rationale

- **frontend/** - Separate Next.js application for clear frontend/backend separation, enables independent deployment to Vercel
- **backend/** - Python FastAPI application with domain-driven structure (agents, sandbox, database, storage as separate concerns)
- **routers/** - API endpoint handlers organized by feature, follows FastAPI best practices
- **agents/** - AI agent logic isolated from API layer, enables testing and reuse
- **sandbox/** - Security-critical code execution isolated in dedicated module
- **docker/** - Containerization configs separate from application code, supports multi-stage builds
- **docker-compose.yml** - Single-command local development environment (frontend + backend + PostgreSQL + sandbox)

## Architectural Patterns

### Pattern 1: Multi-Agent Orchestration with LangGraph

**What:** Coordinate multiple specialized AI agents (Onboarding, Coding, Code Checker, Data Analysis) using LangGraph's graph-based workflow orchestration with shared state.

**When to use:** When tasks require multiple specialized agents with sequential dependencies and state management.

**Trade-offs:**
- **Pros:** Type-safe state management, flexible routing (handoffs, supervision), built-in streaming support, production-ready patterns
- **Cons:** More complex than single-agent, requires careful state design, potential for coordination overhead

**Example:**
```python
# backend/agents/orchestrator.py
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from typing import TypedDict, Sequence

class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    file_metadata: dict
    generated_code: str
    validation_result: dict
    execution_result: dict
    analysis: str

# Define workflow graph
workflow = StateGraph(AgentState)

# Add agent nodes
workflow.add_node("onboarding", onboarding_agent)
workflow.add_node("coding", coding_agent)
workflow.add_node("code_checker", code_checker_agent)
workflow.add_node("data_analysis", data_analysis_agent)

# Define sequential workflow
workflow.set_entry_point("onboarding")
workflow.add_edge("onboarding", "coding")
workflow.add_edge("coding", "code_checker")

# Conditional edge: code_checker decides if code is safe
workflow.add_conditional_edges(
    "code_checker",
    lambda state: "execute" if state["validation_result"]["safe"] else "regenerate",
    {
        "execute": "data_analysis",
        "regenerate": "coding"  # Loop back to regenerate code
    }
)

workflow.add_edge("data_analysis", END)

app = workflow.compile()
```

**Recommended for Spectra:** Use **Handoffs Pattern** initially (linear: Onboarding → Coding → Code Checker → Data Analysis), then add conditional edges for code regeneration loops.

### Pattern 2: Server-Sent Events (SSE) Streaming

**What:** Stream AI agent responses from FastAPI backend through Next.js API route to frontend using SSE, allowing users to see real-time agent progress.

**When to use:** When users need to see incremental AI responses (code generation, analysis streaming) rather than waiting for complete results.

**Trade-offs:**
- **Pros:** Native browser support (no WebSocket complexity), unidirectional (simpler than bidirectional), works through Next.js API routes
- **Cons:** One-way only (frontend → backend requires separate POST), reconnection logic needed for reliability

**Example:**
```python
# backend/routers/chat.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

async def stream_agent_response(query: str, file_id: str, user_id: str):
    """Stream agent workflow execution with intermediate steps."""
    async for chunk in agent_workflow.astream(
        {
            "messages": [{"role": "user", "content": query}],
            "file_id": file_id,
            "user_id": user_id
        }
    ):
        # Stream each agent step as SSE event
        if "onboarding" in chunk:
            yield f"data: {json.dumps({'type': 'onboarding', 'content': chunk['onboarding']})}\n\n"
        elif "coding" in chunk:
            yield f"data: {json.dumps({'type': 'code', 'content': chunk['generated_code']})}\n\n"
        elif "data_analysis" in chunk:
            yield f"data: {json.dumps({'type': 'analysis', 'content': chunk['analysis']})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        stream_agent_response(request.query, request.file_id, request.user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

```typescript
// frontend/app/api/chat/route.ts
export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  const body = await req.json();

  const backendResponse = await fetch('http://backend:8000/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  // Proxy SSE stream to frontend
  return new Response(backendResponse.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    }
  });
}
```

### Pattern 3: Multi-Layer Sandbox Security

**What:** Implement defense-in-depth for code execution using multiple isolation layers: AST validation (RestrictedPython) → Docker containers → gVisor user-space kernel → resource limits.

**When to use:** When executing untrusted AI-generated code that processes user data. Essential for Spectra's security requirements.

**Trade-offs:**
- **Pros:** Defense-in-depth prevents single-point failures, gVisor provides VM-like isolation with container-like performance, production-proven (used by Google)
- **Cons:** Linux-only, adds syscall overhead, Docker + gVisor setup complexity

**Example:**
```python
# backend/sandbox/validator.py
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins

ALLOWED_IMPORTS = {'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly'}
FORBIDDEN_PATTERNS = [
    'os.', 'sys.', 'subprocess', 'eval', 'exec', 'open',
    '__import__', 'importlib', 'dropna', 'drop', 'to_sql'
]

def validate_code(code: str) -> tuple[bool, str]:
    """AST-level validation before execution."""
    # Check for forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in code:
            return False, f"Forbidden operation: {pattern}"

    # Compile with RestrictedPython
    byte_code = compile_restricted(code, '<user_code>', 'exec')
    if byte_code.errors:
        return False, f"Validation failed: {byte_code.errors}"

    return True, "Code validated"

# backend/sandbox/executor.py
import docker
import asyncio

async def execute_in_sandbox(code: str, data_path: str, timeout: int = 30) -> dict:
    """Execute code in gVisor-secured Docker container."""
    client = docker.from_env()

    # Layer 1: Validate code
    is_valid, message = validate_code(code)
    if not is_valid:
        return {"success": False, "error": message}

    try:
        # Layer 2-3: Docker + gVisor execution
        container = client.containers.run(
            image="python:3.10-slim",
            command=["python", "-c", code],
            runtime="runsc",  # gVisor runtime
            volumes={data_path: {"bind": "/data", "mode": "ro"}},
            mem_limit="512m",  # Layer 4: Resource limits
            cpu_quota=50000,
            network_mode="none",  # Layer 5: Network isolation
            detach=True,
            remove=True
        )

        # Wait for completion with timeout
        result = container.wait(timeout=timeout)
        logs = container.logs().decode('utf-8')

        return {
            "success": result["StatusCode"] == 0,
            "output": logs,
            "exit_code": result["StatusCode"]
        }
    except docker.errors.ContainerError as e:
        return {"success": False, "error": str(e)}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Execution timeout"}
```

**Docker Compose gVisor configuration:**
```yaml
# docker-compose.yml
services:
  sandbox:
    image: python:3.10-slim
    runtime: runsc  # gVisor runtime
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    read_only: true
    tmpfs:
      - /tmp
    networks:
      - isolated
```

### Pattern 4: Per-File Chat History

**What:** Store chat messages with references to both user and file, enabling independent chat contexts per uploaded file.

**When to use:** When users interact with multiple files simultaneously and need separate conversation contexts for each.

**Trade-offs:**
- **Pros:** Clean separation of concerns, enables tabbed interface, natural multi-file workflow
- **Cons:** More complex queries (joins on user + file), higher storage if users have many files

**Example:**
```python
# backend/database/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    files = relationship("File", back_populates="user")

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    metadata = Column(JSON)  # AI-generated metadata from Onboarding Agent
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="files")
    messages = relationship("ChatMessage", back_populates="file")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    agent_type = Column(String)  # 'onboarding', 'coding', 'data_analysis'
    created_at = Column(DateTime, default=datetime.utcnow)

    file = relationship("File", back_populates="messages")

# Query chat history for a specific file
async def get_file_chat_history(file_id: int, user_id: int):
    """Retrieve chat messages for a file, ensuring user owns the file."""
    result = await db.execute(
        select(ChatMessage)
        .join(File)
        .where(File.id == file_id, File.user_id == user_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()
```

## Data Flow

### Request Flow: File Upload → AI Interpretation

```
User uploads file (Excel/CSV)
    ↓
[Next.js FileUpload Component]
    ↓ (POST /files/upload with multipart form-data)
[FastAPI /files/upload endpoint]
    ↓
1. Validate file format and size
2. Generate unique file_id
3. Save to /uploads/user_id/file_id/filename
4. Create File record in PostgreSQL
    ↓
[Trigger Onboarding Agent]
    ↓
1. Load file with pandas
2. Analyze schema (columns, types, sample data)
3. Generate metadata (LLM call)
4. Update File.metadata in PostgreSQL
    ↓
[Return file metadata to frontend]
    ↓
[Frontend creates new file tab, displays metadata]
```

### Request Flow: Chat Query → AI Code Generation → Sandbox Execution → Results

```
User types query in chat
    ↓
[Next.js ChatInterface Component]
    ↓ (POST /api/chat → SSE stream)
[Next.js API Route /api/chat/route.ts]
    ↓ (Proxy to backend)
[FastAPI /chat/stream endpoint]
    ↓
[LangGraph Agent Workflow starts streaming]
    ↓
┌─────────────────────────────────────────────────┐
│ Step 1: Coding Agent                            │
│ - Receives query + file metadata + chat history │
│ - Generates Python code (LLM call)              │
│ - Streams: {"type": "code", "content": "..."}   │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│ Step 2: Code Checker Agent                      │
│ - Validates code with RestrictedPython          │
│ - Checks for forbidden operations               │
│ - If invalid: loop back to Coding Agent         │
│ - Streams: {"type": "validation", "safe": true} │
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│ Step 3: Sandbox Executor                        │
│ - Execute code in Docker + gVisor container     │
│ - Load user's data file (read-only mount)       │
│ - Capture output (DataFrame, plots, errors)     │
│ - Streams: {"type": "execution", "status": "..."│
└─────────────────┬───────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────┐
│ Step 4: Data Analysis Agent                     │
│ - Interprets execution results                  │
│ - Generates natural language explanation (LLM)  │
│ - Streams: {"type": "analysis", "content": "..."│
└─────────────────┬───────────────────────────────┘
                  ↓
[Save ChatMessage to PostgreSQL]
    ↓
[Stream final event: {"type": "done"}]
    ↓
[Next.js receives stream, updates UI incrementally]
    ↓
[Render Data Card with results]
```

### State Management in Multi-Agent Workflow

```
LangGraph Shared State (AgentState)
    ↓ (all agents read/write)
┌──────────────────────────────────────┐
│ messages: [user query, agent replies]│  ← Chat history context
│ file_id: 123                         │  ← Which file to analyze
│ file_metadata: {columns, types, ...} │  ← From Onboarding Agent
│ generated_code: "import pandas..."  │  ← From Coding Agent
│ validation_result: {safe: true, ...}│  ← From Code Checker
│ execution_result: {output, plots}   │  ← From Sandbox
│ analysis: "The data shows..."       │  ← From Data Analysis Agent
└──────────────────────────────────────┘
```

### Key Data Flows

1. **File Upload Flow:** Frontend → FastAPI → Local Storage → PostgreSQL → Onboarding Agent → LLM → PostgreSQL (metadata) → Frontend
2. **Chat Query Flow:** Frontend SSE → FastAPI → LangGraph → Coding Agent → Code Checker → Sandbox → Data Analysis Agent → SSE stream → Frontend
3. **Per-File Chat History:** Query includes file_id → PostgreSQL join (File + ChatMessage) → Agent receives context → New message saved with file_id reference

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-100 users (MVP)** | Monolith deployment: Single Docker Compose stack (Next.js, FastAPI, PostgreSQL, sandbox). Local file storage. Single backend server handles all agent orchestration. LangSmith for debugging. |
| **100-1K users** | Separate frontend (Vercel) and backend (Railway/Render). Managed PostgreSQL (RDS/Cloud SQL). Optimize: Add Redis for session caching. Connection pooling (asyncpg). Add rate limiting per user. Consider managed sandbox (E2B Cloud) if Docker scaling becomes complex. |
| **1K-10K users** | Horizontal scaling: Multiple FastAPI backend instances behind load balancer. Separate sandbox execution service (dedicated containers). Object storage (S3) for file uploads. Add background workers (Celery) for async tasks. PostgreSQL read replicas. Cache file metadata in Redis. |
| **10K+ users** | Microservices: Split agent orchestration into separate service. Dedicated sandbox cluster (Kubernetes + Kata Containers). Event-driven architecture (Kafka) for agent communication. CDN for frontend. Multi-region deployment. Vector database for semantic search. Full observability stack (LangSmith + Prometheus + Grafana). |

### Scaling Priorities

1. **First bottleneck (100-1K users):** Database connections and LLM API rate limits. Fix: Connection pooling (asyncpg max_size=20), LLM response caching for common queries, batch LLM calls where possible.
2. **Second bottleneck (1K-10K users):** Sandbox execution throughput and file storage I/O. Fix: Separate sandbox service with dedicated worker pool, migrate to S3 for file storage, implement queue for sandbox tasks.
3. **Third bottleneck (10K+ users):** Agent orchestration overhead and real-time streaming connections. Fix: Dedicated agent service with horizontal scaling, use message queue (Kafka) for agent coordination, WebSocket connection management layer.

## Anti-Patterns

### Anti-Pattern 1: Single Shared State Across Users

**What people do:** Use a global in-memory state for agent workflows, sharing LangGraph state objects across different users.

**Why it's wrong:** Data leakage between users (User A sees User B's chat history), race conditions on shared state, impossible to scale horizontally (state tied to single process).

**Do this instead:** Isolate state per request. Each agent workflow execution gets its own AgentState instance with user_id and file_id scoping. Use PostgreSQL for persistent state, not in-memory globals.

```python
# WRONG: Shared global state
agent_state = AgentState()  # Global variable

@app.post("/chat/stream")
async def chat(request: ChatRequest):
    agent_state["messages"].append(request.query)  # Race condition!

# CORRECT: Per-request state
@app.post("/chat/stream")
async def chat(request: ChatRequest):
    state = AgentState(  # Fresh state per request
        messages=await get_chat_history(request.file_id, request.user_id),
        file_id=request.file_id,
        user_id=request.user_id
    )
    async for chunk in agent_workflow.astream(state):
        yield chunk
```

### Anti-Pattern 2: Mixing User Data in Sandbox

**What people do:** Execute all users' code in the same sandbox instance, or mount entire uploads directory into sandbox.

**Why it's wrong:** User A's code can access User B's data files, no isolation between tenants, violates data privacy requirements.

**Do this instead:** Per-execution sandboxes with read-only mounts of ONLY the specific user's specific file. Use user_id and file_id to construct isolated paths.

```python
# WRONG: Mount entire uploads directory
volumes={"/uploads": {"bind": "/data", "mode": "ro"}}

# CORRECT: Mount only the specific file for this user
volumes={
    f"/uploads/{user_id}/{file_id}": {"bind": "/data", "mode": "ro"}
}
```

### Anti-Pattern 3: Synchronous Agent Workflows

**What people do:** Call agents sequentially with blocking calls, waiting for each LLM response before proceeding.

**Why it's wrong:** High latency (30-60s for 4-agent workflow), poor user experience (no streaming feedback), can't scale to concurrent requests.

**Do this instead:** Use async/await throughout, stream intermediate results via SSE, use LangGraph's async streaming (astream).

```python
# WRONG: Blocking sequential calls
def execute_workflow(query):
    code = coding_agent.invoke(query)  # Blocks 5-10s
    validation = code_checker.invoke(code)  # Blocks 2-3s
    result = execute_code(code)  # Blocks 10-20s
    analysis = data_analysis.invoke(result)  # Blocks 5-10s
    return analysis  # Total: 22-43s with no feedback

# CORRECT: Async streaming
async def execute_workflow(query):
    async for chunk in agent_workflow.astream({"messages": [query]}):
        if "coding" in chunk:
            yield {"type": "code", "content": chunk["coding"]}  # Stream code as generated
        elif "data_analysis" in chunk:
            yield {"type": "analysis", "content": chunk["analysis"]}  # Stream analysis
```

### Anti-Pattern 4: Storing Chat History in Frontend State

**What people do:** Keep chat messages only in React state, losing history on page refresh or tab close.

**Why it's wrong:** Poor UX (chat history lost), can't support multi-device access, no audit trail, violates user expectations.

**Do this instead:** Persist every message to PostgreSQL immediately, load from database on component mount, frontend state is ephemeral cache only.

### Anti-Pattern 5: Unvalidated Code Execution

**What people do:** Execute LLM-generated code directly without validation, trusting the LLM to be safe.

**Why it's wrong:** LLMs can generate dangerous code (file deletion, infinite loops, network calls to exfiltrate data), prompt injection attacks can manipulate code generation.

**Do this instead:** Multi-layer validation (AST validation → manual checks → sandbox isolation). Always assume generated code is untrusted.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **OpenAI/Anthropic LLM API** | Direct API calls via LangChain | Use langchain-openai or langchain-anthropic, set OPENAI_API_KEY in env, implement retry logic for rate limits |
| **LangSmith** | Auto-tracing via env vars | Set LANGCHAIN_TRACING_V2=true, zero code changes, traces all agent calls |
| **Docker Runtime (gVisor)** | Python docker SDK | Configure gVisor runtime in Docker daemon, use runtime="runsc" in container.run() |
| **PostgreSQL** | asyncpg connection pool | Use SQLAlchemy async engine, pool_size=20, pool_recycle=3600, handle connection failures gracefully |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **Frontend ↔ Backend** | HTTP/SSE (Next.js API routes proxy FastAPI) | CORS config for local dev, separate domains in prod (frontend.com → api.frontend.com) |
| **API Layer ↔ Agent Orchestrator** | Direct async function calls | Keep thin: routers handle HTTP, agents handle business logic |
| **Agent Orchestrator ↔ Individual Agents** | LangGraph shared state (dict-based) | Agents read/write to shared AgentState, no direct agent-to-agent calls |
| **Backend ↔ Sandbox** | Docker SDK (async exec) | Backend creates containers, passes code + data path, waits for result with timeout |
| **Backend ↔ Database** | asyncpg (connection pool) | All database access through single pool, use async context managers |
| **Backend ↔ File Storage** | Direct filesystem I/O (async aiofiles) | User/file isolation via path structure: /uploads/{user_id}/{file_id}/ |

## Deployment Architecture

### Development (Local)

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/spectra
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - sandbox
    volumes:
      - ./backend:/app
      - ./uploads:/uploads

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=spectra
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  sandbox:
    image: python:3.10-slim
    runtime: runsc  # gVisor runtime
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    networks:
      - isolated

volumes:
  postgres_data:

networks:
  isolated:
    driver: bridge
```

**Run:** `docker-compose up`
**Access:** Frontend at http://localhost:3000, Backend at http://localhost:8000

### Production (MVP - Single Developer)

**Recommended stack:**
- **Frontend:** Vercel (automatic deployments from Git, global CDN, zero config)
- **Backend:** Railway or Render (Dockerfile deployment, easy Docker support)
- **Database:** Managed PostgreSQL (Railway/Render/RDS)
- **Sandbox:** Run on same backend instance initially, migrate to E2B Cloud if scaling issues

**Deployment steps:**
1. Push frontend to Vercel (automatic build/deploy)
2. Deploy backend to Railway with Dockerfile
3. Configure environment variables (DATABASE_URL, LANGCHAIN_API_KEY, OPENAI_API_KEY)
4. Set up gVisor runtime on Railway (if supported) or use E2B Cloud for sandboxing
5. Configure CORS: Allow frontend domain in FastAPI middleware

### Production (1K+ Users)

**Architecture evolution:**
```
Users
  ↓
Cloudflare CDN (caching, DDoS protection)
  ↓
├─→ Frontend (Vercel) → Next.js SSR/SSG
│
└─→ Backend API (Railway/AWS)
      ↓
      ├─→ FastAPI instances (2-4 behind load balancer)
      ├─→ Managed PostgreSQL (RDS with read replicas)
      ├─→ Redis (session caching, rate limiting)
      ├─→ S3 (file storage instead of local FS)
      └─→ Sandbox service (E2B Cloud or Kubernetes + Kata Containers)
```

**Observability:**
- LangSmith: Agent execution tracing
- Prometheus + Grafana: Backend metrics
- Sentry: Error tracking
- Vercel Analytics: Frontend performance

## Build Order & Dependencies

### Phase 1: Foundation (Week 1)
1. **Backend skeleton** - FastAPI app, database models, authentication
2. **Frontend skeleton** - Next.js app, basic layout, authentication UI
3. **Database setup** - PostgreSQL schema (Users, Files, ChatMessages)
4. **File upload** - Backend endpoint + frontend component (no AI yet)

**Dependencies:** PostgreSQL → Backend models → API endpoints → Frontend UI

### Phase 2: AI Agents (Week 2)
1. **Onboarding Agent** - Standalone function: file → metadata
2. **Coding Agent** - Standalone function: query → Python code
3. **Code Checker Agent** - Validation rules + RestrictedPython integration
4. **LangGraph Orchestrator** - Wire agents together with shared state

**Dependencies:** Individual agents → LangGraph workflow → Testing with mock data

### Phase 3: Sandbox Security (Week 2-3)
1. **Docker sandbox** - Basic container execution
2. **gVisor integration** - Add runsc runtime configuration
3. **Validation layer** - RestrictedPython + custom rules
4. **Resource limits** - Memory, CPU, timeout enforcement

**Dependencies:** Docker setup → gVisor runtime → RestrictedPython → Integration with Code Checker

### Phase 4: Integration (Week 3)
1. **Chat endpoint** - FastAPI SSE streaming endpoint
2. **Agent workflow integration** - Connect chat → LangGraph → sandbox
3. **Frontend streaming** - Next.js SSE client, Data Card rendering
4. **Per-file chat history** - Database queries + frontend tabs

**Dependencies:** Backend streaming → Frontend SSE → UI components → Database persistence

### Phase 5: Polish & Deploy (Week 4)
1. **Settings page** - Profile editing, password change
2. **Error handling** - Graceful failures throughout pipeline
3. **LangSmith integration** - Environment variables only
4. **Deployment** - Docker Compose local → Vercel + Railway production

**Parallel tasks:** Settings (independent), LangSmith (config only), Error handling (throughout)

## Sources

### High Confidence (Official Documentation & Recent 2025-2026 Sources)

- [LangChain Multi-Agent Architecture Patterns](https://www.blog.langchain.com/choosing-the-right-multi-agent-architecture/) - Four core patterns: subagents, skills, handoffs, routers
- [LangGraph Workflows and Agents Documentation](https://docs.langchain.com/oss/python/langgraph/workflows-agents) - Official workflow patterns
- [4 Ways to Sandbox Untrusted Code in 2026](https://dev.to/mohameddiallo/4-ways-to-sandbox-untrusted-code-in-2026-1ffb) - Comparison of sandbox approaches
- [Setting Up a Secure Python Sandbox for LLM Agents](https://dida.do/blog/setting-up-a-secure-python-sandbox-for-llm-agents) - gVisor architecture patterns
- [gVisor Security Introduction](https://gvisor.dev/docs/architecture_guide/intro/) - Official gVisor documentation
- [What's the Best Code Execution Sandbox for AI Agents in 2026?](https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents) - Sandbox comparison
- [How to Sandbox LLMs & AI Shell Tools](https://www.codeant.ai/blogs/agentic-rag-shell-sandboxing) - Docker, gVisor, Firecracker comparison

### Medium Confidence (Multiple Community Sources)

- [Building Multi-Agent Workflows with LangChain](https://www.ema.co/additional-blogs/addition-blogs/multi-agent-workflows-langchain-langgraph) - Practical implementation patterns
- [Data Engineering Trends 2026 for AI-Driven Enterprises](https://www.trigyn.com/insights/data-engineering-trends-2026-building-foundation-ai-driven-enterprises) - Data architecture patterns
- [AI-First Data Architecture: The Future of Enterprise Intelligence](https://www.altimetrik.com/blog/ai-first-data-architecture-enterprise-guide) - Architectural trends
- [Next.js FastAPI Template](https://www.vintasoftware.com/blog/next-js-fastapi-template) - Architecture separation patterns
- [Modern SPA Development with Next.js and FastAPI](https://blog.greeden.me/en/2025/06/16/modern-spa-development-with-next-js-and-fastapi-a-complete-guide-from-design-to-operation/) - Full-stack architecture guide

---

**Architecture Research for:** AI-Powered Data Analytics Platform with Secure Code Execution
**Researched:** 2026-02-02
**Confidence:** HIGH - Architecture patterns verified with official LangChain/LangGraph documentation, gVisor security documentation, and multiple 2025-2026 production implementation guides
