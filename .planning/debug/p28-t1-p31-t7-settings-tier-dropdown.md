---
status: diagnosed
trigger: "P28-T1 + P31-T7 — Settings tier dropdown hardcoded + credit reset policy should be per-tier"
created: 2026-02-17T00:00:00Z
updated: 2026-02-17T00:01:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: CONFIRMED — two independent bugs: (1) SettingsForm.tsx has three hardcoded SelectItems instead of fetching from /api/admin/tiers; (2) credit_reset_policy is a single DEFAULTS key in platform_settings.py, completely divorced from per-tier YAML definitions
test: read all relevant files — complete
expecting: confirmed
next_action: return diagnosis

## Symptoms

expected: Dropdown fetches tier list from /api/admin/tiers; credit reset policy displayed and editable per-tier
actual: Dropdown hardcoded to Free/Standard/Premium; credit reset policy shown as single global setting
errors: none (cosmetic/data issue)
reproduction: Open admin Settings page; observe tier dropdown options and credit reset policy field
started: Since settings page was built (phase 31)

## Eliminated

(none yet — first hypothesis confirmed)

## Evidence

- timestamp: 2026-02-17T00:01:00Z
  checked: admin-frontend/src/components/settings/SettingsForm.tsx lines 144-148
  found: Three hardcoded SelectItems: value="free" Free, value="standard" Standard, value="premium" Premium
  implication: Free Trial and Internal tiers defined in user_classes.yaml are invisible in the dropdown

- timestamp: 2026-02-17T00:01:00Z
  checked: backend/app/config/user_classes.yaml
  found: Five tiers defined — free_trial (Free Trial), free (Free), standard (Standard), premium (Premium), internal (Internal). Each has its own reset_policy: none/weekly/weekly/monthly/unlimited
  implication: The YAML is authoritative; frontend only shows 3 of 5 tiers

- timestamp: 2026-02-17T00:01:00Z
  checked: backend/app/routers/admin/tiers.py GET /tiers endpoint
  found: Reads all tiers from get_user_classes() and returns list[TierSummaryResponse] with name, display_name, credits, reset_policy, user_count for ALL five tiers
  implication: Backend already returns complete tier list including free_trial and internal — frontend simply does not call this endpoint for the dropdown

- timestamp: 2026-02-17T00:01:00Z
  checked: admin-frontend/src/hooks/useSettings.ts + hooks directory
  found: No useTiers hook exists. useSettings only fetches/patches /api/admin/settings. No hook fetches the tiers list for dropdown population.
  implication: Frontend has zero mechanism to dynamically populate the tier dropdown

- timestamp: 2026-02-17T00:01:00Z
  checked: backend/app/services/platform_settings.py DEFAULTS dict
  found: credit_reset_policy is a single top-level key with default "weekly". validate_setting() only accepts manual/weekly/monthly (missing "none" and "unlimited" which are valid YAML values). No per-tier reset_policy structure exists in platform_settings at all.
  implication: credit_reset_policy is architecturally global in the DB layer. The per-tier reset_policy in user_classes.yaml is only read by the credit reset scheduler/tier-change service — never surfaced in admin settings UI.

- timestamp: 2026-02-17T00:01:00Z
  checked: backend/app/schemas/platform_settings.py
  found: SettingsResponse and SettingsUpdateRequest both have a single credit_reset_policy: str field. TierSummaryResponse separately has reset_policy: str per tier.
  implication: The schema split already exists — tiers carry their own reset_policy in TierSummaryResponse, but the settings form never renders or edits them.

- timestamp: 2026-02-17T00:01:00Z
  checked: backend/app/services/admin/tiers.py change_user_tier()
  found: Uses class_config.get("reset_policy") from YAML directly during tier change — not platform_settings. So per-tier reset_policy is already applied during tier changes but not editable via admin UI.
  implication: The YAML reset_policy is the live source of truth for credits; the global credit_reset_policy in platform_settings appears to be a vestigial/redundant field that is not actually consumed by the tier-change logic.

## Resolution

root_cause: SettingsForm.tsx hardcodes three tier SelectItems instead of fetching from the existing /api/admin/tiers endpoint (which already returns all 5 tiers with display_name and reset_policy); simultaneously, credit_reset_policy is stored as a single global key in platform_settings and its admin UI is a single dropdown — but per-tier reset_policy already lives in user_classes.yaml and is already read by tier-change logic, making the global platform_settings key redundant and misleading.
fix: N/A (research only)
verification: N/A
files_changed: []
