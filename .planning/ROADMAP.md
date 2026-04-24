# Roadmap: Spectra

## Milestones

- ✅ **v0.1 Beta MVP** - Phases 1-6 (shipped 2026-02-06)
- ✅ **v0.2 Intelligence & Integration** - Phases 7-13 (shipped 2026-02-10)
- ✅ **v0.3 Multi-file Conversation Support** - Phases 14-19 (shipped 2026-02-12)
- ✅ **v0.4 Data Visualization** - Phases 20-25 (shipped 2026-02-15)
- ✅ **v0.5 Admin Portal** - Phases 26-32 (shipped 2026-02-18)
- ✅ **v0.6 Docker and Dokploy Support** - Phases 33-37 (shipped 2026-02-21)
- ✅ **v0.7 API Services & MCP** - Phases 38-41 (shipped 2026-02-25)
- ✅ **v0.7.12 Spectra Pulse Mockup** - Phases 42-46 (shipped 2026-03-05)
- ✅ **v0.8 Spectra Pulse (Detection)** - Phases 47-52.1 (shipped 2026-03-10)
- ✅ **v0.8.1 UI Fixes & Enhancement** - Phases 53-54 (shipped 2026-03-10)
- ✅ **v0.9 Monetization** - Phases 55-59 (shipped 2026-04-14)
- 🚧 **v0.10 Streamline Pricing Configuration** - Phases 60-61 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>Phases 1-59 (v0.1 through v0.9) - SHIPPED</summary>

See MILESTONES.md for completed phase details.

</details>

### v0.10 Streamline Pricing Configuration

- [x] **Phase 60: Config-Driven Pricing & Startup Sync** - Add pricing fields to config, seed defaults to DB, auto-create Stripe Products/Prices on startup (completed 2026-04-23)
- [ ] **Phase 61: Admin Pricing Management UI** - Admin can view, edit, and reset subscription pricing and credit packages

## Phase Details

### Phase 60: Config-Driven Pricing & Startup Sync
**Goal**: Subscription pricing and credit packages are fully defined in config files and automatically provisioned in both the database and Stripe on first startup -- zero manual setup required
**Depends on**: Phase 59 (v0.9 Monetization complete)
**Requirements**: SUB-01, SUB-02, SUB-03, SUB-04, PKG-01, PKG-02, PKG-03, SAFE-01, SAFE-02
**Success Criteria** (what must be TRUE):
  1. user_classes.yaml includes `has_plan` and `price_cents` fields for subscription tiers, and the backend reads them correctly
  2. A config file defines default credit packages (name, price_cents, credit_amount, display_order) and the backend reads them correctly
  3. On first startup with an empty database, subscription pricing is seeded to platform_settings and credit packages are seeded to the credit_packages table from config defaults
  4. On startup, Stripe Products and Prices are auto-created for any subscription tier or credit package that is missing a Stripe Price ID -- no manual Stripe Dashboard configuration required
  5. Existing admin-customized Stripe Price IDs in the database are never overwritten by the startup sync (fills gaps only)
**Plans:** 3/3 plans complete
Plans:
- [x] 60-01-PLAN.md -- Extend user_classes.yaml with pricing fields and add get_credit_packages() loader
- [x] 60-02-PLAN.md -- Create pricing_sync.py service with seeding, Stripe sync, readiness check, and unit tests
- [x] 60-03-PLAN.md -- Wire pricing sync into lifespan() and add monetization toggle guard

### Phase 61: Admin Pricing Management UI
**Goal**: Admin can view, edit, and reset both subscription pricing and credit packages from the admin portal
**Depends on**: Phase 60
**Requirements**: SUB-05, SUB-06, SUB-07, PKG-04, PKG-05, PKG-06, UI-01, UI-02
**Success Criteria** (what must be TRUE):
  1. Admin can view all subscription pricing plans showing both config-file defaults and current database values side by side
  2. Admin can edit subscription pricing (price changes auto-create new Stripe Prices)
  3. Admin can reset subscription pricing back to config-file defaults with a single action
  4. Admin can view all credit packages from the database with their current configuration
  5. Admin can edit credit package details (name, price, credits, active status) with changes persisted to the database
  6. Admin can reset credit packages to config-file defaults with a single action
  7. Plan Selection page dynamically renders subscription plans from tiers with `has_plan: true` instead of hardcoded entries
  8. Billing page displays credit packages and pricing as defined in the database
**Plans:** 4 plans
**UI hint**: yes
Plans:
- [ ] 61-01-PLAN.md -- Backend API: schemas, billing-settings extensions, credit-packages router
- [ ] 61-02-PLAN.md -- Config features + dynamic /subscriptions/plans endpoint
- [ ] 61-03-PLAN.md -- Admin frontend: PasswordConfirmDialog + extended hooks
- [ ] 61-04-PLAN.md -- Admin frontend: billing-settings page refactor with view/edit/reset modals

## Progress

**Execution Order:**
Phases execute in numeric order: 60 → 61

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 60. Config-Driven Pricing & Startup Sync | 3/3 | Complete    | 2026-04-23 |
| 61. Admin Pricing Management UI | 0/4 | Not started | - |
