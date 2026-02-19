# Phase 35: Docker Compose and Local Validation - Research

**Researched:** 2026-02-19
**Domain:** Docker Compose orchestration, local development stack
**Confidence:** HIGH

## Summary

Phase 35 creates a `docker-compose.yml` (or `compose.yaml`) that orchestrates the four existing Dockerfiles (backend, public frontend, admin frontend) plus a PostgreSQL container into a single `docker compose up` command. The Dockerfiles already exist from Phase 34 and are well-structured with health checks, non-root users, and proper entrypoint handling.

The core challenges are: (1) correct service networking so frontends reach backend via Docker DNS (`http://backend:8000`), (2) named volumes for both PostgreSQL data and file uploads that survive `docker compose down`, (3) healthcheck-gated startup ordering so the backend waits for PostgreSQL, and (4) correct `SPECTRA_MODE` and `BACKEND_URL` environment variables per service.

**Primary recommendation:** Create a single `compose.yaml` file at project root with four services (db, backend, public-frontend, admin-frontend), two named volumes (postgres_data, uploads_data), and one custom network. Use `SPECTRA_MODE=dev` for the local dev compose file so all routes are available. Override `BACKEND_URL=http://backend:8000` for both frontend services.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COMP-01 | Full local stack with `docker compose up` -- backend:8000, public:3000, admin:3001, postgres:5432 | Service definitions with port mappings; build contexts pointing to existing Dockerfiles |
| COMP-02 | File uploads survive `docker compose down && docker compose up` -- named volume `uploads_data` at `/app/uploads` | Named volumes persist across down/up by default; only removed with `-v` flag |
| COMP-03 | Backend starts only after PostgreSQL healthcheck passes (`depends_on: condition: service_healthy`) | PostgreSQL healthcheck using `pg_isready`; backend `depends_on` with `condition: service_healthy` |
| COMP-04 | Correct `SPECTRA_MODE` per service and `BACKEND_URL=http://backend:8000` for inter-service routing | Environment variables in compose override Dockerfile ENV defaults; Docker DNS resolves service names |
</phase_requirements>

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Docker Compose V2 | 2.x (bundled with Docker Desktop) | Multi-container orchestration | Built-in `docker compose` command, no separate install |
| PostgreSQL | 16-alpine | Local database | Matches production; alpine saves image size |
| compose.yaml | V2 spec (no `version:` key needed) | Compose file format | Modern compose files omit the `version` field |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| `pg_isready` | PostgreSQL healthcheck probe | In db service healthcheck and backend entrypoint |
| Docker named volumes | Data persistence | For postgres_data and uploads_data |
| Docker networks | Inter-service DNS | Frontend containers resolve `backend` hostname |

## Architecture Patterns

### Recommended Compose Structure
```
project-root/
├── compose.yaml              # NEW: Docker Compose orchestration
├── .env.docker               # NEW: Environment variables for compose
├── Dockerfile.backend        # EXISTS (Phase 34)
├── Dockerfile.frontend       # EXISTS (Phase 34)
├── Dockerfile.admin          # EXISTS (Phase 34)
├── Dockerfile.backend.dockerignore   # EXISTS
├── Dockerfile.frontend.dockerignore  # EXISTS
├── Dockerfile.admin.dockerignore     # EXISTS
├── backend/
│   └── docker-entrypoint.sh  # EXISTS
├── frontend/
└── admin-frontend/
```

### Pattern 1: Service Definitions with Build Contexts

**What:** Each service uses `build.dockerfile` pointing to the project-root Dockerfile, with the project root as build context.
**Why:** The existing Dockerfiles use `COPY backend/...` and `COPY frontend/...` paths, meaning they expect the project root as context.

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - uploads_data:/app/uploads
    environment:
      DATABASE_URL: postgresql+asyncpg://spectra:spectra@db:5432/spectra
      SECRET_KEY: local-dev-secret-key-change-in-production
      SPECTRA_MODE: dev
      CORS_ORIGINS: '["http://localhost:3000","http://localhost:3001"]'
      FRONTEND_URL: http://localhost:3000
      ADMIN_CORS_ORIGIN: http://localhost:3001
    depends_on:
      db:
        condition: service_healthy
```

### Pattern 2: PostgreSQL with Healthcheck

**What:** PostgreSQL service with `pg_isready` healthcheck so dependent services wait for actual readiness.
**Why:** `depends_on` without `condition` only waits for container start, not database readiness.

```yaml
  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: spectra
      POSTGRES_PASSWORD: spectra
      POSTGRES_DB: spectra
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U spectra -d spectra"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
```

### Pattern 3: Frontend Services with Port Mapping and BACKEND_URL Override

**What:** Both frontends expose internal port 3000 but map to different host ports. BACKEND_URL overridden to use Docker DNS.
**Why:** Admin Dockerfile uses `EXPOSE 3000` and `ENV PORT=3000` internally. Docker compose maps 3001:3000 for admin.

```yaml
  public-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      backend:
        condition: service_healthy

  admin-frontend:
    build:
      context: .
      dockerfile: Dockerfile.admin
    ports:
      - "3001:3000"    # Map host 3001 -> container 3000
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
```

### Pattern 4: Named Volumes Declaration

**What:** Top-level `volumes:` block declares named volumes that persist across `down`/`up`.
**Why:** `docker compose down` removes containers and networks but preserves named volumes. Only `docker compose down -v` removes them.

```yaml
volumes:
  postgres_data:
    driver: local
  uploads_data:
    driver: local
```

### Anti-Patterns to Avoid
- **Bind mounts for persistent data:** Don't use `./data:/var/lib/postgresql/data` -- named volumes are managed by Docker and avoid permission issues
- **`depends_on` without condition:** `depends_on: [db]` only waits for container start, not readiness. Always use `condition: service_healthy`
- **Hardcoded localhost in BACKEND_URL:** Inside Docker network, services reach each other by service name, not localhost. `http://backend:8000` not `http://localhost:8000`
- **Setting `version:` in compose.yaml:** The `version` field is obsolete in modern Docker Compose V2. Omit it entirely
- **Using `SPECTRA_MODE=public` for local dev compose:** The requirement says `dev` mode for local development. The `public` mode is for production Dokploy deployment only

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DB wait logic | Custom wait-for-it scripts | `depends_on: condition: service_healthy` + backend entrypoint `pg_isready` loop | Docker Compose V2 handles this natively; the entrypoint already has a pg_isready wait loop as defense-in-depth |
| Service discovery | Hardcoded IPs or link aliases | Docker Compose default network DNS | Services resolve each other by name automatically |
| Data persistence | Bind-mount host directories | Named Docker volumes | Avoids UID/GID permission issues between host and container |
| Port conflict detection | Manual port checks | Docker Compose error output | Compose will fail clearly if ports are already in use |

## Common Pitfalls

### Pitfall 1: DATABASE_URL Format Mismatch
**What goes wrong:** Backend uses SQLAlchemy async engine requiring `postgresql+asyncpg://` scheme, but Alembic needs plain `postgresql://`. The entrypoint parses DATABASE_URL with sed to extract host/port for `pg_isready`.
**Why it happens:** Different components expect different URL formats.
**How to avoid:** Set `DATABASE_URL=postgresql+asyncpg://spectra:spectra@db:5432/spectra` in compose. The entrypoint sed regex handles both formats. Alembic env.py already strips `+asyncpg` (line 233-234 in main.py shows this pattern). Verify the entrypoint sed regex works with the `+asyncpg` prefix.
**Warning signs:** Backend container crash loops with "could not connect to database" errors.

### Pitfall 2: Admin Frontend Internal Port
**What goes wrong:** Both frontend Dockerfiles use `EXPOSE 3000` and `ENV PORT=3000`. If you try to set `PORT=3001` in compose environment, the standalone server inside the container listens on 3001 but the healthcheck still hits port 3000.
**How to avoid:** Keep internal port at 3000 for both frontends. Use Docker port mapping `3001:3000` for admin. Do NOT override PORT env var.
**Warning signs:** Admin frontend healthcheck fails; container marked unhealthy.

### Pitfall 3: CORS Origins Must Include Both Frontend URLs
**What goes wrong:** Backend CORS rejects requests from admin frontend.
**Why it happens:** Default `CORS_ORIGINS` only includes `http://localhost:3000`. Admin is on `http://localhost:3001`.
**How to avoid:** Set `CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]` and `ADMIN_CORS_ORIGIN=http://localhost:3001` in backend environment.

### Pitfall 4: Upload Volume Permissions
**What goes wrong:** Backend runs as `appuser` (UID 1001) but volume may be owned by root on first creation.
**Why it happens:** Docker creates named volumes as root. The Dockerfile declares `VOLUME ["/app/uploads"]` but the volume mount in compose overrides this.
**How to avoid:** The backend Dockerfile copies `/app` with `--chown=appuser:appuser`. The entrypoint creates the uploads dir via `Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)` in the lifespan handler. Since the volume is mounted at `/app/uploads` and the container runs as UID 1001, Docker should handle permissions correctly for named volumes. If issues arise, add an init container or entrypoint step to `chown`.
**Warning signs:** "Permission denied" errors when uploading files.

### Pitfall 5: Entrypoint sed Regex with asyncpg URL
**What goes wrong:** The entrypoint extracts DB_HOST from DATABASE_URL using sed. The `+asyncpg` in the scheme could theoretically confuse the regex.
**How to avoid:** The sed regex `'s|.*@([^:/]+).*|\1|'` matches everything after `@`, so it correctly handles `postgresql+asyncpg://user:pass@host:port/db`. Verified: the regex only cares about `@` delimiter, not the scheme. This is safe.

### Pitfall 6: Build Cache and Context Size
**What goes wrong:** First `docker compose up --build` takes very long because all three images build from scratch.
**Why it happens:** Large build contexts if .dockerignore is missing, or no layer cache.
**How to avoid:** The .dockerignore files already exist from Phase 34. Use `docker compose build` separately to pre-warm cache. Subsequent builds use layer caching.

## Code Examples

### Complete compose.yaml Structure
```yaml
# compose.yaml — Spectra Local Development Stack
# Usage: docker compose up --build
# Teardown: docker compose down (preserves data)
# Full reset: docker compose down -v (destroys data)

services:
  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: spectra
      POSTGRES_PASSWORD: spectra
      POSTGRES_DB: spectra
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U spectra -d spectra"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - uploads_data:/app/uploads
    env_file:
      - .env.docker
    environment:
      DATABASE_URL: postgresql+asyncpg://spectra:spectra@db:5432/spectra
      SPECTRA_MODE: dev
    depends_on:
      db:
        condition: service_healthy

  public-frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      backend:
        condition: service_healthy

  admin-frontend:
    build:
      context: .
      dockerfile: Dockerfile.admin
    ports:
      - "3001:3000"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      backend:
        condition: service_healthy

volumes:
  postgres_data:
    driver: local
  uploads_data:
    driver: local
```

### .env.docker Template
```bash
# .env.docker — Docker Compose environment variables for local development
# This file provides secrets/config that shouldn't be hardcoded in compose.yaml
# Copy from .env.example and fill in values

# JWT (required -- backend will fail without this)
SECRET_KEY=local-dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Frontend URLs for CORS
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
ADMIN_CORS_ORIGIN=http://localhost:3001

# LLM Keys (at least one required for agent functionality)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=

# Optional services
E2B_API_KEY=
TAVILY_API_KEY=
```

### Validation Commands
```bash
# Start full stack
docker compose up --build

# Verify all containers are running and healthy
docker compose ps

# Check backend logs for SPECTRA_MODE and pg_isready
docker compose logs backend | head -20

# Test backend health
curl http://localhost:8000/health

# Test public frontend
curl -s http://localhost:3000 | head -5

# Test admin frontend
curl -s http://localhost:3001 | head -5

# Test file upload persistence
# 1. Upload a file via http://localhost:3000
# 2. docker compose down
# 3. docker compose up
# 4. Verify file still accessible

# Full teardown (removes volumes too)
docker compose down -v
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `docker-compose.yml` with `version: "3.8"` | `compose.yaml` with no `version:` field | Docker Compose V2 (2023+) | Cleaner file, no version confusion |
| `docker-compose` (hyphenated binary) | `docker compose` (subcommand) | Docker Compose V2 (2023+) | Bundled with Docker Desktop, no separate install |
| `depends_on: [db]` | `depends_on: { db: { condition: service_healthy } }` | Compose spec (2022+) | Proper startup ordering based on readiness |
| `links:` for service discovery | Default network DNS resolution | Docker Compose V2 | Services auto-resolve by name; links deprecated |

## Open Questions

1. **LLM API keys in .env.docker**
   - What we know: Backend validates LLM providers at startup and logs warnings but does not crash if no key is set
   - What's unclear: Whether the agent functionality is required for local validation testing
   - Recommendation: Make .env.docker a template; user copies and fills in API keys. Backend should still start without them (just logs warnings)

2. **PostgreSQL version alignment with production**
   - What we know: Dokploy manages PostgreSQL in production; compose uses postgres:16-alpine for local
   - What's unclear: Exact PostgreSQL version in Dokploy production
   - Recommendation: Use postgres:16-alpine for local dev; this is safe for development purposes

3. **Backend health endpoint path**
   - What we know: Dockerfile.backend healthcheck uses `curl -f http://localhost:8000/health`
   - Verified: The health router is imported in main.py
   - Recommendation: Use same `/health` endpoint in compose healthcheck; already handled by Dockerfile HEALTHCHECK

## Sources

### Primary (HIGH confidence)
- Project files: Dockerfile.backend, Dockerfile.frontend, Dockerfile.admin (Phase 34 outputs)
- Project files: backend/docker-entrypoint.sh, backend/app/config.py, backend/app/main.py, backend/app/database.py
- [Docker Compose startup order docs](https://docs.docker.com/compose/how-tos/startup-order/)
- [Docker Compose services reference](https://docs.docker.com/reference/compose-file/services/)
- [Docker compose down reference](https://docs.docker.com/reference/cli/docker/compose/down/)

### Secondary (MEDIUM confidence)
- [Docker Compose healthcheck patterns (2025)](https://www.tvaidyan.com/2025/02/13/health-checks-in-docker-compose-a-practical-guide/)
- [Docker Compose volumes guide](https://kinsta.com/blog/docker-compose-volumes/)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Docker Compose V2 is mature, well-documented, and the patterns are standard
- Architecture: HIGH - All Dockerfiles exist and are verified; compose is straightforward orchestration
- Pitfalls: HIGH - Based on direct code inspection of existing Dockerfiles, entrypoint, and config files
- Environment variables: HIGH - Verified against backend/app/config.py for exact field names and defaults

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (stable domain, Docker Compose patterns change slowly)
