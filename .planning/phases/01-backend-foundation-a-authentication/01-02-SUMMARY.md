---
phase: 01-backend-foundation
plan: 02
subsystem: authentication
tags: [jwt, pwdlib, argon2, oauth2, fastapi, pydantic]

# Dependency graph
requires:
  - 01-01 (database foundation)
provides:
  - JWT-based authentication with access and refresh tokens
  - Password hashing with Argon2 via pwdlib
  - Auth endpoints (signup, login, refresh)
  - get_current_user dependency for protecting endpoints
  - Security utilities for token management
affects: [01-03, file-upload, chat-system, all-protected-endpoints]

# Tech tracking
tech-stack:
  added:
    - pyjwt>=2.9.0 (JWT token creation/verification)
    - pwdlib[argon2]>=0.3.0 (password hashing)
    - email-validator (EmailStr validation via Pydantic)
  patterns:
    - JWT with type claim validation (access vs refresh)
    - OAuth2PasswordBearer for token extraction
    - Typed dependencies (CurrentUser, DbSession)
    - Constant-time password verification to prevent timing attacks
    - No PII in JWT tokens (only user_id in 'sub' claim)

key-files:
  created:
    - backend/app/utils/security.py
    - backend/app/schemas/auth.py
    - backend/app/schemas/user.py
    - backend/app/services/auth.py
    - backend/app/dependencies.py
    - backend/app/routers/auth.py
  modified: []

key-decisions:
  - "JWT tokens contain only user_id (no email/PII) to minimize exposure"
  - "Separate access (30min) and refresh (30days) tokens for security"
  - "Argon2id password hashing via pwdlib (more modern than passlib)"
  - "JSON body for login (not OAuth2PasswordRequestForm) for frontend compatibility"
  - "Constant-time dummy hash in authenticate_user to prevent email enumeration"
  - "Explicit algorithm specification in jwt.decode() to prevent 'none' algorithm attack"

patterns-established:
  - "get_current_user dependency pattern for all protected endpoints"
  - "Typed Annotated dependencies for cleaner endpoint signatures"
  - "Service layer separation (routers call services, not direct DB)"
  - "Auto-login after signup (return tokens immediately)"

# Metrics
duration: 4min
completed: 2026-02-03
---

# Phase 01 Plan 02: Authentication Summary

**JWT-based authentication with signup, login, refresh, and protected endpoint access using Argon2 password hashing**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-03T01:41:18Z
- **Completed:** 2026-02-03T01:45:15Z
- **Tasks:** 2
- **Files created:** 10

## Accomplishments

- Password hashing with pwdlib Argon2id (modern, secure)
- JWT token creation with separate access (30min) and refresh (30day) tokens
- Token verification with type validation to prevent token type confusion
- Pydantic schemas for all auth requests/responses with email validation
- Auth service layer with timing-attack prevention
- Four API endpoints: POST /auth/signup, POST /auth/login, POST /auth/refresh, GET /auth/me
- get_current_user dependency for protecting any endpoint
- Typed dependencies (CurrentUser, DbSession) for clean endpoint signatures

## Task Commits

Each task was committed atomically:

1. **Task 1: Create security utilities and Pydantic schemas** - `278bdb6` (feat)
2. **Task 2: Create auth service, dependencies, and API endpoints** - `faff6f1` (feat)

## Files Created/Modified

**Created:**
- `backend/app/utils/__init__.py` - Utils package
- `backend/app/utils/security.py` - Password hashing (Argon2) and JWT utilities (create/verify tokens)
- `backend/app/schemas/__init__.py` - Schemas package
- `backend/app/schemas/auth.py` - SignupRequest, LoginRequest, RefreshRequest, TokenResponse, MessageResponse
- `backend/app/schemas/user.py` - UserResponse with from_attributes=True for SQLAlchemy
- `backend/app/services/__init__.py` - Services package
- `backend/app/services/auth.py` - create_user, authenticate_user, get_user_by_id
- `backend/app/routers/__init__.py` - Routers package
- `backend/app/routers/auth.py` - /auth/signup, /auth/login, /auth/refresh, /auth/me endpoints
- `backend/app/dependencies.py` - get_current_user, CurrentUser, DbSession typed dependencies

**Modified:**
- None (only new files created)

## Decisions Made

**JWT Structure - User ID Only:**
- JWT tokens contain ONLY user_id in 'sub' claim (no email, name, or other PII)
- Rationale: Minimizes data exposure if token is intercepted or logged
- Verified: JWT payload has exactly 3 keys: sub (user_id), exp (expiration), type (access/refresh)

**pwdlib Instead of passlib:**
- Using pwdlib[argon2] for password hashing instead of the abandoned passlib library
- Argon2id is the modern recommended algorithm (winner of Password Hashing Competition)
- Verified: Passwords stored with $argon2id$v=19$ prefix in database

**Timing Attack Prevention:**
- authenticate_user always hashes a dummy password when user not found
- Prevents attackers from determining if email exists based on response time
- pwdlib's verify() already uses constant-time comparison internally

**JSON Login (Not Form Data):**
- Login endpoint uses LoginRequest (JSON) not OAuth2PasswordRequestForm
- Rationale: Frontend will send JSON; form data is OAuth2 spec but not required
- OAuth2PasswordBearer is still used for token extraction in dependencies

**Token Type Validation:**
- Access and refresh tokens have explicit 'type' claim
- verify_token enforces type matching to prevent using refresh token as access token
- Security improvement over typical JWT implementations

**Algorithm Explicit in jwt.decode():**
- Always specify algorithms=[settings.algorithm] in jwt.decode()
- Prevents "none" algorithm attack where attacker removes signature
- Critical security best practice

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verification criteria met:

1. **Full auth flow works:**
   - Signup creates user and returns tokens (201)
   - Login validates credentials and returns tokens (200)
   - Protected /auth/me endpoint accessible with valid token (200)
   - Refresh token generates new token pair (200)

2. **Error handling correct:**
   - Invalid credentials return 401 "Incorrect email or password"
   - Missing/invalid token returns 401 "Not authenticated"
   - Duplicate email returns 409 "Email already registered"

3. **Security verified:**
   - Password stored as Argon2 hash: `$argon2id$v=19$m=655...`
   - JWT contains only user_id: `{'sub': 'uuid', 'exp': timestamp, 'type': 'access'}`
   - No email or other PII in JWT payload
   - Token type enforcement prevents refresh-as-access abuse

4. **Endpoints tested:**
   - POST /auth/signup → 201 with tokens
   - POST /auth/login → 200 with tokens
   - POST /auth/refresh → 200 with new tokens
   - GET /auth/me (with token) → 200 with user data
   - GET /auth/me (no token) → 401 unauthorized

## Requirements Satisfied

- **AUTH-01:** User can sign up with email and password ✓
- **AUTH-02:** User can log in with email and password ✓
- **AUTH-04:** Refresh tokens enable session persistence ✓
- **AUTH-05:** get_current_user dependency foundation for protecting all endpoints ✓

## Next Phase Readiness

**Ready for next phase:**
- Authentication system fully functional and tested
- get_current_user dependency available for protecting all future endpoints
- CurrentUser and DbSession typed dependencies ready for use
- Auth router ready to be included in main.py (Plan 01-03 handles final wiring)

**No blockers or concerns.**

All endpoints work correctly. Security best practices implemented (Argon2 hashing, no PII in JWT, timing attack prevention, explicit algorithm specification, token type validation).

---
*Phase: 01-backend-foundation*
*Completed: 2026-02-03*
