# Requirements: Spectra

**Defined:** 2026-04-22
**Core Value:** Accurate data analysis through correct, safe Python code generation

## v0.10 Requirements

Requirements for v0.10 Streamline Pricing Configuration. Each maps to roadmap phases.

### Subscription Pricing Config

- [ ] **SUB-01**: User classes config includes `has_plan` flag indicating whether a tier has a subscription pricing plan
- [ ] **SUB-02**: User classes config includes `price_cents` for tiers with `has_plan: true`
- [ ] **SUB-03**: Default subscription pricing is seeded to platform_settings on first startup when no value exists
- [ ] **SUB-04**: Stripe Products/Prices are auto-created on startup for subscription tiers missing a Stripe Price ID
- [ ] **SUB-05**: Admin can view all subscription pricing plans with their config defaults and current DB values
- [ ] **SUB-06**: Admin can edit subscription pricing plans (existing functionality)
- [ ] **SUB-07**: Admin can reset subscription pricing to config-file defaults

### Credit Package Config

- [ ] **PKG-01**: Default credit packages are defined in a config file (name, price_cents, credit_amount, display_order)
- [ ] **PKG-02**: Credit packages from config are seeded to DB on first startup when no packages exist
- [ ] **PKG-03**: Stripe Products/Prices are auto-created on startup for credit packages missing a Stripe Price ID
- [ ] **PKG-04**: Admin can view all credit packages from the database
- [ ] **PKG-05**: Admin can edit credit packages (name, price, credits, active status)
- [ ] **PKG-06**: Admin can reset credit packages to config-file defaults

### Safeguards

- [ ] **SAFE-01**: Existing admin-customized Stripe Price IDs in the database are preserved (startup sync fills gaps, never overwrites)
- [ ] **SAFE-02**: No manual Stripe Price ID configuration needed for initial deployment

## Out of Scope

| Feature | Reason |
|---------|--------|
| Admin creating new credit packages from scratch | Config-defined packages only; new packages require config file change |
| Admin deleting credit packages | Deactivate via is_active flag instead; preserves payment history references |
| Stripe Price ID in config files | Auto-created on startup; manual Stripe IDs defeat the purpose of this milestone |
| Per-environment pricing overrides | Single config per deploy; admin UI handles customization |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SUB-01 | — | Pending |
| SUB-02 | — | Pending |
| SUB-03 | — | Pending |
| SUB-04 | — | Pending |
| SUB-05 | — | Pending |
| SUB-06 | — | Pending |
| SUB-07 | — | Pending |
| PKG-01 | — | Pending |
| PKG-02 | — | Pending |
| PKG-03 | — | Pending |
| PKG-04 | — | Pending |
| PKG-05 | — | Pending |
| PKG-06 | — | Pending |
| SAFE-01 | — | Pending |
| SAFE-02 | — | Pending |

**Coverage:**
- v0.10 requirements: 15 total
- Mapped to phases: 0
- Unmapped: 15 ⚠️

---
*Requirements defined: 2026-04-22*
*Last updated: 2026-04-22 after initial definition*
