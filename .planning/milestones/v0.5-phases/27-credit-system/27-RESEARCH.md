# Phase 27: Credit System - Research

**Researched:** 2026-02-16
**Domain:** Credit balance management, atomic deduction, scheduled resets, admin controls
**Confidence:** HIGH

## Summary

Phase 27 implements the credit system for Spectra: atomic per-message credit deduction, balance tracking with transaction history, admin adjustment controls, and scheduled auto-resets. The existing codebase already has the database tables (`user_credits`, `credit_transactions`) and models created in Phase 26. This phase builds the service layer, integrates credit checks into the chat flow, creates admin API endpoints, adds the `user_classes.yaml` config file, and implements the scheduler for rolling resets.

The primary technical challenges are: (1) atomic balance deduction using `SELECT FOR UPDATE` to prevent concurrent overdraw, (2) rolling reset scheduling anchored to each user's signup date, and (3) integrating credit checks into the existing SSE streaming chat flow without breaking the current architecture.

**Primary recommendation:** Use SQLAlchemy `with_for_update()` for atomic deduction within a single transaction, APScheduler 3.x `AsyncIOScheduler` for periodic reset jobs, and a dedicated `CreditService` class following the existing service-layer pattern (`ChatService`, `AuthService`).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Out-of-credits: user can type but send is blocked with error "You're out of credits. Credits reset on [date]."
- User retains full read access when out of credits -- only sending new messages is blocked
- Credit balance always visible in sidebar/nav (frontend concern -- Phase 31)
- Low-credit warning when below threshold (e.g., <20% or <3 credits)
- Silent deduction per message -- balance updates without showing per-message cost
- Reset cadence is per-class via `reset_policy` in user_classes.yaml (weekly, monthly, none, unlimited)
- Rolling reset relative to each user's signup date
- No carry-over: balance resets to tier allocation regardless of remaining
- Admin manual reset restarts user's cycle from today
- In-app notice when credits refresh (toast/banner -- frontend concern)
- Individual user adjustments only (bulk deferred)
- Admin must re-enter password to confirm credit adjustments
- Admin must provide reason/note for every adjustment
- Auto-reset always sets balance to tier allocation, ignoring admin bonuses
- Transaction types: 'usage', 'admin_adjustment', 'auto_reset', 'manual_reset'
- Three credit models: weekly/monthly (recurring), none (one-time grant), unlimited (log but don't deduct)
- YAML config structure as specified in CONTEXT.md
- All new users assigned default class from platform_settings
- No tier selection at invite time

### Claude's Discretion
- Low-credit threshold exact value (percentage or absolute)
- Toast/banner implementation for credit refresh notification
- Scheduler implementation details (APScheduler configuration)
- How to represent "unlimited" balance in the database (sentinel value vs null)
- Credit balance API endpoint design

### Deferred Ideas (OUT OF SCOPE)
- Bulk credit adjustments
- Self-service tier upgrade/downgrade
- Per-model credit costs
- User-facing transaction history endpoint
</user_constraints>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| SQLAlchemy | >=2.0.0 | ORM, `with_for_update()` for row locking | Already installed |
| asyncpg | >=0.29.0 | PostgreSQL async driver | Already installed |
| FastAPI | >=0.115.0 | API framework | Already installed |
| Alembic | >=1.13.0 | Database migrations | Already installed |
| PyYAML | >=6.0.0 | YAML config parsing | Already installed |
| Pydantic | (via FastAPI) | Request/response schemas | Already installed |

### New Dependencies
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | >=3.11.0,<4.0 | Scheduled credit resets | Production-stable, AsyncIOScheduler for asyncio event loop, widely adopted |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler | Celery Beat | Celery is overkill for a single periodic job; APScheduler is lighter, runs in-process |
| APScheduler | asyncio.create_task + sleep loop | Fragile, no persistence, no missed-job handling |
| APScheduler 4.x | APScheduler 3.x | v4 is not yet production-stable; stick with 3.x |

**Installation:**
```bash
pip install "APScheduler>=3.11.0,<4.0"
```

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
├── config/
│   └── user_classes.yaml          # NEW: tier definitions with reset_policy
├── models/
│   ├── user_credit.py             # EXISTS: needs no changes
│   └── credit_transaction.py      # EXISTS: needs no changes
├── services/
│   ├── credit.py                  # NEW: CreditService class
│   └── user_class.py              # NEW: UserClassService (YAML loader + cache)
├── routers/
│   ├── admin/
│   │   ├── credits.py             # NEW: admin credit management endpoints
│   │   └── __init__.py            # UPDATE: register credits router
│   └── credits.py                 # NEW: public credit balance endpoint
├── schemas/
│   └── credit.py                  # NEW: credit request/response schemas
└── scheduler.py                   # NEW: APScheduler setup + reset job
```

### Pattern 1: Atomic Credit Deduction with SELECT FOR UPDATE
**What:** Lock the user's credit row, check balance, deduct, record transaction -- all in one DB transaction.
**When to use:** Every time a message is sent (before agent runs).
**Example:**
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_credit import UserCredit
from app.models.credit_transaction import CreditTransaction
from decimal import Decimal

async def deduct_credit(
    db: AsyncSession,
    user_id: UUID,
    cost: Decimal,
) -> tuple[bool, Decimal]:
    """Atomically deduct credits. Returns (success, new_balance).

    Uses SELECT FOR UPDATE to prevent concurrent overdraw.
    """
    # Lock the row -- blocks other concurrent deductions for this user
    result = await db.execute(
        select(UserCredit)
        .where(UserCredit.user_id == user_id)
        .with_for_update()
    )
    credit = result.scalar_one_or_none()

    if credit is None:
        return False, Decimal("0")

    if credit.balance < cost:
        return False, credit.balance

    # Deduct
    credit.balance = credit.balance - cost

    # Record transaction
    tx = CreditTransaction(
        user_id=user_id,
        amount=-cost,
        balance_after=credit.balance,
        transaction_type="usage",
    )
    db.add(tx)
    await db.flush()  # flush within caller's transaction

    return True, credit.balance
```

### Pattern 2: YAML Config with Cached Loading
**What:** Load user_classes.yaml once at startup, cache with TTL (reuse existing platform_settings 30s TTL pattern).
**When to use:** Resolving tier allocation, reset policy, display name.
**Example:**
```python
import yaml
from pathlib import Path
from functools import lru_cache
from datetime import datetime, timezone

_user_classes_cache = None
_cache_loaded_at = None
CACHE_TTL_SECONDS = 30

def get_user_classes() -> dict:
    """Load user_classes.yaml with 30s cache (matches platform_settings TTL)."""
    global _user_classes_cache, _cache_loaded_at
    now = datetime.now(timezone.utc)

    if _user_classes_cache is None or (now - _cache_loaded_at).total_seconds() > CACHE_TTL_SECONDS:
        config_path = Path(__file__).parent.parent / "config" / "user_classes.yaml"
        with open(config_path) as f:
            data = yaml.safe_load(f)
        _user_classes_cache = data.get("user_classes", {})
        _cache_loaded_at = now

    return _user_classes_cache
```

### Pattern 3: Scheduler Integration via FastAPI Lifespan
**What:** Start APScheduler in the FastAPI lifespan context manager, shut down cleanly.
**When to use:** App startup/shutdown.
**Example:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

# In lifespan:
async def lifespan(app: FastAPI):
    # ... existing startup code ...

    scheduler.add_job(
        process_credit_resets,
        IntervalTrigger(minutes=15),  # Check every 15 minutes
        id="credit_reset_job",
        replace_existing=True,
    )
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)
```

### Pattern 4: Rolling Reset Calculation
**What:** Determine if a user's credits are due for reset based on signup date + reset_policy.
**When to use:** In the periodic scheduler job.
**Example:**
```python
from datetime import datetime, timezone, timedelta

def is_reset_due(
    signup_date: datetime,
    last_reset_at: datetime | None,
    reset_policy: str,
) -> bool:
    """Check if user's credits need resetting based on rolling cycle."""
    if reset_policy in ("none", "unlimited"):
        return False

    now = datetime.now(timezone.utc)
    anchor = last_reset_at or signup_date

    if reset_policy == "weekly":
        return (now - anchor) >= timedelta(weeks=1)
    elif reset_policy == "monthly":
        # Approximate: 30 days (or use dateutil.relativedelta for exact months)
        return (now - anchor) >= timedelta(days=30)

    return False
```

### Pattern 5: Credit Check as Pre-Send Gate in Chat Router
**What:** Check credit balance before invoking the agent pipeline. Reject with 402 if insufficient.
**When to use:** In `stream_query` and `query_with_ai` endpoints.
**Example:**
```python
# In chat router, before agent invocation:
from app.services.credit import CreditService

# Check and deduct before agent runs
success, balance = await CreditService.deduct_credit(db, current_user.id, credit_cost)
if not success:
    next_reset = await CreditService.get_next_reset_date(db, current_user)
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            "error": "insufficient_credits",
            "message": f"You're out of credits. Credits reset on {next_reset.strftime('%B %d, %Y')}.",
            "balance": float(balance),
            "next_reset": next_reset.isoformat() if next_reset else None,
        }
    )
```

### Anti-Patterns to Avoid
- **Read-then-write without lock:** Reading balance, checking in Python, then writing back -- race condition. Always use `with_for_update()`.
- **Deducting after agent runs:** If agent fails or takes long, user already consumed API costs. Deduct before (matches LLM billing pattern).
- **Global reset time:** User decision is rolling per-user anchored to signup date. Do not use a single cron time.
- **Storing "unlimited" as a very large number:** Use sentinel logic in the service layer -- check `reset_policy == "unlimited"` and skip deduction, still log the transaction.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Job scheduling | Custom sleep loop / cron | APScheduler AsyncIOScheduler | Handles missed jobs, graceful shutdown, configurable intervals |
| Row-level locking | Application-level locks / Redis | PostgreSQL `SELECT FOR UPDATE` | Database-native, works with existing SQLAlchemy stack, no new infra |
| YAML parsing | Custom config parser | PyYAML (already installed) | Standard, handles all YAML features |
| Date arithmetic for monthly resets | Manual day counting | `dateutil.relativedelta` or `timedelta(days=30)` | Edge cases with month lengths |

**Key insight:** The atomic deduction is the most critical correctness requirement. PostgreSQL row locking via `SELECT FOR UPDATE` is the proven pattern -- do not attempt application-level locking.

## Common Pitfalls

### Pitfall 1: Race Condition in Balance Check
**What goes wrong:** Two concurrent requests read balance=1, both deduct, balance goes to -1.
**Why it happens:** Read-then-write without row lock.
**How to avoid:** Always use `with_for_update()` on the UserCredit row before checking balance.
**Warning signs:** Negative balances in user_credits table.

### Pitfall 2: Transaction Boundary Mismatch in Streaming
**What goes wrong:** Credit deduction commits, but agent stream fails -- user lost a credit for nothing.
**Why it happens:** Deduction and agent invocation are in separate transactions.
**How to avoid:** Accept this by design (decision: "deduct before agent runs, no refund on failure"). Document this matches LLM billing patterns where API costs are incurred regardless of downstream use.
**Warning signs:** Users complaining about lost credits on errors (acceptable per user decision).

### Pitfall 3: Scheduler Runs on Multiple Instances
**What goes wrong:** In production with multiple app instances, the reset job runs N times, creating duplicate transactions.
**Why it happens:** APScheduler is in-process; each instance starts its own scheduler.
**How to avoid:** Either (a) run scheduler only on one designated instance (env var flag), or (b) make the reset idempotent with `last_reset_at` check + `SELECT FOR UPDATE`.
**Warning signs:** Multiple `auto_reset` transactions for the same user within the same cycle.

### Pitfall 4: Stale Session in Streaming Credit Deduction
**What goes wrong:** Credit deduction uses the request-scoped `db` session, but during long streams the session times out.
**Why it happens:** Agent service already identified this issue (see `_save_stream_result` using `async_session_maker()`).
**How to avoid:** Deduct credits at the START of the request (before streaming begins), using the request-scoped session. The deduction is fast (single SELECT FOR UPDATE + UPDATE). The streaming result save already uses a fresh session.
**Warning signs:** "connection already closed" errors during credit operations.

### Pitfall 5: NUMERIC Precision Handling
**What goes wrong:** Python float arithmetic introduces rounding errors (e.g., 10.0 - 1.0 = 8.999999...).
**Why it happens:** SQLAlchemy NUMERIC maps to Python float by default.
**How to avoid:** Use `Decimal` in Python for all credit arithmetic. SQLAlchemy NUMERIC(10,1) will round to 1 decimal place on DB side, but use Decimal in service code for clarity.
**Warning signs:** Balance values with many decimal places in the database.

### Pitfall 6: Missing UserCredit Row for New Users
**What goes wrong:** New user signs up, tries to chat, no UserCredit row exists, deduction fails.
**Why it happens:** Registration flow doesn't create UserCredit row.
**How to avoid:** Create UserCredit row during registration (in `create_user` service or as a post-signup hook). Initialize balance from user_classes.yaml based on the assigned default class.
**Warning signs:** 500 errors when new users try to chat.

### Pitfall 7: Admin Password Re-entry Security
**What goes wrong:** Admin adjustment endpoint accepts only the admin JWT, no password re-entry -- weaker accountability.
**Why it happens:** Forgetting the user decision requiring password re-entry.
**How to avoid:** Require `password` field in the admin adjustment request body, verify against admin's hashed password before processing.
**Warning signs:** Admin adjustments without password verification in the endpoint.

## Code Examples

### Credit Deduction Integration Point (in agent_service.py)
```python
# At the top of run_chat_query_stream(), before file loading:
from app.services.credit import CreditService

# Deduct credit BEFORE agent runs (user decision: deduct before, no refund)
deduction = await CreditService.deduct_credit(db, user_id, credit_cost)
if not deduction.success:
    yield {
        "type": "error",
        "error_code": "insufficient_credits",
        "message": deduction.error_message,
        "balance": float(deduction.balance),
        "next_reset": deduction.next_reset.isoformat() if deduction.next_reset else None,
    }
    return
```

### Admin Credit Adjustment Endpoint
```python
@router.post("/users/{user_id}/credits/adjust")
async def adjust_user_credits(
    user_id: UUID,
    body: CreditAdjustmentRequest,  # amount, reason, password
    current_admin: CurrentAdmin,
    db: DbSession,
    request: Request,
):
    """Adjust a user's credit balance (admin only, requires password re-entry)."""
    # Verify admin password
    if not verify_password(body.password, current_admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    result = await CreditService.admin_adjust(
        db, user_id, body.amount, body.reason, current_admin.id
    )

    # Audit log
    await log_admin_action(
        db, current_admin.id, "credit_adjustment", "user_credit",
        target_id=str(user_id),
        details={"amount": float(body.amount), "reason": body.reason, "balance_after": float(result.balance)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    return result
```

### Rolling Reset Job
```python
async def process_credit_resets():
    """Periodic job: check all users and reset credits where due."""
    async with async_session_maker() as db:
        # Query users with recurring reset policies
        result = await db.execute(
            select(UserCredit, User.user_class, User.created_at)
            .join(User, UserCredit.user_id == User.id)
            .where(User.is_active == True)
        )

        user_classes = get_user_classes()

        for credit, user_class_name, signup_date in result.all():
            class_config = user_classes.get(user_class_name, {})
            reset_policy = class_config.get("reset_policy", "none")
            allocation = class_config.get("credits", 0)

            if is_reset_due(signup_date, credit.last_reset_at, reset_policy):
                # Lock row, reset balance, record transaction
                await _execute_reset(db, credit, allocation)

        await db.commit()
```

## Discretion Decisions (Recommendations)

### Low-Credit Threshold
**Recommendation:** Use both percentage AND absolute: warn when balance < 20% of tier allocation OR balance < 3 credits, whichever triggers first. This handles both high-allocation tiers (20% of 500 = 100, too high as absolute) and low-allocation tiers (20% of 10 = 2, reasonable).
**Implementation:** Calculate threshold in the balance API response so frontend can compare.

### Unlimited Balance Representation
**Recommendation:** Store balance as -1 (sentinel) in the database for unlimited users. The service layer checks `reset_policy == "unlimited"` and skips deduction. The balance field is meaningless for unlimited users, so -1 clearly signals "not applicable" without conflating with actual zero balance or null (which could mean "not initialized").
**Alternative considered:** NULL for balance -- but NULL creates ambiguity with "credit row not yet created" vs "unlimited user."

### Credit Balance API Endpoint Design
**Recommendation:**
```
GET /credits/balance  (public app, authenticated user)
Response: {
    "balance": 8.0,
    "tier_allocation": 10,
    "reset_policy": "weekly",
    "next_reset_at": "2026-02-23T14:30:00Z",  // null for "none" policy
    "is_low": true,
    "is_unlimited": false,
    "display_class": "Free"
}
```
Single endpoint returns everything the frontend sidebar needs. No need for separate endpoints.

### Scheduler Configuration
**Recommendation:** Run the reset check job every 15 minutes via APScheduler `AsyncIOScheduler`. This balances timeliness (credits reset within 15 min of due time) against database load (one query per run scanning active users). For production multi-instance deployment, use an env var `ENABLE_SCHEDULER=true` on exactly one instance. The reset job is idempotent via `last_reset_at` check, so double-runs are safe but wasteful.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Application-level locks for balance | PostgreSQL SELECT FOR UPDATE | Standard practice | Eliminates race conditions without Redis |
| APScheduler 4.x (alpha) | APScheduler 3.11.x (stable) | 2025 | v4 not production-ready; use 3.x |
| Global credit reset (cron) | Per-user rolling reset | User decision | More complex scheduler logic, better UX |

## SearchQuota Coexistence Decision

Per prior decisions, Phase 27 needs to decide: do web searches deduct credits or keep the separate SearchQuota system?

**Recommendation:** Keep SearchQuota separate for now. Rationale:
1. Search quotas are daily, credits are weekly/monthly -- different cadences
2. Credits represent "messages sent," search is a sub-feature within a message
3. Merging would require removing the SearchQuota model (breaking change)
4. Future per-model costs may also affect this -- keep it simple now

Mark as a platform_setting `search_deducts_credits: false` for future flexibility.

## Open Questions

1. **Exact credit cost per message**
   - What we know: configurable via platform_settings `default_credit_cost`
   - What's unclear: initial default value (1.0 is standard)
   - Recommendation: Default to `1.0`, admin can change at runtime

2. **Month length for monthly resets**
   - What we know: "monthly" reset policy exists
   - What's unclear: 30 days vs calendar month (Feb has 28/29 days)
   - Recommendation: Use `timedelta(days=30)` for simplicity; exact calendar months add complexity for minimal benefit

3. **Credit initialization for existing users**
   - What we know: Migration backfilled user_credits with balance=0
   - What's unclear: Should existing users get their tier's credit allocation?
   - Recommendation: Yes, update migration or add data migration to set balance to tier allocation for existing users

## Sources

### Primary (HIGH confidence)
- SQLAlchemy 2.0 async docs: `with_for_update()` support confirmed -- https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Existing codebase: all models, services, routers examined directly
- APScheduler 3.11.x docs: AsyncIOScheduler production-stable -- https://apscheduler.readthedocs.io/en/3.x/userguide.html

### Secondary (MEDIUM confidence)
- APScheduler PyPI: v3.11.2 is latest stable (Dec 2025) -- https://pypi.org/project/APScheduler/
- SQLAlchemy discussions on atomic balance updates -- https://github.com/sqlalchemy/sqlalchemy/discussions/6630

### Tertiary (LOW confidence)
- APScheduler 4.x status (not production-ready, API may change) -- https://github.com/agronholm/apscheduler

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in project except APScheduler (well-known, stable)
- Architecture: HIGH - follows existing codebase patterns exactly (services, routers, models, schemas)
- Pitfalls: HIGH - race conditions and streaming session issues are well-documented PostgreSQL patterns
- Scheduler: MEDIUM - APScheduler 3.x is stable but multi-instance deployment needs env var gating
- Rolling reset logic: MEDIUM - date arithmetic edge cases (month boundaries) need testing

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (30 days - stable domain, no fast-moving dependencies)
