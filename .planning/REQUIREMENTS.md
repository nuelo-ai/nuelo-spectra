# Requirements: Spectra

**Defined:** 2026-02-23
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.7 Requirements

### API Key Management (APIKEY)

- [x] **APIKEY-01**: User can view their API keys on the Settings/API Keys page
- [x] **APIKEY-02**: User can create an API key with a name and description
- [x] **APIKEY-03**: User can revoke their own API keys
- [x] **APIKEY-04**: Revoked API keys cannot be used for authentication
- [x] **APIKEY-05**: API keys are stored securely (hashed, full key shown only once at creation)
- [x] **APIKEY-06**: Admin can view API keys for all users from User Management
- [x] **APIKEY-07**: Admin can create API keys on behalf of any user
- [x] **APIKEY-08**: Admin can revoke any user's API keys

### API Authentication & Security (APISEC)

- [x] **APISEC-01**: API requests authenticate via API key in `Authorization: Bearer` header
- [x] **APISEC-02**: Invalid or revoked API keys return 401 Unauthorized
- [x] **APISEC-03**: API calls deduct credits from the user's balance (same cost as chat)
- [x] **APISEC-04**: API usage is logged per user and per API key (timestamp, endpoint, credits used)

### API Use Cases — Files (APIF)

- [ ] **APIF-01**: API caller can upload a CSV or Excel file, triggering onboarding (data brief + suggestions)
- [ ] **APIF-02**: API caller can list all files for the authenticated user
- [ ] **APIF-03**: API caller can delete a file by ID
- [ ] **APIF-04**: API caller can download a file by ID

### API Use Cases — File Context (APIC)

- [ ] **APIC-01**: API caller can get file detail including data brief, summary, and context
- [ ] **APIC-02**: API caller can update file data summary or context
- [ ] **APIC-03**: API caller can get query suggestions for a file

### API Use Cases — Chat (APIQ)

- [ ] **APIQ-01**: API caller can send a query against a file and receive the full analysis result (code, chart spec, analysis summary) synchronously

### API Infrastructure (APIINFRA)

- [x] **APIINFRA-01**: `SPECTRA_MODE=api` enables API routes on the existing backend — no separate codebase
- [x] **APIINFRA-02**: API routes are versioned under `/api/v1/`
- [x] **APIINFRA-03**: API service is deployable as a 5th Dokploy service with its own public HTTPS domain
- [x] **APIINFRA-04**: API requests and errors are logged (structured, per-request)
- [x] **APIINFRA-05**: In `SPECTRA_MODE=dev` (Docker Compose local), all `/api/v1/` routes are active alongside existing backend routes — no separate service needed for local development

### MCP Server (MCP)

- [ ] **MCP-01**: MCP server exposes a tool to upload a file and trigger onboarding
- [ ] **MCP-02**: MCP server exposes a tool to query a file (ask a question, get analysis result)
- [ ] **MCP-03**: MCP server exposes tools to list, delete, and download files
- [ ] **MCP-04**: MCP server exposes a tool to get file context, data brief, and query suggestions
- [ ] **MCP-05**: MCP server authenticates using a user's API key

## Future Requirements

### Rate Limiting (deferred to v0.8+)

- **RATELIMIT-01**: Per-API-key request rate limiting (X requests/minute)
- **RATELIMIT-02**: Rate limit headers returned on all API responses (X-RateLimit-Limit, X-RateLimit-Remaining)
- **RATELIMIT-03**: 429 Too Many Requests response with Retry-After header

### Deferred Admin Features (from v0.5)

- **CREDIT-11**: Bulk-adjust credits by user class
- **SETTINGS-06**: Per-tier credit overrides in platform_settings
- **TIER-02**: Admin editing tier credit amounts via UI

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rate limiting | Defer — credit system provides natural throttling; add after seeing real usage |
| Streaming API responses | Keep it simple for v0.7; add SSE or async polling later if needed |
| OAuth for API | API keys sufficient for v0.7; OAuth adds significant complexity |
| Webhooks | Event-push model deferred; polling/synchronous sufficient for now |
| SDK / client library | Generate after the API is stable |
| GraphQL endpoint | REST is simpler and sufficient for current use cases |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| APIKEY-01 | Phase 38 | Complete |
| APIKEY-02 | Phase 38 | Complete |
| APIKEY-03 | Phase 38 | Complete |
| APIKEY-04 | Phase 38 | Complete |
| APIKEY-05 | Phase 38 | Complete |
| APIKEY-06 | Phase 39 | Complete |
| APIKEY-07 | Phase 39 | Complete |
| APIKEY-08 | Phase 39 | Complete |
| APISEC-01 | Phase 38 | Complete |
| APISEC-02 | Phase 38 | Complete |
| APISEC-03 | Phase 40 | Complete |
| APISEC-04 | Phase 40 | Complete |
| APIF-01 | Phase 40 | Pending |
| APIF-02 | Phase 40 | Pending |
| APIF-03 | Phase 40 | Pending |
| APIF-04 | Phase 40 | Pending |
| APIC-01 | Phase 40 | Pending |
| APIC-02 | Phase 40 | Pending |
| APIC-03 | Phase 40 | Pending |
| APIQ-01 | Phase 40 | Pending |
| APIINFRA-01 | Phase 38 | Complete |
| APIINFRA-02 | Phase 38 | Complete |
| APIINFRA-03 | Phase 39 | Complete |
| APIINFRA-04 | Phase 40 | Complete |
| APIINFRA-05 | Phase 38 | Complete |
| MCP-01 | Phase 41 | Pending |
| MCP-02 | Phase 41 | Pending |
| MCP-03 | Phase 41 | Pending |
| MCP-04 | Phase 41 | Pending |
| MCP-05 | Phase 41 | Pending |

**Coverage:**
- v0.7 requirements: 30 total
- Mapped to phases: 30 (Phase 38: 10, Phase 39: 4, Phase 40: 11, Phase 41: 5)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-23*
*Last updated: 2026-02-23 — APIINFRA-05 added (Docker Compose dev mode includes api/v1 routes)*
