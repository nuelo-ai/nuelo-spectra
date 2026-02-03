# Requirements: Spectra

**Defined:** 2026-02-02
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v1.0 Requirements

Requirements for initial MVP release. Each maps to roadmap phases.

### Authentication

- [x] **AUTH-01**: User can sign up with email and password
- [x] **AUTH-02**: User can log in with email and password
- [x] **AUTH-03**: User can reset password via email link
- [x] **AUTH-04**: User session persists across browser refresh
- [x] **AUTH-05**: User data is isolated (each user sees only their own files and chat history)

### File Management

- [ ] **FILE-01**: User can upload Excel files (.xlsx, .xls) up to 50MB
- [ ] **FILE-02**: User can upload CSV files (.csv) up to 50MB
- [ ] **FILE-03**: System validates file format and structure before acceptance
- [ ] **FILE-04**: AI Onboarding Agent analyzes uploaded data structure and generates natural language summary
- [ ] **FILE-05**: User can provide optional context during upload to improve AI interpretation
- [ ] **FILE-06**: User can refine AI's understanding of the data after initial analysis
- [ ] **FILE-07**: User can view list of uploaded files with metadata (name, size, upload date)
- [ ] **FILE-08**: User can delete files with confirmation dialog
- [ ] **FILE-09**: Each file has its own chat tab in the interface
- [ ] **FILE-10**: User can switch between file tabs with independent chat histories

### AI Agents & Chat

- [ ] **AGENT-01**: User can ask questions about their data in natural language
- [ ] **AGENT-02**: System streams AI responses in real-time (shows thinking process)
- [ ] **AGENT-03**: Onboarding Agent analyzes data structure and generates initial insights
- [ ] **AGENT-04**: Coding Agent generates Python scripts based on user queries
- [ ] **AGENT-05**: Code Checker Agent validates generated code for safety and correctness before execution
- [ ] **AGENT-06**: Data Analysis Agent interprets code execution results and generates natural language explanations
- [ ] **AGENT-07**: Chat history persists per file across browser sessions
- [ ] **AGENT-08**: AI agent system prompts are externalized to YAML configuration files for easy tuning and iteration
- [ ] **AGENT-09**: When code execution fails, system automatically analyzes error, regenerates code, and retries (with maximum retry limit to prevent infinite loops)

### Code Execution & Security

- [ ] **EXEC-01**: Python code executes in E2B microVM sandbox environment
- [ ] **EXEC-02**: Sandbox prevents risky operations (file deletion, table drops, network access)
- [ ] **EXEC-03**: Code execution is resource-limited (CPU, memory, timeout)
- [ ] **EXEC-04**: User data in sandbox is isolated (no access to other users' data)
- [ ] **EXEC-05**: Generated code is displayed with explanation before execution
- [ ] **EXEC-06**: Allowed Python libraries are defined in YAML configuration file (library allowlist)
- [ ] **EXEC-07**: Code Checker Agent validates that generated code only imports allowed libraries from allowlist

### Interactive Data Cards

- [ ] **CARD-01**: Query results display as Data Cards with streaming responses
- [ ] **CARD-02**: Data Cards show Query Brief, Data Table, and AI Explanation sections
- [ ] **CARD-03**: Data tables within cards are sortable and filterable
- [ ] **CARD-04**: Results stream progressively (appear while AI is still processing)
- [ ] **CARD-05**: Visual polish includes smooth animations, loading states, and transitions
- [ ] **CARD-06**: User can view Python code generated for each analysis in Data Card
- [ ] **CARD-07**: User can download data tables as CSV from Data Cards
- [ ] **CARD-08**: User can download analysis report as Markdown from Data Cards

### Settings & Profile

- [ ] **SETT-01**: User can view and edit profile information (first name, last name)
- [ ] **SETT-02**: User can view account details (email address, account creation date)
- [ ] **SETT-03**: User can change password from settings page

## v2 Requirements

Deferred to future releases. Tracked but not in current roadmap.

### Authentication & Access

- **AUTH-06**: User can sign in with Google OAuth
- **AUTH-07**: User can sign in with Microsoft OAuth
- **AUTH-08**: User receives email verification after signup

### File Management

- **FILE-11**: User can organize files into Collections
- **FILE-12**: User can download files in bulk
- **FILE-13**: Files are stored in cloud storage (S3)

### Export & Sharing

- **EXPORT-01**: User can export Data Cards as PDF
- **EXPORT-02**: User can save Data Cards to Collections for later review
- **EXPORT-03**: User can export analysis as PowerPoint presentation

### AI Capabilities

- **AGENT-10**: Visualization Agent generates charts and graphs from data
- **AGENT-11**: System implements long-term memory (cross-session learning with pgvector)

### Billing & Subscription

- **BILL-01**: User can subscribe to paid plan
- **BILL-02**: System tracks credit usage per user
- **BILL-03**: User can manage subscription and payment methods

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Email verification on signup | Deferred to v2. Let users in immediately; add verification later for security. Focus on reducing friction for MVP validation. |
| Google/Microsoft OAuth | Deferred to v2. Email/password sufficient for MVP. OAuth adds integration complexity not needed to validate core value. |
| Save Data Cards to Collections | Deferred to v2. Focus on real-time analysis first; saving for later review is polish. Users can re-run queries if needed. |
| PDF export from Data Cards | Deferred to v2. CSV and Markdown export included in v1.0; PDF adds formatting complexity. Add when users request formatted reports. |
| Full Collections organization | Deferred to v2. Basic file list with tabs sufficient for v1; organizing into collections adds UI/UX complexity. |
| Bulk file download | Deferred to v2. Users can delete individual files; bulk operations not essential for MVP validation. |
| Visualization Agent | Deferred to v2. Focus on accurate analysis first; charts can come later. Tables + text explanations sufficient for MVP. |
| PowerPoint export | Deferred to v2. PDF export (also deferred) proves the concept; PowerPoint adds significant formatting complexity. |
| Billing and subscription management | Deferred to v2. Need to validate product-market fit before building payment infrastructure (Stripe integration, credit tracking). |
| Credit tracking system | Deferred to v2. No billing means no credits needed yet. Monitor usage in production, add limits when converting to paid. |
| S3/cloud file storage | Deferred to v2. Local storage sufficient for MVP; cloud storage adds deployment complexity and cost management. |
| Long-term memory (pgvector) | Deferred to v2. Session-based conversation sufficient for v1. Add semantic memory when users return weekly+ and want personalization. |
| Real-time collaboration | Not planned. Single-user experience for v1. Collaboration (share links, team workspaces) deferred until validated team use case. |
| Mobile native apps | Not planned. Web-responsive design only. Mobile apps double development cost; wait until mobile usage >20% of traffic. |
| Data source integrations (APIs, databases) | Not planned. File upload only for v1. SQL connectors defer until >10 users request database connections vs CSV upload. |
| Multi-language support (R, Julia, Scala) | Not planned. Python only. 83% of data science uses Python; wait until Python insufficient for >5% of users before adding languages. |
| Unlimited file sizes | Anti-feature. 50MB limit prevents memory exhaustion (100MB CSV = 800MB+ pandas DataFrame). Guide users to filter/sample large datasets. |
| Real-time data refresh | Anti-feature. Adds streaming pipeline complexity for minimal value. Most analytics are retrospective; manual refresh sufficient. |
| AI training on user data | Anti-feature. Privacy nightmare, GDPR violations. Use paid LLM API tiers with explicit no-training contracts. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| FILE-01 | Phase 2 | Pending |
| FILE-02 | Phase 2 | Pending |
| FILE-03 | Phase 2 | Pending |
| FILE-04 | Phase 3 | Pending |
| FILE-05 | Phase 3 | Pending |
| FILE-06 | Phase 3 | Pending |
| FILE-07 | Phase 2 | Pending |
| FILE-08 | Phase 2 | Pending |
| FILE-09 | Phase 2 | Pending |
| FILE-10 | Phase 2 | Pending |
| AGENT-01 | Phase 4 | Pending |
| AGENT-02 | Phase 4 | Pending |
| AGENT-03 | Phase 3 | Pending |
| AGENT-04 | Phase 3 | Pending |
| AGENT-05 | Phase 3 | Pending |
| AGENT-06 | Phase 3 | Pending |
| AGENT-07 | Phase 4 | Pending |
| AGENT-08 | Phase 3 | Pending |
| AGENT-09 | Phase 5 | Pending |
| EXEC-01 | Phase 5 | Pending |
| EXEC-02 | Phase 5 | Pending |
| EXEC-03 | Phase 5 | Pending |
| EXEC-04 | Phase 5 | Pending |
| EXEC-05 | Phase 5 | Pending |
| EXEC-06 | Phase 5 | Pending |
| EXEC-07 | Phase 5 | Pending |
| CARD-01 | Phase 6 | Pending |
| CARD-02 | Phase 6 | Pending |
| CARD-03 | Phase 6 | Pending |
| CARD-04 | Phase 6 | Pending |
| CARD-05 | Phase 6 | Pending |
| CARD-06 | Phase 6 | Pending |
| CARD-07 | Phase 6 | Pending |
| CARD-08 | Phase 6 | Pending |
| SETT-01 | Phase 6 | Pending |
| SETT-02 | Phase 6 | Pending |
| SETT-03 | Phase 6 | Pending |

**Coverage:**
- v1.0 requirements: 42 total
- Mapped to phases: 42/42 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-02-02*
*Last updated: 2026-02-02 after roadmap creation*
