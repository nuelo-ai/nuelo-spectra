"""ApiKeyService for key generation, CRUD, and authentication."""

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.services.auth import get_user_by_id


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key with prefix and hash.

    Returns:
        Tuple of (full_key, key_prefix, token_hash) where:
        - full_key: 'spe_<base64url random>' (~47 chars)
        - key_prefix: first 12 chars of full_key
        - token_hash: SHA-256 hex digest of full_key (64 chars)
    """
    random_part = secrets.token_urlsafe(32)
    full_key = f"spe_{random_part}"
    key_prefix = full_key[:12]
    token_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, token_hash


class ApiKeyService:
    """Service for API key operations: create, list, revoke, authenticate."""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> tuple[ApiKey, str]:
        """Create a new API key for a user.

        Returns:
            Tuple of (ApiKey record, full_raw_key). The full_raw_key is only
            available at creation time and must be shown to the user once.
        """
        full_key, key_prefix, token_hash = generate_api_key()

        api_key = ApiKey(
            user_id=user_id,
            name=name,
            description=description,
            key_prefix=key_prefix,
            token_hash=token_hash,
        )
        db.add(api_key)
        await db.flush()

        return api_key, full_key

    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: UUID) -> list[ApiKey]:
        """List all API keys for a user (active and revoked), newest first."""
        result = await db.execute(
            select(ApiKey)
            .where(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke(db: AsyncSession, key_id: UUID, user_id: UUID) -> bool:
        """Revoke an API key. Returns True if revoked, False if not found.

        Only the key owner can revoke their own key (user_id checked in query).
        """
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.user_id == user_id,
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return False

        api_key.is_active = False
        await db.flush()
        return True

    @staticmethod
    async def authenticate(db: AsyncSession, raw_key: str):
        """Authenticate a request using an API key.

        Hashes the raw key, looks up by token_hash with is_active=True filter.
        Updates last_used_at on successful authentication.

        Returns:
            User object if key is valid and active, None otherwise.
        """
        token_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        result = await db.execute(
            select(ApiKey).where(
                ApiKey.token_hash == token_hash,
                ApiKey.is_active == True,  # noqa: E712 - SQLAlchemy requires == for column comparison
            )
        )
        api_key = result.scalar_one_or_none()

        if api_key is None:
            return None

        # Update last_used_at
        api_key.last_used_at = datetime.now(timezone.utc)
        await db.flush()

        # Return the user
        return await get_user_by_id(db, api_key.user_id)
