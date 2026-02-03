"""Security utilities for password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from app.config import Settings

# Initialize password hasher with Argon2 (recommended)
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a password using Argon2.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: str, settings: Settings) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID to encode in the token
        settings: Application settings containing JWT configuration

    Returns:
        Encoded JWT access token
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: str, settings: Settings) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: User ID to encode in the token
        settings: Application settings containing JWT configuration

    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_tokens(user_id: str, settings: Settings) -> dict[str, str]:
    """Create both access and refresh tokens.

    Args:
        user_id: User ID to encode in the tokens
        settings: Application settings containing JWT configuration

    Returns:
        Dictionary with access_token, refresh_token, and token_type
    """
    return {
        "access_token": create_access_token(user_id, settings),
        "refresh_token": create_refresh_token(user_id, settings),
        "token_type": "bearer"
    }


def verify_token(token: str, token_type: str, settings: Settings) -> str:
    """Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')
        settings: Application settings containing JWT configuration

    Returns:
        User ID extracted from the token

    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]  # Explicitly set algorithm to prevent 'none' attack
        )

        # Validate token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Extract user_id from 'sub' claim
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_password_reset_token(email: str, settings: Settings) -> str:
    """Create a JWT password reset token.

    Args:
        email: User email to encode in the token
        settings: Application settings containing JWT configuration

    Returns:
        Encoded JWT password reset token (valid for 10 minutes)
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {
        "sub": email,
        "exp": expire,
        "type": "password_reset"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def verify_password_reset_token(token: str, settings: Settings) -> str:
    """Verify and decode a password reset token.

    Args:
        token: JWT password reset token to verify
        settings: Application settings containing JWT configuration

    Returns:
        Email address extracted from the token

    Raises:
        HTTPException: If token is invalid, expired, or wrong type
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]  # Explicitly set algorithm to prevent 'none' attack
        )

        # Validate token type
        if payload.get("type") != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Extract email from 'sub' claim
        email: str | None = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        return email

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
