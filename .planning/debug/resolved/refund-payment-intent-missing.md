---
status: awaiting_human_verify
trigger: "Refund button on admin Billing tab is greyed out because stripe_payment_intent_id is NULL in payment_history rows"
created: 2026-03-25T00:00:00Z
updated: 2026-03-25T00:00:00Z
---

## Current Focus

hypothesis: checkout.session.completed for subscriptions has payment_intent=None (Stripe subscription checkouts use invoices, not direct payment intents). The code uses session.get("payment_intent") which returns None. Additionally, invoice.paid with billing_reason=subscription_create is skipped entirely, so no handler ever saves the payment_intent for the initial subscription payment.
test: Confirmed by reading code — session.get("payment_intent") on line 556 of subscription.py gets None for subscription-mode checkouts; invoice.paid handler returns early on line 685 for subscription_create.
expecting: Fix by retrieving the invoice's payment_intent from Stripe in _handle_subscription_checkout
next_action: Implement fix in _handle_subscription_checkout to fetch payment_intent from the session's invoice

## Symptoms

expected: When a subscription payment succeeds via Stripe, the PaymentHistory row should have stripe_payment_intent_id populated so the admin can issue refunds against it.
actual: stripe_payment_intent_id is NULL for all payment_history rows. Refund button correctly disables itself (it needs a payment intent to refund against).
errors: None — the field is simply never populated.
reproduction: Subscribe a user -> check payment_history table -> stripe_payment_intent_id is NULL.
started: Never worked — the payment_intent extraction was never implemented correctly for subscription checkouts.

## Eliminated

(none)

## Evidence

- timestamp: 2026-03-25T00:00:00Z
  checked: backend/app/services/subscription.py — _handle_subscription_checkout (line 554-556)
  found: PaymentHistory created with stripe_payment_intent_id=session.get("payment_intent"). For subscription-mode checkouts, Stripe sets payment_intent to None on the session (payments go through invoices instead).
  implication: Initial subscription payments always get NULL payment_intent.

- timestamp: 2026-03-25T00:00:00Z
  checked: backend/app/services/subscription.py — handle_invoice_paid (line 678-685)
  found: invoice.paid handler explicitly skips billing_reason=="subscription_create" with early return. This means the invoice that DOES have the payment_intent is never processed for initial subscriptions.
  implication: Even though handle_invoice_paid correctly extracts invoice.get("payment_intent") on line 736, it never runs for initial subscription invoices.

- timestamp: 2026-03-25T00:00:00Z
  checked: All PaymentHistory creation sites (lines 405, 554, 621, 734, 812, 1217)
  found: Renewal invoices (line 734) and failed invoices (line 812) DO extract payment_intent correctly. But the system likely has no renewals yet, so all rows come from initial checkouts.
  implication: Root cause is specifically in the initial subscription checkout flow.

## Resolution

root_cause: In _handle_subscription_checkout, PaymentHistory is created with session.get("payment_intent") which is always None for Stripe subscription-mode checkouts. Stripe subscription payments are processed through invoices, not direct payment intents on the session. The checkout session has an "invoice" field instead, and the actual payment_intent lives on that invoice object. Additionally, the invoice.paid handler skips subscription_create invoices, so no handler ever saves the payment_intent for initial subscription payments.
fix: In _handle_subscription_checkout, after retrieving the Stripe subscription, also retrieve the invoice (from session["invoice"]) to get the payment_intent. Pass this to the PaymentHistory row instead of session.get("payment_intent").
verification: All 20 previously-passing tests still pass. 5 pre-existing test failures confirmed unrelated. Code review confirms client variable is in scope and invoice retrieval is guarded by try/except.
files_changed:
  - backend/app/services/subscription.py
