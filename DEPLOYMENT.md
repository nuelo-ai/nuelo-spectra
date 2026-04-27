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
| `APP_VERSION` | *(use latest version from [GitHub releases](https://github.com/nuelo-ai/nuelo-spectra/releases))* |
| `ANTHROPIC_API_KEY` | `sk-ant-...` *(required — default LLM provider)* |
| `OPENAI_API_KEY` | *(optional — required if using OpenAI models)* |
| `GOOGLE_API_KEY` | *(optional — required if using Gemini models)* |
| `OLLAMA_BASE_URL` | *(optional, default: `http://localhost:11434`)* |
| `OPENROUTER_API_KEY` | *(optional — required if using OpenRouter models)* |
| `E2B_API_KEY` | *(required — code execution sandbox for chat and Pulse)* |
| `TAVILY_API_KEY` | *(required — web search integration)* |
| `SEARCH_DEPTH` | `basic` *(optional, default: `basic` — or `advanced`)* |
| `STRIPE_SECRET_KEY` | `sk_live_...` or `sk_test_...` *(required for billing)* |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` *(required for Stripe webhook signature verification)* |
| `SMTP_HOST` | *(recommended — leave empty for console email logging)* |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | *(required if SMTP_HOST is set)* |
| `SMTP_PASS` | *(required if SMTP_HOST is set)* |
| `SMTP_FROM_EMAIL` | *(optional, default: `noreply@spectra.app`)* |
| `SMTP_FROM_NAME` | *(optional, default: `Spectra`)* |
| `PULSE_ORPHAN_TIMEOUT_MINUTES` | *(optional, default: `10` — refund credits for stuck Pulse runs)* |
| `MAX_FILE_SIZE_MB` | *(optional, default: `50` — max upload size in MB)* |
| `UVICORN_WORKERS` | *(optional, default: `1` — number of uvicorn worker processes)* |
| `ENABLE_SCHEDULER` | `true` |
| `ADMIN_EMAIL` | *(required — backend refuses to start without this)* |
| `ADMIN_PASSWORD` | *(required — backend refuses to start without this)* |
| `ADMIN_FIRST_NAME` | *(optional, default: `Admin`)* |
| `ADMIN_LAST_NAME` | *(optional, default: `User`)* |

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
| `APP_VERSION` | *(use latest version from [GitHub releases](https://github.com/nuelo-ai/nuelo-spectra/releases))* |
| `ANTHROPIC_API_KEY` | *Same as public backend* |
| `OPENAI_API_KEY` | *Same as public backend (if set)* |
| `GOOGLE_API_KEY` | *Same as public backend (if set)* |
| `OPENROUTER_API_KEY` | *Same as public backend (if set)* |
| `E2B_API_KEY` | *Same as public backend* |
| `TAVILY_API_KEY` | *Same as public backend* |
| `STRIPE_SECRET_KEY` | *Same as public backend* |
| `STRIPE_WEBHOOK_SECRET` | *(not needed — webhooks only hit public backend)* |
| `SMTP_HOST` | *Same as public backend (if set)* |
| `SMTP_PORT` | *Same as public backend* |
| `SMTP_USER` | *Same as public backend (if set)* |
| `SMTP_PASS` | *Same as public backend (if set)* |
| `ENABLE_SCHEDULER` | `false` |
| `ADMIN_EMAIL` | *Same as public backend* |
| `ADMIN_PASSWORD` | *Same as public backend* |

**Critical notes:**
- `SECRET_KEY` must match the public backend (they share the same database)
- `ENABLE_SCHEDULER=false` — only one service should run the credit reset scheduler
- `CORS_ORIGINS` and `ADMIN_CORS_ORIGIN` must use the Tailscale IP
- `STRIPE_SECRET_KEY` is needed for admin billing operations (force-set tier, refunds)

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
| `SPECTRA_MODE` | `api` | API-only mode — no frontend, auth, or admin routes |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Same as other backends |
| `SECRET_KEY` | *(same as other backends)* | Shared JWT signing key |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | |
| `APP_VERSION` | *(use latest version from [GitHub releases](https://github.com/nuelo-ai/nuelo-spectra/releases))* | Returned in `/health` and `/api/v1/health` responses |
| `ANTHROPIC_API_KEY` | *(your key)* | Required for analysis queries |
| `E2B_API_KEY` | *(your key)* | Required for code execution sandbox |
| `TAVILY_API_KEY` | *(your key)* | Required for web search in queries |
| `SEARCH_DEPTH` | `basic` | `basic` or `advanced` |
| `OPENAI_API_KEY` | *(optional)* | If using OpenAI models |
| `GOOGLE_API_KEY` | *(optional)* | If using Gemini models |
| `OPENROUTER_API_KEY` | *(optional)* | If using OpenRouter models |
| `MCP_API_BASE_URL` | `http://<api-swarm-service-name>:8000` | Internal loopback URL for MCP tools to call the REST API. Set to the service's own Swarm DNS name. |
| `ENABLE_SCHEDULER` | `false` | API service does not run scheduled tasks |

**CORS note:** `SPECTRA_MODE=api` uses open CORS (`Access-Control-Allow-Origin: *`) with no credentials. No `CORS_ORIGINS` variable is needed — it is not read in this mode.

### Step 9c -- Domain Configuration

In Dokploy Application -> Domains:
| Field | Value |
|-------|-------|
| Host | `api.yourdomain.com` |
| Container Port | `8000` |
| HTTPS | Enabled |
| Certificate | `letsencrypt` |

This domain serves both the REST API (`https://api.yourdomain.com/api/v1/*`) and the MCP server (`https://api.yourdomain.com/mcp/`). No separate domain is needed for MCP.

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

### Billing (Stripe)
- [ ] Plan Selection page loads with live pricing from backend
- [ ] Stripe Checkout redirects correctly (use Stripe test card `4242 4242 4242 4242`)
- [ ] Webhook endpoint reachable: `curl -s https://app.yourdomain.com/api/webhooks/stripe` → 400 (no payload, but not 404)
- [ ] Credit balance updates after subscription activation
- [ ] Credit top-up purchase completes and credits appear

### Pulse (Anomaly Detection)
- [ ] Create a collection and upload a CSV file
- [ ] Run Pulse analysis — signals appear with Plotly charts
- [ ] Credits deducted after Pulse run (5 credits per run)

### Isolation Verification (from non-Tailscale network)
- [ ] `curl --max-time 5 http://<SERVER_PUBLIC_IP>:8001/health` → timeout
- [ ] `curl --max-time 5 http://<SERVER_PUBLIC_IP>:3001` → timeout

## Redeployment

### Auto-Deploy via GitHub Webhooks (Recommended)

Each Dokploy application has a unique webhook URL. When configured, pushing to `master` triggers automatic redeployment.

**Setup (per service):**

1. In Dokploy: Application → General tab → toggle **Auto Deploy** ON
2. In Dokploy: Application → Deployments tab → copy the **Webhook URL**
3. In GitHub: Repository → Settings → Webhooks → Add webhook:
   - Payload URL: paste the Dokploy webhook URL
   - Content type: `application/json`
   - Trigger: **Just the push event**

You need **4-5 separate webhooks** in GitHub — one for each Dokploy application service.

**Verify:** After pushing to `master`, check GitHub → Settings → Webhooks → Recent Deliveries for 200 responses, and Dokploy → Deployments tab for build activity.

### Manual Redeployment

To redeploy any service manually:
1. Push changes to the `master` branch
2. In Dokploy UI → click the service → click Deploy

### Notes

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
