"""API key management endpoints. Authenticated via JWT (users managing their own keys)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.api_key import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyListItem
from app.services.api_key import ApiKeyService

router = APIRouter(prefix="/keys", tags=["API Keys"])


@router.get("", response_model=list[ApiKeyListItem])
async def list_api_keys(current_user: CurrentUser, db: DbSession):
    """List all API keys for the authenticated user (active and revoked)."""
    return await ApiKeyService.list_for_user(db, current_user.id)


@router.post("", response_model=ApiKeyCreateResponse, status_code=201)
async def create_api_key(
    body: ApiKeyCreateRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    """Create a new API key. The full key is returned ONCE and cannot be retrieved again."""
    api_key, full_key = await ApiKeyService.create(
        db, current_user.id, body.name, body.description
    )
    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        full_key=full_key,
        created_at=api_key.created_at,
    )


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(key_id: UUID, current_user: CurrentUser, db: DbSession):
    """Revoke an API key. Revoked keys immediately return 401 on any API request."""
    revoked = await ApiKeyService.revoke(db, key_id, current_user.id)
    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")
