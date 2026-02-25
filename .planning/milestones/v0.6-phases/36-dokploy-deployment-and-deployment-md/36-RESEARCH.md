# Phase 36: Dokploy Deployment and DEPLOYMENT.md - Research

**Researched:** 2026-02-19
**Domain:** Dokploy PaaS deployment, Tailscale VPN, split-horizon service topology
**Confidence:** MEDIUM (Dokploy docs verified; Tailscale-only binding approach requires VPS firewall as workaround due to unresolved Dokploy limitation)

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DPLY-01 | Public backend deployed as Dokploy Application service with Dockerfile.backend, SPECTRA_MODE=public, all required env vars, volume mount at /app/uploads, Alembic migration runs against Dokploy-managed PostgreSQL on first deploy | Dockerfile.backend entrypoint already runs `alembic upgrade head` before uvicorn; Dokploy Advanced → Mounts supports named volume; internal DB URL format documented |
| DPLY-02 | Admin backend deployed as second Dokploy Application service from same Dockerfile.backend with SPECTRA_MODE=admin — binds to Tailscale network interface only, NOT exposed through Dokploy's public Traefik router | Dokploy cannot natively bind to a specific interface; isolation achieved by: (a) no domain assigned in Dokploy, (b) no published ports in Advanced, (c) VPS cloud firewall blocks admin service port from public internet; service reachable via Tailscale subnet routing |
| DPLY-03 | Public frontend deployed as Dokploy Application service with Dockerfile.frontend, BACKEND_URL pointing to public backend — accessible via public HTTPS domain with Traefik SSL | Dokploy Domains tab → Add Domain, enable HTTPS, select letsencrypt cert resolver; BACKEND_URL is runtime env var (not baked at build); set in Environment tab |
| DPLY-04 | Admin frontend deployed as Dokploy Application service with Dockerfile.admin, BACKEND_URL pointing to admin backend Tailscale hostname — Tailscale-only, NOT exposed through public Traefik router | Same isolation approach as DPLY-02: no domain, no published ports; BACKEND_URL points to admin-api Tailscale hostname and port |
| DPLY-05 | Tailscale installed on Dokploy host — admin backend and admin frontend reachable at admin-api.spectra.ts.net and admin.spectra.ts.net via Tailscale client only | Tailscale host install + advertise-routes for dokploy-network subnet; Tailscale MagicDNS provides .ts.net hostnames; client devices need --accept-routes; VPS cloud firewall enforces public internet blocking |
| DPLY-06 | User file uploads persist across Dokploy redeployments — Dokploy Advanced → Mounts configured with named volume at /app/uploads on public backend service before first production deploy | Dokploy Advanced → Mounts → Volume Mount; volume name + /app/uploads mount path; must be configured BEFORE first deploy |
| DPLY-07 | Public backend and public frontend accessible via custom public HTTPS domains with valid SSL (Traefik certificates managed by Dokploy) | Dokploy Domains tab → Add Domain → enable HTTPS → select letsencrypt; DNS A record must point to server IP BEFORE adding domain in Dokploy |
| DPLY-08 | DEPLOYMENT.md covers complete setup — all 4 service configurations with env var tables, Tailscale installation and Tailscale-only binding for admin services, volume mount steps, public domain/SSL assignment, SECRET_KEY generation, and a post-deploy smoke test checklist | Document must cover all 8 DPLY requirements in sequential step format |
</phase_requirements>

---

## Summary

This phase deploys four Spectra services to a Dokploy server: public backend, public frontend, admin backend, and admin frontend. The public services are fully exposed via Traefik with HTTPS; the admin services are "Tailscale-only" — reachable only by devices in the Tailscale VPN. All four are Dokploy Application services deploying from the same Git repository with different Dockerfiles and environment variables.

The critical technical challenge is admin service isolation. Dokploy does not natively support binding a published port to a specific network interface (this is an open feature request, GitHub issue #2915). The workaround is: configure admin services with NO domain in Dokploy (so Traefik never routes to them publicly) and NO published ports in Advanced (so no host-port binding exists). Services are still accessible on the Docker internal network; Tailscale subnet routing (advertising the `dokploy-network` subnet) makes them reachable from Tailscale clients. A VPS cloud firewall provides the enforcement layer that Docker's iptables manipulation cannot bypass — cloud firewalls operate at the infrastructure level, before packets reach the host.

The file uploads persistence requirement (DPLY-06) is straightforward: Dokploy Advanced → Mounts → Volume Mount must be configured before the first deploy so the named volume is created and attached on first container run. The Alembic migration requirement is already satisfied: `docker-entrypoint.sh` runs `alembic upgrade head` before starting uvicorn, and it reads `DATABASE_URL` from the environment.

**Primary recommendation:** Use the three-layer isolation strategy for admin services: (1) no Dokploy domain assigned, (2) no Advanced ports published, (3) VPS cloud firewall blocks admin service ports from the public internet. Tailscale subnet routing provides access.

---

## Standard Stack

### Core

| Component | Version/Notes | Purpose | Why Standard |
|-----------|--------------|---------|--------------|
| Dokploy | Self-hosted PaaS | Deploys all 4 Application services from Git | Chosen by user; manages Traefik, Docker, databases |
| Traefik | Managed by Dokploy | HTTP/HTTPS routing, Let's Encrypt SSL | Bundled with Dokploy; handles cert automation |
| Tailscale | Latest (install.sh) | VPN overlay for admin service isolation | Chosen by user; zero-config WireGuard mesh |
| Docker | Managed by Dokploy | Container runtime for all services | Required by Dokploy |
| PostgreSQL 16 | Dokploy-managed DB | Application database | Chosen by user in prior phases |

### Supporting

| Component | Version/Notes | Purpose | When to Use |
|-----------|--------------|---------|-------------|
| Let's Encrypt | Via Traefik/Dokploy | TLS certificates for public services | Auto-provisioned when domain added with HTTPS enabled |
| Tailscale MagicDNS | Built into Tailscale | `.ts.net` hostnames for Tailscale devices | Enabled automatically; gives `hostname.tailnet.ts.net` addresses |
| VPS Cloud Firewall | Provider-specific | Block admin service ports from public internet | Required because Docker bypasses UFW |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| VPS cloud firewall for admin isolation | UFW | UFW is bypassed by Docker iptables rules; cloud firewall is not |
| Named Docker volume for uploads | Bind mount | Bind mounts work but named volumes are required for Dokploy Volume Backup feature |
| Tailscale host install + subnet routing | Tailscale sidecar container | Host install is simpler for this use case; sidecar is better when individual containers need separate Tailscale identities |

---

## Architecture Patterns

### Recommended Service Layout

```
Dokploy Server (VPS)
├── Public Services (exposed via Traefik)
│   ├── spectra-public-backend    → api.yourdomain.com (port 8000 via Traefik)
│   └── spectra-public-frontend   → app.yourdomain.com (port 3000 via Traefik)
│
├── Admin Services (NO domain, NO published ports)
│   ├── spectra-admin-backend     → reachable at 100.x.x.x:8001 via Tailscale
│   └── spectra-admin-frontend    → reachable at 100.x.x.x:3001 via Tailscale
│
├── Databases
│   └── Dokploy-managed PostgreSQL → internal hostname: [service-name]
│
└── Tailscale (host daemon)
    ├── Advertises: dokploy-network subnet (e.g. 10.254.0.0/24)
    ├── MagicDNS: server.tailnet.ts.net → 100.x.x.x
    └── Admin clients connect with: --accept-routes
```

### Pattern 1: Dokploy Application Service — Public (with Traefik domain)

**What:** Deploy a service from Git using a specific Dockerfile, expose via Traefik HTTPS.

**Configuration in Dokploy UI:**
1. Create Application → General tab:
   - Source: Git (GitHub/GitLab/Generic)
   - Repository: spectra-dev repo
   - Branch: main (or production branch)
   - Build Type: Dockerfile
   - Dockerfile Path: `Dockerfile.backend`
   - Docker Context Path: `.` (root of repo)
2. Environment tab: paste all required env vars
3. Advanced → Mounts (public backend only): add Volume Mount
   - Volume Name: `spectra-uploads`
   - Mount Path: `/app/uploads`
4. Domains tab: Add Domain
   - Host: `api.yourdomain.com`
   - Container Port: `8000`
   - HTTPS: enabled
   - Certificate: `letsencrypt`
5. Deploy

**Critical:** DNS A record for `api.yourdomain.com` must point to server IP BEFORE clicking Deploy with HTTPS enabled. If domain is added before DNS propagates, Let's Encrypt certificate provisioning fails and must be recreated.

### Pattern 2: Dokploy Application Service — Admin (Tailscale-only, no domain)

**What:** Deploy admin services without assigning any domain. No Traefik routing is created. Service is only reachable internally.

**Configuration in Dokploy UI:**
1. Create Application → General tab:
   - Same Git source as public service
   - Build Type: Dockerfile
   - Dockerfile Path: `Dockerfile.backend` (or `Dockerfile.admin`)
   - Docker Context Path: `.`
2. Environment tab: paste env vars with `SPECTRA_MODE=admin` (or set `BACKEND_URL` for admin frontend)
3. Advanced → Ports: configure a published port mapping for Tailscale access
   - Published Port: `8001` (host port, different from public backend's port)
   - Target Port: `8000` (container port)
4. Domains tab: ADD NO DOMAIN
5. Deploy

**Note on port publishing for admin services:** A published port is needed for Tailscale clients to reach the service at `<tailscale-ip>:<port>`. However, this same port would be accessible from the public internet unless blocked by the VPS cloud firewall. VPS cloud firewall must block ports 8001 and 3001 from `0.0.0.0/0` while allowing the Tailscale CIDR (or all — since Tailscale auth handles identity).

### Pattern 3: Tailscale Host Installation with Subnet Routing

**What:** Install Tailscale on the Dokploy host server and advertise the Docker internal network subnet, making all Docker services reachable via Tailscale IP without individual containers needing Tailscale installed.

**Steps:**
```bash
# 1. Find Docker network subnet
docker network inspect dokploy-network | grep Subnet
# Example output: "Subnet": "10.254.0.0/24"

# 2. Install Tailscale with subnet route advertisement
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up \
  --ssh \
  --advertise-routes=10.254.0.0/24 \
  --auth-key=tskey-auth-XXXXXX \
  --hostname=spectra-prod

# 3. In Tailscale admin console: approve the advertised route

# 4. On each admin client device:
tailscale up --accept-routes
```

**MagicDNS hostnames:** After installation, the server is reachable at `spectra-prod.tailnet-name.ts.net` or short `spectra-prod`. The `.ts.net` suffix depends on your tailnet name.

**Accessing services:** Admin backend at `<tailscale-ip>:8001`, admin frontend at `<tailscale-ip>:3001`. Or if MagicDNS is enabled: `spectra-prod:8001`.

Note on custom hostname requirement (DPLY-05 wants `admin-api.spectra.ts.net`): The `.ts.net` hostname is automatically `<machine-name>.<tailnet-name>.ts.net`. To get `admin-api.spectra.ts.net`, the tailnet name must be `spectra` — this is set in the Tailscale admin console as a custom tailnet domain, or you use the default machine hostname to form the address. If the tailnet name is fixed by the account, the hostnames will differ from the DPLY-05 spec's example; adjust DEPLOYMENT.md accordingly. The requirement says "reachable at admin-api.spectra.ts.net" as an example — document the actual hostname format.

### Pattern 4: Dokploy-managed PostgreSQL — Internal Connection

**What:** Create a PostgreSQL database in Dokploy's Databases section. Use the internal connection URL to connect application services.

**Steps:**
1. In Dokploy: Databases → New → PostgreSQL → create with strong password
2. Copy the "Internal Connection URL" from the database's Connection section
3. The URL format is: `postgresql://user:password@<service-name>:5432/dbname`
   - The hostname is the Dokploy service name (e.g., `spectra-db-abc123`)
4. For the FastAPI backend (uses asyncpg), convert the URL prefix:
   - `postgresql://` → `postgresql+asyncpg://`
5. Set this as `DATABASE_URL` in the backend service's Environment tab

**Important:** Both public backend and admin backend connect to the SAME database instance. They share the same `DATABASE_URL`. This is by design (shared schema for split-horizon).

### Anti-Patterns to Avoid

- **Adding domain to admin services:** If you add a domain to Dokploy for an admin service, Traefik creates a routing rule for it. Even if you want a private domain, Traefik's ACME challenge is public. Do not add any domain to admin services.
- **Relying on UFW to block admin ports:** Docker directly manipulates iptables and can bypass UFW. Use the VPS cloud firewall (DigitalOcean, Hetzner, etc.) for port blocking.
- **Publishing admin ports without VPS firewall rules:** Published ports in Dokploy Advanced bind to the host public IP by default. Without VPS cloud firewall blocking those ports, they are accessible from the internet.
- **Setting volume mount after first deploy:** If you configure the volume mount in Dokploy Advanced after the first deployment, the uploads directory may already contain data in the container's writable layer that will not be migrated. Configure the volume BEFORE the first deploy.
- **Adding domain before DNS propagation:** Let's Encrypt certificate provisioning happens at domain-add time. If DNS hasn't propagated yet, the certificate request fails. Recreating the domain entry re-triggers provisioning.
- **Using DATABASE_URL with asyncpg prefix in psycopg connection pool:** `main.py` converts `postgresql+asyncpg://` to `postgresql://` for psycopg. Provide `DATABASE_URL=postgresql+asyncpg://...` in env vars; the code handles conversion.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TLS/SSL certificate management | Custom ACME client | Dokploy + Traefik Let's Encrypt | Automatic renewal, zero configuration |
| VPN for admin isolation | Custom VPN setup | Tailscale | Zero-config WireGuard, works through NAT, free for small teams |
| Service routing rules | Manual Traefik config files | Dokploy domain configuration | Dokploy writes /etc/dokploy/traefik/dynamic/ files automatically |
| Database backups | Custom pg_dump scripts | Dokploy Volume Backups + S3 | Dokploy has built-in scheduled backup to S3-compatible storage |

---

## Common Pitfalls

### Pitfall 1: Let's Encrypt Fails Because DNS Not Propagated

**What goes wrong:** Domain is added to Dokploy with HTTPS enabled before the DNS A record has propagated. Traefik's ACME challenge fails silently. The domain shows as added in Dokploy UI but the service is unreachable via HTTPS. Traefik logs show "Unable to obtain ACME certificate".

**Why it happens:** Let's Encrypt performs an HTTP challenge at the domain before issuing a certificate. If DNS doesn't resolve to the server's IP, the challenge fails.

**How to avoid:** Verify DNS propagation with `dig api.yourdomain.com` (should return server IP) before adding the domain in Dokploy. If the certificate fails, delete the domain entry in Dokploy and re-add it after DNS is confirmed.

**Warning signs:** HTTPS not working after domain setup; Traefik logs contain ACME errors (visible in Dokploy's Traefik logs).

### Pitfall 2: Admin Services Accidentally Exposed

**What goes wrong:** Admin services are deployed with a published port but the VPS cloud firewall is not configured to block that port. A port scan from the internet reveals the service.

**Why it happens:** Docker manipulates iptables directly, bypassing UFW rules. Published ports become reachable even if UFW says deny.

**How to avoid:** Configure VPS cloud firewall (not UFW) to block the admin service ports (e.g., 8001, 3001) from all sources except Tailscale IPs. Verify with `nmap -p 8001 <server-public-ip>` from outside the tailnet — should return "filtered" or no response.

**Warning signs:** `nmap` scan from non-Tailscale network returns "open" on admin ports.

### Pitfall 3: Volume Mount Configured After First Deploy

**What goes wrong:** You deploy the public backend first (to test it works), then add the volume mount in Advanced → Mounts. Uploads from the first deployment are in the container's writable layer, not the named volume. After adding the volume mount and redeploying, the volume is empty.

**Why it happens:** Volume mounts are applied at container creation time, not retroactively.

**How to avoid:** Configure the Dokploy Advanced → Mounts (Volume Mount, `/app/uploads`) BEFORE deploying for the first time. This is step 1 in the deployment sequence.

**Warning signs:** Uploads appear to work but disappear after redeployment.

### Pitfall 4: DATABASE_URL Format Mismatch

**What goes wrong:** The Dokploy PostgreSQL internal URL uses the `postgresql://` prefix. The FastAPI backend requires `postgresql+asyncpg://` for SQLAlchemy's async driver. If you paste the Dokploy-provided URL directly, the backend crashes at startup with a driver error.

**Why it happens:** SQLAlchemy AsyncEngine requires an explicit async driver prefix.

**How to avoid:** When setting `DATABASE_URL` in the Dokploy Environment tab, use `postgresql+asyncpg://` prefix. The `main.py` lifespan function also converts the URL back to `postgresql://` for the psycopg connection pool — this is intentional and already handled in code.

**Warning signs:** Backend fails to start with SQLAlchemy driver or dialect errors.

### Pitfall 5: Tailscale Subnet Route Not Accepted by Clients

**What goes wrong:** Tailscale is installed and subnet routes advertised on the server, but admin clients cannot reach the Docker services. They can reach the server's Tailscale IP but not Docker container IPs.

**Why it happens:** Tailscale subnet routes require explicit opt-in on client devices: `tailscale up --accept-routes`.

**How to avoid:** After installing Tailscale on admin client devices, run `tailscale up --accept-routes`. Also approve the advertised routes in the Tailscale admin console (required once per tailnet).

**Warning signs:** `ping 10.254.x.x` fails from Tailscale client even though `ping <server-tailscale-ip>` works.

### Pitfall 6: CORS Configuration for Admin Frontend

**What goes wrong:** Admin frontend connects to admin backend via Tailscale IP/hostname. The admin backend's CORS configuration only allows `http://localhost:3001`. Browser blocks the request.

**Why it happens:** `ADMIN_CORS_ORIGIN` defaults to `localhost:3001` and must be updated to the admin frontend's actual URL.

**How to avoid:** Set `ADMIN_CORS_ORIGIN=http://<tailscale-ip>:3001` (or the MagicDNS hostname) in the admin backend's environment variables. Also set `CORS_ORIGINS` to include the public frontend URL for the public backend.

**Warning signs:** Browser console shows CORS errors on the admin frontend.

### Pitfall 7: Both Backend Services Share SECRET_KEY — Consistency Required

**What goes wrong:** Public backend uses one `SECRET_KEY` and admin backend uses a different `SECRET_KEY`. JWT tokens issued by one service are rejected by the other. (Less critical since they serve different clients, but worth flagging.)

**Why it happens:** Two separately configured services can have separate secrets.

**How to avoid:** Use the same `SECRET_KEY` value for both backend services (since they share the same database). Generate once: `python3 -c "import secrets; print(secrets.token_hex(32))"` and use that value for both.

---

## Code Examples

### Generating SECRET_KEY

```bash
# Run this once; copy the output for both backend service env vars
python3 -c "import secrets; print(secrets.token_hex(32))"
# Example output: a3f8c2e1d5b9f4a2e8c1d3b5f9a2e4c7...
```

### Verifying Tailscale Subnet Route

```bash
# On the server after tailscale up:
tailscale status
# Should show: subnet routes advertised

# On admin client after --accept-routes:
ping 10.254.0.1   # Replace with an IP in your dokploy-network subnet
# Should succeed

# From NON-Tailscale network, verify admin port is blocked:
nmap -p 8001 <server-public-ip>
# Expected: "filtered" or timeout (not "open")
```

### Checking Dokploy Internal Service Hostname

```bash
# On the Dokploy server:
docker network inspect dokploy-network --format '{{json .Containers}}' | python3 -m json.tool
# Identifies container names/IPs on the dokploy-network

# Inside a backend container, verify DB connectivity:
docker exec -it <backend-container-id> /app/.venv/bin/python -c \
  "import os; print(os.getenv('DATABASE_URL'))"
```

### Verifying Volume Mount Before Deploy

```bash
# After first deploy, check the volume exists and is mounted:
docker volume ls | grep spectra-uploads
docker inspect <backend-container-id> | python3 -m json.tool | grep -A5 "Mounts"
# Should show /app/uploads bound to spectra-uploads volume
```

### Environment Variables: Public Backend

```
DATABASE_URL=postgresql+asyncpg://user:pass@<dokploy-db-hostname>:5432/spectra
SPECTRA_MODE=public
SECRET_KEY=<generated-value>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
FRONTEND_URL=https://app.yourdomain.com
CORS_ORIGINS=["https://app.yourdomain.com"]
ADMIN_CORS_ORIGIN=          # leave empty in public mode
APP_VERSION=v0.5.0
ANTHROPIC_API_KEY=sk-ant-...
# ... other API keys as needed
ENABLE_SCHEDULER=true       # for credit reset job
```

### Environment Variables: Admin Backend

```
DATABASE_URL=postgresql+asyncpg://user:pass@<dokploy-db-hostname>:5432/spectra
SPECTRA_MODE=admin
SECRET_KEY=<same-generated-value-as-public>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
FRONTEND_URL=              # not used in admin mode
CORS_ORIGINS=["http://<tailscale-ip>:3001"]
ADMIN_CORS_ORIGIN=http://<tailscale-ip>:3001
APP_VERSION=v0.5.0
ANTHROPIC_API_KEY=sk-ant-...
# ... same API keys as public backend
ENABLE_SCHEDULER=false
```

### Environment Variables: Public Frontend

```
BACKEND_URL=https://api.yourdomain.com
```

### Environment Variables: Admin Frontend

```
BACKEND_URL=http://<tailscale-ip>:8001
```

---

## Dokploy Application Service Configuration Reference

### General Tab — Dockerfile Build Type Fields

| Field | Value |
|-------|-------|
| Source | Git (GitHub / GitLab / Generic) |
| Repository | your-org/spectra-dev |
| Branch | main (or production branch) |
| Build Type | Dockerfile |
| Dockerfile Path | `Dockerfile.backend` (or `.frontend` or `.admin`) |
| Docker Context Path | `.` (repo root — needed for COPY backend/ instructions in Dockerfiles) |

### Advanced Tab — Mounts (Public Backend Only)

| Field | Value |
|-------|-------|
| Type | Volume |
| Volume Name | `spectra-uploads` |
| Mount Path | `/app/uploads` |

**Must configure BEFORE first deploy.**

### Advanced Tab — Ports (Admin Services)

| Field | Value |
|-------|-------|
| Published Port | `8001` (admin backend) or `3001` (admin frontend) |
| Target Port | `8000` (both run on 8000/3000 internally) |
| Protocol | TCP |

**Requires VPS cloud firewall to block these ports from public internet.**

### Domains Tab (Public Services Only)

| Field | Value |
|-------|-------|
| Host | `api.yourdomain.com` (backend) or `app.yourdomain.com` (frontend) |
| Container Port | `8000` (backend) or `3000` (frontend) |
| HTTPS | Enabled |
| Certificate | letsencrypt |

**Admin services: NO domain configured.**

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| iptables/UFW for Docker port blocking | VPS cloud firewall (pre-iptables) | UFW is bypassed by Docker; cloud firewall is the only reliable block |
| Self-managed Nginx + certbot for HTTPS | Dokploy + Traefik + Let's Encrypt | Automatic cert renewal, no manual configuration |
| OpenVPN for private services | Tailscale (WireGuard-based) | Zero-config, handles NAT traversal, free tier is sufficient |
| docker-compose file-based deployment | Dokploy Application service (per-service) | Enables independent rollback per service |

---

## Open Questions

1. **Exact Tailscale MagicDNS hostname for admin services**
   - What we know: Tailscale assigns `<machine-name>.<tailnet-name>.ts.net`. The server `--hostname` flag controls machine name.
   - What's unclear: The tailnet name depends on the user's Tailscale account. DPLY-05 references `admin-api.spectra.ts.net` and `admin.spectra.ts.net` — this implies the tailnet is named `spectra`. This may not match the user's actual tailnet name.
   - Recommendation: In DEPLOYMENT.md, document as `<hostname>.<tailnet-name>.ts.net` with a note to substitute actual values. The planner should not hardcode `spectra.ts.net`.

2. **Admin services: publish port or rely on Docker network IP only**
   - What we know: Without a published port, admin services are reachable only by their Docker container IP. Tailscale subnet routing can reach those IPs if the subnet is advertised. No public exposure at all.
   - What's unclear: Can the admin frontend reliably reach the admin backend by Docker container IP via Tailscale subnet routing (container IPs can change on redeploy)?
   - Recommendation: Use published ports on the host (8001, 3001) for stable addressing. Block those ports with VPS cloud firewall. This is more predictable than relying on container IP stability.

3. **Single SECRET_KEY for both backends**
   - What we know: Both backends share the same PostgreSQL database. The admin backend issues JWT tokens for admin users; the public backend issues for regular users.
   - What's unclear: Whether there's any scenario where a JWT from one needs to be accepted by the other (there shouldn't be — admin JWT is only for admin frontend).
   - Recommendation: Use the same SECRET_KEY for operational simplicity. Document in DEPLOYMENT.md that the value must be identical across both backend services.

4. **Dokploy internal DB hostname format**
   - What we know: Dokploy uses Docker service/container names as internal hostnames. The exact hostname appears in the Dokploy database Connection section as "Internal Host".
   - What's unclear: Whether the hostname is stable across DB redeployments or changes if the database is recreated.
   - Recommendation: Copy the Internal Connection URL from Dokploy UI at database creation time. Treat it as authoritative.

---

## Sources

### Primary (HIGH confidence)
- https://docs.dokploy.com/docs/core/applications — Application service tabs and configuration
- https://docs.dokploy.com/docs/core/applications/build-type — Dockerfile build type fields (Dockerfile Path, Context Path)
- https://docs.dokploy.com/docs/core/applications/advanced — Advanced settings: Mounts, Ports, Networks
- https://docs.dokploy.com/docs/core/domains — Domain and HTTPS/SSL configuration with Traefik
- https://docs.dokploy.com/docs/core/databases/connection — Internal vs external connection URLs
- https://docs.dokploy.com/docs/core/guides/tailscale — Official Tailscale integration guide
- https://tailscale.com/kb/1019/subnets — Subnet routers (advertise-routes)
- https://tailscale.com/kb/1081/magicdns — MagicDNS .ts.net hostnames

### Secondary (MEDIUM confidence)
- https://github.com/Dokploy/dokploy/issues/2915 — Feature request for IP-specific port binding (confirms limitation is unresolved)
- https://github.com/Dokploy/dokploy/issues/507 — Internal DB hostname format (service-name as hostname)
- Multiple Dokploy community discussions confirming Docker bypasses UFW; VPS cloud firewall is recommended

### Tertiary (LOW confidence)
- DPLY-05 requirement mentions `admin-api.spectra.ts.net` — actual Tailscale hostname depends on user's tailnet name; cannot be verified without knowing the account

---

## Metadata

**Confidence breakdown:**
- Dokploy service configuration: HIGH — verified against official docs
- Let's Encrypt / SSL setup: HIGH — official Dokploy docs
- Tailscale host install + subnet routing: HIGH — official Tailscale docs
- Admin isolation approach (published port + VPS firewall): MEDIUM — confirmed Docker bypasses UFW; cloud firewall approach is community-verified best practice but exact VPS provider steps vary
- Internal DB connection hostname: MEDIUM — behavior inferred from GitHub issues and Docker networking fundamentals

**Research date:** 2026-02-19
**Valid until:** 2026-03-21 (30 days — Dokploy is actively developed; check release notes for UI changes)
