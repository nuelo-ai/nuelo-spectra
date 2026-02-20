# Pitfalls Research: Docker + Dokploy Deployment

**Domain:** Containerizing and deploying an existing FastAPI + Next.js monorepo to Dokploy
**Researched:** 2026-02-18
**Confidence:** HIGH (based on official Next.js docs, Docker official docs, verified GitHub issues, and Dokploy documentation)

**Context:** Spectra is adding Docker containerization and Dokploy deployment to an existing production app. The app has two Next.js frontends (`frontend/`, `admin-frontend/`) and one FastAPI backend (`backend/`) in a monorepo, with SPECTRA_MODE env var controlling routing, file uploads stored on local disk, Alembic migrations, and multiple API keys in environment variables. No Dockerfiles exist yet.

---

## Critical Pitfalls

Mistakes at this level cause silent failures, broken deploys, or security exposures.

### Pitfall 1: NEXT_PUBLIC_API_URL Baked as `undefined` at Build Time

**What goes wrong:**
Both Next.js apps make API calls through a proxy rewrite configured in `next.config.ts`. Currently `frontend/next.config.ts` rewrites `/api/:path*` to `http://localhost:8000/:path*` and `admin-frontend/next.config.ts` rewrites to `http://localhost:8000/api/:path*`. In Docker, `localhost` inside the container refers to the container itself, not the backend service. If the rewrite destination is hardcoded to `localhost:8000`, the Next.js server-side proxy will fail with `ECONNREFUSED` — no requests reach the backend.

More critically: any `NEXT_PUBLIC_` variables (like `NEXT_PUBLIC_API_URL`) must be provided at `docker build` time as `ARG` values, not injected at container runtime. If they are passed only at `docker run` time (as `--env` flags or in `docker-compose.yml`'s `environment:` block), `next build` runs during the image build step — before those runtime env values exist — and the variable is baked into the compiled JavaScript as `undefined`.

**Why it happens:**
Next.js inlines `NEXT_PUBLIC_*` values during the `next build` process by doing string replacement in the compiled JavaScript output. The build happens inside the Dockerfile's `RUN npm run build` step. At that point, only `ARG` values (build arguments) and build-stage environment variables are available. Container runtime `environment:` values in `docker-compose.yml` are not available during `docker build`. Developers familiar with runtime env injection assume Docker works the same way as their local `.env` file.

**Spectra-specific impact:**
If `NEXT_PUBLIC_API_URL` is undefined, API calls in the public frontend will silently point to `undefined` and fail. The admin frontend has no `NEXT_PUBLIC_` vars currently (it uses relative `/api` paths via rewrites), but the rewrite destination `http://localhost:8000/api/:path*` must become `http://backend:8000/api/:path*` (the Docker service name) to work inside the container network.

**How to avoid:**
1. In each `next.config.ts`, make the rewrite destination configurable via an environment variable:
   ```typescript
   const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
   const nextConfig: NextConfig = {
     async rewrites() {
       return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
     },
   };
   ```
2. Pass `BACKEND_URL` as a Docker `ARG` so it is available at build time:
   ```dockerfile
   ARG BACKEND_URL=http://backend:8000
   ENV BACKEND_URL=$BACKEND_URL
   RUN npm run build
   ```
3. For any `NEXT_PUBLIC_*` variables added in the future, always pass them as build `ARG`s, not runtime `ENV` in `docker-compose.yml`.
4. Do NOT use `docker-compose.yml`'s `environment:` block for `NEXT_PUBLIC_*` — it runs after the image is built.

**Warning signs:**
- API calls from the Next.js app return `fetch failed` or `ECONNREFUSED` in container logs
- Browser network tab shows requests to `undefined/api/...` or `http://localhost:8000/api/...`
- The app renders but all data-fetching fails silently (auth, file list, chat all broken)
- `console.log(process.env.NEXT_PUBLIC_API_URL)` returns `undefined` in the browser

**Severity:** BLOCKING — the app silently renders but no data loads. No obvious error message to diagnose.

**Phase to address:**
Phase 1 (Dockerfiles) — Before writing any Dockerfile for the Next.js apps, update `next.config.ts` rewrites to use `BACKEND_URL` env var. Verify by running `docker build` and inspecting the compiled `.next/` output.

---

### Pitfall 2: File Uploads Lost on Container Restart

**What goes wrong:**
The backend stores uploaded files at `backend/uploads/{user_id}/{file_uuid}.csv`. The `settings.upload_dir` defaults to `"uploads"` (relative path). In Docker, this resolves to `/app/uploads` inside the container's writable layer. When Dokploy redeploys (new image pushed), the old container is destroyed and a new one starts. All files in `/app/uploads` are gone. Users find their uploaded datasets have disappeared, but database records still exist (file rows remain in PostgreSQL), creating a broken state: DB says the file exists, but the file is not on disk.

**Why it happens:**
Container filesystems are ephemeral by design. Anything written inside the container (outside of mounted volumes) is discarded when the container is replaced. The `FileService.upload_file` method writes to `Path(settings.upload_dir) / str(user_id)` which is a path inside the container unless a volume is mounted at that path. The Alembic migration tables and LangGraph checkpoint tables survive in PostgreSQL (external service), but files on local disk do not.

**Spectra-specific impact:**
`FileService.upload_file` saves to disk first, then creates a DB record. On redeploy: DB records point to files that no longer exist. The Onboarding Agent stored the data summary, but agents that re-read the file for new queries (E2B sandbox receives the file path) will get a FileNotFoundError. The admin file management UI will show files that 404 on download.

**How to avoid:**
1. In `docker-compose.yml` (and Dokploy volume config), mount a named volume to the upload directory:
   ```yaml
   services:
     backend:
       volumes:
         - uploads_data:/app/uploads
   volumes:
     uploads_data:
   ```
2. Set `UPLOAD_DIR=/app/uploads` explicitly as an environment variable so the path is predictable.
3. In Dokploy's application settings, configure a persistent volume mount: host path or named volume at `/app/uploads`.
4. Verify volume persistence by uploading a file, then redeploying and confirming the file is still accessible.

**Warning signs:**
- Users report "my files disappeared after the update"
- Backend logs show `FileNotFoundError` for existing DB file records
- File download endpoints return 404 for files that appear in the list
- `docker exec backend ls /app/uploads` returns empty after redeploy

**Severity:** BLOCKING — user data loss after every deployment. Silent (no error at upload time, fails only when files are accessed post-redeploy).

**Phase to address:**
Phase 1 (Dockerfiles) — Add the volume mount to `docker-compose.yml` before any production deployment. Add a post-deploy smoke test that verifies an uploaded file survives a container restart.

---

### Pitfall 3: FastAPI Starts Before PostgreSQL Is Ready (Migration Race Condition)

**What goes wrong:**
`main.py` runs Alembic-dependent startup logic in `lifespan()`: it initializes the `AsyncPostgresSaver` checkpointer (`checkpointer.setup()` creates LangGraph tables), connects to the DB engine, and the SQLAlchemy `engine` is created at module import time. If the FastAPI container starts before the PostgreSQL container is ready to accept connections, the backend crashes on startup with `asyncpg.exceptions.TooManyConnectionsError`, `Connection refused`, or `FATAL: the database system is starting up`. Docker Compose's `depends_on` does not wait for the database to be ready — it only waits for the container to start.

**Why it happens:**
PostgreSQL container starts in seconds, but it takes additional time (5-30 seconds on cold start) to initialize the data directory and accept connections. `depends_on: postgres` only means the postgres container process started, not that PostgreSQL accepted its first connection. Without an explicit wait mechanism, FastAPI's SQLAlchemy engine tries to connect before PostgreSQL is ready. In Dokploy, services may start in parallel without dependency ordering.

**Spectra-specific impact:**
The `lifespan()` function in `main.py` has multiple DB-dependent operations in sequence: LLM validation (httpx calls, safe), then `validate_smtp_connection` (safe), then `AsyncConnectionPool` for LangGraph checkpointer (DB-dependent), then `checkpointer.setup()` (DB-dependent). If the pool creation fails, the entire `lifespan()` throws, FastAPI never starts serving requests, and health checks fail. Dokploy will mark the deployment as failed and may not retry.

**How to avoid:**
1. Add a `wait-for-db.sh` script that loops until PostgreSQL accepts a connection, then exec the main process:
   ```bash
   #!/bin/bash
   echo "Waiting for PostgreSQL..."
   until pg_isready -h "$POSTGRES_HOST" -p 5432 -U "$POSTGRES_USER"; do
     sleep 1
   done
   echo "PostgreSQL ready. Running migrations..."
   alembic upgrade head
   echo "Starting FastAPI..."
   exec uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
2. Use this as the Docker `CMD` or `ENTRYPOINT`:
   ```dockerfile
   COPY scripts/entrypoint.sh /entrypoint.sh
   RUN chmod +x /entrypoint.sh
   CMD ["/entrypoint.sh"]
   ```
3. Run `alembic upgrade head` inside this script before starting uvicorn — this ensures migrations run before the app serves any traffic.
4. In `docker-compose.yml`, add a healthcheck to the postgres service and use `depends_on: condition: service_healthy` for the backend:
   ```yaml
   postgres:
     healthcheck:
       test: ["CMD-SHELL", "pg_isready -U $POSTGRES_USER"]
       interval: 5s
       timeout: 5s
       retries: 10
   backend:
     depends_on:
       postgres:
         condition: service_healthy
   ```

**Warning signs:**
- Backend container exits immediately on first deploy with `Connection refused` in logs
- LangGraph checkpointer tables missing from DB after deploy (setup() never ran)
- Dokploy marks deployment as failed on the first attempt but works on retry
- `asyncpg.exceptions.TooManyConnectionsError` in backend logs during startup

**Severity:** BLOCKING — backend may start before DB is ready, causing deployment failures. Intermittent: sometimes works on retry, making it hard to diagnose.

**Phase to address:**
Phase 1 (Dockerfiles) — Write the entrypoint script as part of the backend Dockerfile. Test by intentionally delaying the postgres container and verifying the backend waits correctly.

---

### Pitfall 4: Secrets Baked into Docker Image Layers

**What goes wrong:**
A `.env` file or `ARG` instruction in a Dockerfile permanently stores secrets (API keys, JWT secret, SMTP password) in the image's layer history. Even if the `.env` file is later deleted with `RUN rm .env`, Docker layers are immutable — the file exists in an earlier layer and is recoverable with `docker history --no-trunc` or by extracting earlier layers. If the image is pushed to Docker Hub or a public registry, all secrets are exposed. This is the most common and most severe Docker security mistake.

**Why it happens:**
Developers often copy their entire project directory with `COPY . .` which includes the `.env` file if it is not in `.dockerignore`. Alternatively, secrets are passed as Docker `ARG` values which also persist in layer history (unlike BuildKit secrets). The `.env` file approach feels natural because it works identically to local development.

**Spectra-specific impact:**
The `backend/.env` file contains: `ANTHROPIC_API_KEY`, `E2B_API_KEY`, `TAVILY_API_KEY`, `OPENROUTER_API_KEY`, `SECRET_KEY` (JWT), `SMTP_PASS`, and `ADMIN_PASSWORD`. If any of these end up in a Docker image layer, they are exposed to anyone with image pull access. The `SECRET_KEY` is particularly dangerous — leaking it allows forging admin JWTs.

**How to avoid:**
1. Create `.dockerignore` at the monorepo root and in each service directory:
   ```
   .env
   .env.*
   !.env.example
   .git
   node_modules/
   __pycache__/
   .venv/
   venv/
   *.pyc
   ```
2. Never use `ARG SECRET_KEY` or `ENV SECRET_KEY=...` in Dockerfiles for secrets.
3. Pass secrets at container runtime only, via `docker-compose.yml`'s `environment:` block referencing host env vars:
   ```yaml
   environment:
     - SECRET_KEY=${SECRET_KEY}
     - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
   ```
4. In Dokploy, use the "Environment Variables" section of each service to inject secrets at runtime (they are not stored in image layers).
5. Use BuildKit secret mounts if a secret is needed at build time (e.g., private npm registry):
   ```dockerfile
   RUN --mount=type=secret,id=npm_token npm install
   ```
6. Scan images before pushing: `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image spectra-backend:latest`

**Warning signs:**
- `docker history spectra-backend:latest` shows `ARG` or `ENV` entries with key names
- `docker run --rm spectra-backend:latest env` outputs API keys
- `.env` file is not listed in `.dockerignore`
- `COPY . .` instruction in Dockerfile without a restrictive `.dockerignore`

**Severity:** BLOCKING (security) — silent in operation but catastrophically exposed if images reach any registry.

**Phase to address:**
Phase 1 (Dockerfiles) — Write `.dockerignore` files before writing any `COPY` instruction. Add a CI check that runs `docker history` on built images and fails if any secrets pattern is found.

---

### Pitfall 5: Wrong SPECTRA_MODE Per Service Silently Breaks Routing

**What goes wrong:**
The `SPECTRA_MODE` env var controls which routers FastAPI registers. `public` mode registers public routes only; `admin` mode registers admin routes only; `dev` mode registers both. If `SPECTRA_MODE` is set to `dev` on the public-facing service, the admin API endpoints (`/api/admin/*`) are exposed to the public internet — a security breach. If set to `public` on the admin service, all admin API calls return 404 and the admin frontend appears completely broken with no obvious error. Both failures are silent: the app starts successfully, logs no warnings, and appears to function normally until someone tries to use it.

**Why it happens:**
There are two FastAPI instances planned for production: one serving the public frontend (SPECTRA_MODE=public) and one serving the admin frontend (SPECTRA_MODE=admin). Developers copying environment variables between services, or using a shared `.env` file, may set the same `SPECTRA_MODE` value for both services. The `dev` mode is appropriate locally but must never be used in production.

**Spectra-specific impact:**
- `SPECTRA_MODE=admin` on the public service: users cannot log in (auth router not registered), file upload fails (files router not registered). Silent 404 on all user-facing routes.
- `SPECTRA_MODE=public` on the admin service: admin dashboard loads, login works, then every admin API call returns 404.
- `SPECTRA_MODE=dev` on both (the "it works in dev, let me just copy the config" failure): admin routes exposed publicly, enabling credential enumeration and potential admin login attempts from the internet.

**How to avoid:**
1. Use separate `docker-compose` services with explicitly different environment variables:
   ```yaml
   backend-public:
     environment:
       SPECTRA_MODE: public
   backend-admin:
     environment:
       SPECTRA_MODE: admin
   ```
2. In Dokploy, create two separate Application services for the backend, each with its own environment variable set.
3. Add a startup log line that prominently displays the active mode: `logger.info(f"Starting Spectra in {mode.upper()} mode")` — this already exists in `main.py`.
4. Add a health check endpoint that returns the current mode (NOT sensitive config, just the mode string) so Dokploy health checks can verify the correct mode is running.
5. Never use `SPECTRA_MODE=dev` in production. If you need both admin and public on one process (dev only), that is the dev mode — not a production configuration.

**Warning signs:**
- Admin frontend shows 404 on every API call after login
- Public frontend login returns 404 (router not mounted)
- Backend logs show `Starting Spectra in DEV mode` on a production deployment
- Admin routes accessible from the public internet (check with `curl https://your-public-domain/api/admin/users`)

**Severity:** BLOCKING (wrong mode = feature completely broken) AND security risk (dev mode in production).

**Phase to address:**
Phase 2 (Dokploy Services) — When configuring Dokploy services, explicitly set and verify `SPECTRA_MODE` for each service as a named check in the deployment task. Add post-deploy smoke test that calls `GET /health` and checks the mode in logs.

---

### Pitfall 6: Monorepo Build Context Set to Wrong Directory

**What goes wrong:**
Docker's `COPY` instruction can only access files within the build context directory. In a monorepo with structure `spectra-dev/backend/`, `spectra-dev/frontend/`, `spectra-dev/admin-frontend/`, if the Dockerfile for the backend is at `backend/Dockerfile` and the Docker build context is set to `backend/`, then `COPY . .` copies only backend files — correct. But if the Dockerfile tries to `COPY ../shared/ /app/shared/` to access a shared directory, it fails with `COPY failed: forbidden path outside the build context`. Conversely, if the build context is set to the monorepo root (`spectra-dev/`), then `COPY . .` copies everything including `node_modules/`, `.venv/`, `.git/`, `.env` files, and the entire `frontend/` directory into the backend image — massively bloating the image and potentially including secrets.

**Why it happens:**
Monorepo Docker builds require careful coordination between: (1) where the Dockerfile is, (2) what directory is the build context, and (3) what `.dockerignore` applies to that context. In Dokploy's Application settings, the "Docker Context Path" and "Dockerfile Path" are configured separately. Setting context to the wrong path is the most common source of `COPY` failures and image bloat.

**Spectra-specific impact:**
The monorepo has three separate services each needing its own Docker build:
- `frontend/Dockerfile` — context should be `frontend/`
- `admin-frontend/Dockerfile` — context should be `admin-frontend/`
- `backend/Dockerfile` — context should be `backend/`

Each service's `.dockerignore` must live in its context directory. If the context is set to the monorepo root instead:
- `node_modules/` from frontend (hundreds of MB) ends up in the backend image
- `backend/.venv/` (hundreds of MB) ends up in the frontend image
- `backend/.env` (with API keys) ends up in every image

**How to avoid:**
1. Place each Dockerfile inside its service directory (`backend/Dockerfile`, `frontend/Dockerfile`, `admin-frontend/Dockerfile`).
2. Place a `.dockerignore` inside each service directory that excludes the service's own build artifacts.
3. In `docker-compose.yml`, set context to the service subdirectory:
   ```yaml
   services:
     backend:
       build:
         context: ./backend
         dockerfile: Dockerfile
     frontend:
       build:
         context: ./frontend
         dockerfile: Dockerfile
   ```
4. In Dokploy Application settings: set "Docker Context Path" to `./backend` (or `./frontend`), and "Dockerfile Path" to `Dockerfile`.
5. Verify by running `docker build` locally with the exact context path and confirming the image size is reasonable (backend: ~500MB-1GB, Next.js: ~200-400MB with standalone output).

**Warning signs:**
- `COPY failed: file not found in build context` errors during `docker build`
- Docker image sizes are unexpectedly large (>2GB for a simple service)
- `docker run backend python -m pip list` shows no packages (COPY copied wrong directory)
- Build succeeds but the wrong files are present in the container

**Severity:** BLOCKING — build fails or produces broken images. Build-time error (easy to detect during development if tested locally first).

**Phase to address:**
Phase 1 (Dockerfiles) — Test each `docker build` command locally with the explicit context path before configuring Dokploy. Check image sizes.

---

### Pitfall 7: JWT_SECRET_KEY Randomly Generated Per Container Restart

**What goes wrong:**
If `SECRET_KEY` (the JWT signing key) is generated randomly at startup instead of being a fixed secret, every container restart invalidates all existing user sessions. Users will be logged out mid-session. Worse: if the public backend and admin backend services use different `SECRET_KEY` values, admin tokens issued by the admin service cannot be verified by the public service (or vice versa, if they ever share token verification logic).

**Why it happens:**
In local development, `SECRET_KEY` may be set to a generated value in `.env` or even hardcoded. In production Docker environments, if `SECRET_KEY` is not explicitly provided as an environment variable, Pydantic's `BaseSettings` may fall back to a default value (if one is set in `config.py`) or raise a validation error. Some developers generate a random `SECRET_KEY` at container startup as a "sensible default" — this causes session invalidation on every deploy.

**Spectra-specific impact:**
The `backend/app/config.py` has `secret_key: str` with no default value, meaning Pydantic will raise `ValidationError` if `SECRET_KEY` is not set — which is the correct behavior and prevents the random-generation problem. However, if a developer adds a fallback default (`secret_key: str = secrets.token_hex(32)`) to make local startup easier, every container restart generates a new key and invalidates all JWTs.

**How to avoid:**
1. Generate a single `SECRET_KEY` once: `python -c "import secrets; print(secrets.token_hex(32))"` and store it in Dokploy's environment variables (not in the image, not in `.env` files committed to git).
2. Use the same `SECRET_KEY` value for both the public backend and admin backend services.
3. Never set a dynamic default for `secret_key` in `config.py`. The existing behavior (no default = fail to start if not set) is correct.
4. Document the `SECRET_KEY` generation procedure in the deployment runbook.

**Warning signs:**
- Users are logged out after every deployment
- JWT verification errors in logs after container restart
- `Settings()` startup logs show `secret_key` being set to a random value
- Admin tokens fail to authenticate on the public backend (different keys)

**Severity:** ANNOYING (users get logged out on deploy) to BLOCKING (if secret changes break service-to-service token verification).

**Phase to address:**
Phase 2 (Dokploy Services) — When configuring environment variables in Dokploy, generate `SECRET_KEY` once and use it for all backend services. Add it to the deployment checklist.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Use `SPECTRA_MODE=dev` in production | One process handles everything | Admin routes exposed publicly, no isolation | Never in production |
| Skip `.dockerignore`, use `COPY . .` | Simpler Dockerfile | Bloated images, potential secret leakage | Never |
| Mount source code as volume (`./backend:/app`) | Live code changes without rebuild | Works locally, breaks in Dokploy (no local filesystem on server) | Local dev only |
| Hardcode `localhost:8000` in `next.config.ts` | Works locally | Broken in Docker (localhost = container itself) | Never |
| Store `SECRET_KEY` in `.env` committed to git | Easy team sharing | Security breach if repo is ever public | Never |
| Skip entrypoint wait-for-db script | Simpler deployment | Intermittent startup failures on cold deploys | Never in production |
| Use the same `.env` file for public and admin backends | One file to manage | Wrong `SPECTRA_MODE` silently breaks routing | Never in production |
| Use `output: 'export'` (static) for Next.js | Smaller image, no Node server | No rewrites, no server-side rendering, no API routes | Only if Next.js is fully static (Spectra is not) |

---

## Integration Gotchas

Common mistakes when connecting services inside Docker and Dokploy.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Next.js → Backend | Rewrite destination uses `localhost:8000` | Use `http://backend:8000` (Docker service name) or env var `BACKEND_URL` |
| FastAPI → PostgreSQL | `DATABASE_URL=postgresql://...@localhost/...` | Use `postgresql://...@postgres/...` (service name) or `db` — whatever the compose service is named |
| FastAPI → PostgreSQL (async) | `postgresql://` prefix instead of `postgresql+asyncpg://` | SQLAlchemy async requires `postgresql+asyncpg://` driver prefix |
| LangGraph checkpointer → PostgreSQL | `postgresql+asyncpg://` prefix — asyncpg driver incompatible with psycopg | LangGraph's `AsyncPostgresSaver` requires `postgresql://` (psycopg3), not asyncpg |
| Backend startup → PostgreSQL | No wait-for-db logic | Entrypoint script with `pg_isready` loop before `alembic upgrade head` |
| Dokploy services → each other | Services in different Dokploy applications cannot communicate on `dokploy-network` by default | Add `dokploy-network` external network to both services in `docker-compose.yml` |
| E2B sandbox | E2B makes outbound calls to `api.e2b.dev` — no Docker networking change needed | E2B is external cloud; only the `E2B_API_KEY` env var matters |
| APScheduler | APScheduler runs inside FastAPI — works in Docker as long as DB is available | Set `ENABLE_SCHEDULER=true` only on the public backend service, not admin |

---

## Performance Traps

Patterns that work in development but cause problems in production containers.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No multi-stage Dockerfile for Next.js | Image includes all `node_modules` (dev deps) — 1-2GB image | Use Next.js `standalone` output + multi-stage build | Every deploy (slow build, slow push) |
| `echo=True` in SQLAlchemy engine in production | All SQL queries logged to stdout, high log volume | Set `echo=False` in production via env var | From first request |
| No Next.js `output: 'standalone'` | Image includes full Next.js + all node_modules | Add `output: 'standalone'` to `next.config.ts` | Every deploy (300MB → 100MB savings) |
| Python `.venv` in Docker context | `.venv/` copied into image (hundreds of MB of redundant packages) | Exclude `.venv/` in `.dockerignore`, install deps fresh via `pip install -r requirements.txt` | Build time (slow builds, bloated images) |
| Uvicorn with single worker | Handles only 1 concurrent request | Use `--workers 2` or `--workers 4` for production (adjust to available CPU) | >5 concurrent users |

---

## Security Mistakes

Docker and Dokploy-specific security issues.

| Mistake | Risk | Prevention |
|---------|------|------------|
| `.env` file not in `.dockerignore` | API keys, JWT secret baked into image layers | Add `.env*` to `.dockerignore` in every service directory |
| `ARG SECRET_KEY` in Dockerfile | Secret persists in `docker history` output | Pass secrets at runtime only via compose `environment:` or Dokploy env vars |
| Running container as root | Container escape → root on host | Add `USER appuser` in Dockerfile, create non-root user |
| `SPECTRA_MODE=dev` in production | Admin API exposed publicly | Always use `public` or `admin` mode in production |
| Using `latest` tag for images | Undetermined image version, unpredictable deploys | Tag images with git SHA or semantic version |
| Exposing PostgreSQL port publicly | Database accessible from internet | PostgreSQL should only be reachable by the backend service, not bound to `0.0.0.0` |
| CORS_ORIGINS=* in production | Any website can make authenticated requests to the API | Set explicit origins (e.g., `["https://app.spectra.io"]`) in the public backend |

---

## "Looks Done But Isn't" Checklist

Things that appear to work but are missing critical pieces.

- [ ] **Volume mount:** File uploads survive a container restart — verify by uploading a file, running `docker-compose down && docker-compose up`, then confirming the file is still accessible
- [ ] **NEXT_PUBLIC_ vars:** API calls work in the Docker container — verify by building the image WITHOUT any `.env` file and running `docker run spectra-frontend` then checking the browser network tab
- [ ] **Migrations run:** Alembic tables exist after first deploy — run `docker exec backend alembic current` and confirm the revision matches the latest migration
- [ ] **SPECTRA_MODE correct:** Run `docker logs backend-public | grep "Starting Spectra"` and confirm `PUBLIC` mode; same for admin service confirming `ADMIN` mode
- [ ] **Secrets not in layers:** Run `docker history --no-trunc spectra-backend:latest | grep -i key` and confirm no API keys appear
- [ ] **Backend URL in frontend:** Open the public frontend in a browser pointed at the Docker deployment and verify the network tab shows requests going to the correct backend URL (not `localhost:8000`)
- [ ] **DB ready before backend:** Force-stop and restart the postgres container; confirm the backend waits and reconnects rather than exiting
- [ ] **No hardcoded localhost:** Run `grep -r "localhost:8000" frontend/src admin-frontend/src` and confirm no hardcoded localhost references remain after the `next.config.ts` update

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| NEXT_PUBLIC_ baked as `undefined` | LOW | Rebuild image with correct `ARG BACKEND_URL=...` passed to `docker build`, redeploy |
| File uploads lost after redeploy | HIGH | Files cannot be recovered from container filesystem. Instruct users to re-upload. Add volume mount immediately before next deploy to prevent recurrence. |
| Migration race condition failure | LOW | Re-trigger deploy in Dokploy. Add entrypoint wait script before next deploy. Check `docker logs backend` to confirm "PostgreSQL ready" before startup. |
| Secrets in image layers | HIGH | Immediately rotate all exposed keys (E2B, Anthropic, Tavily, OpenRouter, JWT secret). Rebuild image without secrets in layers. Push new image and delete old image from registry. |
| Wrong SPECTRA_MODE | LOW | Update environment variable in Dokploy, redeploy. No data loss, just service downtime during redeploy. |
| Monorepo context issues | LOW | Fix `context:` path in `docker-compose.yml` or Dokploy settings. Rebuild. |
| JWT secret changes on restart | MEDIUM | Set `SECRET_KEY` as persistent env var in Dokploy. Redeploy. All current sessions invalidated (users must re-login). |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| NEXT_PUBLIC_ baked as `undefined` | Phase 1: Dockerfiles | Build `frontend` image without env file; confirm API calls work in container |
| File uploads lost on restart | Phase 1: Dockerfiles | Upload file, run `docker-compose down && up`, confirm file accessible |
| Migration race condition | Phase 1: Dockerfiles | Force postgres delay; confirm backend waits with `pg_isready` loop |
| Secrets in image layers | Phase 1: Dockerfiles | `docker history spectra-backend:latest` shows no key values |
| Wrong SPECTRA_MODE | Phase 2: Dokploy Services | Smoke test: public frontend cannot access `/api/admin/*`; admin frontend can |
| Monorepo build context | Phase 1: Dockerfiles | Local `docker build` with explicit context path succeeds; check image size |
| JWT secret per restart | Phase 2: Dokploy Services | Redeploy backend; existing browser session still works (no re-login required) |

---

## Sources

### Next.js NEXT_PUBLIC_ Build-Time Behavior
- [Next.js Official Docs: Environment Variables](https://nextjs.org/docs/pages/guides/environment-variables) — "After being built, your app will no longer respond to changes to these environment variables"
- [Runtime environment variables in Next.js — build reusable Docker images](https://nemanjamitic.com/blog/2025-12-13-nextjs-runtime-environment-variables/) — December 2025
- [docker image with NEXT_PUBLIC_ env variables · vercel/next.js Discussion #17641](https://github.com/vercel/next.js/discussions/17641) — Official repo discussion, ongoing
- [Solving Next.js Env Var Puzzles in Docker Containers](https://junkangworld.com/blog/solving-nextjs-env-var-puzzles-in-docker-containers)
- [Better support for runtime environment variables · vercel/next.js Discussion #44628](https://github.com/vercel/next.js/discussions/44628)

### Docker Secrets and Layer Security
- [SecretsUsedInArgOrEnv — Docker Official Docs](https://docs.docker.com/reference/build-checks/secrets-used-in-arg-or-env/)
- [Don't leak your Docker image's build secrets — Python Speed](https://pythonspeed.com/articles/docker-build-secrets/)
- [Dockerfile Secrets: Why Layers Keep Your Data Forever — Xygeni](https://xygeni.io/blog/dockerfile-secrets-why-layers-keep-your-sensitive-data-forever/)
- [Docker Build Args: Hidden Vector for Leaks in Images — Xygeni](https://xygeni.io/blog/docker-build-args-the-hidden-vector-for-secret-leaks-in-images/)
- [Over 10 Thousand Docker Hub Images Leak Credentials and API Keys](https://jeffbruchado.com.br/en/blog/docker-hub-credentials-leak-10-thousand-images-security)

### Alembic Migration + Docker Startup Timing
- [Solving the FastAPI, Alembic, Docker Problem — HackerNoon](https://hackernoon.com/solving-the-fastapi-alembic-docker-problem)
- [Setup FastAPI Project with Async SQLAlchemy 2, Alembic, PostgreSQL and Docker](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/)
- [A Scalable Approach to FastAPI Projects with PostgreSQL, Alembic, Pytest, and Docker Using uv](https://blog.devops.dev/a-scalable-approach-to-fastapi-projects-with-postgresql-alembic-pytest-and-docker-using-uv-78ebf6f7fb9a)

### Docker Volume Persistence
- [Docker Volumes and Data Persistence](https://www.owais.io/blog/2025-09-12_docker-volumes-data-persistence-part1/)
- [FastAPI in Containers - Docker — FastAPI Official Docs](https://fastapi.tiangolo.com/deployment/docker/)
- [Mounting volumes docker-compose fastApi — Docker Community Forums](https://forums.docker.com/t/mounting-volumes-docker-compose-fastapi/123637)

### Docker Monorepo Build Context
- [Build context — Docker Official Docs](https://docs.docker.com/build/concepts/context/)
- [Solving Cross-Container Communication Issues Between Next.js and FastAPI in a Docker Environment](https://medium.com/@szz185/solving-cross-container-communication-issues-between-next-js-and-fastapi-in-a-docker-environment-7b218a270236)
- [Next.js outputFileTracingRoot for monorepo setups](https://nextjs.org/docs/pages/api-reference/config/next-config-js/output)

### Dokploy-Specific
- [Dokploy Build Type Documentation](https://docs.dokploy.com/docs/core/applications/build-type)
- [Dokploy Environment Variables Documentation](https://docs.dokploy.com/docs/core/variables)
- [Deploying Next.js Projects with Dokploy](https://medium.com/@weijunext/deploying-next-js-projects-with-dokploy-a0ecc386da3c)
- [Next.js Dokploy VPS Deploy Failed? 5 Proven Fixes for 2025](https://junkangworld.com/blog/nextjs-dokploy-vps-deploy-failed-5-proven-fixes-for-2025)
- [Warn users about needing dokploy-network for domain configuration · Discussion #1067](https://github.com/Dokploy/dokploy/discussions/1067)

---

*Pitfalls research for: Spectra Docker + Dokploy Deployment (v0.6 milestone)*
*Researched: 2026-02-18*
*Confidence: HIGH (based on official Next.js documentation, Docker official documentation, verified GitHub issues, and Dokploy documentation)*
