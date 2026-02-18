"""Admin platform settings endpoints.

Provides GET and PATCH for runtime platform configuration.
"""

import json

from fastapi import APIRouter, HTTPException, Request

from app.dependencies import CurrentAdmin, DbSession
from app.schemas.platform_settings import SettingsResponse, SettingsUpdateRequest
from app.services import platform_settings
from app.services.admin.audit import log_admin_action

router = APIRouter(prefix="/settings", tags=["admin-settings"])


@router.get("", response_model=SettingsResponse)
async def get_settings(
    db: DbSession,
    current_admin: CurrentAdmin,
) -> SettingsResponse:
    """Return all platform settings with parsed values (SETTINGS-01, SETTINGS-02)."""
    raw = await platform_settings.get_all(db)
    parsed = {k: json.loads(v) for k, v in raw.items()}
    return SettingsResponse(**parsed)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdateRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> SettingsResponse:
    """Update platform settings (SETTINGS-03, SETTINGS-04, SETTINGS-05).

    Validates each changed key, upserts to DB, invalidates cache,
    and creates an audit log entry.
    """
    changed = body.model_dump(exclude_none=True)

    # Validate all values before writing
    for key, value in changed.items():
        error = platform_settings.validate_setting(key, value)
        if error:
            raise HTTPException(status_code=422, detail=error)

    # Upsert each changed key
    for key, value in changed.items():
        await platform_settings.upsert(db, key, value, current_admin.id)

    # Invalidate cache after all upserts
    platform_settings.invalidate_cache()

    # Audit log
    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db=db,
        admin_id=current_admin.id,
        action="update_settings",
        target_type="platform_settings",
        target_id="global",
        details={"changed_keys": list(changed.keys())},
        ip_address=client_ip,
    )

    await db.commit()

    # Re-read and return all settings
    raw = await platform_settings.get_all(db)
    parsed = {k: json.loads(v) for k, v in raw.items()}
    return SettingsResponse(**parsed)
