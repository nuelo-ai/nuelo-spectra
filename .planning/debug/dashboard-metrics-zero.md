---
status: diagnosed
trigger: "P31-T2 — Dashboard active today and credit used metrics show 0"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:00:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED - two independent bugs cause both metrics to be 0
test: completed
expecting: n/a
next_action: return diagnosis

## Symptoms

expected: Active Today shows count of users active today; Credit Used shows total credits consumed
actual: Both metrics show 0
errors: none reported
reproduction: visit admin dashboard
started: unknown

## Eliminated

- hypothesis: frontend reading wrong field from API response
  evidence: dashboard/page.tsx line 62 reads metrics.active_today and line 87 reads credit_summary.total_used — both field names match the backend schema
  timestamp: 2026-02-17

- hypothesis: last_login_at column missing from DB
  evidence: alembic migration a66a91bbb9fa_add_last_login_at_to_users.py confirms column exists; user model has it defined
  timestamp: 2026-02-17

## Evidence

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/dashboard.py lines 49-51
  found: active_today query filters User.last_login_at >= today_start
  implication: relies entirely on last_login_at being set on login

- timestamp: 2026-02-17
  checked: backend/app/routers/auth.py lines 151-153 (login endpoint)
  found: sets user.last_login_at = datetime.now(timezone.utc) then calls await db.flush() — NO await db.commit()
  implication: the flush writes to the transaction buffer but the session is never committed; get_db does not auto-commit; last_login_at stays NULL in DB permanently

- timestamp: 2026-02-17
  checked: backend/app/database.py get_db function
  found: yields session, then closes it in finally block — no commit call anywhere
  implication: confirms flush without commit = data never persists for last_login_at

- timestamp: 2026-02-17
  checked: backend/app/routers/admin/dashboard.py lines 89-96 (credit_used query)
  found: filters CreditTransaction.transaction_type == "deduction"
  implication: queries for a type that is never written

- timestamp: 2026-02-17
  checked: backend/app/services/credit.py (all usages of transaction_type)
  found: credit deductions are written as transaction_type="usage" (lines 47 and 99); other types used are "admin_adjustment", "auto_reset", "manual_reset", "tier_change" — "deduction" is never written
  implication: dashboard query for "deduction" always returns zero rows; SUM is NULL, coalesced to 0

## Resolution

root_cause: |
  Two independent bugs:
  1. ACTIVE_TODAY=0: login endpoint (auth.py:152) sets last_login_at then calls db.flush() but not db.commit(). The get_db session never auto-commits. last_login_at stays NULL for all users.
  2. CREDIT_USED=0: dashboard query (dashboard.py:91) filters transaction_type=="deduction" but credit service writes deductions as transaction_type="usage". Type string mismatch means the SUM always returns 0.
fix:
verification:
files_changed: []
