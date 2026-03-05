# Milestone v0.5 Requirements: Admin Portal

## Overview
An internal admin portal for Spectra, accessible only to platform administrators. The admin portal is fully network-isolated from the public-facing application — deployed as a separate service accessible only via Tailscale VPN. Used to manage users, control platform features, and monitor usage.

---

## 1. Admin Authentication

- Admin accounts are separate from regular user accounts (different role/flag, not the same signup flow)
- Admin login page served by the admin frontend (Tailscale-only)
- Only users with `is_admin` role can access the admin portal
- Standard email + password authentication (no self-signup for admin accounts)
- First admin account is seeded via CLI command or environment variable
- Session timeout after inactivity (configurable, default 30 minutes)
- All admin actions are audit-logged (who did what, when)

---

## 2. Admin Dashboard

- Overview of key platform metrics at a glance:
  - Total registered users (active vs inactive)
  - New user signups (today / this week / this month)
  - Total chat sessions created
  - Total files uploaded
  - Total messages sent (platform-wide)
  - Credit consumption summary (total used / total remaining across all users)
- Simple charts/graphs for trends (signups over time, messages over time)

---

## 3. User Management

- List all registered users with search and filter capabilities
  - Filter by: active/inactive, user class, signup date
  - Search by: email, name
- View user details:
  - Profile info (name, email, signup date, last login)
  - Account status (active/inactive)
  - User class (tier)
  - Credit balance and usage history
  - Number of files, chat sessions
- Admin actions per user:
  - Activate / deactivate user account
  - Reset user password (sends reset email to user)
  - Change user class (tier)
  - Adjust credit balance
  - Delete user account (with confirmation)

---

## 4. Signup Control (Feature Toggle)

- Global toggle: **Allow public signup** (enabled/disabled)
  - When **enabled**: anyone can register through the normal signup flow
  - When **disabled**: signup page shows "Registration is currently invite-only" message; only users with a valid invite link can register
- This setting is stored in a platform settings/config table
- Changes take effect immediately (no server restart required)

---

## 5. User Invitation System

- Admin can invite users by entering their email address
- System generates a unique, time-limited invite link (e.g., expires in 7 days)
- Invite email is sent to the user via the existing SMTP/email service
- Invited user clicks the link and is taken to a registration form (pre-filled email, locked)
- Invited user completes registration (sets password, name)
- Admin can view list of pending invitations:
  - Email, invite date, expiry date, status (pending / accepted / expired)
- Admin can revoke or resend pending invitations
- Invite links are single-use (invalidated after registration)

---

## 6. User Class Management

### Approach: Static Tiers, Configurable Credits (Option B)
- User classes are **defined in a config file** (`user_classes.yaml`), not created dynamically via the admin UI
- Predefined tiers: `free`, `standard`, `premium` (adding a new tier requires a config change + redeployment)
- Admin portal can **edit credit amounts and display names** per tier, but cannot create or delete tiers
- Users table gets a `user_class` field (enum, defaults to `free`)

### Config Structure
```yaml
user_classes:
  free:
    display_name: "Free"
    credits_per_week: 10
    stripe_price_id: null          # future: Stripe integration
  standard:
    display_name: "Standard"
    credits_per_week: 100
    stripe_price_id: null          # future: e.g., "price_xxx"
  premium:
    display_name: "Premium"
    credits_per_week: 500
    stripe_price_id: null          # future: e.g., "price_yyy"
```

### Admin Portal Capabilities for User Classes
- View all tiers with their current credit allocations
- Edit credit amounts per tier (persisted in `platform_settings`, overrides config defaults)
- Assign / change a user's tier manually
- View how many users are in each tier

### Future: Pricing & Subscription Integration
- **Not in scope for this milestone** — will be a separate monetization milestone
- The config structure is **forward-compatible** with payment providers (Stripe)
- Strategy: **separate what the tier gives from what the tier costs**
  - Spectra config manages **features** (credits per week, access limits)
  - Stripe manages **pricing** (monthly cost, billing, invoices, payment collection)
  - Linked via `stripe_price_id` in the config
- Future self-service upgrade flow:
  1. User clicks "Upgrade to Standard" in the public app
  2. Redirected to Stripe Checkout (handles payment)
  3. Payment succeeds → Stripe sends webhook to backend
  4. Backend maps `stripe_price_id` → `user_class` = `standard`
  5. User's class updated + credits reset to new tier allocation
- Downgrades and cancellations follow the same webhook pattern
- Admin manual overrides (e.g., for partners, beta testers) bypass Stripe entirely — same `user_class` field, no payment required

---

## 7. Credit Management

- **Credit cost per message**:
  - Credits are float values (e.g., 0.5, 1.0, 2.0, 3.0)
  - Default cost per message is configurable by admin in Platform Settings (e.g., `default_credit_cost = 1.0`)
  - When a user sends a message, the system deducts the applicable credit cost from their balance
  - When credits reach 0 (or below the cost of the next message), user cannot send new messages (show "out of credits" message)
  - Credits reset weekly based on user class allocation (configurable: weekly or monthly)
- **Future: Per-model credit cost**:
  - **Not in scope for this milestone** — will be added when multi-model selection is available to users
  - Each LLM model will have its own credit cost (e.g., Opus 4.5 = 3.0, Sonnet = 1.0, Haiku = 0.5)
  - Cost is determined at message time based on which model the user selects
  - Model credit costs will be defined in a config file (e.g., `credit_costs.yaml`):
    ```yaml
    credit_costs:
      default: 1.0                  # fallback if model not listed
      models:
        claude-opus-4-5: 3.0
        claude-sonnet-4-5: 1.0
        claude-haiku-4-5: 0.5
        gpt-4o: 2.0
        gemini-pro: 1.5
    ```
  - Admin can override model costs via Platform Settings without redeployment
- **Per-user credit management** (admin portal):
  - View remaining credits for each user (float balance)
  - Manually add or deduct credits for a specific user (with a reason/note)
  - View credit usage history per user (date, model used, cost, remaining balance, admin note)
- **Credit overview** (admin portal):
  - Dashboard widget showing credit distribution across user classes
  - List of users with low credits (e.g., < 10% remaining)
  - Option to bulk-adjust credits by user class (e.g., grant 50 extra credits to all Free-tier users)
- **Credit reset policy**:
  - Configurable: manual-only or auto-reset (weekly/monthly) based on user class defaults
  - Admin can trigger manual reset for individual users or by class

---

## 8. Platform Settings

- Centralized settings page for global platform configuration:
  - Signup toggle (from section 4)
  - Default user class for new signups
  - Invite link expiry duration
  - Credit reset policy (manual / weekly auto-reset / monthly auto-reset)
  - Credit amount overrides per user class (overrides config file defaults)
  - Default credit cost per message (float, e.g., `1.0`)
  - Future: per-model credit cost overrides
- Settings are persisted in a `platform_settings` table (key-value or JSON)

---

## 9. Architecture: Split-Horizon Deployment

### Deployment Model
- **Same FastAPI codebase, three modes** controlled by `SPECTRA_MODE` env var
  - `SPECTRA_MODE=public` — mounts only user-facing routers (auth, chat, files, etc.)
  - `SPECTRA_MODE=admin` — mounts only admin routers (admin auth, user management, settings, etc.)
  - `SPECTRA_MODE=dev` (default) — mounts **all** routers (public + admin) for local development
- In production, only `public` and `admin` modes are used
- Admin endpoints do **not exist** on the public deployment — zero public attack surface
- Both deployments connect to the **same PostgreSQL database**

### Network Topology
```
┌──────────────────────────────────────────────────────┐
│  Public Internet                                     │
│                                                      │
│   Users ──▶ app.yourdomain.com (Next.js frontend)    │
│               │                                      │
│               ▼                                      │
│          api.yourdomain.com (FastAPI, MODE=public)    │
│               │                                      │
└───────────────┼──────────────────────────────────────┘
                │
                ▼
          ┌──────────┐
          │ PostgreSQL │  (shared database)
          └──────────┘
                ▲
                │
┌───────────────┼──────────────────────────────────────┐
│  Tailscale VPN (internal only)                       │
│               │                                      │
│   admin-api.spectra.ts.net (FastAPI, MODE=admin)     │
│               ▲                                      │
│               │                                      │
│   admin.spectra.ts.net (Next.js admin frontend)      │
│               ▲                                      │
│               │                                      │
│          Admin via Tailscale client                   │
└──────────────────────────────────────────────────────┘
```

### Backend: Mode-Based Router Mounting
- `main.py` reads `SPECTRA_MODE` env var at startup
- In `public` mode: mounts `auth`, `chat`, `files`, `chat_sessions`, `search`, `health` routers
- In `admin` mode: mounts `admin_auth`, `admin_users`, `admin_settings`, `admin_invitations`, `admin_credits`, `health` routers
- In `dev` mode: mounts all of the above
- Shared code (models, database, services) is reused across all modes
- Admin routers live under `app/routers/admin/` directory
- All admin endpoints are prefixed with `/api/admin/...`

### Admin Frontend
- Separate Next.js application (not a route within the existing frontend)
- Deployed on Tailscale network only (binds to Tailscale IP) in production
- Talks to the admin backend API (`admin-api.spectra.ts.net` in production, `localhost:8000` in dev)
- Can be a simpler setup (no SSR needed, SPA is fine)

### Project Structure
```
spectra-dev/
  backend/              # single FastAPI app (all modes)
  frontend/             # public user app (existing Next.js)
  admin-frontend/       # admin portal app (new Next.js)
```

### Local Development Workflow
- **No Docker, no Tailscale, no VPN needed for local dev**
- Network isolation is a deployment concern only — locally everything runs on localhost
- Single backend serves both public and admin endpoints in `dev` mode
- Run three processes:
  - Backend on `localhost:8000` — `SPECTRA_MODE=dev` (default, all endpoints)
  - Public frontend on `localhost:3000` — talks to `localhost:8000`
  - Admin frontend on `localhost:3001` — talks to the same `localhost:8000`
- `.env` defaults to `SPECTRA_MODE=dev` so no extra config needed for local work
- Both frontends can be developed and tested independently against the same backend
- API docs at `localhost:8000/docs` show all endpoints (public + admin) in dev mode

### Production Deployment (Docker Compose on Tailscale Node)
- Admin API container: same Docker image as public, with `SPECTRA_MODE=admin`
- Admin frontend container: separate image built from admin frontend codebase
- Both bind to Tailscale interface IP only (e.g., `100.x.x.x`)
- Not reachable from public internet even if server ports are scanned

### Security Layers (Defense in Depth)
1. **Network isolation** — admin services only accessible via Tailscale VPN
2. **Authentication** — admin must log in with admin credentials
3. **Role enforcement** — backend checks `is_admin` flag on every admin endpoint
4. **Audit logging** — all admin actions logged with timestamp, admin ID, and action details

---

## 10. Database Changes

- Admin role is a field on the existing `users` table (`is_admin` boolean or `role` enum)
- `user_class` field added to `users` table (enum: free/standard/premium, default: free)
- No new database for admin; extends the existing Spectra database with new tables:
  - `platform_settings` — global config key-value store (includes credit overrides per tier)
  - `user_credits` — per-user credit balance and transaction log (user_id, balance, last_reset)
  - `credit_transactions` — credit usage/adjustment history (user_id, amount, type, reason, timestamp, admin_id)
  - `invitations` — invite records with token, status, expiry
  - `admin_audit_log` — admin action log (admin_id, action, target, timestamp, details)
- User class definitions live in `user_classes.yaml` config file, **not** in a database table
- Credit deduction is handled at the chat message creation layer (existing `chat` service)
- All new tables managed via Alembic migrations (same migration chain as existing)
