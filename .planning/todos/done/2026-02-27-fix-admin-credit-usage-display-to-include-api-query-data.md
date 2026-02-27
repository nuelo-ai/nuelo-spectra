---
created: 2026-02-27T14:24:54.189Z
title: Fix admin credit usage display to include API query data
area: api
files:
  - backend/app/services/admin/users.py:259-322
  - backend/app/services/admin/users.py:209-256
  - admin-frontend/src/components/users/UserDetailTabs.tsx:500-571
  - admin-frontend/src/components/users/UserDetailTabs.tsx:576-608
  - backend/app/models/credit_transaction.py
  - backend/app/services/credit.py:21-102
  - backend/app/routers/api_v1/query.py:74
---

## Problem

Admin-frontend Activity Tab and User Detail Stats only reflect chat session data (`chat_messages`, `chat_sessions`). API queries via `POST /v1/chat/query` never create `ChatSession` or `ChatMessage` rows — they only write to `api_usage_logs` and `credit_transactions`. This means:

- **Activity Tab** (`get_user_activity()` in `users.py:259`): monthly breakdown shows only `message_count` and `session_count`. A user making 100 API calls per month shows zero activity.
- **Sessions Tab stats** (`get_user_detail()` in `users.py:209`): `session_count` and `message_count` exclude API usage. `last_message_at` uses `max(ChatMessage.created_at)` — a pure API user shows "No session activity yet."
- **Credits tab transaction history**: `credit_transactions` has no `source` or `api_key_id` field, so chat vs API deductions are indistinguishable.

Public frontend is NOT affected — sidebar balance (`user_credits.balance`) is decremented by both paths, and per-key "Credit Usage" on API key card (`api_keys.total_credits_used`) is correct by design.

## Solution

Three fixes in priority order:

**Fix 1 — Activity Tab (no migration)**
- In `get_user_activity()` (`users.py:259`): add third query counting `api_usage_logs` grouped by month for the same `user_id`
- Merge `api_query_count` into monthly activity map
- Add `api_query_count` to response schema (`UserActivityResponse`)
- Add "API Queries" column to `ActivityTab` table in `UserDetailTabs.tsx:548`

**Fix 2 — User Detail Stats (no migration)**
- In `get_user_detail()` (`users.py:209`): add `api_query_count` aggregate from `COUNT(api_usage_logs.id) WHERE user_id = ?`
- Fix `last_message_at` to `MAX(COALESCE(chat_last, api_last))` across both tables
- Add "API Queries" stat card in `SessionsTab` in `UserDetailTabs.tsx:586`

**Fix 3 — Credit transaction source attribution (requires Alembic migration)**
- Add `api_key_id: UUID | None` column to `credit_transactions` table
- Thread through `CreditService.deduct_credit()` as optional param
- Pass `api_key_id` from `query.py:74` when calling deduct; leave `None` for chat path
- In Credits tab, label API-sourced transactions with key prefix

Fixes 1+2 are safe, read-only additions — plan together in one phase. Fix 3 is a separate phase due to DB migration risk.
