---
status: complete
phase: 37-admin-seed-on-startup-and-mandatory-credentials
source: [37-01-SUMMARY.md]
started: 2026-02-21T15:10:00Z
updated: 2026-02-21T15:10:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Fail-fast validation — dev mode missing credentials
expected: Running the backend Python import with SPECTRA_MODE=dev and empty ADMIN_EMAIL/ADMIN_PASSWORD raises an error that names the missing variables and says "must be set" — the process exits before uvicorn starts.
result: pass

### 2. Fail-fast validation — admin mode missing credentials
expected: Same fail-fast behavior with SPECTRA_MODE=admin — missing credentials cause immediate process exit with a clear error message before uvicorn accepts requests.
result: pass

### 3. Public mode unaffected — no credentials needed
expected: Starting the backend with SPECTRA_MODE=public and no ADMIN_EMAIL or ADMIN_PASSWORD set starts successfully with no error. The validator is completely silent in public mode.
result: pass

### 4. Dev mode with credentials — starts normally
expected: SPECTRA_MODE=dev with both ADMIN_EMAIL and ADMIN_PASSWORD set passes the validator with no error — the settings object is created successfully.
result: pass

### 5. Docker entrypoint seed block ordering
expected: Inspecting docker-entrypoint.sh shows: (1) alembic upgrade head runs first, (2) then the conditional ADMIN_EMAIL check / seed-admin block, (3) then exec uvicorn last. The seed block uses `[ -n "${ADMIN_EMAIL:-}" ]` as its gate condition.
result: pass

### 6. .env.docker.example documentation
expected: The ADMIN_EMAIL / ADMIN_PASSWORD section in .env.docker.example reads "REQUIRED when SPECTRA_MODE=dev or SPECTRA_MODE=admin" (no longer "optional"). The auto-seed behavior and password-reset-on-restart warning are documented.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

[none yet]
