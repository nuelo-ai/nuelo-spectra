---
phase: 60-config-driven-pricing-startup-sync
fixed_at: 2026-04-23T00:00:00Z
review_path: .planning/phases/60-config-driven-pricing-startup-sync/60-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 60: Code Review Fix Report

**Fixed at:** 2026-04-23
**Source review:** .planning/phases/60-config-driven-pricing-startup-sync/60-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `monetization_enabled` fallback defaults to `True` (inverted security default)

**Files modified:** `backend/app/routers/admin/billing_settings.py`
**Commit:** 897c335
**Applied fix:** Changed the fallback string in `settings.get("monetization_enabled", ...)` from `"true"` to `"false"` to match the `DEFAULTS` dict in `platform_settings.py`, preventing monetization from being accidentally enabled on cache miss.

### WR-01: Cache invalidated before DB commit -- race window for stale cache reload

**Files modified:** `backend/app/routers/admin/billing_settings.py`
**Commit:** 1490af0
**Applied fix:** Swapped the order of `invalidate_cache()` and `await db.commit()` so the database commit completes before the cache is cleared, preventing concurrent requests from caching stale pre-commit data.

### WR-02: `upsert` called with `admin_id=None` but type annotation requires `UUID`

**Files modified:** `backend/app/services/platform_settings.py`
**Commit:** f1d27a9
**Applied fix:** Changed `admin_id` parameter type from `UUID` to `Optional[UUID]` with default `None`. Added guard to skip updating `updated_by` on existing rows when `admin_id is None`, supporting system-level seeding operations in `pricing_sync.py`.

### WR-03: Zero-price path skips Stripe creation but still writes to DB

**Files modified:** `backend/app/services/platform_settings.py`
**Commit:** bbdf009
**Applied fix:** Tightened `validate_setting` for price fields from `value < 0` to `value <= 0`, rejecting zero prices that would be written to DB without a corresponding Stripe Price object.

### WR-04: YAML load has no error handling -- crash on missing or malformed file

**Files modified:** `backend/app/services/user_class.py`
**Commit:** 301744a
**Applied fix:** Added explicit error handling in `_load_yaml()`: checks for missing config file (`FileNotFoundError`), malformed YAML (`yaml.YAMLError` caught and re-raised as `ValueError`), and missing `user_classes` key. Provides clear diagnostic messages instead of raw exceptions.

---

_Fixed: 2026-04-23_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
