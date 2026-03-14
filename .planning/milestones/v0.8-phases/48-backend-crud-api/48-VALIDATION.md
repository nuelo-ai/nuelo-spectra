---
phase: 48
slug: backend-crud-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 48 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0.0 + pytest-asyncio >=0.23.0 |
| **Config file** | backend/pyproject.toml |
| **Quick run command** | `cd backend && python -m pytest tests/test_collections.py -x` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_collections.py -x`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 48-01-01 | 01 | 1 | COLL-01 | unit | `cd backend && python -m pytest tests/test_collections.py::test_create_collection -x` | No -- Wave 0 | pending |
| 48-01-02 | 01 | 1 | COLL-01 | unit | `cd backend && python -m pytest tests/test_collections.py::test_create_collection_free_tier_403 -x` | No -- Wave 0 | pending |
| 48-01-03 | 01 | 1 | COLL-02 | unit | `cd backend && python -m pytest tests/test_collections.py::test_list_collections -x` | No -- Wave 0 | pending |
| 48-01-04 | 01 | 1 | COLL-03 | unit | `cd backend && python -m pytest tests/test_collections.py::test_collection_detail -x` | No -- Wave 0 | pending |
| 48-01-05 | 01 | 1 | COLL-04 | unit | `cd backend && python -m pytest tests/test_collections.py::test_update_collection -x` | No -- Wave 0 | pending |
| 48-02-01 | 02 | 1 | FILE-01 | unit | `cd backend && python -m pytest tests/test_collections.py::test_upload_file_to_collection -x` | No -- Wave 0 | pending |
| 48-02-02 | 02 | 1 | FILE-02 | manual | Verify File.data_summary accessible via file detail | N/A | pending |
| 48-02-03 | 02 | 1 | FILE-03 | manual | Frontend-only state -- no backend test | N/A | pending |
| 48-02-04 | 02 | 1 | FILE-04 | unit | `cd backend && python -m pytest tests/test_collections.py::test_remove_file_from_collection -x` | No -- Wave 0 | pending |
| 48-03-01 | 03 | 1 | REPORT-01 | unit | `cd backend && python -m pytest tests/test_collections.py::test_list_reports -x` | No -- Wave 0 | pending |
| 48-03-02 | 03 | 1 | REPORT-02 | unit | `cd backend && python -m pytest tests/test_collections.py::test_report_detail -x` | No -- Wave 0 | pending |
| 48-03-03 | 03 | 1 | REPORT-03 | unit | `cd backend && python -m pytest tests/test_collections.py::test_download_report -x` | No -- Wave 0 | pending |
| 48-03-04 | 03 | 1 | REPORT-04 | manual | Frontend-only -- no backend PDF endpoint | N/A | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_collections.py` — stubs for COLL-01 through COLL-04, FILE-01, FILE-04, REPORT-01 through REPORT-03
- [ ] Test for WorkspaceAccess dependency (403 for free tier users)
- [ ] Test for max_active_collections limit enforcement
- [ ] Test for file link duplicate prevention (409 conflict)

*Existing infrastructure (pytest, pytest-asyncio) already installed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Column profile via data_summary | FILE-02 | Uses existing File.data_summary -- no new endpoint | Upload file via POST /collections/{id}/files, verify file detail response includes data_summary |
| File selection for detection | FILE-03 | Frontend-only state | N/A -- no backend involvement |
| PDF download disabled | REPORT-04 | Frontend-only UI control | N/A -- no backend endpoint |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
