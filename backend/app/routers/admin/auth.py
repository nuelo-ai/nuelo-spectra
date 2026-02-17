"""Admin authentication router with login lockout protection."""

import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import CurrentAdmin
from app.schemas.admin import AdminLoginRequest, AdminLoginResponse
from app.schemas.admin_dashboard import AdminMeResponse
from app.services.admin.auth import authenticate_admin
from app.services.admin.audit import log_admin_action
from app.utils.security import create_admin_tokens

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])

# In-memory lockout tracker: ip -> {"attempts": int, "locked_until": float}
_login_attempts: dict[str, dict] = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AdminLoginResponse:
    """Authenticate admin user and return JWT with is_admin claim.

    Includes IP-based lockout protection: after 5 failed attempts,
    further attempts are blocked for 15 minutes.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    # Check lockout
    attempt_record = _login_attempts.get(client_ip, {})
    locked_until = attempt_record.get("locked_until", 0)
    if now < locked_until:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    # Reset attempts if lockout has expired
    if now >= locked_until and attempt_record.get("attempts", 0) >= MAX_ATTEMPTS:
        _login_attempts[client_ip] = {"attempts": 0, "locked_until": 0}

    user = await authenticate_admin(db, login_data.email, login_data.password)

    if user is None:
        # Track failed attempt
        record = _login_attempts.get(client_ip, {"attempts": 0, "locked_until": 0})
        record["attempts"] = record.get("attempts", 0) + 1
        if record["attempts"] >= MAX_ATTEMPTS:
            record["locked_until"] = now + LOCKOUT_SECONDS
        _login_attempts[client_ip] = record
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials or insufficient permissions",
        )

    # Reset attempts on success
    _login_attempts.pop(client_ip, None)

    tokens = create_admin_tokens(str(user.id), settings)

    # Audit log the login
    await log_admin_action(
        db=db,
        admin_id=user.id,
        action="admin_login",
        target_type="session",
        target_id=str(user.id),
        details={"email": user.email},
        ip_address=client_ip,
    )
    await db.commit()

    return AdminLoginResponse(**tokens)


@router.get("/me", response_model=AdminMeResponse)
async def admin_me(admin: CurrentAdmin) -> AdminMeResponse:
    """Return the current admin user's profile.

    Used by the admin frontend to verify session and display user info.
    """
    return AdminMeResponse(
        id=admin.id,
        email=admin.email,
        first_name=admin.first_name,
        last_name=admin.last_name,
        is_admin=admin.is_admin,
        created_at=admin.created_at,
    )
