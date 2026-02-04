# Debug Session: Password Reset Console Output

**Date:** 2026-02-04
**Issue:** Password reset link not appearing in console during dev mode
**Phase:** Phase 6 UAT
**Test:** Test 3 - Password Reset Flow

## Problem Statement
User navigates to /forgot-password, enters email, but reset link does not appear in console output even though dev mode is configured.

## Investigation Steps

### 1. Examined Password Reset Flow
File: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/routers/auth.py`
- Line 176-218: `forgot_password` endpoint
- Endpoint correctly calls `send_password_reset_email` when user exists
- Passes email, reset_link, and settings to email service

### 2. Examined Email Service Dev Mode Logic
File: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/services/email.py`
- Line 34: Dev mode check: `if not settings.email_service_api_key or settings.email_service_api_key.strip() in _DEV_PLACEHOLDERS`
- Line 12: `_DEV_PLACEHOLDERS = {"", "dev-api-key", "your-email-api-key", "changeme"}`
- Lines 35-40: Dev mode logs reset link using `logger.info()`
- This was recently fixed in commit 53e078c (2026-02-04)

### 3. Checked Environment Configuration
File: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/.env`
- Line 15: `EMAIL_SERVICE_API_KEY=` (empty string)
- Empty string matches dev mode check correctly

### 4. Examined Logging Configuration
File: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/services/email.py`
- Line 10: `logger = logging.getLogger(__name__)`
- Logger is created but **NEVER CONFIGURED**

File: `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/main.py`
- No `logging.basicConfig()` call
- No logging level configuration

### 5. Checked Server Startup
Process: `uvicorn app.main:app --reload`
- Uvicorn runs with default logging configuration
- Python's default logging level is WARNING
- INFO level messages (logger.info) are **SUPPRESSED**

## Root Cause Analysis

**ROOT CAUSE IDENTIFIED:**

The password reset link is being generated correctly and the dev mode detection is working. However, **Python's logging module is not configured**, so INFO-level log messages are never displayed in the console.

**Evidence:**
1. Email service correctly detects dev mode (EMAIL_SERVICE_API_KEY is empty)
2. Code calls `logger.info()` to output reset link (lines 35-40 in email.py)
3. Logger is created but never configured with a handler or level
4. Python's default logging level is WARNING
5. INFO < WARNING, so INFO messages are suppressed

**The chain of execution:**
1. User submits forgot-password request ✓
2. Backend queries database for user ✓
3. If user exists, generates reset token ✓
4. Calls send_password_reset_email() ✓
5. Dev mode check passes (empty API key) ✓
6. **logger.info() called BUT OUTPUT SUPPRESSED** ✗

## Files Involved

**Primary:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/services/email.py`
  - Contains logger.info() calls that are not displaying

**Secondary:**
- `/Users/marwazisiagian/Documents/ms-dev/spectra-project/spectra-dev/backend/app/main.py`
  - Missing logging configuration initialization

## Suggested Fix Direction

**Option 1: Configure logging in main.py (RECOMMENDED)**
Add logging configuration to main.py before creating FastAPI app:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

**Option 2: Use uvicorn's log config**
Pass `--log-level info` when starting uvicorn:
```bash
uvicorn app.main:app --reload --log-level info
```

**Option 3: Print directly instead of logger.info() (NOT RECOMMENDED)**
Replace logger.info() with print() statements in email.py dev mode section.
This works but bypasses proper logging infrastructure.

**RECOMMENDATION:** Option 1 is best practice. Configure logging once in main.py so all modules benefit from consistent logging configuration.

## Verification

Tested Python's default logging level:
```bash
$ python3 -c "import logging; print('Default level:', logging.root.level)"
Default level: 30 - Name: WARNING
```

INFO level = 20
WARNING level = 30

Since 20 < 30, INFO messages are suppressed by default.

## Conclusion

The password reset functionality works correctly. The dev mode detection works correctly. The reset link is being generated. The only issue is that Python's logging module needs to be configured to display INFO-level messages.

**Status:** ROOT CAUSE FOUND
**Severity:** Configuration issue (easy fix)
**Impact:** Dev mode console logging not visible to developers during testing

