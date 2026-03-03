---
quick_task: 1
description: commit cleanup changes to non-codebase files
date: 2026-03-03
---

# Quick Task 1: Commit Cleanup Changes to Non-Codebase Files

## Objective

Commit the project folder cleanup the owner performed — reorganized requirements/ directory (archiving old UX flow docs, staging stale milestone reqs for removal) and removed old mockup files.

## Tasks

### Task 1: Stage and commit cleanup changes

**Files to stage:**
- `mockups/` — deleted old mockup files (5 files)
- `requirements/archieved/` — newly created archive of old UX flow docs
- `requirements/to-be-removed/` — stale milestone reqs staged for removal
- `requirements/milestone-04-req.md` through `milestone-07-req.md` — new milestone requirement files
- `requirements/brainstorm-idea-1.md` — modified
- `.planning/todos/pending/2026-03-01-review-and-finalize-analysis-workspace-brainstorm.md` — deleted

**Files to exclude:**
- `.planning/debug/admin-apikey-revoke-error.md` — separate debug session
- `.planning/debug/health-endpoint-404.md` — separate debug session
- `requirements/.build-pdf.sh` — utility script (separate concern)
- `requirements/brainstorm-idea-1.pdf` — generated artifact (separate concern)

**Action:** git add scoped to above files, then commit with descriptive message.
