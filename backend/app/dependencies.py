"""FastAPI dependencies for authentication and database access."""

import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.models.user import User
from app.services.api_key import ApiKeyService
from app.services.auth import get_user_by_id
from app.utils.security import verify_token

# OAuth2 scheme for token extraction (tokenUrl points to login endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Scheme for unified auth (API keys + JWT) — auto_error=False lets us handle auth manually
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# In-memory set of recently deactivated user IDs for immediate token invalidation.
# TTL matches access token expiry. After TTL, the DB is_active=False check suffices.
_deactivated_users: dict[UUID, float] = {}
_deactivation_lock = threading.Lock()


def mark_user_deactivated(user_id: UUID, ttl_seconds: int = 1800) -> None:
    """Add user to revocation set. TTL defaults to 30 min (token expiry)."""
    with _deactivation_lock:
        _deactivated_users[user_id] = time.time()
        # Cleanup expired entries
        cutoff = time.time() - ttl_seconds
        expired = [uid for uid, ts in _deactivated_users.items() if ts < cutoff]
        for uid in expired:
            del _deactivated_users[uid]


def clear_user_deactivation(user_id: UUID) -> None:
    """Remove user from revocation set (on reactivation)."""
    with _deactivation_lock:
        _deactivated_users.pop(user_id, None)


def is_user_deactivated(user_id: UUID) -> bool:
    """Check if user was recently deactivated."""
    return user_id in _deactivated_users


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)]
) -> User:
    """Get current authenticated user from JWT token.

    Args:
        token: JWT access token from Authorization header
        db: Database session
        settings: Application settings

    Returns:
        Authenticated user instance

    Raises:
        HTTPException: If token is invalid or user not found/inactive
    """
    # Verify token and extract user_id
    user_id_str = verify_token(token, "access", settings)

    # Convert user_id string to UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check in-memory revocation set BEFORE DB lookup (immediate logout on deactivation)
    if is_user_deactivated(user_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account has been deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


async def get_authenticated_user(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Unified auth dependency accepting either JWT or API key as Bearer token.

    JWT fast path (token does NOT start with 'spe_'):
      - Try verify_token() -> get user from DB
      - If expired JWT: raise 401 "Token has expired" (do NOT fall through to key lookup)
      - If invalid JWT format: raise 401 "Invalid token"
      - Sets request.state.api_key_id = None

    API key path (token starts with 'spe_'):
      - Call ApiKeyService.authenticate()
      - None -> raise 401 "Invalid or revoked API key"
      - Sets request.state.api_key_id to the authenticated key's UUID

    Used by Phase 40 external API endpoints only. Not used by APIKEY CRUD endpoints.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fast path: if token looks like an API key, skip JWT entirely
    if token.startswith("spe_"):
        result = await ApiKeyService.authenticate(db, token)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user, api_key_id = result
        request.state.api_key_id = api_key_id
        await db.commit()
        return user

    # JWT path: try to verify as JWT
    try:
        user_id_str = verify_token(token, "access", settings)
        user_id = UUID(user_id_str)
        user = await get_user_by_id(db, user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        request.state.api_key_id = None
        return user
    except HTTPException:
        # Re-raise JWT-specific errors (expired token, invalid token, etc.) as-is
        raise
    except Exception:
        # Non-HTTP exception means something unexpected; treat as invalid credentials
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_admin_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    """Verify JWT has is_admin=True claim AND verify is_admin in DB (defense in depth).

    Checks:
    1. JWT signature and expiration
    2. is_admin claim in JWT (fast pre-filter)
    3. Token type is "access"
    4. Sliding window timeout via iat claim
    5. User exists and is active in DB
    6. is_admin flag in DB (defense in depth)

    Args:
        token: JWT access token from Authorization header
        db: Database session
        settings: Application settings

    Returns:
        Authenticated admin user instance

    Raises:
        HTTPException: If any check fails
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Admin session expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fast pre-filter: check JWT claim
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    # Check sliding window timeout via iat claim
    iat = payload.get("iat")
    if iat:
        issued_at = datetime.fromtimestamp(iat, tz=timezone.utc)
        if datetime.now(timezone.utc) - issued_at > timedelta(
            minutes=settings.admin_session_timeout_minutes
        ):
            raise HTTPException(status_code=401, detail="Admin session expired")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user_id = UUID(user_id_str)
    user = await get_user_by_id(db, user_id)

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Defense in depth: verify is_admin in database (not just JWT claim)
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user


# Typed dependencies for cleaner endpoint signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin_user)]
ApiAuthUser = Annotated[User, Depends(get_authenticated_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
