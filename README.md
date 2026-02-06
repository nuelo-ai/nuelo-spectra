# Spectra

> **⚠️ BETA RELEASE (v0.1)** - This is an early beta version. Core features are functional, but UI/UX improvements and additional features are in active development. We welcome feedback and issue reports!

AI-powered conversational data analytics platform that transforms how you interact with your data. Upload CSV or Excel files, ask questions in natural language, and receive instant insights with code transparency.

## What is Spectra?

Spectra bridges the gap between raw data and actionable insights. Upload your datasets, and our multi-agent AI system automatically interprets the data structure, generates Python code to analyze it, and presents results as interactive Data Cards—all through a conversational chat interface.

**Key Differentiators:**
- **Code Transparency**: See and verify the Python code generated for each analysis
- **Multi-Agent Accuracy**: 4 specialized AI agents (Onboarding, Coding, Code Checker, Data Analysis) work together to ensure accurate results
- **Production-Grade Security**: E2B Firecracker microVM isolation for safe code execution

## Features

### Core Functionality
- Natural language data queries with real-time streaming responses
- CSV/Excel file upload (up to 50MB) with automated data profiling
- AI-generated Python code with explanations displayed before execution
- Secure sandboxed code execution in isolated microVMs
- Interactive Data Cards with sortable tables and streaming results
- Per-file conversation history with tabbed interface
- User authentication with JWT and refresh tokens
- CSV and Markdown export for analysis results

### Technical Highlights
- Multi-agent orchestration with LangGraph for higher accuracy
- SSE (Server-Sent Events) streaming for real-time progress updates
- AST-based code validation with library allowlisting
- Automatic error recovery with intelligent retry (max 3 attempts)
- PostgreSQL checkpointing for conversation state management

## Tech Stack

**Backend:**
- FastAPI (Python 3.12+)
- PostgreSQL 16 with asyncpg
- SQLAlchemy 2.0 (async)
- LangGraph + LangChain for AI orchestration
- E2B Code Interpreter for secure sandboxing
- PyJWT for authentication
- Argon2 password hashing via pwdlib

**Frontend:**
- Next.js 16 with App Router
- React 19
- TypeScript 5
- TanStack Query for server state
- Zustand for client state
- Radix UI / shadcn/ui components
- Tailwind CSS 4

**AI/ML:**
- LangChain framework for agent orchestration
- Support for multiple LLM providers (OpenAI, Anthropic, Google)
- LangSmith for agent tracing and debugging
- 4 specialized agents with YAML-configured prompts

**Security:**
- E2B Firecracker microVMs for isolated code execution
- AST-based code validation with allowlist enforcement
- Resource limits (60s timeout, 1GB memory per execution)
- Fresh sandbox per execution (no cross-user data leakage)
- Future: Docker + gVisor for self-hosted deployments

## AI Agent Architecture

Spectra uses a multi-agent system orchestrated by LangGraph to ensure accurate and safe data analysis:

1. **Onboarding Agent**: Analyzes uploaded file structure, generates natural language summary of data columns, types, and suggests initial analyses
2. **Coding Agent**: Generates Python pandas code from natural language queries, incorporating file context and data summary
3. **Code Checker Agent**: Validates generated code using AST analysis and LLM logical verification, checks against library allowlist and unsafe operations
4. **Data Analysis Agent**: Interprets code execution results and generates natural language explanations

All agents use YAML-configured system prompts for easy tuning without code changes. The system includes automatic retry logic (max 3 attempts) when code execution fails, with intelligent error feedback to guide regeneration.

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL 16+
- E2B API key (sign up at [e2b.dev](https://e2b.dev))
- LLM API key (OpenAI, Anthropic, or Google)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/marwazihs/nuelo-spectra.git
cd nuelo-spectra
```

2. Set up the backend:
```bash
cd backend

# Install uv (recommended) or use pip
pip install uv
uv sync

# Or with traditional pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL (PostgreSQL connection string)
# - E2B_API_KEY (for code sandbox)
# - AGENT_LLM_PROVIDER (openai/anthropic/google)
# - OPENAI_API_KEY or ANTHROPIC_API_KEY or GOOGLE_API_KEY
# - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
# - EMAIL_SERVICE_API_KEY (optional, for password reset emails)
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the backend server:
```bash
uvicorn app.main:app --reload
```

6. Set up the frontend (in a new terminal):
```bash
cd frontend
npm install
npm run dev
```

7. Access the application at `http://localhost:3000`

## Current Status (v0.1 Beta)

### Completed (42/42 Requirements)
- ✅ **Authentication (5/5)**: JWT-based auth, email/password signup/login, password reset, session persistence, user data isolation
- ✅ **File Management (10/10)**: Excel/CSV upload (up to 50MB), format validation, AI data profiling, tabbed interface, per-file chat history
- ✅ **AI Agents (9/9)**: 4-agent system (Onboarding, Coding, Code Checker, Data Analysis), YAML-configured prompts, automatic error recovery
- ✅ **Code Execution (8/8)**: E2B microVM sandbox, AST validation, library allowlisting, resource limits, isolated execution
- ✅ **Interactive Data Cards (8/8)**: Streaming responses, sortable/filterable tables, code display, CSV/Markdown export
- ✅ **Settings (3/3)**: Profile editing, account info display, password change

### Known Limitations
- PostgreSQL checkpointing temporarily disabled (queries start fresh, no conversation memory across queries)
- E2B sandboxes created per-execution (~150ms cold start per query, no warm pools)
- Basic mobile responsiveness (functional but not optimized)

### Roadmap (v0.2+)
- UI/UX polish and refinements
- Conversation memory restoration (re-enable PostgreSQL checkpointing)
- Google OAuth integration
- Advanced data visualization (charts/graphs)
- PDF/PowerPoint export
- Collections for organizing analyses
- Performance optimizations (warm sandbox pools)

## Contributing

We welcome contributions! This is a beta release and we're actively improving the platform. Please:

1. Check existing issues before creating new ones
2. Follow the existing code style
3. Write tests for new features
4. Update documentation as needed

## License

MIT License - See LICENSE file for details

## Contact & Support

- **GitHub**: [https://github.com/marwazihs/nuelo-spectra](https://github.com/marwazihs/nuelo-spectra)
- **Issues**: Report bugs or request features via GitHub Issues
- **Version**: v0.1 Beta (February 2026)

---

*Spectra: Turn your data into decisions through the power of conversation.*
