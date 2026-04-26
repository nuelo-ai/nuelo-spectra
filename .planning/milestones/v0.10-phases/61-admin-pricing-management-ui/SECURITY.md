# SECURITY AUDIT — Phase 61: admin-pricing-management-ui

**Audit date:** 2026-04-25
**Auditor:** automated security audit (claude-sonnet-4-6)
**Branch:** feature/v0.10-streamline-pricing-configuration
**Result:** SECURED — 10/10 threats closed

---

## Threat Verification

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-61-01 | Tampering | mitigate | CLOSED | `billing_settings.py:108-111` verifies password before price mutations; `admin_billing.py:96-97` `Field(None, ge=100)` on both price fields; `admin_billing.py:128` `Field(..., ge=100)` on `CreditPackageUpdateRequest.price_cents` |
| T-61-02 | Tampering | mitigate | CLOSED | `billing_settings.py:219` calls `verify_password` before `reset_subscription_pricing`; `credit_packages.py:187` calls `verify_password` before `reset_credit_packages`; both resets are idempotent service-layer calls |
| T-61-03 | Elevation of Privilege | mitigate | CLOSED | `dependencies.py:247-282` — JWT signature, `is_admin` JWT claim, token type, sliding window timeout, and DB `is_admin` re-check all enforced in `get_current_admin_user`; `CurrentAdmin` applied to every endpoint in both routers |
| T-61-05 | DoS | mitigate | CLOSED | `billing_settings.py:219` and `credit_packages.py:187` — `verify_password` called as first action in both reset endpoints before any DB write |
| T-61-06 | Spoofing | mitigate | CLOSED | `billing_settings.py:110-111` raises `HTTPException(status_code=403)` on mismatch, not 401; same pattern at `credit_packages.py:72-73` and `billing_settings.py:219` |
| T-61-09 | Info Disclosure | mitigate | CLOSED | `PasswordConfirmDialog.tsx:39` ephemeral `useState("")`; `PasswordConfirmDialog.tsx:68` `type="password"`; state cleared on open (`line 41-45`) and on close (`line 47-51`); no `localStorage` write in file |
| T-61-10 | Spoofing | mitigate | CLOSED | `admin-api-client.ts:70-75` logout only on status 401, not 403; `useBilling.ts` throws `Error(body.detail)`; `page.tsx:234-239` "Incorrect password" sets `confirmError` inline without closing dialog or triggering logout |
| T-61-11 | Tampering | mitigate | CLOSED | `page.tsx:152-156` and `page.tsx:167-177` — all edit paths call `setConfirmAction` to queue intent; mutation fires only inside `handleConfirm(password)` at `page.tsx:188` after `PasswordConfirmDialog` delivers password |
| T-61-12 | Spoofing | mitigate | CLOSED | `PasswordConfirmDialog.tsx:68` `type="password"`; state resets on open and close; no `localStorage.setItem` for password anywhere in component or `admin-api-client.ts` |
| T-61-14 | DoS | mitigate | CLOSED | Each reset endpoint independently requires password per-request; `verify_password` called unconditionally before any state mutation at `billing_settings.py:219` and `credit_packages.py:187` |

---

## Accepted Risks

None declared.

## Transferred Risks

None declared.

## Unregistered Flags

None. All mutation paths covered by the threat register.

---

## Files Audited

- `backend/app/routers/admin/billing_settings.py`
- `backend/app/routers/admin/credit_packages.py`
- `backend/app/schemas/admin_billing.py`
- `backend/app/dependencies.py`
- `admin-frontend/src/components/shared/PasswordConfirmDialog.tsx`
- `admin-frontend/src/app/(admin)/billing-settings/page.tsx`
- `admin-frontend/src/hooks/useBilling.ts`
- `admin-frontend/src/lib/admin-api-client.ts`
