"""Admin invitation management endpoints.

Provides endpoints for creating, listing, revoking, and resending
user invitations with audit logging and email delivery.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.config import Settings, get_settings
from app.dependencies import CurrentAdmin, DbSession
from app.schemas.invitation import (
    CreateInviteRequest,
    InviteListResponse,
    InviteResponse,
)
from app.services.admin.audit import log_admin_action
from app.services.admin.invitations import (
    DuplicateInviteError,
    create_invitation,
    list_invitations,
    resend_invitation,
    revoke_invitation,
)
from app.services.email import send_invite_email

router = APIRouter(prefix="/invitations", tags=["admin-invitations"])


def _invitation_to_response(inv) -> dict:
    """Convert an Invitation model to a response dict."""
    return {
        "id": inv.id,
        "email": inv.email,
        "status": inv.status,
        "created_at": inv.created_at,
        "expires_at": inv.expires_at,
        "accepted_at": inv.accepted_at,
    }


@router.post("", response_model=InviteResponse, status_code=201)
async def create_invitation_endpoint(
    body: CreateInviteRequest,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    settings: Settings = Depends(get_settings),
) -> InviteResponse:
    """Create an invitation and send invite email (INVITE-01)."""
    try:
        result = create_invitation(
            db, body.email, current_admin.id, settings
        )
        # Handle both sync and async
        if hasattr(result, "__await__"):
            result = await result
    except DuplicateInviteError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "message": str(e),
                "existing_invite_id": str(e.invite_id),
            },
        )
    except ValueError as e:
        error_msg = str(e)
        if "already registered" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    invitation = result["invitation"]
    raw_token = result["raw_token"]

    # Audit log (added to transaction before commit)
    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="create_invitation",
        target_type="invitation",
        target_id=str(invitation.id),
        details={"email": body.email},
        ip_address=client_ip,
    )

    # Commit BEFORE sending email (anti-pattern: send email after commit)
    await db.commit()

    # Build invite link and send email
    invite_link = f"{settings.frontend_url}/invite/{raw_token}"
    expiry_date = invitation.expires_at.strftime("%B %d, %Y")
    await send_invite_email(body.email, invite_link, expiry_date, settings)

    return InviteResponse(**_invitation_to_response(invitation))


@router.get("", response_model=InviteListResponse)
async def list_invitations_endpoint(
    db: DbSession,
    current_admin: CurrentAdmin,
    status: str | None = Query(
        default=None, pattern="^(pending|accepted|expired)$"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> InviteListResponse:
    """List invitations with optional status filter and pagination (INVITE-06)."""
    result = await list_invitations(db, status_filter=status, page=page, page_size=page_size)

    items = [
        InviteResponse(**_invitation_to_response(inv))
        for inv in result["items"]
    ]

    return InviteListResponse(
        items=items,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post("/{invite_id}/revoke", response_model=InviteResponse)
async def revoke_invitation_endpoint(
    invite_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
) -> InviteResponse:
    """Revoke a pending invitation (INVITE-07)."""
    try:
        invitation = await revoke_invitation(db, invite_id)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="revoke_invitation",
        target_type="invitation",
        target_id=str(invite_id),
        ip_address=client_ip,
    )
    await db.commit()

    return InviteResponse(**_invitation_to_response(invitation))


@router.post("/{invite_id}/resend", response_model=InviteResponse)
async def resend_invitation_endpoint(
    invite_id: UUID,
    request: Request,
    db: DbSession,
    current_admin: CurrentAdmin,
    settings: Settings = Depends(get_settings),
) -> InviteResponse:
    """Resend an invitation with a fresh token (INVITE-07)."""
    try:
        result = await resend_invitation(db, invite_id, current_admin.id, settings)
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    new_invitation = result["invitation"]
    raw_token = result["raw_token"]

    client_ip = request.client.host if request.client else None
    await log_admin_action(
        db,
        admin_id=current_admin.id,
        action="resend_invitation",
        target_type="invitation",
        target_id=str(invite_id),
        details={"new_invitation_id": str(new_invitation.id)},
        ip_address=client_ip,
    )
    await db.commit()

    # Send email AFTER commit
    invite_link = f"{settings.frontend_url}/invite/{raw_token}"
    expiry_date = new_invitation.expires_at.strftime("%B %d, %Y")
    await send_invite_email(
        new_invitation.email, invite_link, expiry_date, settings
    )

    return InviteResponse(**_invitation_to_response(new_invitation))
