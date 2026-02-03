# Project Research Summary

**Project:** Spectra - AI-powered data analytics platform
**Domain:** AI agent orchestration + data analysis SaaS
**Researched:** 2026-02-02
**Confidence:** HIGH

## Executive Summary

Spectra is a conversational data analytics platform targeting the gap between consumer tools (ChatGPT) and enterprise BI platforms (Tableau, ThoughtSpot). The product enables users to upload CSV/Excel files and analyze them through natural language chat, with AI generating and executing Python code to produce interactive visualizations. The core differentiators are code transparency (users see generated Python), multi-agent accuracy (4 specialized agents with validation), and production-grade security (multi-layer sandbox isolation).

The recommended architecture uses modern async-first stack (FastAPI + Next.js 16) with LangGraph-based multi-agent orchestration and E2B/gVisor sandboxing for secure code execution. Critical technical decisions: LangGraph over vanilla LangChain for agent loops, gVisor + Docker multi-layer isolation (Python-level sandboxing like RestrictedPython is fundamentally insecure in 2026), SSE streaming for real-time responses, and PostgreSQL with per-file chat isolation. Timeline feasibility for single developer: 2-4 weeks is aggressive but achievable if scope discipline is maintained (defer OAuth, long-term memory, advanced export to v1.x).

The primary risks are AI code hallucinations (56.2% fix accuracy for pandas-specific errors), sandbox escape vulnerabilities (CVE-2025-52881 demonstrated CVSS 9.8 severity), and uncontrolled LLM token costs (output tokens cost 3-10x input, multi-agent amplifies costs). Mitigation requires Code Checker Agent with AST validation, multi-layer sandbox defense, and token-aware rate limiting from day one. These are non-negotiable for MVP credibility and cannot be deferred.

## Key Findings

### Recommended Stack

The stack prioritizes single-developer maintainability, 2-4 week timeline feasibility, and security for AI-generated code execution. Key architectural decision: async-first throughout (FastAPI + asyncpg + Next.js streaming) to support SSE-based real-time responses that are table stakes in 2026.

**Core technologies:**
- **FastAPI 0.115+**: Async-first ASGI framework with native Pydantic v2, 5-10x faster than Flask, ideal for AI streaming responses
- **Next.js 16**: React 19 compatible with built-in streaming support, App Router for server components, excellent single-developer DX
- **PostgreSQL 16+**: Robust relational database with JSON support for chat history, async SQLAlchemy 2.0 integration
- **LangGraph 0.2.65+**: Graph-based agent orchestration with loops/branching (needed for Code Checker retry logic), production-ready state management
- **E2B 1.0+**: Production-grade microVM isolation using Firecracker (~150ms boot), purpose-built for AI code execution (RestrictedPython alone is fundamentally insecure)
- **Python 3.12+**: Latest stable with excellent async support, required for FastAPI/LangGraph ecosystem
- **TypeScript 5.6+**: Type safety critical for AI streaming interfaces, reduces bugs in single-developer context

**Critical security update:** passlib (password hashing) and python-jose (JWT) are abandoned. Use pwdlib with Argon2 and PyJWT instead per FastAPI 2026 recommendations.

**Development tooling:** uv (Python package manager) replaces pip/poetry per FastAPI team 2026 recommendation, Docker + gVisor for containerized sandbox, LangSmith for agent debugging (table stakes - agent debugging without tracing is nightmare fuel).

### Expected Features

Conversational analytics is table stakes in 2026, not a differentiator. 65% of organizations use generative AI regularly - users expect ChatGPT-style streaming and code generation as baseline. Differentiation comes from execution quality (accuracy, transparency, security).

**Must have (table stakes):**
- Natural language query interface with real-time streaming (ChatGPT-style UX expected)
- CSV/Excel file upload (<100MB) with automated data profiling
- Code generation with explanation (transparency builds trust)
- Sandboxed Python execution (security non-negotiable)
- Interactive Data Cards (streaming, sortable results)
- Conversation persistence (survives browser refresh)
- User authentication with per-user data isolation
- Basic export (CSV download for results)

**Should have (competitive advantage):**
- Multi-agent orchestration (Supervisor + 4 specialized agents for higher accuracy)
- Streaming Data Cards (results appear progressively while AI processes)
- Code transparency with edit capability (users verify and customize logic)
- Inline error recovery (AI auto-fixes failed code and retries)
- Two-layer memory (short-term conversation + long-term preferences with pgvector)

**Defer (v2+):**
- OAuth integration (Google, Microsoft) - trigger: >100 users complain about signup friction
- Long-term memory with pgvector - trigger: users returning weekly+ want personalization
- Advanced export (PDF reports, PNG charts) - trigger: users request formatted reports
- SQL data sources - trigger: >10 users request database connections vs file upload
- Real-time collaboration - defer until validated team use case (currently individual-focused)
- Mobile apps - defer until mobile usage >20% of traffic (currently desktop workflow)

**Anti-features to avoid:** Unlimited file sizes (memory exhaustion), support for all data sources (maintenance nightmare), real-time collaboration (10x complexity for rarely-used feature), AI training on user data (GDPR nightmare), unlimited query history (storage bloat).

### Architecture Approach

The architecture uses Next.js frontend with FastAPI backend connected via SSE streaming, LangGraph multi-agent workflow orchestration, and Docker + gVisor multi-layer sandbox for secure code execution. Per-file chat history enables tabbed multi-file workflow with independent conversation contexts.

**Major components:**

1. **Next.js Frontend** — User interface with SSE streaming client, file upload UI, interactive Data Cards, tabbed file management
2. **FastAPI Backend API** — Authentication, file handling, agent orchestration, SSE streaming via StreamingResponse
3. **LangGraph Multi-Agent Orchestrator** — Coordinates 4 specialized agents (Onboarding, Coding, Code Checker, Data Analysis) with shared state and conditional routing
4. **Multi-Layer Sandbox Executor** — Defense-in-depth: RestrictedPython AST validation → Docker containers → gVisor user-space kernel → resource limits → network isolation
5. **PostgreSQL Database** — Users, file metadata, per-file chat history (ChatMessage linked to both user_id and file_id)
6. **Local File Storage** — User-isolated upload directories (/uploads/{user_uuid}/{random_filename})

**Key architectural patterns:**
- **SSE streaming**: Backend streams agent steps through Next.js API route to frontend EventSource client
- **Per-file chat isolation**: ChatMessage table references both file_id and user_id for tabbed multi-file workflow
- **Multi-agent handoffs**: LangGraph sequential workflow with conditional edges (Code Checker decides if code is safe → execute or regenerate)
- **Async-first**: All I/O operations (database, LLM, file) use async/await to prevent blocking

**Data flow:** User uploads file → Onboarding Agent analyzes structure → User asks question via chat → Coding Agent generates Python → Code Checker validates → Sandbox executes → Data Analysis Agent interprets results → Stream to frontend as Data Cards → Persist to PostgreSQL.

### Critical Pitfalls

1. **AI code hallucinations (56.2% fix accuracy)** — LLMs generate syntactically correct Python calling non-existent pandas functions (e.g., `df.advanced_stats()`). Mitigation: Code Checker Agent with AST validation against function allowlists, unit test generation, deterministic hallucination detection (77.0% fix accuracy with static analysis).

2. **Sandbox escape via container vulnerabilities** — CVE-2025-52881 (CVSS 9.8) demonstrated critical container escapes. Single-layer Docker insufficient. Mitigation: Multi-layer defense (RestrictedPython + Docker + gVisor + resource limits + network isolation). E2B Cloud or self-hosted gVisor are only viable options. Python-level sandboxing (RestrictedPython alone) is fundamentally insecure per 2026 research.

3. **Streaming connection failures without recovery** — SSE connections break during long queries (mobile networks, proxy timeouts), user sees infinite loading. Mitigation: Client-side auto-reconnect with EventSource, server disconnect detection (`await request.is_disconnected()`), checkpoint partial results in database, yield error events instead of raising exceptions.

4. **Uncontrolled LLM token costs** — Output tokens cost 3-10x more than input, multi-agent systems multiply costs (4 agents = 4x API calls). Budget can explode from $100/month to $5,000/month. Mitigation: Token-aware rate limiting (per user, not just request count), max_tokens caps on outputs, caching layer for common queries (15-30% reduction), model routing (GPT-4o-mini for simple queries).

5. **Multi-tenant data isolation failure (IDOR)** — User A accesses User B's files via predictable IDs or missing user_id filters in database queries. Legal liability (GDPR violations, T-Mobile paid $350M for 2021 breach). Mitigation: User-specific storage paths with UUIDs, database queries with mandatory `WHERE user_id = :current_user`, object-level permissions, penetration testing for IDOR vulnerabilities.

## Implications for Roadmap

Based on research, recommended 5-phase structure for 2-4 week timeline:

### Phase 1: Backend Foundation + Authentication
**Rationale:** User isolation must be designed from day one - retrofitting authorization after building features causes complete rewrites. All downstream features depend on authentication for security and multi-tenancy.

**Delivers:** FastAPI app skeleton, PostgreSQL database with Users/Files/ChatMessages models, JWT-based auth (email/password), file upload with user-isolated storage paths

**Addresses:** Authentication (table stakes), per-user data isolation (critical security), file upload infrastructure

**Avoids:** Pitfall #5 (multi-tenant data isolation failure) - designing user_id filters and UUID-based file paths from start prevents IDOR vulnerabilities

**Tech stack:** FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic, PyJWT, pwdlib (Argon2)

**Research flag:** Standard patterns, skip research-phase (well-documented FastAPI auth)

### Phase 2: AI Agents + Orchestration
**Rationale:** Core differentiation is multi-agent accuracy. Building agent infrastructure before UI ensures we can deliver on accuracy promise. Code Checker is non-negotiable for MVP - generates incorrect/unsafe code destroys trust.

**Delivers:** LangGraph workflow orchestrating 4 agents (Onboarding, Coding, Code Checker, Data Analysis), LangSmith tracing for debugging, cost controls (token limits, max_tokens caps)

**Addresses:** Natural language queries, code generation with explanation, multi-agent orchestration (differentiator)

**Avoids:** Pitfall #1 (AI hallucinations) via Code Checker Agent with AST validation, Pitfall #4 (token costs) via rate limiting and monitoring from day one, Pitfall #6 (orchestration failures) via LangSmith tracing

**Tech stack:** LangGraph, LangChain, langchain-openai, LangSmith, pandas for data profiling

**Research flag:** **Needs research-phase** - Complex LangGraph graph design with retry loops (Code Checker → Coding regeneration), agent prompt engineering, hallucination detection patterns

### Phase 3: Streaming Infrastructure
**Rationale:** SSE streaming is table stakes in 2026 (ChatGPT normalized token-by-token responses). Must be built before UI to test robustness (connection drops, long queries, error handling).

**Delivers:** FastAPI SSE streaming endpoint (/chat/stream), Next.js API route proxy, EventSource client with reconnection, database persistence during streaming

**Addresses:** Real-time streaming responses (table stakes), conversation persistence (survives browser refresh)

**Avoids:** Pitfall #3 (streaming connection failures) via auto-reconnect, disconnect detection, checkpoint partial results

**Tech stack:** sse-starlette, Next.js Route Handlers, EventSource API, PostgreSQL for chat persistence

**Research flag:** Standard SSE patterns, skip research-phase (well-documented streaming)

### Phase 4: Sandbox Security + Code Execution
**Rationale:** Must be completed before any user code execution. Sandbox escape destroys entire product and all user data. Multi-layer defense is non-negotiable (cannot defer gVisor to v2).

**Delivers:** Docker containers with gVisor runtime, RestrictedPython AST validation in Code Checker, resource limits (memory, CPU, timeout), network isolation (`--network=none`), read-only filesystem

**Addresses:** Sandboxed code execution (table stakes), security baseline for production

**Avoids:** Pitfall #2 (sandbox escape) via multi-layer defense (RestrictedPython + Docker + gVisor + resource limits)

**Tech stack:** Docker, gVisor (runsc runtime), E2B (alternative if self-hosting fails), RestrictedPython

**Research flag:** **Needs research-phase** - gVisor setup complexity, E2B integration if self-hosting blocked, Docker security hardening, RestrictedPython allowlist patterns

### Phase 5: Frontend UI + Data Cards
**Rationale:** Build UI last after proving backend works (streaming, agents, sandbox). Streaming Data Cards are complex (progressive rendering, SSE integration) - easier to build when backend is stable.

**Delivers:** File upload component with drag-and-drop, tabbed file interface, chat UI with streaming messages, interactive Data Cards (sortable tables, charts with Plotly), basic export (CSV download)

**Addresses:** Interactive Data Cards (table stakes), file upload UX, chat interface

**Avoids:** Performance issues via streaming progressive rendering (UX pitfall: no progress indication during long analysis)

**Tech stack:** Next.js 16, React 19, shadcn/ui components, TanStack Query for server state, zustand for client state, Plotly for visualizations

**Research flag:** Standard React patterns, skip research-phase (shadcn/ui well-documented)

### Phase Ordering Rationale

- **Authentication first (Phase 1):** All features require user context. Building auth later requires rewriting all endpoints to add authorization checks.
- **Agents before UI (Phase 2):** Prove core value proposition (accurate AI analysis) before polishing UX. Agents are complex - need time for prompt engineering and debugging.
- **Streaming before UI (Phase 3):** Test streaming robustness independently. Easier to debug SSE issues without UI complexity.
- **Sandbox before production (Phase 4):** Non-negotiable security requirement. Cannot deploy user code execution without multi-layer isolation.
- **UI last (Phase 5):** Leverage stable backend for efficient frontend development. Streaming Data Cards easier to build when backend reliably streams results.

**Dependency chain:** Authentication → File Upload → Agents → Streaming → Sandbox → UI

**Parallel opportunities:** Phase 3 (streaming) and Phase 4 (sandbox) can partially overlap if different developer or clear separation of concerns.

### Research Flags

**Phases needing deeper research during planning:**
- **Phase 2 (AI Agents):** Complex LangGraph workflow design with conditional edges, retry loop logic, hallucination detection patterns, prompt engineering for 4 specialized agents
- **Phase 4 (Sandbox Security):** gVisor runtime configuration, E2B Cloud integration as fallback, RestrictedPython allowlist maintenance, Docker security hardening

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (Backend Foundation):** FastAPI + SQLAlchemy + JWT auth is well-documented, established patterns
- **Phase 3 (Streaming):** SSE with FastAPI is standard pattern, EventSource API is browser-native
- **Phase 5 (Frontend):** Next.js + shadcn/ui + TanStack Query are mainstream stack with excellent docs

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All critical components verified with official 2026 documentation (FastAPI, Next.js 16, LangGraph, E2B). Security decisions (gVisor, pwdlib, PyJWT) based on recent CVE alerts and framework updates. |
| Features | **HIGH** | Cross-referenced 15+ sources from 2025-2026, validated against competitor analysis (ChatGPT, Tableau Pulse, ThoughtSpot). Feature prioritization aligns with user journey mapping. |
| Architecture | **HIGH** | Patterns verified with official LangChain/LangGraph docs, gVisor security documentation, and multiple 2025-2026 production implementation guides. Multi-agent and sandbox patterns are production-proven. |
| Pitfalls | **HIGH** | All critical failure modes verified with 2026 research sources and real-world incident data (CVE-2025-52881, T-Mobile $350M breach). Hallucination fix rates from peer-reviewed 2026 study. |

**Overall confidence:** **HIGH**

Research based on authoritative sources (official documentation, peer-reviewed papers, recent CVE databases, production incident post-mortems). Technology choices reflect 2026 ecosystem state (FastAPI team recommendations, abandoned libraries flagged, container security updates).

### Gaps to Address

**LangGraph multi-agent retry loops:** Research shows pattern exists (Code Checker validation → regenerate code), but implementation details need deeper dive during Phase 2 planning. Use `/gsd:research-phase` for LangGraph conditional edges and state management patterns.

**gVisor production deployment:** Research confirms gVisor provides VM-like isolation, but setup complexity for single developer unclear. May need to pivot to E2B Cloud if self-hosting gVisor proves too complex for 2-4 week timeline. Validate during Phase 4 planning.

**pandas memory optimization at scale:** Research shows chunking and dtype optimization work, but thresholds for when to apply (file size triggers) need validation with real user data patterns. Monitor in production, optimize if OOM issues emerge.

**Token cost modeling:** Research provides pricing (output tokens 3-10x input), but actual cost depends on prompt design and user query patterns. Implement monitoring from day one, tune rate limits based on real usage data.

**Streaming reconnection edge cases:** Browser behavior during network transitions (WiFi ↔ cellular) not fully documented. Test with real mobile networks during Phase 3 to validate EventSource auto-reconnect works as expected.

## Sources

### Primary (HIGH confidence)

**Stack Research:**
- FastAPI official documentation — Core framework features, deployment, async patterns
- Next.js 16 documentation — App Router, React 19 compatibility, streaming
- LangChain/LangGraph documentation — Multi-agent orchestration, state management
- E2B documentation — Sandbox setup, API, security model
- Pydantic v2, SQLAlchemy 2.0, shadcn/ui official docs
- FastAPI GitHub discussions #11773 (passlib deprecation), PR #11589 (PyJWT migration)

**Features Research:**
- AI-Driven Conversational Analytics Platforms: Top Tools for 2026 (ovaledge.com)
- ChatGPT for Data Analysis: Comparing Alternatives (displayr.com)
- Tableau Ask Data documentation, ThoughtSpot SearchIQ comparison
- 15+ industry sources on conversational analytics features

**Architecture Research:**
- LangChain Multi-Agent Architecture Patterns (blog.langchain.com)
- gVisor Security Introduction (gvisor.dev/docs)
- Setting Up a Secure Python Sandbox for LLM Agents (dida.do)
- 4 Ways to Sandbox Untrusted Code in 2026 (dev.to)

**Pitfalls Research:**
- "Detecting and Correcting Hallucinations in LLM-Generated Code via Deterministic AST Analysis" (arXiv 2601.19106) — 56.2% fix rate for pandas hallucinations
- CVE-2025-52881 vm2 Sandbox Escape (CVSS 9.8)
- NVIDIA Practical Security Guidance for Sandboxing Agentic Workflows
- Complete LLM Pricing Comparison 2026 (cloudidr.com)
- State of Agent Engineering (langchain.com) — 89% use observability, 32% cite quality as blocker

### Secondary (MEDIUM confidence)

- Better Stack: Best Sandbox Runners 2026, FastAPI Docker Best Practices
- TestDriven.io: FastAPI with Async SQLAlchemy setup patterns
- Medium: Next.js 16 + React Query guide, FastAPI at Scale in 2026
- Strapi: OpenAI SDK vs Vercel AI SDK comparison
- Programming Helper: Docker Python containerization trends 2026
- T-Mobile $350M settlement for 2021 cloud breach (multi-tenant isolation failure)

### Tertiary (LOW confidence)

- Specific competitor pricing models (not publicly documented) — inferred from market positioning
- Future roadmap predictions for proprietary platforms — extrapolated from announcements
- User adoption statistics for niche features — self-reported surveys with small sample sizes

---
*Research completed: 2026-02-02*
*Ready for roadmap: yes*
*Next step: Requirements definition with SUMMARY.md as context*
