---
status: resolved
phase: 40-rest-api-v1-endpoints
source: [40-01-SUMMARY.md, 40-02-SUMMARY.md, 40-03-SUMMARY.md, 40-04-SUMMARY.md]
started: 2026-02-24T17:00:00Z
updated: 2026-02-24T19:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Upload File via API
expected: POST /v1/files/upload with a valid API key and a file returns JSON envelope with success: true, data contains file_id, filename, data_brief, and suggestions. Onboarding runs synchronously.
result: pass

### 2. List Files via API
expected: GET /v1/files with a valid API key returns JSON envelope with success: true and data containing an array of the user's files with id, filename, and metadata.
result: pass

### 3. Download File via API
expected: GET /v1/files/{id}/download with a valid API key returns the raw file content as a binary stream (not JSON envelope). Content-Type matches the original file type.
result: pass

### 4. Get File Context
expected: GET /v1/files/{id}/context with a valid API key returns JSON envelope with data_summary and user_context for the file.
result: pass

### 5. Update File Context
expected: PUT /v1/files/{id}/context with JSON body containing user_context updates the file's context. Returns success envelope. Changes persist on subsequent GET.
result: pass (re-tested after 40-04 gap closure)

### 6. Get File Suggestions
expected: GET /v1/files/{id}/suggestions with a valid API key returns JSON envelope with analysis suggestions for the file.
result: pass

### 7. Query via API with Credit Deduction
expected: POST /v1/chat/query with a valid API key, query text, and file_ids runs stateless analysis and returns JSON envelope with the agent's response. Credits are deducted from the user's balance.
result: pass

### 8. Query Credit Refund on Failure
expected: If the query fails (e.g., invalid file_ids), credits are refunded. Error response uses ApiErrorResponse envelope with machine-readable error code.
result: pass

### 9. API Error Envelope Format
expected: Invalid requests (e.g., missing auth header) return ApiErrorResponse envelope with success: false, error object containing code (machine-readable), message, and appropriate HTTP status code.
result: pass (re-tested after 40-04 gap closure — confirmed {"success": false, "error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}})

### 10. Delete File via API
expected: DELETE /v1/files/{id} with a valid API key removes the file. Returns success envelope. Subsequent GET /v1/files no longer includes deleted file.
result: pass

### 11. File Ownership Isolation
expected: Attempting to access another user's file with your API key returns a 404 or 403 error, not the other user's data.
result: pass

## Summary

total: 11
passed: 11
issues: 0
pending: 0
skipped: 0

## Gaps

- truth: "PUT /v1/files/{id}/context persists user_context updates and data_summary is not user-editable"
  status: resolved
  reason: "User reported: PUT returns success but changes not persisted — GET context afterwards shows old values. Also data_summary should not be user-editable (it's AI-generated), only user_context should be updatable."
  severity: major
  test: 5
  root_cause: "context.py uses db.flush() instead of db.commit() — changes staged but never committed, rolled back on session close. Also data_summary field exposed in UpdateContextRequest when it should be AI-only."
  artifacts:
    - path: "backend/app/routers/api_v1/context.py"
      issue: "Line 64: flush() instead of commit(); Lines 18,59-60: data_summary in UpdateContextRequest"
  missing:
    - "Change db.flush() to db.commit() on line 64"
    - "Remove data_summary from UpdateContextRequest model"
    - "Remove data_summary update conditional block (lines 59-60)"
  fix: "40-04 Task 1 (commit 8256b4b)"

- truth: "Auth errors return ApiErrorResponse envelope format"
  status: resolved
  reason: "User reported: 401 Unauthorized returns raw FastAPI default {\"detail\": \"Not authenticated\"} instead of ApiErrorResponse envelope."
  severity: major
  test: 9
  root_cause: "No custom exception handler in main.py to intercept HTTPException and wrap in ApiErrorResponse. FastAPI default handler returns raw {\"detail\": \"...\"} format. OAuth2PasswordBearer auto_error=True raises HTTPException directly."
  artifacts:
    - path: "backend/app/main.py"
      issue: "No custom HTTPException handler registered"
    - path: "backend/app/dependencies.py"
      issue: "oauth2_scheme with auto_error=True raises raw HTTPException"
  missing:
    - "Add custom exception handler in main.py for HTTPException that wraps 401/403 in ApiErrorResponse envelope"
  fix: "40-04 Task 2 (commit fb0b601)"
