"""Admin API key management endpoints.

Provides endpoints for listing, creating, and revoking API keys
on behalf of any user. All actions require admin authentication
and are recorded in the audit log.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from app.dependencies import CurrentAdmin, DbSession
from app.schemas.api_key import (
    AdminApiKeyListItem,
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
)
from app.services.admin.audit import log_admin_action
from app.services.api_key import ApiKeyService

router = APIRouter(prefix="/users/{user_id}/api-keys", tags=["admin-api-keys"])


@router.get("", response_model=list[AdminApiKeyListItem])
async def list_user_api_keys(
    user_id: UUID,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> list[AdminApiKeyListItem]:
    """List all API keys (active and revoked) for a user."""
    keys = await ApiKeyService.list_for_user(db, user_id)
    return [AdminApiKeyListItem.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_user_api_key(
    user_id: UUID,
    body: ApiKeyCreateRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> ApiKeyCreateResponse:
    """Create an API key on behalf of a user (tracks admin who created it)."""
    api_key, full_key = await ApiKeyService.create(
        db,
        user_id=user_id,
        name=body.name,
        description=body.description,
        created_by_admin_id=current_admin.id,
    )

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="create_api_key",
        target_type="api_key",
        target_id=str(api_key.id),
        details={"user_id": str(user_id), "key_name": body.name},
        ip_address=client_ip,
    )
    await db.commit()

    return ApiKeyCreateResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        full_key=full_key,
        created_at=api_key.created_at,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_user_api_key(
    user_id: UUID,
    key_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> None:
    """Revoke a user's API key (admin override, no ownership check)."""
    revoked = await ApiKeyService.admin_revoke(db, key_id)

    if not revoked:
        raise HTTPException(status_code=404, detail="API key not found")

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="revoke_api_key",
        target_type="api_key",
        target_id=str(key_id),
        details={"user_id": str(user_id)},
        ip_address=client_ip,
    )
    await db.commit()
