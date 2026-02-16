# Phase 29: User Management - Research

**Researched:** 2026-02-16
**Domain:** Admin API endpoints for user listing, detail, account actions, and bulk operations
**Confidence:** HIGH

## Summary

Phase 29 builds admin API endpoints for comprehensive user management on the existing FastAPI + SQLAlchemy async + PostgreSQL stack. The codebase already has a mature admin pattern: `CurrentAdmin` dependency for auth, `log_admin_action` for audit logging, service-layer separation (routers -> services), and Pydantic v2 schemas with `from_attributes=True`. The existing admin module (`/api/admin/`) already includes auth, credits, settings, and tiers sub-routers, so this phase adds a `users` sub-router following identical patterns.

Key technical challenges: (1) the User model currently lacks `last_login` and `last_message_at` fields -- these must be added via migration; (2) hard-delete with cascade requires careful ordering across 7+ related tables; (3) token invalidation for immediate logout on deactivation requires a mechanism since the current JWT system is stateless (no token blacklist exists); (4) bulk operations need transaction management for atomicity while handling partial failures gracefully.

**Primary recommendation:** Add a `users` sub-router to the admin module following the exact same patterns as `admin/credits.py` and `admin/tiers.py`. Add `last_login_at` column to the User model. For token invalidation on deactivation, use a lightweight in-memory revocation set (similar to `_reset_cooldowns` pattern already in the codebase) keyed by user_id with TTL matching token expiry -- this is sufficient because setting `is_active=False` already blocks the `get_current_user` dependency on next token refresh.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### User listing & search
- Offset-based pagination with classic page numbers (page 1, 2, 3...)
- 20 users per page (fixed default)
- Search uses partial match (ILIKE contains) on email and name fields
- Multiple sort columns supported: signup date, last login, name, credit balance
- Filters: active/inactive status, user class (tier), signup date range

#### User detail view
- Summary counts: total files, total sessions, total messages
- Activity timeline computed on-the-fly from existing tables (messages, sessions grouped by month)
- Last login timestamp + last message sent tracked for activity visibility

#### Account actions -- Deactivation
- Deactivating a user triggers immediate logout -- all tokens invalidated, user kicked out immediately
- Deactivation is a soft flag (user record preserved, can be reactivated)

#### Account actions -- Deletion
- Hard delete immediately when admin confirms -- user and all their data (files, sessions, messages, credits) permanently removed
- Anonymized audit log entry created before deletion (e.g., "deleted_user_123" replaces actual email/name in audit references)
- Deletion confirmation requires a random 6-character alphanumeric challenge code displayed to admin; admin must manually type it to confirm
- Paste disabled on the confirmation text field to ensure deliberate action (frontend concern - Phase 31)

#### Account actions -- Tier change
- Changing a user's tier always resets their credit balance to the new tier's allocation (clean slate)
- This applies to both upgrades and downgrades

#### Account actions -- Password reset
- Admin triggers password reset which sends a reset email to the user via existing SMTP service
- Admin does not set the password directly

#### Bulk operations
- Full bulk actions supported: bulk activate/deactivate, bulk tier change, bulk credit adjustment, bulk delete
- User selection via checkboxes on the user list (manual selection, not filter-based)
- Bulk credit adjustment supports both modes: set exact amount OR add/deduct a delta from current balance
- Bulk delete uses the same 6-char confirmation challenge as individual delete (paste disabled -- frontend concern)

### Claude's Discretion
- API endpoint structure (single detail endpoint vs split endpoints for profile/activity)
- Exact query optimization for activity timeline aggregation
- Error response format and validation patterns
- How token invalidation is implemented for immediate logout on deactivation

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| USER-01 | Admin can list all registered users with pagination | Offset-based pagination with page numbers, 20/page. Use SQLAlchemy `offset`/`limit` on `select(User)`. Sort by multiple columns. |
| USER-02 | Admin can search users by email or name | ILIKE contains search: `User.email.ilike(f"%{q}%")` combined with first_name/last_name using OR. |
| USER-03 | Admin can filter users by active/inactive status, user class, and signup date | Chain `.where()` clauses: `is_active`, `user_class`, `created_at` range filters. All optional. |
| USER-04 | Admin can view user profile info (name, email, signup date, last login) | Requires adding `last_login_at` column to User model + migration. Returned in user detail endpoint. |
| USER-05 | Admin can view user account status (active/inactive) | `is_active` field already on User model. Include in detail response. |
| USER-06 | Admin can view user's current tier (user class) | `user_class` field already on User model. Include in detail response with tier display name from `get_class_config()`. |
| USER-07 | Admin can view user's credit balance and usage history | Join with `UserCredit` for balance. Use existing `CreditService.get_transaction_history()` for usage history. |
| USER-08 | Admin can view user's file count and chat session count | Aggregate counts: `select(func.count(File.id)).where(File.user_id == user_id)` and same for ChatSession. Also total messages count. |
| USER-09 | Admin can activate or deactivate a user account | Set `User.is_active` flag. On deactivation, invalidate tokens for immediate logout. |
| USER-10 | Admin can trigger password reset for a user (sends reset email to user) | Reuse existing `create_reset_token()` + `send_password_reset_email()` from `services/email.py`. |
| USER-11 | Admin can change a user's tier (user class) | Reuse existing `change_user_tier()` from `services/admin/tiers.py`. Already handles credit reset. |
| USER-12 | Admin can adjust a user's credit balance (with reason/note) | Reuse existing `CreditService.admin_adjust()`. For bulk: support both "set exact" and "add/deduct delta" modes. |
| USER-13 | Admin can delete a user account (with confirmation, proper cascade) | Hard delete with DB-level CASCADE. Anonymize audit logs first. Backend generates 6-char challenge code, validates admin's response. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | (existing) | API framework | Already used for all routes |
| SQLAlchemy 2.x | (existing) | Async ORM with mapped_column | Already used for all models |
| Pydantic v2 | (existing) | Request/response schemas | Already used with `from_attributes=True` |
| Alembic | (existing) | Database migrations | Already used for schema changes |
| PostgreSQL | (existing) | Database with ILIKE, JSONB | Already the database |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiosmtplib | (existing) | Async email sending | Password reset email trigger |
| pwdlib | (existing) | Password hashing (Argon2) | Not directly needed (admin doesn't set passwords) |

### Alternatives Considered
None needed -- this phase uses 100% existing stack with no new dependencies.

**Installation:**
No new packages required.

## Architecture Patterns

### Recommended Project Structure
```
backend/app/
  routers/admin/
    users.py             # NEW: User management endpoints
    __init__.py           # UPDATE: Register users sub-router
  services/admin/
    users.py             # NEW: User management service layer
  schemas/
    admin_users.py       # NEW: Request/response schemas for user management
```

### Pattern 1: Admin Router + Service Layer (existing pattern)
**What:** Router handles HTTP concerns (request parsing, response formatting, audit logging). Service handles business logic (DB queries, validation).
**When to use:** All admin endpoints follow this pattern.
**Example:**
```python
# Router pattern (from admin/credits.py and admin/tiers.py)
@router.get("/", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    current_admin: CurrentAdmin,
    page: int = Query(default=1, ge=1),
    search: str | None = Query(default=None),
    # ... filters
) -> UserListResponse:
    result = await user_service.list_users(db, page=page, search=search, ...)
    return result
```

### Pattern 2: Offset Pagination Response
**What:** Return paginated results with total count, page info, and items.
**When to use:** User listing endpoint.
**Example:**
```python
class UserListResponse(BaseModel):
    users: list[UserSummary]
    total: int
    page: int
    per_page: int
    total_pages: int
```

### Pattern 3: Audit-Then-Commit (existing pattern)
**What:** Perform action, log audit entry, then commit once. The `log_admin_action` function adds to the session but does NOT commit.
**When to use:** Every mutating admin action.
**Example:**
```python
# Perform action
await user_service.deactivate_user(db, user_id)
# Log audit (adds to session, no commit)
await log_admin_action(db, admin_id=..., action="deactivate_user", ...)
# Single commit covers both action + audit
await db.commit()
```

### Pattern 4: Bulk Operations with Transaction
**What:** Process multiple user IDs in a single transaction. Validate all upfront, then apply.
**When to use:** Bulk activate, deactivate, tier change, credit adjust, delete.
**Example:**
```python
@router.post("/bulk/deactivate")
async def bulk_deactivate(
    body: BulkUserActionRequest,  # user_ids: list[UUID]
    db: DbSession,
    current_admin: CurrentAdmin,
    request: Request,
):
    results = await user_service.bulk_deactivate(db, body.user_ids)
    # Audit log
    await log_admin_action(db, admin_id=..., action="bulk_deactivate", ...)
    await db.commit()
    return results
```

### Pattern 5: Challenge Code for Destructive Actions
**What:** Two-step API flow for delete: (1) GET generates a random 6-char alphanumeric code, (2) POST/DELETE requires that code in the request body.
**When to use:** Individual and bulk delete.
**Example:**
```python
# Step 1: Generate challenge
@router.post("/users/{user_id}/delete-challenge")
async def generate_delete_challenge(user_id: UUID, ...) -> DeleteChallengeResponse:
    code = generate_challenge_code()  # 6 chars alphanumeric
    # Store in-memory or short-lived cache keyed by (admin_id, user_id)
    return DeleteChallengeResponse(challenge_code=code, expires_in=300)

# Step 2: Confirm delete with code
@router.delete("/users/{user_id}")
async def delete_user(user_id: UUID, body: DeleteConfirmRequest, ...):
    # body.challenge_code must match stored code
    verify_challenge_code(current_admin.id, user_id, body.challenge_code)
    await user_service.delete_user(db, user_id)
```

### Anti-Patterns to Avoid
- **Loading all users without pagination:** Always use LIMIT/OFFSET. The User table can grow indefinitely.
- **N+1 queries in user listing:** Do NOT load credits/file counts per user in a loop. Use JOINs or subqueries in a single query.
- **Committing inside service functions:** Follow existing pattern where services flush but callers commit.
- **Deleting without anonymizing audit logs first:** Must anonymize audit log references BEFORE deleting the user, otherwise FK constraints or data loss.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password reset email | Custom email logic | Existing `create_reset_token()` + `send_password_reset_email()` | Already handles SMTP/dev mode, token hashing, template rendering |
| Tier change + credit reset | Custom tier logic | Existing `change_user_tier()` from `services/admin/tiers.py` | Already handles atomic tier change with credit reset |
| Credit adjustment | Custom credit logic | Existing `CreditService.admin_adjust()` | Already handles locking, transaction logging, floor at zero |
| Audit logging | Custom audit logic | Existing `log_admin_action()` | Already handles entry creation within caller's transaction |
| Admin auth check | Custom auth decorator | Existing `CurrentAdmin` dependency | Already checks JWT + DB is_admin flag (defense in depth) |

**Key insight:** This phase is primarily about composing existing services into new admin endpoints. The tier change, credit adjustment, password reset, and audit logging are all already implemented. The new work is: user listing/search/filter queries, user detail aggregation, deactivation with token invalidation, hard delete with cascade, and bulk operation orchestration.

## Common Pitfalls

### Pitfall 1: Missing `last_login_at` Column
**What goes wrong:** The User model has no `last_login_at` field. Without it, USER-04 cannot be satisfied.
**Why it happens:** The original User model was designed for basic auth without admin visibility.
**How to avoid:** Add `last_login_at` (nullable DateTime) to User model + Alembic migration. Update the login endpoint (`auth.py`) to set `user.last_login_at = datetime.now(timezone.utc)` on successful login. Also add `last_message_at` or compute it on-the-fly from `chat_messages`.
**Warning signs:** N/A -- must be addressed in planning.

### Pitfall 2: Stateless JWT Cannot Be Revoked
**What goes wrong:** Deactivating a user sets `is_active=False`, but their existing JWT access token remains valid until expiry (30 minutes). The user is NOT immediately kicked out.
**Why it happens:** JWT is stateless. There is no token blacklist or revocation mechanism.
**How to avoid:** Two complementary approaches:
1. The `get_current_user` dependency already checks `is_active` on every request. Setting `is_active=False` will block the user on their next API call.
2. For "immediate logout" requirement: add a lightweight in-memory revocation set (`_deactivated_users: set[UUID]`) checked in `get_current_user`. This provides instant invalidation. The set can be TTL-limited to `access_token_expire_minutes` (30 min) since after that the token expires naturally.
**Warning signs:** User can still use the app for up to 30 minutes after deactivation without this.

### Pitfall 3: Hard Delete Cascade Ordering
**What goes wrong:** Deleting a user with `db.delete(user)` triggers ORM cascade, but audit log entries reference user via `admin_id` FK (SET NULL). If the user being deleted is also an admin who performed actions, those audit logs need handling.
**Why it happens:** Complex FK relationships across tables.
**How to avoid:** The database schema already uses appropriate FK actions:
- `files.user_id` -> CASCADE (files deleted with user)
- `chat_messages.user_id` -> CASCADE
- `chat_sessions.user_id` -> CASCADE
- `user_credits.user_id` -> CASCADE
- `credit_transactions.user_id` -> CASCADE
- `search_quotas.user_id` -> CASCADE
- `admin_audit_log.admin_id` -> SET NULL (preserves audit log)
- `credit_transactions.admin_id` -> SET NULL
- `invitations.invited_by` -> SET NULL

So a simple `await db.delete(user)` + `await db.flush()` should work because PostgreSQL handles CASCADE at the DB level. BUT: must anonymize audit log entries (replace target_id/details containing user info) BEFORE the delete, per the locked decision.
**Warning signs:** Test with a user who has files, sessions, messages, credits, and transactions.

### Pitfall 4: N+1 in User Listing
**What goes wrong:** Loading user list, then querying credit balance per user in a loop.
**Why it happens:** Naive implementation fetches credits/counts separately.
**How to avoid:** Use a single query with LEFT JOINs and subqueries for file count, session count, and credit balance. Example:
```python
from sqlalchemy import func, select
file_count = select(func.count(File.id)).where(File.user_id == User.id).correlate(User).scalar_subquery()
query = select(User, UserCredit.balance, file_count.label("file_count"))
```
**Warning signs:** Slow user listing with many users.

### Pitfall 5: Activity Timeline Performance
**What goes wrong:** Computing monthly activity (messages + sessions grouped by month) on-the-fly for a user with thousands of messages can be slow.
**Why it happens:** Full table scan with GROUP BY on large tables.
**How to avoid:** Index on `chat_messages.created_at` already exists implicitly through query patterns. The activity endpoint should limit to recent months (e.g., last 12 months) and use `date_trunc('month', created_at)` for grouping. Consider a separate endpoint for activity data so the main detail endpoint stays fast.
**Warning signs:** Slow response time on user detail for active users.

### Pitfall 6: Bulk Delete Without Challenge Verification
**What goes wrong:** Accidentally deleting users without confirmation.
**Why it happens:** Bulk operations process multiple users, making errors more impactful.
**How to avoid:** Bulk delete requires the same 6-char challenge code pattern. The backend generates one code for the entire bulk operation (not per user).
**Warning signs:** Missing challenge verification in bulk delete endpoint.

## Code Examples

### User Listing Query with Search, Filter, Sort, Pagination
```python
# Source: Codebase patterns from admin/credits.py + admin/tiers.py
from sqlalchemy import func, select, or_

async def list_users(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    is_active: bool | None = None,
    user_class: str | None = None,
    signup_after: datetime | None = None,
    signup_before: datetime | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict:
    # Base query
    query = select(User)

    # Search: ILIKE on email, first_name, last_name
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                User.email.ilike(search_term),
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term),
            )
        )

    # Filters
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if user_class:
        query = query.where(User.user_class == user_class)
    if signup_after:
        query = query.where(User.created_at >= signup_after)
    if signup_before:
        query = query.where(User.created_at <= signup_before)

    # Count total (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Sort
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    users = list(result.scalars().all())

    return {
        "users": users,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }
```

### User Detail with Aggregated Counts
```python
# Source: Codebase patterns
from sqlalchemy import func, select

async def get_user_detail(db: AsyncSession, user_id: UUID) -> dict:
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    # Aggregate counts in parallel subqueries
    file_count = (await db.execute(
        select(func.count(File.id)).where(File.user_id == user_id)
    )).scalar()

    session_count = (await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user_id)
    )).scalar()

    message_count = (await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.user_id == user_id)
    )).scalar()

    # Credit balance
    credit_result = await db.execute(
        select(UserCredit).where(UserCredit.user_id == user_id)
    )
    credit = credit_result.scalar_one_or_none()

    return {
        "user": user,
        "file_count": file_count or 0,
        "session_count": session_count or 0,
        "message_count": message_count or 0,
        "credit_balance": float(credit.balance) if credit else 0.0,
    }
```

### Activity Timeline Aggregation
```python
# Source: PostgreSQL date_trunc pattern
from sqlalchemy import func, select, cast, Date

async def get_user_activity_timeline(
    db: AsyncSession, user_id: UUID, months: int = 12
) -> list[dict]:
    """Get monthly message and session counts for activity timeline."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=months * 30)

    # Messages by month
    msg_query = (
        select(
            func.date_trunc("month", ChatMessage.created_at).label("month"),
            func.count(ChatMessage.id).label("message_count"),
        )
        .where(ChatMessage.user_id == user_id)
        .where(ChatMessage.created_at >= cutoff)
        .group_by(func.date_trunc("month", ChatMessage.created_at))
        .order_by(func.date_trunc("month", ChatMessage.created_at))
    )
    msg_result = await db.execute(msg_query)

    # Sessions by month
    sess_query = (
        select(
            func.date_trunc("month", ChatSession.created_at).label("month"),
            func.count(ChatSession.id).label("session_count"),
        )
        .where(ChatSession.user_id == user_id)
        .where(ChatSession.created_at >= cutoff)
        .group_by(func.date_trunc("month", ChatSession.created_at))
        .order_by(func.date_trunc("month", ChatSession.created_at))
    )
    sess_result = await db.execute(sess_query)

    # Merge into timeline
    # ... merge msg and session results by month
```

### Deactivation with Token Invalidation
```python
# Source: Codebase patterns (dependencies.py check + in-memory set)
import threading
from datetime import datetime, timezone

# Module-level revocation set: user_id -> deactivated_at timestamp
_deactivated_users: dict[UUID, float] = {}
_deactivation_lock = threading.Lock()

def mark_user_deactivated(user_id: UUID, ttl_seconds: int = 1800) -> None:
    """Add user to revocation set. TTL matches access token expiry."""
    with _deactivation_lock:
        _deactivated_users[user_id] = time.time()
        # Cleanup expired entries
        cutoff = time.time() - ttl_seconds
        expired = [uid for uid, ts in _deactivated_users.items() if ts < cutoff]
        for uid in expired:
            del _deactivated_users[uid]

def is_user_deactivated(user_id: UUID) -> bool:
    """Check if user was recently deactivated."""
    return user_id in _deactivated_users
```

### Hard Delete with Audit Anonymization
```python
async def delete_user(db: AsyncSession, user_id: UUID, admin_id: UUID) -> None:
    """Hard delete a user after anonymizing audit references."""
    # Step 1: Anonymize audit log entries referencing this user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    anon_label = f"deleted_user_{str(user_id)[:8]}"

    # Create deletion audit entry BEFORE deleting (with anonymized reference)
    await log_admin_action(
        db, admin_id=admin_id, action="delete_user",
        target_type="user", target_id=str(user_id),
        details={"anonymized_as": anon_label, "email_domain": user.email.split("@")[1]},
    )

    # Step 2: Delete user (CASCADE handles related records)
    await db.delete(user)
    await db.flush()
```

### Challenge Code Generation
```python
import secrets
import string
import time

# In-memory challenge store: (admin_id, scope_key) -> (code, expires_at)
_challenge_store: dict[tuple, tuple[str, float]] = {}

def generate_challenge_code(admin_id: UUID, scope_key: str, ttl: int = 300) -> str:
    """Generate a 6-char alphanumeric challenge code."""
    chars = string.ascii_letters + string.digits
    code = "".join(secrets.choice(chars) for _ in range(6))
    _challenge_store[(admin_id, scope_key)] = (code, time.time() + ttl)
    return code

def verify_challenge_code(admin_id: UUID, scope_key: str, submitted: str) -> bool:
    """Verify and consume a challenge code (single-use)."""
    key = (admin_id, scope_key)
    entry = _challenge_store.pop(key, None)
    if entry is None:
        return False
    code, expires_at = entry
    if time.time() > expires_at:
        return False
    return secrets.compare_digest(code, submitted)
```

## Discretionary Recommendations

### API Endpoint Structure (Claude's Discretion)
**Recommendation: Split into two endpoints** -- one for user profile/summary and one for activity timeline.

Rationale:
- The profile + summary counts query is fast (simple joins/subqueries).
- The activity timeline requires GROUP BY with date_trunc across potentially large tables.
- Keeping them separate lets the frontend load the profile instantly and lazy-load the activity chart.
- This also matches the pattern of the credit endpoints (balance vs transaction history are separate).

Proposed endpoints:
- `GET /api/admin/users/{user_id}` -- profile, status, tier, credit balance, summary counts
- `GET /api/admin/users/{user_id}/activity` -- monthly activity timeline (messages, sessions by month)

### Token Invalidation Approach (Claude's Discretion)
**Recommendation: In-memory revocation set + existing `is_active` check.**

The `get_current_user` dependency in `dependencies.py` already checks `is_active` on every request. Setting `is_active=False` in the database means:
1. Any new `get_current_user` call will reject the user (401 "User account is inactive").
2. Token refresh will also be blocked (auth.py refresh endpoint checks `is_active`).

The gap is that a user with a valid access token could make API calls for up to 30 minutes (token expiry) before being blocked. To close this gap, add a lightweight in-memory set of recently-deactivated user IDs, checked in `get_current_user`. This avoids the complexity of a Redis-backed blacklist while providing near-instant invalidation.

The same pattern is already used in the codebase for `_reset_cooldowns` (in auth.py) and `_login_attempts` (in admin/auth.py).

### Query Optimization for Activity Timeline (Claude's Discretion)
**Recommendation:** Use two separate GROUP BY queries (messages by month, sessions by month) and merge in Python. This is simpler and more maintainable than a complex UNION or CTE. Limit to last 12 months to bound query cost.

### Error Response Format (Claude's Discretion)
**Recommendation:** Follow existing FastAPI HTTPException pattern with `detail` string or dict. For bulk operations, return a result object with per-user success/failure status:
```python
class BulkActionResult(BaseModel):
    succeeded: int
    failed: int
    errors: list[BulkActionError]  # user_id + error message

class BulkActionError(BaseModel):
    user_id: UUID
    error: str
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `orm_mode=True` | Pydantic v2 `from_attributes=True` | Pydantic v2 (2023) | Already using v2 in codebase |
| Sync SQLAlchemy | Async SQLAlchemy 2.x with `mapped_column` | SA 2.0 (2023) | Already using async in codebase |
| N/A | `with_for_update()` for row locking | N/A | Already used in credit/tier services |

## Open Questions

1. **Sort by credit balance requires JOIN**
   - What we know: Sorting user list by credit balance requires joining with `user_credits` table.
   - What's unclear: Whether to always JOIN with user_credits (even when not sorting by balance) or only when needed.
   - Recommendation: Always LEFT JOIN with user_credits in the listing query. The overhead is minimal (user_credits has a unique index on user_id), and it provides the balance column for display in the user list summary.

2. **Physical file deletion on user delete**
   - What we know: User's files have `file_path` pointing to stored files on disk. DB records cascade-delete, but physical files remain.
   - What's unclear: Whether to also delete physical files from the upload directory.
   - Recommendation: Yes, delete physical files. Before the DB delete, query all file paths for the user and remove them from disk. Handle missing files gracefully (they may have been cleaned up already).

3. **Bulk operation size limits**
   - What we know: Bulk operations accept a list of user IDs.
   - What's unclear: Maximum batch size.
   - Recommendation: Cap at 100 user IDs per bulk request to prevent timeout issues. Validate with Pydantic `Field(max_length=100)` on the user_ids list.

4. **last_message_at tracking**
   - What we know: The context requires "last message sent" for activity visibility.
   - What's unclear: Whether to add a denormalized column to User or compute on-the-fly.
   - Recommendation: Compute on-the-fly via `select(func.max(ChatMessage.created_at)).where(ChatMessage.user_id == user_id)` in the detail endpoint. Adding a denormalized column would require updating it on every message, which adds complexity to the chat flow. The detail endpoint is admin-only and low-traffic, so the extra query is acceptable.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `backend/app/models/user.py` - User model structure
- Codebase analysis: `backend/app/dependencies.py` - CurrentAdmin dependency with is_active check
- Codebase analysis: `backend/app/routers/admin/credits.py` - Admin endpoint patterns
- Codebase analysis: `backend/app/routers/admin/tiers.py` - Tier change with audit logging
- Codebase analysis: `backend/app/services/admin/tiers.py` - Atomic tier change + credit reset
- Codebase analysis: `backend/app/services/credit.py` - CreditService patterns
- Codebase analysis: `backend/app/services/email.py` - Password reset email sending
- Codebase analysis: `backend/app/services/admin/audit.py` - Audit logging utility
- Codebase analysis: `backend/app/models/admin_audit_log.py` - Audit log FK constraints (SET NULL)
- Codebase analysis: All model files - CASCADE/SET NULL FK patterns

### Secondary (MEDIUM confidence)
- SQLAlchemy 2.x async patterns: Confirmed by codebase usage of `select()`, `with_for_update()`, `mapped_column()`
- PostgreSQL `date_trunc` for monthly aggregation: Standard PostgreSQL function

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using 100% existing codebase technologies, no new dependencies
- Architecture: HIGH - Following exact patterns from existing admin endpoints (credits, tiers)
- Pitfalls: HIGH - Identified from direct codebase analysis (missing columns, FK constraints, JWT statelesness)

**Research date:** 2026-02-16
**Valid until:** 2026-03-16 (stable -- internal codebase patterns)
