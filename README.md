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

#### 1. Clone the repository
```bash
git clone https://github.com/marwazihs/nuelo-spectra.git
cd nuelo-spectra
```

#### 2. Set up PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
createdb spectra
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql-16
sudo systemctl start postgresql
sudo -u postgres createdb spectra
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

**Windows:**
```bash
# Download PostgreSQL 16 from https://www.postgresql.org/download/windows/
# Run the installer and set password during installation
# Open SQL Shell (psql) and run:
CREATE DATABASE spectra;
```

**Verify PostgreSQL is running:**
```bash
psql -U postgres -d spectra -c "SELECT version();"
# Should show PostgreSQL 16.x version info
```

#### 3. Set up the backend
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

#### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

**Required environment variables:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/spectra

# JWT (generate a secure secret key)
SECRET_KEY=$(openssl rand -hex 32)

# E2B Sandbox (sign up at https://e2b.dev for API key)
E2B_API_KEY=your-e2b-api-key

# LLM Provider (choose one: anthropic, openai, or google)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
# OR
# OPENAI_API_KEY=your-openai-api-key
# OR
# GOOGLE_API_KEY=your-google-api-key
```

**Optional environment variables:**
```bash
# Email Service (for password reset emails - Mailgun)
EMAIL_SERVICE_API_KEY=your-mailgun-api-key

# LangSmith (for agent debugging and tracing)
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_TRACING=true

# Frontend URL (if different from default)
FRONTEND_URL=http://localhost:3000
```

#### 5. Run database migrations
```bash
# Make sure you're in the backend directory
alembic upgrade head
```

#### 6. Start the backend server
```bash
uvicorn app.main:app --reload
# Backend will run at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

#### 7. Set up the frontend (in a new terminal)
```bash
cd frontend
npm install
npm run dev
# Frontend will run at http://localhost:3000
```

#### 8. Verify the installation

1. **Backend health check**: Visit http://localhost:8000/health (should return `{"status": "healthy"}`)
2. **Frontend**: Open http://localhost:3000 in your browser
3. **Create an account**: Click "Sign Up" and create your first account
4. **Upload a file**: Upload a CSV or Excel file to test the AI analysis

### Troubleshooting

**Database connection errors:**
- Verify PostgreSQL is running: `brew services list` (macOS) or `sudo systemctl status postgresql` (Linux)
- Check DATABASE_URL in .env matches your PostgreSQL credentials
- Ensure database `spectra` exists: `psql -U postgres -l`

**E2B sandbox errors:**
- Verify E2B_API_KEY is set correctly in .env
- Check your E2B account has available credits at https://e2b.dev/dashboard

**LLM API errors:**
- Ensure you've set the correct API key for your chosen LLM_PROVIDER
- Verify your API key has sufficient credits/quota

**Import errors:**
- Make sure you've installed dependencies: `uv sync` or `pip install -e .`
- Activate virtual environment: `source .venv/bin/activate`

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
