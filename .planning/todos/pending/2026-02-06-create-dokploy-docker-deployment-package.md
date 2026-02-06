---
created: 2026-02-06T09:53
title: Create Dokploy Docker deployment package
area: deployment
files:
  - backend/Dockerfile
  - frontend/Dockerfile
  - docker-compose.yml
  - .dockerignore
---

## Problem

Spectra v0.1 Beta MVP is code-complete and ready for production deployment. Need a deployment strategy and package for deploying to Dokploy (Docker-based PaaS).

Current deployment requirements:
- Backend: FastAPI + PostgreSQL + E2B sandbox
- Frontend: Next.js 16 (App Router, SSR)
- Database: PostgreSQL 16
- Environment: E2B_API_KEY, DATABASE_URL, JWT_SECRET_KEY, EMAIL_SERVICE_API_KEY
- File storage: Local uploads directory (50MB limit per file)

Dokploy supports Docker and docker-compose deployments with persistent volumes, environment variable management, and automatic SSL.

## Solution

Create comprehensive Docker deployment package:

1. **Backend Dockerfile:**
   - Multi-stage build (builder + runtime)
   - Python 3.11+ with FastAPI dependencies
   - Expose port 8000
   - Run with uvicorn

2. **Frontend Dockerfile:**
   - Node.js 20+ multi-stage build
   - Next.js production build
   - Expose port 3000
   - Run with `next start`

3. **docker-compose.yml:**
   - Services: postgres, backend, frontend
   - Networks: internal bridge
   - Volumes: postgres-data, uploads
   - Environment variables via .env file
   - Health checks for all services

4. **PostgreSQL setup:**
   - postgres:16-alpine image
   - Persistent volume for data
   - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD from env

5. **.dockerignore files:**
   - Backend: exclude .venv, __pycache__, .pytest_cache, uploads/
   - Frontend: exclude node_modules, .next, .turbo

6. **Deployment documentation:**
   - README-DEPLOYMENT.md with Dokploy setup instructions
   - Environment variable template (.env.example)
   - Database migration commands (alembic upgrade head)
   - Health check endpoints verification

7. **Dokploy-specific configurations:**
   - Port mappings (80→3000 frontend, 8000→backend)
   - Volume mounts for uploads and database
   - Restart policies (always)
   - Network configuration

**Constraints:**
- Backend requires E2B API key for sandbox execution
- Frontend needs NEXT_PUBLIC_API_URL for SSR
- Database URL must use postgresql:// format (not postgresql+asyncpg://)
- Uploads directory must be persistent across container restarts
- CORS configured for production domain (not localhost)

**Testing checklist:**
- [ ] Database migrations run successfully
- [ ] Backend health check (GET /health) returns 200
- [ ] Frontend loads and displays login page
- [ ] File upload and AI chat workflow completes end-to-end
- [ ] E2B sandbox executes code successfully
- [ ] JWT authentication works (login/logout/refresh)
- [ ] Password reset email sent in production mode

**Next steps after deployment:**
- Configure production email service (Mailgun API key)
- Set up monitoring and error tracking (optional: Sentry)
- Monitor E2B sandbox costs
- Test with real user data and queries
