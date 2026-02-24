# Spectra Production Deployment Guide

Spectra deploys as five Dokploy Application services with a split-horizon architecture:
- **Public services** (API + frontend): frontend accessible via HTTPS, backend internal only
- **API service** (standalone REST API): accessible via HTTPS at `api.yourdomain.com`
- **Admin services** (admin API + admin frontend): accessible only via Tailscale VPN

## Architecture Overview

```
Internet → Traefik (Dokploy) → spectra-public-frontend (port 3000)
                                    ↓ route handler proxy (Swarm DNS)
                                spectra-public-backend (port 8000, no public domain)

                              → spectra-api (port 8000, api.yourdomain.com)
                                    ↓ API-only: /api/v1/* routes

Tailscale VPN → host:8001 → spectra-admin-backend
             → host:3001 → spectra-admin-frontend
                                ↓ route handler proxy (Swarm DNS)
                            spectra-admin-backend (port 8000)

All backends   → Dokploy-managed PostgreSQL (shared DB, same SECRET_KEY)
Public backend → spectra-uploads named volume at /app/uploads
API service    → spectra-uploads named volume at /app/uploads (shared)
```

**Key design:** The public backend has no public domain. All API calls go through the public frontend's Next.js route handler proxy, which routes to the backend via Docker Swarm service DNS over the internal overlay network. This reduces the attack surface — only the frontend is publicly exposed.

## Prerequisites

- Dokploy installed on a VPS (see https://dokploy.com)
- Git repository connected to Dokploy
- A domain with DNS management access (one A record needed)
- Tailscale account (free tier is sufficient — https://login.tailscale.com)

## Step 1: Create PostgreSQL Database

In Dokploy UI → Databases → New → PostgreSQL:
- Name: `spectra-db`
- Set a strong password

After creation, copy the **Internal Connection URL** from the Connection tab:
```
postgresql://spectra:PASSWORD@spectra-db-HASH:5432/spectra
```

**Important:** Change `postgresql://` to `postgresql+asyncpg://` when setting DATABASE_URL in service environment variables. FastAPI's async SQLAlchemy requires the asyncpg driver prefix.

## Step 2: Generate SECRET_KEY

Run once. Use the **same value** for both backend services:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Save this value. It must be identical in both spectra-public-backend and spectra-admin-backend.

## Step 3: Install Tailscale on Dokploy Host

SSH into the Dokploy host server:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Get an auth key from: https://login.tailscale.com/admin/settings/keys
sudo tailscale up \
  --ssh \
  --auth-key=<TAILSCALE_AUTH_KEY> \
  --hostname=spectra-prod

# Get and save the server's Tailscale IP (used in admin service env vars)
tailscale ip -4
# Example output: 100.64.0.5
```

On each admin client device:
```bash
tailscale up --accept-routes
```

## Step 4: Configure VPS Firewall

**Critical:** Docker writes iptables rules directly and bypasses UFW entirely. Use iptables DOCKER-USER chain rules or your VPS provider's cloud firewall.

Block admin ports from the public internet:
```bash
# Option A: iptables (works on any VPS)
sudo iptables -I DOCKER-USER -p tcp --dport 8001 -j DROP
sudo iptables -I DOCKER-USER -p tcp --dport 3001 -j DROP

# Option B: VPS provider cloud firewall
# Add DENY inbound TCP rules for ports 8001 and 3001 from 0.0.0.0/0
```

Verify (from a non-Tailscale network):
```bash
curl --max-time 5 http://<SERVER_PUBLIC_IP>:8001/health
# Expected: timeout
curl --max-time 5 http://<SERVER_PUBLIC_IP>:3001
# Expected: timeout
```

## Step 5: Deploy Public Backend

⚠️ **Configure the volume mount (Step 5c) BEFORE clicking Deploy for the first time.**
If you deploy first and add the volume later, existing uploads will not be migrated.

### Step 5a — Create Application in Dokploy

General tab:
| Field | Value |
|-------|-------|
| Name | `spectra-public-backend` |
| Source | Git |
| Branch | `master` |
| Build Type | Dockerfile |
| Dockerfile Path | `Dockerfile.backend` |
| Docker Context Path | `.` |

### Step 5b — Environment Variables

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://spectra:PASSWORD@spectra-db-HASH:5432/spectra` |
| `SPECTRA_MODE` | `public` |
| `SECRET_KEY` | `<generated-hex-value>` |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` |
| `FRONTEND_URL` | `https://app.yourdomain.com` |
| `CORS_ORIGINS` | `["https://app.yourdomain.com"]` |
| `ADMIN_CORS_ORIGIN` | *(leave empty)* |
| `APP_VERSION` | `v0.6.0` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `OPENAI_API_KEY` | *(optional)* |
| `GOOGLE_API_KEY` | *(optional)* |
| `OLLAMA_BASE_URL` | *(optional)* |
| `OPENROUTER_API_KEY` | *(optional)* |
| `E2B_API_KEY` | *(required for code execution sandbox)* |
| `TAVILY_API_KEY` | *(required for web search)* |
| `SEARCH_DEPTH` | `basic` |
| `SMTP_HOST` | *(optional — leave empty for console email logging)* |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | *(optional)* |
| `SMTP_PASS` | *(optional)* |
| `SMTP_FROM_EMAIL` | *(optional)* |
| `SMTP_FROM_NAME` | *(optional)* |
| `ENABLE_SCHEDULER` | `true` |
| `ADMIN_EMAIL` | *(for seed-admin CLI)* |
| `ADMIN_PASSWORD` | *(for seed-admin CLI)* |
| `ADMIN_FIRST_NAME` | *(optional, default: "Admin")* |
| `ADMIN_LAST_NAME` | *(optional, default: "User")* |

### Step 5c — Volume Mount (configure BEFORE deploying)

Advanced tab → Mounts → Add Mount:
| Field | Value |
|-------|-------|
| Type | Volume |
| Volume Name | `spectra-uploads` |
| Mount Path | `/app/uploads` |

### Step 5d — Domains Tab

⚠️ **Leave the Domains tab empty.** The public backend has no public domain — all API traffic goes through the frontend proxy.

### Step 5e — Deploy

Click Deploy. The container runs `alembic upgrade head` on startup, creating all database tables.

Verify:
```bash
CONTAINER=$(docker ps --filter "name=public-backend" --format "{{.ID}}" | head -1)
docker logs $CONTAINER 2>&1 | grep -i alembic
docker exec $CONTAINER curl -s http://localhost:8000/health
# Expected: {"status":"ok"}
```

**Note the Swarm service name** — run `docker service ls | grep publicbackend` and save the name (e.g., `nuelo-spectra-publicbackend-abc123`). The public frontend needs this for `BACKEND_URL`.

## Step 6: Deploy Admin Backend (Tailscale-Only)

### Step 6a — Create Application in Dokploy

General tab:
| Field | Value |
|-------|-------|
| Name | `spectra-admin-backend` |
| Source | Git (same repo) |
| Branch | `master` |
| Build Type | Dockerfile |
| Dockerfile Path | `Dockerfile.backend` |
| Docker Context Path | `.` |

### Step 6b — Environment Variables

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | *Same value as public backend* |
| `SPECTRA_MODE` | `admin` |
| `SECRET_KEY` | *Same value as public backend* |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` |
| `FRONTEND_URL` | *(leave empty)* |
| `CORS_ORIGINS` | `["http://<TAILSCALE_IP>:3001"]` |
| `ADMIN_CORS_ORIGIN` | `http://<TAILSCALE_IP>:3001` |
| `APP_VERSION` | `v0.6.0` |
| `ANTHROPIC_API_KEY` | *Same as public backend* |
| *(other API keys)* | *Same as public backend* |
| `ENABLE_SCHEDULER` | `false` |
| `ADMIN_EMAIL` | *Same as public backend* |
| `ADMIN_PASSWORD` | *Same as public backend* |

**Critical notes:**
- `SECRET_KEY` must match the public backend (they share the same database)
- `ENABLE_SCHEDULER=false` — only one service should run the credit reset scheduler
- `CORS_ORIGINS` and `ADMIN_CORS_ORIGIN` must use the Tailscale IP

### Step 6c — Published Port (Advanced tab)

Advanced → Ports → Add Port:
| Published Port | Target Port | Protocol |
|----------------|-------------|----------|
| `8001` | `8000` | TCP |

### Step 6d — Domains Tab

⚠️ **Leave the Domains tab empty.** Do not add any domain to admin services.

Click Deploy. Alembic will run but apply no new migrations (already applied by public backend).

**Note the Swarm service name** — run `docker service ls | grep adminbackend`. The admin frontend needs this for `BACKEND_URL`.

Verify from Tailscale client:
```bash
curl http://<TAILSCALE_IP>:8001/health
# Expected: {"status":"ok"}
```

## Step 7: Deploy Public Frontend

General tab:
| Field | Value |
|-------|-------|
| Name | `spectra-public-frontend` |
| Source | Git (same repo) |
| Branch | `master` |
| Build Type | Dockerfile |
| Dockerfile Path | `Dockerfile.frontend` |
| Docker Context Path | `.` |

Environment tab:
| Variable | Value |
|----------|-------|
| `BACKEND_URL` | `http://<public-backend-swarm-service-name>:8000` |

Use the Swarm service name from Step 5e (e.g., `http://nuelo-spectra-publicbackend-abc123:8000`). This routes through Docker's internal overlay network — stable across redeployments.

Domains tab: Leave empty until Step 9.

Click Deploy.

## Step 8: Deploy Admin Frontend

General tab:
| Field | Value |
|-------|-------|
| Name | `spectra-admin-frontend` |
| Source | Git (same repo) |
| Branch | `master` |
| Build Type | Dockerfile |
| Dockerfile Path | `Dockerfile.admin` |
| Docker Context Path | `.` |

Environment tab:
| Variable | Value |
|----------|-------|
| `BACKEND_URL` | `http://<admin-backend-swarm-service-name>:8000` |

Use the Swarm service name from Step 6d (e.g., `http://nuelo-spectra-adminbackend-xyz789:8000`). Port `8000` is the container port (not the published host port `8001`).

Advanced → Ports:
| Published Port | Target Port | Protocol |
|----------------|-------------|----------|
| `3001` | `3000` | TCP |

⚠️ **Leave the Domains tab empty.** Admin frontend is Tailscale-only.

Click Deploy.

## Step 9: Deploy API Service (spectra-api)

The API service serves the public REST API at `api.yourdomain.com`. It uses the same Docker image as the backends but runs in API mode — only `/api/v1/*` routes and health checks are mounted, with no auth, files, chat, admin, or frontend routes.

### Step 9a -- Create Application in Dokploy

General tab:
| Field | Value |
|-------|-------|
| Name | `spectra-api` |
| Source | Git (same repository) |
| Branch | `master` |
| Build Type | Dockerfile |
| Dockerfile Path | `Dockerfile.backend` |
| Docker Context Path | `.` |

### Step 9b -- Environment Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `SPECTRA_MODE` | `api` | API-only mode -- no frontend routes, no admin routes |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Same as other backends |
| `SECRET_KEY` | *(same as other backends)* | Shared JWT signing key |
| `ANTHROPIC_API_KEY` | *(your key)* | Required for analysis queries |
| `E2B_API_KEY` | *(your key)* | Required for code execution |
| `GOOGLE_API_KEY` | *(your key)* | If using Google LLM provider |
| `ENABLE_SCHEDULER` | `false` | API service does not run scheduled tasks |
| `TAVILY_API_KEY` | *(your key)* | If web search is configured |

### Step 9c -- Domain Configuration

In Dokploy Application -> Domains:
| Field | Value |
|-------|-------|
| Host | `api.yourdomain.com` |
| Container Port | `8000` |
| HTTPS | Enabled |
| Certificate | `letsencrypt` |

### Step 9d -- Volume Mount (configure BEFORE deploying)

Advanced tab -> Mounts -> Add Mount:
| Field | Value |
|-------|-------|
| Type | Volume |
| Volume Name | `spectra-uploads` |
| Mount Path | `/app/uploads` |

**Important:** The API service needs access to the same uploads volume as the public backend so it can serve file-related API endpoints.

### Step 9e -- Deploy and Verify

Click Deploy. After deployment:
```bash
# Basic health
curl https://api.yourdomain.com/health

# API health with DB check
curl https://api.yourdomain.com/api/v1/health

# API key authentication (requires a valid key)
curl -H "Authorization: Bearer spe_YOUR_KEY" https://api.yourdomain.com/api/v1/keys
```

The standard `/health` endpoint is fast (no DB query) — use it for Dokploy HEALTHCHECK. Use `/api/v1/health` for external monitoring with DB connectivity checks.

## Step 10: Configure Public HTTPS Domain

**DNS must propagate before adding the domain in Dokploy.** Adding the domain before DNS resolves causes Let's Encrypt to fail silently.

### Step 10a — Add DNS A record

In your DNS provider, add:
- `app.yourdomain.com` → `<SERVER_PUBLIC_IP>`
- `api.yourdomain.com` → `<SERVER_PUBLIC_IP>`

If using Cloudflare: set to "DNS only" (grey cloud icon), not Proxied. Traefik's Let's Encrypt HTTP challenge requires direct access to the server.

Verify propagation:
```bash
dig +short app.yourdomain.com   # Must return SERVER_PUBLIC_IP
```

### Step 10b — Add domain to public frontend

Dokploy → spectra-public-frontend → Domains tab → Add Domain:
| Field | Value |
|-------|-------|
| Host | `app.yourdomain.com` |
| Container Port | `3000` |
| HTTPS | Enabled |
| Certificate | `letsencrypt` |

Wait 30-60 seconds, then verify:
```bash
curl -s https://app.yourdomain.com/api/health
# Expected: {"status":"ok"}
```

### Step 10c — Update public backend CORS

In spectra-public-backend → Environment tab, update:
```
FRONTEND_URL=https://app.yourdomain.com
CORS_ORIGINS=["https://app.yourdomain.com"]
```

Redeploy public backend after updating.

## Step 11: Seed Admin User (First Time Only)

```bash
docker exec $(docker ps --filter "name=admin-backend" --format "{{.ID}}" | head -1) \
  /app/.venv/bin/python -m app.cli seed-admin
```

Uses `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `ADMIN_FIRST_NAME`, and `ADMIN_LAST_NAME` from the admin backend environment variables.

## Post-Deploy Smoke Test Checklist

### Public Services
- [ ] `curl -s https://app.yourdomain.com/api/health` → `{"status":"ok"}`
- [ ] `curl -s https://app.yourdomain.com/api/version` → `{"version":"...","environment":"public"}`
- [ ] Open https://app.yourdomain.com — login page renders with no SSL warning (padlock shows)
- [ ] Login with user credentials → chat interface loads
- [ ] Send a chat message — SSE streaming works (response appears token-by-token)
- [ ] Upload a file — appears in file list
- [ ] Redeploy spectra-public-backend → uploaded file still accessible (volume persistence)
- [ ] Version displayed on Settings page

### API Service
- [ ] `curl -s https://api.yourdomain.com/health` → `{"status":"ok"}`
- [ ] `curl -s https://api.yourdomain.com/api/v1/health` → `{"status":"healthy",...}`
- [ ] `curl -H "Authorization: Bearer spe_VALID_KEY" https://api.yourdomain.com/api/v1/keys` → key list JSON
- [ ] `curl -s https://api.yourdomain.com/api/admin/users` → 404 (admin routes not mounted)

### Admin Services (from Tailscale client)
- [ ] `curl -s http://<TAILSCALE_IP>:8001/health` → `{"status":"ok"}`
- [ ] `curl -s http://<TAILSCALE_IP>:8001/version` → `{"version":"...","environment":"admin"}`
- [ ] Open http://<TAILSCALE_IP>:3001 — admin login page renders
- [ ] Login with admin credentials → admin dashboard loads
- [ ] User management page shows user list
- [ ] Platform settings page loads and saves

### Isolation Verification (from non-Tailscale network)
- [ ] `curl --max-time 5 http://<SERVER_PUBLIC_IP>:8001/health` → timeout
- [ ] `curl --max-time 5 http://<SERVER_PUBLIC_IP>:3001` → timeout

## Redeployment

To redeploy any service with updated code:
1. Push changes to the `master` branch
2. In Dokploy UI → click the service → click Deploy

The backend runs `alembic upgrade head` on every startup. New migrations are applied; already-applied migrations are skipped automatically.

**BACKEND_URL stability:** Frontend services use Docker Swarm service DNS names for `BACKEND_URL`, not container IPs. Service names are stable across redeployments — no need to update `BACKEND_URL` when backends are redeployed.

## Troubleshooting

**Let's Encrypt certificate fails:**
DNS not yet propagated. Delete the domain entry in Dokploy and re-add after `dig` confirms propagation.

**Backend crashes at startup with SQLAlchemy driver error:**
`DATABASE_URL` uses `postgresql://` prefix. Change to `postgresql+asyncpg://`.

**Admin frontend CORS errors in browser:**
`CORS_ORIGINS` and `ADMIN_CORS_ORIGIN` in the admin backend must include the Tailscale IP and port 3001. Update both env vars and redeploy the admin backend.

**Frontend healthcheck fails (containers cycling):**
Healthchecks use `wget http://127.0.0.1:3000/api/health`. If you see containers stuck at "health: starting", check that the `/api/health` route handler exists and returns 200. Alpine's wget resolves `localhost` to IPv6 — always use `127.0.0.1`.

**Uploads permission denied:**
The container runs as non-root (`appuser`, uid 1001). If the volume was created before the ownership fix, run:
```bash
docker exec -u root $(docker ps --filter "name=publicbackend" --format "{{.ID}}" | head -1) \
  chown -R appuser:appuser /app/uploads
```

**Uploads disappear after redeploy:**
The volume mount was not configured before the first deploy. Configure the volume in Advanced → Mounts and redeploy.

**Admin ports reachable from public internet:**
UFW is not sufficient — Docker bypasses it. Use iptables DOCKER-USER chain rules or your VPS provider's cloud firewall to block ports 8001 and 3001.

**Swarm service name not found:**
Run `docker service ls` to see all service names. Use the full name (e.g., `nuelo-spectra-publicbackend-ltiq2m`) as the hostname in `BACKEND_URL`.
