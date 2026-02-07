# Requirements: Spectra v0.2 Intelligence & Integration

**Defined:** 2026-02-06
**Core Value:** Accurate data analysis through correct, safe Python code generation. If the code is wrong or the sandbox isn't secure, the entire product fails.

## v0.2 Requirements

Requirements for v0.2 Intelligence & Integration milestone. Each maps to roadmap phases.

### AI Agent Memory Persistence

- [ ] **MEMORY-01**: User can maintain conversation context across multiple queries within same chat tab session
- [ ] **MEMORY-02**: User's conversation context persists after browser refresh (if tab remains open)
- [ ] **MEMORY-03**: User receives warning dialog before closing chat tab explaining context will be lost
- [ ] **MEMORY-04**: Each file tab maintains independent conversation memory (no cross-contamination)
- [ ] **MEMORY-05**: System uses configurable context window size (default: 12,000 tokens)
- [ ] **MEMORY-06**: System displays warning when context reaches 85% of token limit (10,200 tokens)
- [ ] **MEMORY-07**: System automatically prunes oldest messages when context limit exceeded (after user confirmation)
- [ ] **MEMORY-08**: System displays current context usage in chat interface (e.g., "8,543 / 12,000 tokens used")

### Multi-LLM Provider Support

- [ ] **LLM-01**: System supports Ollama LLM provider (local deployment)
- [ ] **LLM-02**: System supports Ollama LLM provider (remote deployment via URL)
- [ ] **LLM-03**: System supports OpenRouter gateway (access to 100+ models)
- [ ] **LLM-04**: LLM provider configuration is externalized to YAML file
- [ ] **LLM-05**: System defaults to Sonnet 4.0 for all agents (maintains current behavior)
- [ ] **LLM-06**: System includes well-defined test scenarios for each provider (Ollama, OpenRouter, existing providers)
- [ ] **LLM-07**: System gracefully handles LLM provider failures (fallback or clear error message)

### Agent-Level LLM Configuration

- [ ] **CONFIG-01**: Each agent (Onboarding, Coding, Code Checker, Data Analysis) can be configured with different LLM provider
- [ ] **CONFIG-02**: Each agent can be configured with different model within same provider
- [ ] **CONFIG-03**: Agent LLM configuration specified in YAML with provider, model, and temperature settings
- [ ] **CONFIG-04**: System validates LLM configuration at startup (detects invalid provider/model combinations)
- [ ] **CONFIG-05**: Configuration changes require server restart (no hot-reload complexity for v0.2)

### Web Search Tool Integration

- [ ] **SEARCH-01**: Data Analysis Agent can search web via Serper.dev API
- [ ] **SEARCH-02**: Data Analysis Agent decides when to use web search based on query content (discretionary, not mandatory)
- [ ] **SEARCH-03**: Web search results are displayed transparently in chat response (shows sources)
- [ ] **SEARCH-04**: Web search tool is configurable (API key, enabled/disabled flag)
- [ ] **SEARCH-05**: System gracefully degrades when web search quota exceeded (continues without search)
- [ ] **SEARCH-06**: System gracefully degrades when web search API unavailable (continues without search)
- [ ] **SEARCH-07**: Web search queries are logged for debugging and cost tracking

### Smart Query Suggestions

- [ ] **SUGGEST-01**: New chat tabs display 5-6 query suggestions when opened
- [ ] **SUGGEST-02**: Query suggestions are grouped into 3 categories: General Analysis (2 suggestions), Benchmarking (2 suggestions), Trend/Predictive (2 suggestions)
- [ ] **SUGGEST-03**: User can click suggestion to start chat with that query
- [ ] **SUGGEST-04**: Suggestions are generated based on Onboarding Agent's data profiling results
- [ ] **SUGGEST-05**: Suggestions adapt to actual data structure (use real column names, data types)
- [ ] **SUGGEST-06**: Suggestions are persisted and displayed consistently until file is re-analyzed

### SMTP Email Service

- [ ] **SMTP-01**: Email service uses standard SMTP protocol (not Mailgun API)
- [ ] **SMTP-02**: SMTP configuration includes host, port, username, password, TLS/SSL settings
- [ ] **SMTP-03**: SMTP configuration is externalized (environment variables or config file)
- [ ] **SMTP-04**: Email templates use Jinja2 for formatting and variable substitution
- [ ] **SMTP-05**: System gracefully degrades to dev mode (console logging) when SMTP not configured
- [ ] **SMTP-06**: System validates SMTP configuration at startup (connection test)

### Production Password Reset Flow

- [ ] **PWRESET-01**: Password reset emails sent via SMTP (no dev mode console logs in production)
- [ ] **PWRESET-02**: Reset email includes secure link with format /reset-password?token=<token>
- [ ] **PWRESET-03**: Reset email uses professional HTML template with branding
- [ ] **PWRESET-04**: Dev mode is automatically disabled when SMTP is properly configured
- [ ] **PWRESET-05**: Reset link expires after configurable time (default: 10 minutes)

## v0.3+ Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Advanced Memory Features

- **MEMORY-ADV-01**: System implements context summarization (compress old messages instead of pruning)
- **MEMORY-ADV-02**: User can manually clear conversation context without closing tab
- **MEMORY-ADV-03**: User can view conversation history with token usage per message
- **MEMORY-ADV-04**: System implements semantic search across conversation history

### Advanced Query Features

- **SUGGEST-ADV-01**: Suggestions update dynamically as user explores data
- **SUGGEST-ADV-02**: System learns from user's query patterns to personalize suggestions
- **SEARCH-ADV-01**: Web search results are cached to reduce API costs (24-hour TTL)
- **SEARCH-ADV-02**: User can manually trigger web search via explicit command

### Advanced Configuration

- **CONFIG-ADV-01**: LLM configuration supports hot-reload without server restart
- **CONFIG-ADV-02**: System includes A/B testing framework for comparing models
- **CONFIG-ADV-03**: User can override LLM provider per query (power user feature)

## Out of Scope

Explicitly excluded from v0.2. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Cross-session memory persistence | Context pollution risk - v0.1 research flagged as anti-feature |
| Visualization Agent | Separate milestone (v0.3+) - presentation vs intelligence |
| Data Cards saved to Collections | Storage/organization feature, not intelligence enhancement |
| Real-time collaboration | Conflicts with session-scoped memory architecture |
| Billing/subscription system | No business need yet (validate v0.2 features first) |
| Google OAuth | Email/password sufficient, OAuth is polish not priority |
| Mobile app | Web-responsive only, native apps out of scope |
| Database connectors | File upload only, connectors are separate milestone |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEMORY-01 | Phase 8 | Pending |
| MEMORY-02 | Phase 8 | Pending |
| MEMORY-03 | Phase 8 | Pending |
| MEMORY-04 | Phase 8 | Pending |
| MEMORY-05 | Phase 8 | Pending |
| MEMORY-06 | Phase 8 | Pending |
| MEMORY-07 | Phase 8 | Pending |
| MEMORY-08 | Phase 8 | Pending |
| LLM-01 | Phase 7 | Pending |
| LLM-02 | Phase 7 | Pending |
| LLM-03 | Phase 7 | Pending |
| LLM-04 | Phase 7 | Pending |
| LLM-05 | Phase 7 | Pending |
| LLM-06 | Phase 7 | Pending |
| LLM-07 | Phase 7 | Pending |
| CONFIG-01 | Phase 7 | Pending |
| CONFIG-02 | Phase 7 | Pending |
| CONFIG-03 | Phase 7 | Pending |
| CONFIG-04 | Phase 7 | Pending |
| CONFIG-05 | Phase 7 | Pending |
| SEARCH-01 | Phase 10 | Pending |
| SEARCH-02 | Phase 10 | Pending |
| SEARCH-03 | Phase 10 | Pending |
| SEARCH-04 | Phase 10 | Pending |
| SEARCH-05 | Phase 10 | Pending |
| SEARCH-06 | Phase 10 | Pending |
| SEARCH-07 | Phase 10 | Pending |
| SUGGEST-01 | Phase 9 | Pending |
| SUGGEST-02 | Phase 9 | Pending |
| SUGGEST-03 | Phase 9 | Pending |
| SUGGEST-04 | Phase 9 | Pending |
| SUGGEST-05 | Phase 9 | Pending |
| SUGGEST-06 | Phase 9 | Pending |
| SMTP-01 | Phase 11 | Pending |
| SMTP-02 | Phase 11 | Pending |
| SMTP-03 | Phase 11 | Pending |
| SMTP-04 | Phase 11 | Pending |
| SMTP-05 | Phase 11 | Pending |
| SMTP-06 | Phase 11 | Pending |
| PWRESET-01 | Phase 11 | Pending |
| PWRESET-02 | Phase 11 | Pending |
| PWRESET-03 | Phase 11 | Pending |
| PWRESET-04 | Phase 11 | Pending |
| PWRESET-05 | Phase 11 | Pending |

**Coverage:**
- v0.2 requirements: 43 total
- Mapped to phases: 43/43 (100%)
- Unmapped: 0

**Phase Distribution:**
- Phase 7 (Multi-LLM Infrastructure): 12 requirements (LLM + CONFIG)
- Phase 8 (Session Memory): 8 requirements (MEMORY)
- Phase 9 (Query Suggestions): 6 requirements (SUGGEST)
- Phase 10 (Web Search): 7 requirements (SEARCH)
- Phase 11 (Production Email): 11 requirements (SMTP + PWRESET)

---
*Requirements defined: 2026-02-06*
*Last updated: 2026-02-06 after roadmap creation*
