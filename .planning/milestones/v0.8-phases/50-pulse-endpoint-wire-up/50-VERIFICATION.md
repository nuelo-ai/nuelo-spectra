---
phase: 50-pulse-endpoint-wire-up
verified: 2026-03-07T16:30:00Z
status: human_needed
score: 11/11 must-haves verified
human_verification:
  - test: "Navigate to a collection with uploaded files and click 'Run Detection'. Observe full-page loading state with 4 animated steps."
    expected: "Page replaces content with full-page detection loading UI showing: Profiling data, Detecting anomalies, Analyzing trends, Generating signals — matching PULSE-04."
    why_human: "Frontend animation and page-replacement behavior cannot be verified by reading backend code."
  - test: "After detection completes (polling endpoint returns status='completed'), verify the app navigates to Detection Results page with generated Signals."
    expected: "User lands on Detection Results page populated with Signal cards from the completed run — matching PULSE-05."
    why_human: "Frontend navigation and signal rendering are not backend artifacts. The polling endpoint and signal data are verified; the UI consumption of that data requires a live browser test."
---

# Phase 50: Pulse Endpoint Wire-up Verification Report

**Phase Goal:** Wire PulseService to HTTP endpoints and register orphan-refund scheduler job so the full Pulse execution cycle is accessible via the API.
**Verified:** 2026-03-07T16:30:00Z
**Status:** human_needed — all automated checks passed; two frontend UX behaviors require human confirmation
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | PulseRunTriggerResponse schema exists with pulse_run_id, status, credit_cost fields | VERIFIED | `backend/app/schemas/pulse.py` lines 76-83: class defined with all three fields and `from_attributes=True` |
| 2  | SignalDetailResponse schema exists with all Signal model fields | VERIFIED | `backend/app/schemas/pulse.py` lines 60-73: id, title, severity, category, analysis, evidence, chart_data, chart_type, created_at — all present |
| 3  | PulseRunDetailResponse includes signals: list[SignalDetailResponse] = [] | VERIFIED | `backend/app/schemas/pulse.py` line 90: `signals: list[SignalDetailResponse] = []` alongside signal_count |
| 4  | run_detection() raises 402 with required+available balance dict in detail | VERIFIED | `backend/app/services/pulse.py` lines 78-85: dict detail with "detail", "required", "available" keys; pre-fetch of UserCredit balance at lines 70-74 |
| 5  | run_detection() raises 409 with active_run_id in detail dict | VERIFIED | `backend/app/services/pulse.py` lines 103-108: dict detail with "detail" and "active_run_id" keys |
| 6  | PULSE_ORPHAN_TIMEOUT_MINUTES env var is wired into Settings | VERIFIED | `backend/app/config.py` line 66: `pulse_orphan_timeout_minutes: int = 10` with inline comment |
| 7  | POST /collections/{id}/pulse returns 202 with pulse_run_id, status, credit_cost | VERIFIED | `backend/app/routers/collections.py` lines 403-438: endpoint with status_code=HTTP_202_ACCEPTED, returns PulseRunTriggerResponse |
| 8  | POST with insufficient credits returns 402 before any credits are spent | VERIFIED | service raises HTTPException(402) before any commit when deduction fails; router passes the exception through |
| 9  | POST with active run returns 409 with active_run_id | VERIFIED | service raises HTTPException(409) with active_run_id in dict detail |
| 10 | GET /collections/{id}/pulse-runs/{run_id} returns status field for polling loop | VERIFIED | `backend/app/routers/collections.py` lines 441-475: endpoint returns PulseRunDetailResponse with status field; collection_id cross-check present at line 467 |
| 11 | Orphan-refund job scans every 5 minutes and refunds + marks failed any stuck PulseRuns older than PULSE_ORPHAN_TIMEOUT_MINUTES | VERIFIED | `backend/app/scheduler.py` lines 97-164: process_orphan_refunds() with FOR UPDATE SKIP LOCKED, registered at IntervalTrigger(minutes=5) with id="pulse_orphan_refund_job" at lines 176-182 |

**Score:** 11/11 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/schemas/pulse.py` | PulseRunTriggerResponse, SignalDetailResponse, extended PulseRunDetailResponse | VERIFIED | All three classes present; PulseRunDetailResponse.signals field added without removing signal_count |
| `backend/app/services/pulse.py` | Enhanced 402/409 error bodies with balance context and active_run_id | VERIFIED | Dict-format HTTPException detail for both 402 and 409; UserCredit pre-fetch before deduction |
| `backend/app/config.py` | pulse_orphan_timeout_minutes setting | VERIFIED | Field present at line 66 with default 10 |
| `backend/app/routers/collections.py` | POST /{collection_id}/pulse and GET /{collection_id}/pulse-runs/{run_id} endpoints | VERIFIED | Both endpoints present; PulseRunCreate, PulseRunTriggerResponse, PulseRunDetailResponse, PulseService imported at lines 22-26 |
| `backend/app/scheduler.py` | process_orphan_refunds() job registered at 5-minute interval | VERIFIED | Function defined lines 97-164; registered in setup_scheduler() lines 176-182 |
| `backend/tests/test_pulse_endpoints.py` | Passing integration tests for trigger 202/402/409 and polling 200/completed | VERIFIED | 7 real tests (not stubs): TestTriggerPulse (202, 402, 409, 404) and TestGetPulseRun (pending, completed, ownership-bypass) |
| `backend/tests/test_orphan_refund.py` | Passing unit test for orphan refund job logic | VERIFIED | 3 real tests: refund-when-no-signals, skip-with-signals, rollback-on-error |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `backend/app/routers/collections.py` | `backend/app/schemas/pulse.py` | `import PulseRunCreate, PulseRunTriggerResponse, PulseRunDetailResponse` | WIRED | Line 22: explicit import; both schemas used in endpoint response_model and return statements |
| `backend/app/routers/collections.py` | `backend/app/services/pulse.py` | `PulseService.run_detection()` and `PulseService.get_pulse_run()` | WIRED | Lines 426-432 and 462-463: both service methods called; results used in responses |
| `backend/app/routers/collections.py` | `backend/app/services/collection.py` | `CollectionService.get_user_collection()` for ownership verification | WIRED | Lines 421 and 458: ownership check called before PulseService on both endpoints |
| `backend/app/routers/collections.py` (polling) | `PulseRun.collection_id` | Cross-check pulse_run.collection_id == collection_id to prevent ownership bypass | WIRED | Lines 467-468: explicit cross-check raises 404 on mismatch |
| `backend/app/scheduler.py` | `backend/app/models/pulse_run.py` + `signal.py` | SQL query joining PulseRun and Signal count for orphan detection | WIRED | Lines 124-133: `PulseRun.status.in_([...])` query; lines 138-143: signal count sub-query |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PULSE-01 | 50-01-PLAN.md | User can trigger Pulse detection on selected files via "Run Detection (N credits)" button showing configured flat credit cost | SATISFIED (backend) / NEEDS HUMAN (frontend) | POST /collections/{id}/pulse endpoint live, returns 202 with credit_cost. Frontend button and credit display require human verification. |
| PULSE-04 | 50-02-PLAN.md | User sees full-page detection loading state with 4 animated steps replacing entire page content | SATISFIED (backend) / NEEDS HUMAN (frontend) | GET polling endpoint returns status transitions (pending → profiling → analyzing → completed). Frontend animation is not a backend artifact. |
| PULSE-05 | 50-02-PLAN.md | After detection completes, user is navigated to Detection Results page with generated Signals | SATISFIED (backend) / NEEDS HUMAN (frontend) | GET endpoint returns signals list when status='completed'. Frontend navigation and Signal card rendering require human verification. |

No orphaned requirements: all three IDs claimed by plans and listed in REQUIREMENTS.md as Phase 50.

---

### Anti-Patterns Found

No anti-patterns detected in modified files.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TODO/FIXME/placeholder comments | — | — |
| — | — | No stub implementations (return null / return {}) | — | — |
| — | — | No handler-only-prevents-default patterns | — | — |

---

### Human Verification Required

#### 1. Full-page Detection Loading State (PULSE-04)

**Test:** Navigate to a collection with uploaded files. Click "Run Detection". Observe the page transition.
**Expected:** Entire page content is replaced by a full-page loading UI showing 4 animated steps in sequence: Profiling data, Detecting anomalies, Analyzing trends, Generating signals.
**Why human:** Frontend animation, page-replacement behavior, and step sequencing cannot be verified by reading backend code. The backend polling endpoint and status transitions are confirmed; only the UI rendering is unconfirmed.

#### 2. Detection Results Navigation and Signal Display (PULSE-05)

**Test:** After the detection loading state completes (polling confirms status='completed'), observe the navigation outcome and page content.
**Expected:** App navigates to the Detection Results page. Generated Signal cards are displayed, populated from the completed run's signals list.
**Why human:** Frontend routing (navigation on completion) and Signal card rendering are not backend artifacts. The GET endpoint returning signals is confirmed; the frontend consumption requires a live browser test.

---

### Gaps Summary

No gaps. All backend must-haves are fully implemented and wired. The two items flagged for human verification are frontend UX behaviors (PULSE-04 animation, PULSE-05 navigation) that depend on work from Phase 51 or earlier frontend phases — they are not regressions introduced by this phase. The backend contract (202 trigger, polling with status + signals list, orphan-refund scheduler) is complete.

---

_Verified: 2026-03-07T16:30:00Z_
_Verifier: Claude (gsd-verifier)_
