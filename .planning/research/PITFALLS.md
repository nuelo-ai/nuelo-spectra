# Pitfalls Research

**Domain:** AI-Powered Data Analytics Platform with Code Generation & Sandbox Execution
**Researched:** 2026-02-02
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: AI Code Hallucinations — Generating Non-Existent pandas Functions

**What goes wrong:**
LLMs generate syntactically correct Python code that calls non-existent pandas/numpy functions (e.g., `pd.read_exel()` instead of `pd.read_excel()`, or inventing functions like `df.advanced_stats()` that don't exist). The code looks correct in the chat but fails at runtime, producing cryptic errors that confuse users and destroy trust in the AI's analysis.

**Why it happens:**
LLMs learn patterns from training data but hallucinate function names by combining real patterns. A 2026 study found that pandas-specific hallucinations have only a 56.2% fix accuracy rate (vs. 97.9% for missing imports), making them particularly persistent. With 30% of code being AI-generated in 2026 and 97% of developers using AI tools, this is widespread.

**How to avoid:**
1. **Code Checker Agent with AST validation** — Parse generated code with Python's `ast` module and validate all function calls against allowlists of pandas/numpy/matplotlib APIs before execution
2. **Unit test generation** — Have Code Checker Agent generate simple assertions (e.g., "result should be DataFrame") and run them before showing results to users
3. **Deterministic hallucination detection** — Use static analysis to catch undefined attributes/methods (research shows 77.0% fix accuracy with this approach)
4. **LLM grounding with official docs** — Provide pandas API reference in context when generating code (via RAG or few-shot examples)

**Warning signs:**
- User reports "error says function doesn't exist"
- Traceback shows `AttributeError: 'DataFrame' object has no attribute 'X'`
- Code works in development but fails with user data (hallucinated function doesn't handle edge cases)
- High ratio of code execution failures vs. successful runs

**Phase to address:**
**Phase 2: AI Agents** — Implement Code Checker Agent with function validation before Coding Agent goes to production. This is non-negotiable for core value (accurate analysis).

---

### Pitfall 2: Sandbox Escape via Container Vulnerabilities

**What goes wrong:**
Malicious or accidentally harmful user code escapes Docker sandbox and compromises the host system. Attackers exploit kernel-level CVEs (all containers share the same kernel), redirect writes to critical system files like `~/.zshrc` or `~/.gitconfig` to establish persistence, or use container runtime vulnerabilities to escalate privileges. A single escape can expose all users' data and destroy the entire platform.

**Why it happens:**
Docker provides process-level isolation but shares the kernel. CVE-2025-52881 (CVSS 9.8) demonstrated critical sandbox escape via promise sanitization bypass. Container escapes stem from architectural weaknesses where kernel vulnerabilities provide direct privilege escalation paths. Solo developers skip multi-layer defense due to complexity and time pressure (2-4 week timeline).

**How to avoid:**
1. **Multi-layer defense (mandatory)**:
   - **Layer 1:** RestrictedPython AST validation to block dangerous constructs at compile-time
   - **Layer 2:** Docker container isolation with `--network=none` (no network access)
   - **Layer 3:** gVisor user-space kernel to intercept system calls (blocks kernel-level escapes)
   - **Layer 4:** Resource limits (`--memory=512m --cpus=0.5 --timeout=30s`)
   - **Layer 5:** Read-only root filesystem, whitelist writable directories
2. **Block file writes outside workspace** — Prevent writes to `~/.zshrc`, `~/.bashrc`, `~/.gitconfig`, `/etc/` (persistence mechanisms)
3. **Disable network egress** — Block external API calls to prevent data exfiltration
4. **Regular security updates** — Subscribe to CVE alerts for Docker/gVisor/RestrictedPython
5. **Consider managed sandbox** — E2B Cloud or Pyodide for serverless if can't maintain Docker security

**Warning signs:**
- Code execution hangs or times out repeatedly
- Unexplained system resource consumption on host
- Network traffic from sandbox containers (should be zero if `--network=none`)
- File modifications in non-whitelisted directories
- Security scanner reports outdated Docker/gVisor versions

**Phase to address:**
**Phase 4: Sandbox Security** — Must be completed before any user code execution. Do NOT defer this to post-MVP. Sandbox escape destroys entire product and all user data.

---

### Pitfall 3: Streaming Response Connection Failures Without Graceful Recovery

**What goes wrong:**
User asks question, sees AI "thinking" for 10 seconds, then connection drops silently. No error message, no partial results, no way to resume. User refreshes and loses entire conversation history. This happens during long analysis queries (complex pandas operations) when SSE connection times out or network hiccups occur. Users perceive the product as broken and unreliable.

**Why it happens:**
SSE connections are long-lived HTTP connections that break easily (mobile networks, proxy timeouts, browser tab backgrounding). FastAPI StreamingResponse generators can throw exceptions after headers are sent, leaving no way to return HTTP error codes. Developers test on localhost (stable connection) and miss production network instability. Solo developer focuses on happy path without implementing reconnection logic.

**How to avoid:**
1. **Client-side reconnection** — Use EventSource with automatic retry (browsers retry SSE by default, but configure retry interval from server: `yield {"event": "retry", "data": "3000"}` for 3s)
2. **Server-side disconnect detection** — Check `if await request.is_disconnected()` in streaming generator and stop processing immediately to free resources
3. **Checkpoint partial results** — Store intermediate Data Card state in database during streaming, allow resume from last checkpoint if connection drops
4. **Yield error events** — Instead of raising exceptions, yield `{"event": "error", "data": json.dumps({"status": 500, "message": "..."})}` to notify client
5. **Progress indicators** — Yield progress events (`{"event": "progress", "data": "30%"}`) so client knows processing is still alive
6. **Timeout configuration** — Set realistic timeouts on both client (EventSource) and server (uvicorn `--timeout-keep-alive 300`)

**Warning signs:**
- Users report "stuck loading" or "nothing happens"
- Server logs show `StreamingResponse` generator exceptions after headers sent
- High ratio of incomplete streaming requests (monitor connection duration)
- Client EventSource shows `readyState === 2` (CLOSED) without receiving "done" event
- Spike in user complaints after deploying to cloud (vs. localhost testing)

**Phase to address:**
**Phase 3: Streaming Infrastructure** — Build robust streaming before Data Cards UI. Test with network throttling, connection drops, and long-running queries (>30s).

---

### Pitfall 4: Uncontrolled LLM Token Costs Leading to Budget Exhaustion

**What goes wrong:**
Production costs explode from $100/month estimate to $5,000/month after 2 weeks. Users trigger expensive queries (uploading 50MB CSV with 100K rows, asking "analyze everything"), running multiple agents (Onboarding + Coding + Code Checker + Data Analysis) on every request. Output tokens cost 3-10x more than input tokens, and long pandas code outputs drain budget. With no rate limiting, a single user can cost $500/day.

**Why it happens:**
Developers estimate costs based on input token pricing ($1/million) but actual cost is $4/million with 1:3 input/output ratio. Solo developer ships MVP without cost monitoring. Multi-agent systems multiply costs (4 agents = 4x API calls per query). Users don't understand that larger files = higher costs. No per-user quotas or cost alerts mean runaway usage goes undetected until bill arrives.

**How to avoid:**
1. **Token-aware rate limiting** — Limit tokens per user per minute/hour/day, not just request count (one request can use 100K tokens)
2. **Input/output token budgets** — Set max_tokens on LLM calls to cap output length (e.g., `max_tokens=2000` for code generation)
3. **Caching layer** — Cache similar queries (Redis) to avoid redundant API calls (15-30% token reduction)
4. **Model routing** — Use cheaper models (GPT-4o-mini) for simple queries, expensive models (GPT-4o) only for complex analysis
5. **Batch processing** — For non-real-time tasks (file onboarding), use OpenAI Batch API (50% discount)
6. **Per-user cost tracking** — Log token usage per user in database, set hard caps (e.g., 1M tokens/month per user)
7. **Cost alerts** — Email admin when daily cost exceeds threshold (e.g., $50/day)
8. **File size warnings** — Warn users that large files cost more to analyze

**Warning signs:**
- LLM API bill increases >2x week-over-week without user growth
- Single user accounts for >50% of daily token usage
- Average output tokens per request >5000 (generating excessive code)
- Multiple retries/re-generations for same query (hallucination loop)
- No cost monitoring dashboard or alerts configured

**Phase to address:**
**Phase 2: AI Agents** — Implement cost controls when building agents. Add monitoring before production launch. This prevents catastrophic budget overruns in first month.

---

### Pitfall 5: Multi-Tenant Data Isolation Failure — One User Accessing Another's Files

**What goes wrong:**
User A uploads confidential financial data. User B exploits file path vulnerability and downloads User A's data. This violates data privacy laws (GDPR, state privacy laws), destroys user trust, and exposes company to lawsuits (e.g., T-Mobile paid $350M for 2021 cloud breach). The platform becomes legally unusable for commercial data.

**Why it happens:**
Developer stores files in shared directory structure (`/uploads/{filename}`) without user segregation, or uses predictable file paths (`/uploads/user_123_data.csv` is guessable). Database queries lack user_id filters (`SELECT * FROM files WHERE id = :file_id` without `AND user_id = :current_user`). IDOR (Insecure Direct Object Reference) vulnerabilities allow user to change file_id in API request. Solo developer skips authorization checks due to time pressure. Code execution sandbox can access all files in `/uploads` directory.

**How to avoid:**
1. **User-specific storage paths** — Store files in non-guessable directories: `/uploads/{user_uuid}/{random_filename}` (e.g., `/uploads/a7f3e8c9-2b4d-4e1f-9a6b-1c3d5e7f9b2c/8f3a2d1b.csv`)
2. **Database-level isolation** — Add `user_id` column to all file/chat/data_card tables, enforce `WHERE user_id = :current_user` in ALL queries
3. **Authorization middleware** — Every file access goes through authorization check: `if file.user_id != current_user.id: raise HTTPException(403)`
4. **Sandbox environment variables** — Pass only authorized file paths to sandbox, not entire `/uploads` directory
5. **Object-level permissions** — Use UUIDs for file IDs (not auto-increment integers), verify ownership before access
6. **Audit logging** — Log all file accesses with user_id and file_id for security monitoring
7. **Penetration testing** — Test IDOR vulnerabilities before launch (try accessing other users' file IDs)

**Warning signs:**
- API endpoints accept file_id without user_id verification
- File paths use sequential integers or predictable patterns
- Database queries don't filter by user_id
- Sandbox mounts entire `/uploads` directory instead of user-specific subdirectory
- No authorization tests in test suite
- User can see file count/metadata that doesn't match their uploads

**Phase to address:**
**Phase 1: Backend Architecture** — Design user isolation from the start. Retrofitting authorization after building features causes rewrites. This is non-negotiable for commercial SaaS (legal requirement).

---

### Pitfall 6: Multi-Agent Orchestration Failures Without Observability

**What goes wrong:**
User asks question, AI generates code, Code Checker rejects it, Coding Agent retries with same hallucination, infinite loop exhausts retries, user sees "Analysis failed" with no explanation. Developer can't debug because agent decisions are non-deterministic and logs don't show why Code Checker rejected code or what context was passed between agents. 32% of organizations cite quality as top production barrier.

**Why it happens:**
LangChain agents make dynamic decisions that vary between runs even with identical prompts. Context degradation occurs during agent handoffs (Coding Agent → Code Checker → Data Analysis). Without tracing, developers can't see why agents made specific decisions. Centralized orchestration (single manager agent) creates single point of failure. Solo developer skips observability tools to save time. Non-determinism makes traditional debugging (print statements, breakpoints) ineffective.

**How to avoid:**
1. **LangSmith tracing (mandatory)** — Set environment variable `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY=xxx`. Zero code changes, automatic tracing of all agent steps, tool calls, and LLM interactions. 89% of organizations use observability (table stakes in 2026).
2. **Structured logging** — Log agent decisions with context: `logger.info(f"Code Checker rejected code: {reason}, original_query={query}, generated_code={code}")`
3. **Retry limits with backoff** — Configure `max_retries=3` with exponential backoff (1s, 2s, 4s) to prevent infinite loops
4. **Circuit breaker pattern** — After 3 consecutive failures from same agent, stop calling it and return actionable error
5. **Agent error recovery** — If Code Checker rejects code, pass rejection reason back to Coding Agent with instruction to fix specific issue
6. **Checkpointing** — LangGraph persists errors in checkpoints for inspection and manual recovery
7. **Fallback strategies** — Define simpler analysis workflow if complex multi-agent flow fails

**Warning signs:**
- "Analysis failed" errors with no details about which agent failed or why
- Users report "AI keeps making same mistake"
- Retry loops consume excessive tokens without progress
- Can't reproduce failures in development (non-deterministic)
- Agent execution time varies wildly for similar queries (5s vs. 60s)
- No visibility into which agent is currently processing request

**Phase to address:**
**Phase 2: AI Agents** — Add LangSmith tracing when building first agent (single environment variable). Build circuit breaker and retry logic into agent orchestration before production.

---

### Pitfall 7: pandas Memory Exhaustion on Large Files Without Chunking

**What goes wrong:**
User uploads 40MB CSV with 500K rows. Backend loads entire file into pandas DataFrame (`pd.read_csv(file)`), consuming 2GB+ RAM. Container hits memory limit (512MB), process killed by OOM (Out of Memory), user sees "Analysis failed". Even if container has more RAM, multiple concurrent users exhaust server memory. Users can't analyze real-world datasets despite product marketing "up to 50MB files."

**Why it happens:**
pandas loads entire file into memory by default. DataFrames use 3-10x more memory than CSV size (40MB CSV → 200MB+ DataFrame due to Python object overhead). int64 uses 8x more memory than int8, and string columns use massive memory without categorical optimization. Developer tests with small sample files (5MB, 10K rows) and misses production scale. Container memory limits assumed sufficient based on CSV file size, not DataFrame size.

**How to avoid:**
1. **Chunked reading** — Use `pd.read_csv(file, chunksize=10000)` to process 10K rows at a time, aggregate results
2. **Memory optimization** — Downcast dtypes (`int64 → int16` for small numbers, use `category` dtype for low-cardinality strings)
3. **Lazy loading** — Use `usecols` parameter to load only required columns (can reduce memory from 71MB to 8MB)
4. **Memory estimation** — Check file size, estimate DataFrame memory = file_size * 5, reject if exceeds container limit
5. **Alternative engines** — Use Dask for files >1GB (processes in parallel chunks, utilizes multiple CPU cores)
6. **Streaming analysis** — For operations like row counts, use streaming without loading full DataFrame
7. **Container memory limits** — Set `--memory=2g` for data processing containers, monitor with `docker stats`
8. **File size warnings** — Warn users: "Files >10MB may take longer" or "Recommend <25MB for fast analysis"

**Warning signs:**
- OOM kills in container logs (`Killed by signal 9`)
- Process memory usage spikes to 100% during file processing
- Docker stats shows memory at limit during CSV reads
- "Analysis failed" only happens with larger files (>20MB)
- Container restarts automatically after memory exhaustion
- Concurrent users cause cascading memory failures

**Phase to address:**
**Phase 4: Data Processing** — Implement before supporting 50MB file limit. Test with real-world file sizes (50MB) with concurrent users to validate memory safety.

---

### Pitfall 8: File Upload Validation Bypass Leading to Code Injection

**What goes wrong:**
Attacker uploads malicious file disguised as CSV (e.g., `malicious.csv` containing Python code, or `exploit.xlsx` with macro formulas). Backend validates file extension only (`.csv`, `.xlsx`), not content. File gets processed by pandas, executes malicious code, compromises sandbox or exfiltrates data. MIME type validation fails because `Content-Type` header is client-controlled and easily spoofed.

**Why it happens:**
Developer validates file extension (`.csv`, `.xlsx`) without validating actual file content. Checking `file.content_type` header is insufficient (attacker controls this). pandas `read_csv()` can execute malicious payloads if file contains crafted content. No file size limits enforced (DoS via 1GB upload). Solo developer ships basic validation to meet timeline. Input validation is often afterthought in rapid development.

**How to avoid:**
1. **Content-based validation** — Read first bytes and validate file signature (CSV: plaintext, XLSX: ZIP magic bytes `PK\x03\x04`)
2. **File size limits (multi-layer)**:
   - **Client-side:** Check file size before upload
   - **Nginx:** `client_max_body_size 50M;`
   - **FastAPI middleware:** Check `Content-Length` header, reject before reading body
   - **Streaming validation:** Count bytes during read, abort if exceeds limit
3. **MIME type validation (defense-in-depth)** — Validate `Content-Type` header against allowlist (`['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']`) but don't rely on it alone
4. **Pandas safe reading** — Avoid eval-based features, disable Excel macro execution
5. **File sanitization** — Re-encode CSV to strip potential exploits before processing
6. **Checksum verification** — Calculate SHA-256 hash for deduplication and integrity checking
7. **Rate limiting** — Limit upload frequency per user (e.g., 10 uploads/hour) to prevent DoS

**Warning signs:**
- File validation only checks extension or `Content-Type` header
- No file size limits configured in Nginx/FastAPI
- No integration tests for malicious file uploads
- Users can upload files >50MB despite stated limit
- No checksum or content validation before pandas processing
- Upload endpoint has no rate limiting

**Phase to address:**
**Phase 1: Backend Infrastructure** — Implement before file upload feature. Multi-layer validation is security basics. Retrofitting after launch exposes vulnerability window.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip Code Checker Agent for MVP | Ship 2 weeks faster with 3 agents instead of 4 | AI generates incorrect/unsafe code, users lose trust, manual validation impossible at scale | Never — Code Checker is core value (accuracy) |
| Use single-layer sandbox (Docker only, no gVisor) | Simpler setup, faster deployment | Kernel CVEs enable container escape, all user data exposed | Never — Multi-layer defense is security basics |
| No LangSmith observability in v1 | Save setup time (5 minutes) | Can't debug agent failures, blind to production issues, 32% cite quality as blocker | Never — Single env variable, zero code changes |
| Store files in shared directory without user isolation | Faster to implement, simpler file paths | IDOR vulnerabilities, data privacy violations, legal liability | Never — Retrofitting authorization causes rewrites |
| No token cost limits or monitoring | Ship faster without rate limiting infrastructure | Budget exhaustion ($5K/month surprise), no per-user quotas, can't identify expensive users | Acceptable for private beta with 5 users, NOT for public launch |
| Validate file extension only (`.csv`) | Simple one-line check | Content-based attacks bypass validation, malicious files compromise sandbox | Never — Multi-layer validation is table stakes |
| No SSE reconnection logic | Works on localhost stable connection | Production network instability breaks streaming, users see "stuck loading" | Acceptable for internal demo, NOT for MVP |
| Load full CSV into pandas without chunking | Simpler code, works for small test files | OOM kills with real file sizes (>20MB), can't support advertised 50MB limit | Acceptable if file limit is <10MB AND enforced |
| Auto-increment integer file IDs | Easier to debug, simpler queries | Guessable IDs enable IDOR attacks, users can access others' files | Never — UUIDs are industry standard for object IDs |
| No circuit breaker in agent orchestration | Simpler retry logic | Infinite hallucination loops waste tokens, users see no progress, costs spike | Acceptable for private beta, add before scaling |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenAI/Anthropic LLM APIs | Estimating cost based on input token pricing only | Output tokens cost 3-10x more. Calculate costs with realistic input/output ratio (1:3 for code generation). Monitor both input and output token usage. |
| LangChain callbacks for streaming | Raising exceptions in StreamingResponse generator after headers sent | Yield error events in SSE format: `{"event": "error", "data": {...}}`. Exceptions after headers sent can't return proper HTTP status codes. |
| Docker sandbox networking | Leaving default network enabled (sandbox can call external APIs) | Use `--network=none` to disable all network access. If external APIs needed, use allowlist-based custom bridge network. |
| PostgreSQL with asyncpg | Using synchronous pandas operations in async FastAPI handlers | Use `asyncio.to_thread()` for pandas CPU-bound work: `await asyncio.to_thread(pd.read_csv, file)`. Blocking operations stall event loop. |
| File uploads with python-multipart | Loading full file into memory before validation | Stream file to disk with size limit: read in chunks (1MB), validate as you go, abort if size/content validation fails. |
| LangSmith tracing | Adding custom logging that duplicates LangSmith traces | LangSmith automatically traces all LangChain operations. Only add custom logs for non-LangChain operations (pandas, business logic). |
| FastAPI SSE with EventSource | No keep-alive ping, connections timeout during long processing | Yield periodic ping events: `yield {"event": "ping", "data": ""}` every 15s to keep connection alive. |
| pandas read_excel for .xlsx | Using deprecated xlrd engine | Explicitly specify engine: `pd.read_excel(file, engine='openpyxl')`. xlrd is deprecated for .xlsx files. |
| Docker resource limits | Setting CPU/memory limits after OOM incidents | Set limits proactively: `--memory=2g --cpus=2.0 --pids-limit=100`. Prevents resource exhaustion from impacting other containers. |
| gVisor runtime for Docker | Assuming all pandas packages work in gVisor | Some native extensions may fail in gVisor. Test pandas, numpy, matplotlib with gVisor before production. Fallback to E2B if compatibility issues. |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading full CSV into pandas without chunking | Single-file analysis works, crashes with realistic file sizes | Use `chunksize` parameter, optimize dtypes (int64→int16, use category), estimate memory = file_size * 5 | Files >20MB, or 2+ concurrent users with 10MB files |
| No connection pooling for PostgreSQL | First queries fast, then slow as connections accumulate | Use SQLAlchemy with asyncpg pool: `pool_size=20, max_overflow=10`. Connection reuse prevents exhaustion. | 50+ concurrent users (each request creates new connection) |
| Synchronous pandas operations in async FastAPI | Single request fast, concurrent requests queue up | Use `await asyncio.to_thread(pd.read_csv, file)` to run pandas in thread pool. Prevents event loop blocking. | 5+ concurrent analysis requests |
| Generating new code for repeated queries | Works initially, token costs grow linearly with users | Cache generated code by query hash. 15-30% token reduction for common queries like "show first 10 rows". | 100+ daily active users (costs spike) |
| Storing all files in single directory | Works for 10 files, `ls` slows down at scale | Use nested directories: `/uploads/{user_id[:2]}/{user_id}/file`. Limits files per directory to <1000. | 10K+ files (filesystem performance degrades) |
| No query timeout in agent execution | Simple queries return fast, complex queries hang | Set LLM timeout: `request_timeout=60` and sandbox timeout: `docker run --timeout=30s`. Prevent runaway queries. | Users ask complex queries ("analyze all correlations in 100K rows") |
| In-memory session storage (no Redis) | Single server works, horizontal scaling impossible | Use Redis for sessions/cache from day one. Enables multi-server deployment. | Scaling beyond 1 FastAPI server instance |
| No file cleanup strategy | Storage works initially, disk fills up | Implement TTL: delete uploaded files after 30 days (or when user deletes). Monitor disk usage alerts. | 1000+ file uploads (depends on file sizes) |
| Streaming without backpressure | Frontend processes chunks fast, no issues | Implement backpressure: pause streaming if client can't keep up. Prevents memory buildup in buffers. | Slow client connections or large result sets (>10K rows) |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Single-layer sandbox (Docker only) | Container escape via kernel CVEs exposes all user data and host system | Multi-layer: RestrictedPython + Docker + gVisor + resource limits + network isolation. Defense in depth is mandatory. |
| Shared file directory without user isolation | User A can access User B's confidential data via IDOR attacks | Store files in user-specific paths: `/uploads/{user_uuid}/{random_filename}`. Enforce user_id filters in all database queries. |
| No function allowlist in Code Checker | AI generates code calling `os.system()`, `eval()`, `__import__()`, bypassing sandbox | Validate AST against allowlist of safe functions (pandas, numpy, matplotlib only). Reject code with dangerous imports/calls. |
| Network access enabled in sandbox | Generated code exfiltrates user data to attacker-controlled server | Use `docker run --network=none`. If external APIs needed, use strict allowlist with proxy. |
| No file content validation (only extension) | Malicious files disguised as .csv contain exploit payloads | Validate file signature (magic bytes), re-encode to strip potential exploits, run pandas in isolated sandbox. |
| Writing sandbox results to shared directory | Race conditions allow user to read another user's analysis results | Write results to user-specific temporary directory with randomized names, clean up after serving response. |
| No output sanitization from sandbox | Generated matplotlib plots contain malicious SVG/PNG payloads | Sanitize all sandbox outputs (images, tables, text) before serving to frontend. Validate file types. |
| Unlimited agent retries without circuit breaker | Hallucination loops waste tokens, user stuck in infinite failures | Limit retries to 3, implement exponential backoff, break circuit after consecutive failures, return actionable error. |
| Auto-increment IDs for files/data_cards | Predictable IDs enable enumeration attacks (user guesses other IDs) | Use UUIDs for all user-owned resources. Never expose sequential integer IDs. |
| No rate limiting on file uploads | Attacker uploads 1000 files, exhausts storage and processing capacity | Rate limit: 10 uploads/hour per user, max 20 files total per user, auto-delete old files after 30 days. |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent SSE connection failures | User sees "Loading..." forever, no error, no way to resume | Implement auto-reconnect with EventSource, yield progress events every 5s, show "Connection lost, retrying..." message. |
| No progress indication during long analysis | User thinks app is frozen, refreshes page, loses work | Stream progress events: "Generating code...", "Running analysis...", "Preparing results...". Show spinner with status text. |
| Generic error messages ("Analysis failed") | User can't debug issue, doesn't know if it's their data or system bug | Return actionable errors: "Your CSV has missing column 'sales'. Please check column names." Link to docs. |
| No file size/complexity warnings | User uploads 50MB file, waits 2 minutes, surprised by slowness | Warn before upload: "Files >10MB may take 30-60s to analyze." Show estimated processing time based on file size. |
| Losing chat history on connection drop | User refreshes page, entire conversation gone, has to start over | Persist chat messages in database during streaming, reload on reconnect, show "Resuming from last message..." |
| No visibility into AI thinking process | User sees final answer, doesn't trust it (black box AI) | Stream intermediate steps: show generated code, Code Checker validation, execution logs in expandable sections. |
| File upload without immediate feedback | User clicks upload, nothing happens for 5s, clicks again (duplicate upload) | Show upload progress bar, "Analyzing file structure..." status, then "Ready to chat" confirmation with file metadata. |
| Data Cards without export/copy options | User sees great analysis, can't share with team or save for later | Add "Copy table to clipboard", "Download as CSV" buttons (even if PDF export is v2 feature). |
| No example queries or suggestions | New user stares at empty chat box, doesn't know what to ask | Show query suggestions based on detected columns: "What's the average sales by region?", "Show me top 10 customers". |
| Overwhelming users with technical errors | User sees Python traceback with pandas error, gets confused | Translate technical errors to plain language: "We couldn't parse column 'date'. Try formatting dates as YYYY-MM-DD." |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Code execution sandbox:** Often missing gVisor isolation layer — verify `docker info | grep Runtime` shows `runsc` not `runc`
- [ ] **File upload validation:** Often missing content-based validation — verify file signature check (magic bytes) not just extension/MIME type
- [ ] **Multi-agent orchestration:** Often missing LangSmith tracing — verify `LANGCHAIN_TRACING_V2=true` set and traces visible in LangSmith dashboard
- [ ] **SSE streaming:** Often missing reconnection logic — verify EventSource auto-reconnects by testing with network throttling/disconnect
- [ ] **User data isolation:** Often missing user_id filters in database queries — verify all file/chat queries include `WHERE user_id = :current_user`
- [ ] **Token cost controls:** Often missing per-user rate limits — verify token budgets enforced at user level, not just global limits
- [ ] **pandas memory optimization:** Often missing chunked reading for large files — verify `chunksize` parameter used for files >10MB
- [ ] **Error handling in agents:** Often missing circuit breaker — verify retry limit enforced (max 3) with exponential backoff, not infinite retries
- [ ] **File size limits:** Often missing multi-layer enforcement — verify limits at Nginx, FastAPI middleware, and streaming read (not just client-side)
- [ ] **Code validation in Code Checker:** Often missing function allowlist — verify AST parsing rejects `os.system()`, `eval()`, `exec()`, `__import__()` calls
- [ ] **Docker resource limits:** Often missing or too generous — verify `--memory`, `--cpus`, `--pids-limit` set to prevent resource exhaustion
- [ ] **Network isolation in sandbox:** Often left at default (network enabled) — verify `docker inspect` shows `NetworkMode: "none"`

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| AI code hallucinations in production | MEDIUM | 1. Enable LangSmith to identify hallucination patterns. 2. Add failing examples to Code Checker's validation rules. 3. Update prompt with "Do not use non-existent pandas functions". 4. Consider switching to newer LLM model with better code accuracy. |
| Sandbox escape via container vulnerability | HIGH | 1. Immediately isolate affected container, rotate all API keys. 2. Audit access logs for data exfiltration. 3. Update Docker/gVisor to patched versions. 4. Add Layer 3 (gVisor) if not present. 5. Notify affected users if data breach confirmed. |
| SSE connection failures losing user work | LOW | 1. Implement database persistence for chat messages retroactively. 2. Add EventSource reconnection logic in frontend. 3. Show "Reconnecting..." UI state. 4. Test with network disruption before redeploying. |
| Budget exhaustion from uncontrolled token usage | MEDIUM | 1. Add emergency rate limits immediately (e.g., 100K tokens/user/day). 2. Audit top token consumers, identify abuse or bugs. 3. Implement per-user cost tracking retroactively. 4. Set up alerts for daily cost >$X threshold. 5. Contact top users to discuss usage patterns. |
| Multi-tenant data isolation failure (IDOR) | HIGH | 1. Immediate: Patch vulnerable endpoints with user_id authorization checks. 2. Audit all database queries for missing user_id filters. 3. Review access logs to identify if breach occurred. 4. Add object-level permission tests to prevent regression. 5. Consider switching to UUIDs for all object IDs. 6. Legal: Assess data breach notification requirements. |
| pandas memory exhaustion (OOM) | MEDIUM | 1. Increase container memory limits temporarily (e.g., 512MB → 2GB). 2. Implement chunked reading for files >10MB. 3. Add memory estimation before processing (reject if exceeds limit). 4. Optimize dtypes (int64→int16, use category). 5. Consider switching to Dask for large files. |
| File upload validation bypass | MEDIUM | 1. Add content-based validation immediately (magic bytes check). 2. Audit uploaded files for suspicious content. 3. Re-validate existing files, quarantine suspicious ones. 4. Add file sanitization step before pandas processing. 5. Scan with antivirus/malware detection. |
| Multi-agent orchestration failures without observability | MEDIUM | 1. Add LangSmith tracing immediately (single env variable). 2. Review traces to identify failure patterns. 3. Implement circuit breaker to prevent retry loops. 4. Add structured logging for custom business logic. 5. Create runbook for common agent failure scenarios. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| AI code hallucinations | Phase 2: AI Agents | Run test suite with 50 diverse queries, Code Checker catches all hallucinated functions (0 false negatives), AST validation rejects dangerous code |
| Sandbox escape | Phase 4: Sandbox Security | Security audit confirms multi-layer defense (RestrictedPython + Docker + gVisor), penetration test shows no escape vectors, network traffic monitoring shows zero external connections |
| Streaming connection failures | Phase 3: Streaming Infrastructure | Network disruption test (disconnect during 30s streaming), EventSource auto-reconnects, partial results preserved, user sees "Reconnecting..." message |
| Uncontrolled LLM costs | Phase 2: AI Agents | Per-user token limits enforced, daily cost alerts configured, LangSmith dashboard shows cost attribution per user, test user hitting limit sees rate limit error |
| Data isolation failure | Phase 1: Backend Architecture | Penetration test shows user cannot access other users' files, all database queries filtered by user_id, object IDs use UUIDs not integers, authorization tests pass |
| pandas memory exhaustion | Phase 4: Data Processing | Load test with 10 concurrent users uploading 50MB files, containers stay under memory limit, chunked reading works for 100K+ row files, no OOM kills |
| File upload validation bypass | Phase 1: Backend Infrastructure | Security test with malicious files (renamed executables, crafted CSV payloads) rejected by content validation, file size limits enforced at all layers |
| Multi-agent orchestration failures | Phase 2: AI Agents | LangSmith traces show all agent steps, circuit breaker activates after 3 failures, retry logic uses exponential backoff, errors include actionable messages |

## Sources

### High Confidence (Official Documentation & Recent Research)

- [Detecting and Correcting Hallucinations in LLM-Generated Code via Deterministic AST Analysis](https://arxiv.org/html/2601.19106) — 2026 research showing 56.2% fix rate for pandas hallucinations
- [Container Escape Vulnerabilities: AI Agent Security for 2026 | Blaxel Blog](https://blaxel.ai/blog/container-escape) — Container security architecture
- [NVIDIA Practical Security Guidance for Sandboxing Agentic Workflows](https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk) — Multi-layer sandbox defense
- [Complete LLM Pricing Comparison 2026](https://www.cloudidr.com/blog/llm-pricing-comparison-2026) — Output token pricing (3-10x input cost)
- [LLM economics: How to avoid costly pitfalls](https://www.aiacceleratorinstitute.com/llm-economics-how-to-avoid-costly-pitfalls/) — Token-aware rate limiting
- [LangChain Multi-Agent Orchestration Docs](https://docs.langchain.com/oss/python/langchain/multi-agent) — Official patterns
- [LangSmith Observability](https://www.langchain.com/langsmith/observability) — Tracing and debugging
- [State of Agent Engineering](https://www.langchain.com/state-of-agent-engineering) — 89% use observability, 32% cite quality as blocker

### Medium Confidence (Industry Best Practices & Tutorials)

- [Setting Up a Secure Python Sandbox for LLM Agents](https://dida.do/blog/setting-up-a-secure-python-sandbox-for-llm-agents) — gVisor architecture
- [FastAPI File Upload Security Best Practices](https://betterstack.com/community/guides/scaling-python/uploading-files-using-fastapi/) — Multi-layer validation
- [FastAPI Streaming SSE Error Handling](https://github.com/fastapi/fastapi/discussions/10138) — Yielding error events
- [Docker Security Best Practices 2026](https://betterstack.com/community/guides/scaling-docker/docker-security-best-practices/) — Resource limits and isolation
- [LangChain Agent Error Handling Best Practices](https://benny.ghost.io/blog/langchain-agent-error-handling-best-practices/) — Circuit breaker patterns
- [pandas Memory Optimization Guide](https://thinhdanggroup.github.io/pandas-memory-optimization/) — Chunking and dtype optimization
- [Multi-Tenant Data Isolation Architecture](https://medium.com/@justhamade/architecting-secure-multi-tenant-data-isolation-d8f36cb0d25e) — Security patterns

### Real-World Incidents & Post-Mortems

- [T-Mobile $350M Settlement for 2021 Cloud Breach](https://www.josys.com/article/multitenancy-how-shared-infrastructure-can-expose-security-vulnerabilities) — Multi-tenant isolation failure
- [CVE-2025-52881 vm2 Sandbox Escape](https://semgrep.dev/blog/2026/calling-back-to-vm2-and-escaping-sandbox/) — CVSS 9.8 container escape
- [30+ Vulnerabilities in AI Coding Tools (IDEsaster)](https://thehackernews.com/2025/12/researchers-uncover-30-flaws-in-ai.html) — Code generation security issues

---

*Pitfalls research for: AI-Powered Data Analytics Platform with Code Generation & Sandbox Execution*
*Researched: 2026-02-02*
*Confidence: HIGH — All critical failure modes verified with 2026 sources and production incident data*
