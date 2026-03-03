# Milestone v0.11 — Admin Portal: Analysis Workspace Management

## Overview

This milestone adds **administrative controls** for the Analysis Workspace feature: tier-based access gating, collection limits, granular credit cost configuration, and comprehensive activity monitoring. Builds on the existing Admin Portal (v0.5), tier system (`user_classes.yaml`), and credit infrastructure.

## 1. Tier-Based Access & Collection Limits

### 1.1 Workspace Access Gating
- Extend `user_classes.yaml` with two new fields per tier: `workspace_access` (boolean) and `max_active_collections` (integer, -1 for unlimited)
- Backend enforcement: API endpoints for Collection creation must check user's tier before allowing access
- Frontend enforcement: hide/disable Analysis Workspace nav entry for users without access
- Upgrade prompt: when user hits collection limit or lacks access, show clear message with upgrade path

### 1.2 Default Tier Configuration

| Tier | Workspace Access | Max Active Collections | Rationale |
|------|:---:|:---:|---|
| `free_trial` | Yes | 1 | Experience the "wow" moment — conversion driver |
| `free` | No | 0 | Chat-only. Workspace is the upgrade incentive |
| `standard` | Yes | 5 | Regular use without friction |
| `premium` | Yes | Unlimited (-1) | Power users, no limits |
| `internal` | Yes | Unlimited (-1) | Admin/testing |

### 1.3 Collection Limit Enforcement
- Limit applies to **active** Collections only (status = `active`)
- Users can **archive** completed Collections to free up slots
- Archived Collections are read-only: view reports, download exports, but cannot run Pulse/Investigate/Model
- Re-activating an archived Collection counts against the limit (blocked if at max)

### 1.4 Admin Tier Configuration UI
- Extend existing Settings page tier table to show `workspace_access` and `max_active_collections` columns
- Read-only display (changes require YAML edit + redeploy — same as current tier config pattern)
- Show current collection usage per tier in the tier summary endpoint

## 2. Granular Credit Cost Configuration

### 2.1 Per-Activity Credit Costs
Store as `platform_settings` entries (same pattern as existing `default_credit_cost`). All configurable at runtime via Admin Portal without redeploy.

| Setting Key | Activity | Default Cost | What It Covers |
|-------------|----------|:---:|---|
| `workspace_credit_cost_pulse` | Pulse: Run Detection | 5.0 | Data profiling + statistical analyses + Signal generation |
| `workspace_credit_cost_investigate_start` | Explain: Start Investigation | 3.0 | First Q&A exchange (ANOVA ranking, initial hypothesis) |
| `workspace_credit_cost_investigate_exchange` | Explain: Per Q&A Exchange | 1.0 | Each subsequent exchange in guided investigation |
| `workspace_credit_cost_sensitivity` | Model: Sensitivity Analysis | 3.0 | Tornado chart generation + regression fitting |
| `workspace_credit_cost_simulation` | Model: Simulation Run | 2.0 | Lever adjustment → projected outcome recalculation |
| `workspace_credit_cost_scenario_compare` | Model: Scenario Save & Compare | 1.0 | Comparison table + overlay chart generation |
| `workspace_credit_cost_report_compile` | Report: Compile & Generate | 1.0 | Markdown compilation from analysis journey |
| `workspace_credit_cost_report_export` | Report: PDF Export | 0.5 | Server-side PDF rendering |

### 2.2 Admin Settings UI
- New "Workspace Credit Costs" section in Admin Settings page
- Table/form showing all workspace credit cost settings with editable values
- Save button updates `platform_settings` entries
- Changes take effect immediately (existing TTL cache pattern — 30 second refresh)
- Validation: costs must be >= 0, max 2 decimal places

### 2.3 User-Facing Credit Transparency
- Show credit cost estimate **before** each action (e.g., button label: "Run Detection (5 credits)")
- Show running credit total in Collection header: "Credits used: 14"
- Insufficient credits: show clear message with current balance and required cost
- Credit deduction follows existing pattern: deduct before execution, refund on failure

### 2.4 Backend Implementation
- New utility function: `get_workspace_credit_cost(activity_type: str) -> Decimal`
- Reads from `platform_settings` with fallback to defaults
- All Workspace API endpoints call this before execution
- Pre-check: `CreditService.check_balance()` before deduction
- Integrate with existing `CreditService.deduct_credit()` — pass activity type as transaction reason

## 3. Admin Monitoring & Analytics

### 3.1 Workspace Activity Log Table
New database table `workspace_activity_log` to track all Workspace activities:

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID FK | Who performed the action |
| `collection_id` | UUID FK | Which Collection |
| `activity_type` | enum | `pulse_run`, `investigation_start`, `investigation_exchange`, `sensitivity_analysis`, `simulation_run`, `scenario_compare`, `report_compile`, `report_export` |
| `credit_cost` | NUMERIC(10,1) | Credits charged |
| `duration_ms` | INTEGER | E2B/agent execution time |
| `status` | enum | `success`, `failed`, `refunded` |
| `metadata` | JSONB | Activity-specific data (signal count, methods used, etc.) |
| `created_at` | TIMESTAMP | When the activity occurred |

### 3.2 Workspace Dashboard (new Admin page)
New page in Admin Portal: `/admin/workspace`

**Overview Cards (top row):**
- Total Collections created (all time + last 7 days)
- Active vs. Archived Collections (current snapshot)
- Total Workspace credits consumed (last 7 days + last 30 days)
- Average credits per Collection lifecycle

**Activity Charts:**
- Workspace activities over time (daily, grouped by activity_type) — stacked bar chart
- Stage adoption funnel: Pulse → Explain → Model — shows drop-off at each stage
- Credit consumption over time — line chart, broken down by activity type
- Top users by Workspace credit consumption — bar chart (top 10)

**Activity Table:**
- Filterable/searchable table of recent workspace activities
- Columns: user, collection, activity type, credit cost, duration, status, timestamp
- Filters: date range, activity type, user, status

### 3.3 Per-User Workspace Tab
Extend existing Admin user detail page with a **"Workspace" tab** alongside existing Activity/Sessions tabs:

- **Collection list:** name, status (active/archived), created date, signal count, report count, total credits used in this collection
- **Credit breakdown:** pie/donut chart showing Pulse vs. Explain vs. Model vs. Reports credit consumption for this user
- **Usage summary:** total collections created, total workspace credits consumed, last workspace activity date
- **Limit usage:** "3 of 5 active collections" indicator

### 3.4 Workspace Metrics in Tier Summary
Extend existing `GET /api/admin/tiers` endpoint to include:
- Workspace adoption rate per tier: % of users who have created at least 1 Collection
- Average collections per user per tier
- Average workspace credits consumed per user per tier

### 3.5 Alerts & Operational Monitoring
- **High-cost Collection alert:** Configurable threshold (default: 50 credits). Collections exceeding this show a warning badge in the activity table
- **Failed activity tracking:** Surface Pulse runs that failed or returned no signals — helps monitor detection quality
- **Low-adoption alert:** If workspace_access is enabled for a tier but < 10% of users have tried it, surface this insight

## 4. Backend API Endpoints

### 4.1 Workspace Settings
- `GET /api/admin/workspace/settings` — get all workspace credit cost settings
- `PUT /api/admin/workspace/settings` — update workspace credit cost settings (requires password re-entry)

### 4.2 Workspace Dashboard
- `GET /api/admin/workspace/stats` — overview cards (collection counts, credit totals, averages)
- `GET /api/admin/workspace/activity` — activity log with filters (date range, type, user, status, pagination)
- `GET /api/admin/workspace/activity/chart` — aggregated activity data for charts (grouped by day/week, by type)
- `GET /api/admin/workspace/funnel` — stage adoption funnel data
- `GET /api/admin/workspace/top-users` — top N users by workspace credit consumption

### 4.3 Per-User Workspace
- `GET /api/admin/users/{user_id}/workspace` — user's collections, credit breakdown, usage summary
- `GET /api/admin/users/{user_id}/workspace/activity` — user's workspace activity log (paginated)

### 4.4 Tier Workspace Metrics
- Extend `GET /api/admin/tiers` response to include workspace adoption metrics

## 5. Frontend Admin Pages

### 5.1 Settings Page Updates
- Add "Workspace Credit Costs" section below existing credit cost setting
- Editable table with all workspace cost settings + save button

### 5.2 New Workspace Dashboard Page
- Route: `/admin/workspace`
- Add to admin sidebar navigation
- Overview cards + charts + activity table (as described in 3.2)

### 5.3 User Detail Page Update
- Add "Workspace" tab to existing user detail page
- Collections list + credit breakdown + usage summary (as described in 3.3)

### 5.4 Tier Summary Update
- Add workspace columns to existing tier summary table in Settings page

## 6. Out of Scope
- Dynamic tier configuration via Admin UI (tiers remain YAML-based — same as current pattern)
- Per-collection credit budgets/limits (just per-tier collection count limits for now)
- Workspace usage alerts via email/Slack (in-portal only for now)
- Team/organization-level workspace management (individual users only)

## 7. Success Criteria
- Admin can view all workspace credit cost settings and modify them — changes take effect within 30 seconds
- Tier-based access enforcement works: free tier users cannot access Workspace, free_trial users are limited to 1 active collection
- Workspace dashboard loads with accurate activity data, charts, and funnel visualization
- Per-user workspace tab shows correct collection list, credit breakdown, and usage summary
- Activity log captures all workspace activities with correct credit costs and durations
- Archived collections are correctly read-only and don't count against active limit
- Credit cost shown to user before each action matches admin-configured value
