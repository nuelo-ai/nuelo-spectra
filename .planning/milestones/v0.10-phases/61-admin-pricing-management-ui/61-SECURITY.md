---
phase: 61
slug: admin-pricing-management-ui
status: verified
threats_open: 0
asvs_level: 2
created: 2026-04-26
---

# Phase 61 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Admin browser to Backend API | Admin-authenticated requests with JWT + password re-entry for mutations | Pricing data, admin password |
| Backend API to Stripe API | Server-side Stripe calls with secret key | Price IDs, customer data |
| Public browser to Backend API | Authenticated user requests via JWT | Plan pricing, features |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-61-01 | Tampering | PUT billing-settings, credit-packages | mitigate | Password re-entry via verify_password() before price mutations. Field(ge=100) prevents sub-$1 prices | closed |
| T-61-02 | Tampering | POST reset endpoints | mitigate | Password required for resets. Reset functions idempotent | closed |
| T-61-03 | Elevation of Privilege | All admin endpoints | mitigate | CurrentAdmin dependency: JWT signature, is_admin claim, token type, sliding window timeout, DB re-check | closed |
| T-61-04 | Info Disclosure | GET credit-packages (Stripe IDs) | accept | Stripe Price IDs are public lookup keys, only exposed to authenticated admins | closed |
| T-61-05 | DoS | POST reset endpoints | mitigate | Password verification first action before any DB write or Stripe call | closed |
| T-61-06 | Spoofing | Password verification | mitigate | Argon2 verification via pwdlib. 403 on mismatch (not 401), no logout triggered | closed |
| T-61-07 | Info Disclosure | GET /subscriptions/plans | accept | Plan pricing intentionally public to authenticated users | closed |
| T-61-08 | Tampering | user_classes.yaml | accept | Server-side only config, not editable via API. Requires deployment access | closed |
| T-61-09 | Info Disclosure | Password dialog | mitigate | Ephemeral useState, type="password", state resets on open and close, no localStorage persistence | closed |
| T-61-10 | Spoofing | 403 vs 401 handling | mitigate | Admin API client only triggers logout on 401. 403 shows inline error, dialog stays open | closed |
| T-61-11 | Tampering | Edit modals | mitigate | setConfirmAction opens dialog (no mutation). Mutation fires only after PasswordConfirmDialog delivers password | closed |
| T-61-12 | Spoofing | Password dialog state | mitigate | type="password", state cleared on open/close, JWT in localStorage but never password | closed |
| T-61-13 | Info Disclosure | Stripe Price IDs in cards | accept | Public lookup keys, only visible to authenticated admins | closed |
| T-61-14 | DoS | Reset to Defaults buttons | mitigate | Each reset unconditionally requires password re-entry, no session bypass | closed |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-61-01 | T-61-04, T-61-13 | Stripe Price IDs are public lookup keys, not secrets | gsd-security-auditor | 2026-04-26 |
| AR-61-02 | T-61-07 | Plan pricing is user-facing by design | gsd-security-auditor | 2026-04-26 |
| AR-61-03 | T-61-08 | YAML config is server-side only, requires deployment access to modify | gsd-security-auditor | 2026-04-26 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-26 | 14 | 14 | 0 | gsd-security-auditor (sonnet) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-26
