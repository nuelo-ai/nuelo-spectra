# Phase 1: Backend Foundation & Authentication - Research

**Researched:** 2026-02-02
**Domain:** FastAPI backend with async SQLAlchemy 2.0, PostgreSQL, JWT authentication
**Confidence:** HIGH

## Summary

This phase builds a secure FastAPI backend with JWT-based authentication, PostgreSQL database, and user data isolation. The modern Python async ecosystem has consolidated around specific libraries in 2026: **PyJWT** for JWT tokens (python-jose is abandoned), **pwdlib** for password hashing (passlib won't work in Python 3.13+), and **SQLAlchemy 2.0 with asyncpg** for async database operations.

The standard approach uses OAuth2 password flow with Bearer tokens, Argon2 password hashing via pwdlib, and Alembic for database migrations. User data isolation is achieved through UUID-based user IDs and mandatory user_id filters on all queries to prevent IDOR vulnerabilities.

Key architectural decisions: FastAPI dependency injection for session management, pydantic-settings with @lru_cache for configuration, and asyncpg connection pooling for performance. Password reset flows use JWT-based time-limited tokens sent via email.

**Primary recommendation:** Use FastAPI with async SQLAlchemy 2.0, PostgreSQL/asyncpg, PyJWT, pwdlib[argon2], and Alembic. Structure the project with layered separation (routers, services, models, schemas) and enforce user_id scoping from day one.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Async web framework | Industry standard for async Python APIs, excellent docs, built-in OpenAPI |
| SQLAlchemy | 2.0+ | Async ORM | De-facto Python ORM, version 2.0 has mature async support |
| asyncpg | 0.29+ | PostgreSQL driver | Fastest async PostgreSQL driver, built for asyncio from ground up |
| PostgreSQL | 14+ | Database | Most reliable open-source RDBMS, excellent JSON support |
| PyJWT | 2.9+ | JWT tokens | Actively maintained, recommended by FastAPI docs (python-jose abandoned) |
| pwdlib | 0.3+ | Password hashing | Modern replacement for passlib (Python 3.13 compatible) |
| Alembic | 1.13+ | Database migrations | SQLAlchemy's official migration tool, async-aware |
| Pydantic | 2.0+ | Validation/Settings | Built into FastAPI, version 2 brings major performance improvements |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.0+ | Environment config | Managing .env files and validated settings (required for FastAPI settings pattern) |
| python-dotenv | 1.0+ | Load .env files | Development environment variable management |
| httpx | 0.27+ | HTTP client | Async email service API calls (SendGrid, Mailgun) |
| pytest | 8.0+ | Testing framework | Unit and integration tests |
| pytest-asyncio | 0.23+ | Async test support | Testing async endpoints and database operations |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Django REST / Flask | FastAPI has superior async support and auto-docs; Django better for monoliths with admin UI |
| PyJWT | authlib/joserfc | PyJWT simpler for JWT-only use; authlib better if you need full OAuth2 provider |
| asyncpg | psycopg3 (async mode) | asyncpg faster; psycopg3 offers sync/async flexibility |
| Mailgun | SendGrid, Resend | Mailgun best for developers (simple API, no marketing bloat); SendGrid adds marketing features |

**Installation:**
```bash
pip install "fastapi[standard]>=0.115.0"
pip install "sqlalchemy[asyncio]>=2.0.0"
pip install "asyncpg>=0.29.0"
pip install "alembic>=1.13.0"
pip install "pyjwt>=2.9.0"
pip install "pwdlib[argon2]>=0.3.0"
pip install "pydantic-settings>=2.0.0"
pip install "python-dotenv>=1.0.0"

# Email (choose one)
pip install "httpx>=0.27.0"  # For API-based email services

# Testing
pip install "pytest>=8.0.0"
pip install "pytest-asyncio>=0.23.0"
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, lifespan events
│   ├── config.py               # Settings with pydantic-settings
│   ├── database.py             # Async engine, session factory
│   ├── dependencies.py         # Reusable dependencies (get_db, get_current_user)
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py            # Base class with common fields
│   │   └── user.py            # User model
│   ├── schemas/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── auth.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py            # Authentication logic
│   │   └── email.py           # Email sending
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py            # /auth endpoints
│   │   └── users.py           # /users endpoints
│   └── utils/                  # Helper functions
│       ├── __init__.py
│       └── security.py        # Password hashing, JWT helpers
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_auth.py
│   └── test_users.py
├── .env                        # Local environment variables (gitignored)
├── .env.example                # Template for .env
├── alembic.ini                 # Alembic configuration
├── pyproject.toml              # Python project metadata
└── requirements.txt            # or use pyproject.toml with Poetry/uv
```

### Pattern 1: Settings Management with Dependency Injection
**What:** Use pydantic-settings with @lru_cache to load configuration once, inject via FastAPI dependencies
**When to use:** All configuration (DB URLs, secrets, email settings)
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/settings/
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated
from fastapi import Depends

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings():
    return Settings()

# Usage in endpoints
async def protected_route(settings: Annotated[Settings, Depends(get_settings)]):
    # Settings loaded once, cached for all requests
    pass
```

### Pattern 2: Async Database Session with Dependency
**What:** Create async session per request, automatically close after use
**When to use:** All database operations
**Example:**
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

engine = create_async_engine(settings.database_url, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

# Usage in endpoints
async def create_user(db: AsyncSession = Depends(get_db)):
    # Session auto-closed after request
    pass
```

### Pattern 3: JWT Authentication with User Dependency
**What:** Extract and validate JWT token, return current user
**When to use:** Protected endpoints requiring authentication
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
```

### Pattern 4: User Data Isolation with Mandatory Filters
**What:** All queries include user_id filter to prevent IDOR
**When to use:** Every query that fetches user-owned resources
**Example:**
```python
# Source: https://escape.tech/blog/how-to-secure-fastapi-api/
from uuid import UUID

# BAD - IDOR vulnerability
async def get_file(file_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(File).where(File.id == file_id))
    return result.scalar_one_or_none()

# GOOD - User isolation enforced
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(File).where(
            File.id == file_id,
            File.user_id == current_user.id  # MANDATORY
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file
```

### Pattern 5: Password Reset with Time-Limited JWT
**What:** Generate JWT token with short expiration, send via email
**When to use:** Password reset flow
**Example:**
```python
# Source: https://pramod4040.medium.com/fastapi-forget-password-api-setup-632ab90ba958
from datetime import datetime, timedelta, timezone

def create_password_reset_token(email: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    data = {"sub": email, "exp": expire, "type": "password_reset"}
    return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)

async def verify_password_reset_token(token: str, settings: Settings) -> str:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token type")
        email = payload.get("sub")
        return email
    except InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
```

### Pattern 6: Refresh Token Flow
**What:** Short-lived access tokens (30 min) + long-lived refresh tokens (30 days)
**When to use:** Production authentication to balance security and UX
**Example:**
```python
# Source: https://medium.com/@jagan_reddy/jwt-in-fastapi-the-secure-way-refresh-tokens-explained-f7d2d17b1d17
def create_tokens(user_id: str, settings: Settings) -> dict:
    access_expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    refresh_expire = datetime.now(timezone.utc) + timedelta(days=30)

    access_token = jwt.encode(
        {"sub": user_id, "exp": access_expire, "type": "access"},
        settings.secret_key,
        algorithm=settings.algorithm
    )

    refresh_token = jwt.encode(
        {"sub": user_id, "exp": refresh_expire, "type": "refresh"},
        settings.secret_key,
        algorithm=settings.algorithm
    )

    return {"access_token": access_token, "refresh_token": refresh_token}
```

### Anti-Patterns to Avoid
- **Using session.query() with async:** SQLAlchemy 2.0 async requires select() statements, not session.query()
- **Sharing AsyncSession across tasks:** Each concurrent task needs its own session
- **Auto-increment IDs in URLs:** Enables enumeration attacks; use UUIDs for user-facing IDs
- **Storing JWTs in localStorage:** Vulnerable to XSS; use httpOnly cookies or secure storage
- **Missing user_id filters:** Every resource query MUST filter by current user to prevent IDOR
- **Calling Base.metadata.create_all():** Always use Alembic migrations for schema changes

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt wrapper | pwdlib.PasswordHash.recommended() | Handles algorithm upgrades, uses secure Argon2 defaults, Python 3.13 compatible |
| JWT token generation | Manual JWT encoding/decoding | PyJWT with helper functions | Handles expiration, signature verification, exception handling |
| Database migrations | Manual SQL scripts | Alembic autogenerate | Tracks migration history, handles rollbacks, generates migrations from models |
| Email sending | SMTP directly | Email service API (Mailgun, SendGrid) | Better deliverability, handles bounces, provides analytics |
| Environment config | Manual os.getenv() | pydantic-settings BaseSettings | Type validation, .env file support, auto-documentation |
| Password reset tokens | UUID + database table | JWT with expiration | Self-contained, no database cleanup needed, built-in expiration |
| API documentation | Manual OpenAPI spec | FastAPI automatic docs | Auto-generated from type hints, always in sync with code |
| Request validation | Manual dict parsing | Pydantic models | Type coercion, validation errors, auto-docs |

**Key insight:** Authentication has countless edge cases (timing attacks, token revocation, password policies, account enumeration). Use battle-tested libraries (PyJWT, pwdlib) rather than implementing cryptographic operations from scratch.

## Common Pitfalls

### Pitfall 1: AsyncSession Shared Across Concurrent Tasks
**What goes wrong:** Using a single AsyncSession instance in asyncio.gather() or multiple tasks causes "Session is already active" errors or data corruption
**Why it happens:** SQLAlchemy async sessions are not thread-safe or task-safe
**How to avoid:** Create separate sessions per task; use async_session_maker() to generate new sessions
**Warning signs:** Intermittent "Session is already active" errors, race conditions in tests
```python
# BAD
session = async_session_maker()
await asyncio.gather(task1(session), task2(session))

# GOOD
async def task_with_own_session():
    async with async_session_maker() as session:
        # work here
        pass
await asyncio.gather(task_with_own_session(), task_with_own_session())
```

### Pitfall 2: Lazy Loading with Async Sessions
**What goes wrong:** Accessing relationships outside async context raises "MissingGreenlet" errors
**Why it happens:** SQLAlchemy can't perform lazy loading (implicit IO) in async without explicit awaiting
**How to avoid:** Use eager loading (selectinload, joinedload) for all relationships or set expire_on_commit=False
**Warning signs:** "greenlet_spawn has not been called" errors when accessing model.relationship
```python
# BAD
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalar_one()
files = user.files  # MissingGreenlet error!

# GOOD - eager load
from sqlalchemy.orm import selectinload
result = await db.execute(
    select(User).options(selectinload(User.files)).where(User.id == user_id)
)
user = result.scalar_one()
files = user.files  # Works!
```

### Pitfall 3: Missing IDOR Prevention
**What goes wrong:** Users can access other users' data by changing IDs in URLs (/files/123 -> /files/124)
**Why it happens:** Endpoints query by resource ID without verifying ownership
**How to avoid:** Add user_id filter to EVERY query for user-owned resources
**Warning signs:** Security audit finds unauthorized data access, users report seeing others' data
```python
# BAD - IDOR vulnerability
@app.get("/files/{file_id}")
async def get_file(file_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(File).where(File.id == file_id))
    return result.scalar_one_or_none()

# GOOD - ownership check
@app.get("/files/{file_id}")
async def get_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(File).where(File.id == file_id, File.user_id == current_user.id)
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404)
    return file
```

### Pitfall 4: Storing Sensitive Data in JWT
**What goes wrong:** JWTs are base64-encoded (not encrypted), anyone can decode and read the payload
**Why it happens:** Developers treat JWTs like encrypted session storage
**How to avoid:** Only store non-sensitive identifiers (user_id) in JWTs, never passwords or PII
**Warning signs:** JWT contains email, phone numbers, or sensitive user attributes
```python
# BAD - sensitive data in JWT
jwt.encode({"sub": user.id, "email": user.email, "ssn": user.ssn}, secret)

# GOOD - only identifier
jwt.encode({"sub": user.id}, secret)
```

### Pitfall 5: Accepting JWT "none" Algorithm
**What goes wrong:** Attackers can forge tokens by setting algorithm to "none", bypassing signature verification
**Why it happens:** Some JWT libraries accept unsigned tokens if algorithm header is "none"
**How to avoid:** Always specify allowed algorithms explicitly in jwt.decode()
**Warning signs:** Security scanner reports "JWT none algorithm accepted"
```python
# BAD - accepts any algorithm
jwt.decode(token, secret_key)

# GOOD - explicit algorithm
jwt.decode(token, secret_key, algorithms=["HS256"])
```

### Pitfall 6: Using Wildcard CORS with Credentials
**What goes wrong:** Browser rejects requests when allow_origins=["*"] with allow_credentials=True
**Why it happens:** Security spec forbids credential-enabled CORS with wildcard origins
**How to avoid:** Specify exact allowed origins in production
**Warning signs:** CORS errors in browser console despite middleware being configured
```python
# BAD - rejected by browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # Incompatible!
)

# GOOD - explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.yourdomain.com"],
    allow_credentials=True,
)
```

### Pitfall 7: Not Setting expire_on_commit=False
**What goes wrong:** Accessing model attributes after commit triggers implicit async queries, causing errors
**Why it happens:** By default SQLAlchemy expires all objects after commit
**How to avoid:** Set expire_on_commit=False in async_sessionmaker
**Warning signs:** "MissingGreenlet" errors when accessing model attributes after await session.commit()
```python
# BAD
async_session_maker = async_sessionmaker(engine)

# GOOD
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
```

### Pitfall 8: Alembic Not Seeing Model Changes
**What goes wrong:** alembic revision --autogenerate produces empty migration
**Why it happens:** Alembic's env.py doesn't import models or target_metadata not set
**How to avoid:** Import all models in alembic/env.py and set target_metadata = Base.metadata
**Warning signs:** Autogenerate creates empty migrations despite model changes
```python
# In alembic/env.py
from app.models.base import Base
# Import all models so Alembic can see them
from app.models import user, file, chat_message

target_metadata = Base.metadata
```

## Code Examples

Verified patterns from official sources:

### User Model with UUID and Timestamps
```python
# Source: SQLAlchemy 2.0 best practices
from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime, timezone
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
```

### Password Hashing with pwdlib
```python
# Source: https://frankie567.github.io/pwdlib/guide/
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()  # Uses Argon2

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# Auto-upgrade old hashes
valid, updated_hash = password_hash.verify_and_update(plain_password, old_hash)
if updated_hash:
    # Save updated_hash to database
    user.hashed_password = updated_hash
```

### Login Endpoint with Token Generation
```python
# Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    # Find user
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return {"access_token": access_token, "token_type": "bearer"}

def create_access_token(data: dict, expires_delta: timedelta, settings: Settings) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
```

### Alembic Configuration for Async
```python
# Source: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
# In alembic/env.py
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.models.base import Base
from app.config import get_settings

config = context.config
settings = get_settings()

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Import all models
from app.models import user, file, chat_message

target_metadata = Base.metadata

def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def do_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    def do_run_migrations(connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    import asyncio
    asyncio.run(do_migrations())
```

### Password Reset Flow
```python
# Source: https://pramod4040.medium.com/fastapi-forget-password-api-setup-632ab90ba958
@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    # Always return 202 to prevent user enumeration
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        reset_token = create_password_reset_token(email, settings)
        reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"

        # Send email (implementation depends on email service)
        await send_password_reset_email(user.email, reset_link)

    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
):
    email = await verify_password_reset_token(token, settings)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    user.hashed_password = hash_password(new_password)
    await db.commit()

    return {"message": "Password reset successful"}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| passlib for password hashing | pwdlib with Argon2 | 2025 | passlib won't work in Python 3.13+; pwdlib is actively maintained |
| python-jose for JWT | PyJWT | 2024-2025 | python-jose abandoned; PyJWT is now FastAPI's recommended library |
| SQLAlchemy 1.4 with session.query() | SQLAlchemy 2.0 with select() | 2023 | Async support requires 2.0 syntax; better type hints, performance |
| Bcrypt for passwords | Argon2 | Ongoing | Argon2 winner of Password Hashing Competition, more resistant to GPU attacks |
| psycopg2 | asyncpg | 2018+ | Built for asyncio, 3-5x faster than psycopg2, required for async SQLAlchemy |
| Manual env loading | pydantic-settings | 2023 (Pydantic v2) | Type-safe config, validation, better testing with dependency overrides |
| Integer auto-increment IDs | UUIDs for user-facing IDs | Ongoing | UUIDs prevent enumeration attacks, but keep int IDs for internal foreign keys |
| SendGrid for everything | Specialized email services | 2024+ | Mailgun for transactional, Resend for developers; SendGrid lost developer focus |

**Deprecated/outdated:**
- **passlib**: Won't work on Python 3.13+ due to crypt module removal; use pwdlib
- **python-jose**: Abandoned in 2021, multiple CVEs; use PyJWT or authlib
- **SQLAlchemy 1.4 session.query()**: Deprecated in 2.0; use select() statements
- **FastAPI Security(auto_error=False)**: Deprecated; use Optional[str] in dependency return type
- **Pydantic Config class**: Removed in Pydantic v2; use model_config = ConfigDict(...)

## Open Questions

Things that couldn't be fully resolved:

1. **Email Service Choice**
   - What we know: Mailgun and SendGrid are most popular; Resend emerging for developers; all support API-based sending
   - What's unclear: Which specific service fits project budget and volume needs (free tiers: Mailgun 5k/month, SendGrid 100/day)
   - Recommendation: Start with Mailgun (better developer UX, 5k free emails/month). Abstract email sending behind a service interface to allow easy switching.

2. **JWT Secret Key Rotation**
   - What we know: JWT tokens signed with single SECRET_KEY; rotation requires invalidating existing tokens
   - What's unclear: Best practice for zero-downtime key rotation in production
   - Recommendation: For v1.0, use single long-lived key. For production, implement token versioning (add "v" claim) and support multiple keys with fallback.

3. **Database Connection Pool Sizing**
   - What we know: asyncpg supports connection pooling; SQLAlchemy async engine manages pool
   - What's unclear: Optimal pool_size and max_overflow for expected load
   - Recommendation: Start with defaults (pool_size=5, max_overflow=10). Monitor with connection metrics; adjust based on concurrent request volume.

4. **Testing Database Isolation**
   - What we know: pytest-asyncio supports async tests; can use function-scoped event loops
   - What's unclear: Best pattern for test database (separate DB vs. transactions rollback vs. in-memory SQLite)
   - Recommendation: Use PostgreSQL test database with function-scoped sessions that rollback. SQLite incompatible with asyncpg; transaction rollback provides best isolation.

5. **Rate Limiting for Auth Endpoints**
   - What we know: Login endpoints vulnerable to brute force; rate limiting needed
   - What's unclear: Whether to implement at middleware layer, use Redis-backed solution, or rely on reverse proxy
   - Recommendation: For v1.0 MVP, defer to reverse proxy (Nginx, Cloudflare). For production, add slowapi (async-compatible rate limiter).

## Sources

### Primary (HIGH confidence)
- FastAPI Official Docs - OAuth2 with JWT: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- FastAPI Official Docs - Settings Management: https://fastapi.tiangolo.com/advanced/settings/
- FastAPI Official Docs - CORS: https://fastapi.tiangolo.com/tutorial/cors/
- SQLAlchemy 2.0 Official Docs - Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- pwdlib Official Docs: https://frankie567.github.io/pwdlib/guide/
- pwdlib GitHub README: https://github.com/frankie567/pwdlib
- PyJWT Documentation (verified via FastAPI docs referencing it)

### Secondary (MEDIUM confidence)
- Medium - JWT in FastAPI, the Secure Way (Jan 2026): https://medium.com/@jagan_reddy/jwt-in-fastapi-the-secure-way-refresh-tokens-explained-f7d2d17b1d17
- TestDriven.io - FastAPI JWT Auth: https://testdriven.io/blog/fastapi-jwt-auth/
- Medium - FastAPI Forget Password Setup: https://pramod4040.medium.com/fastapi-forget-password-api-setup-632ab90ba958
- GitHub FastAPI Discussion #11589 - PyJWT recommendation: https://github.com/fastapi/fastapi/pull/11589
- Escape.tech - FastAPI Security Guide (IDOR prevention): https://escape.tech/blog/how-to-secure-fastapi-api/
- Medium - Building High-Performance Async APIs (SQLAlchemy 2.0 + asyncpg): https://leapcell.io/blog/building-high-performance-async-apis-with-fastapi-sqlalchemy-2-0-and-asyncpg
- Mailgun Blog - Password Reset Email Workflows: https://www.mailgun.com/blog/dev-life/how-to-build-transactional-password-reset-email-workflows/

### Tertiary (LOW confidence - community sources, needs validation)
- GitHub - zhanymkanov/fastapi-best-practices: https://github.com/zhanymkanov/fastapi-best-practices
- Various Medium articles on FastAPI project structure (Jan 2026)
- StackOverflow discussions on UUID vs auto-increment security

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified through official docs and recent community adoption
- Architecture: HIGH - Patterns from official FastAPI and SQLAlchemy documentation
- Pitfalls: HIGH - Common issues documented in official GitHub discussions and error documentation
- Code examples: HIGH - Sourced from official documentation and verified technical blogs
- Email services: MEDIUM - Comparison based on service marketing and third-party comparisons, not hands-on testing

**Research date:** 2026-02-02
**Valid until:** 2026-03-04 (30 days - stable ecosystem, libraries mature)

**Notes:**
- PyJWT and pwdlib recommendations based on deprecation of python-jose and passlib (confirmed by FastAPI team)
- SQLAlchemy async patterns verified against SQLAlchemy 2.0 official docs
- All security patterns (IDOR prevention, JWT algorithms) cross-referenced with OWASP and security blogs
- FastAPI version 0.115+ includes recent updates to security documentation recommending PyJWT
