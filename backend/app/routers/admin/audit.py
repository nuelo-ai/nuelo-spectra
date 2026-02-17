"""Admin audit log listing endpoint with pagination and filtering."""

import math
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.dependencies import CurrentAdmin, DbSession
from app.models.admin_audit_log import AdminAuditLog
from app.models.user import User
from app.schemas.admin_audit import AuditLogEntry, AuditLogListResponse

router = APIRouter(prefix="/audit-log", tags=["Admin Audit Log"])


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    admin: CurrentAdmin,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    action: str | None = Query(default=None),
    admin_id: UUID | None = Query(default=None),
    target_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> AuditLogListResponse:
    """Return paginated audit log entries with optional filters.

    Supports filtering by action type, admin user, target type, and date range.
    Results are ordered by created_at descending (newest first).
    """
    # Base query with admin email join
    base_query = select(
        AdminAuditLog.id,
        AdminAuditLog.admin_id,
        User.email.label("admin_email"),
        AdminAuditLog.action,
        AdminAuditLog.target_type,
        AdminAuditLog.target_id,
        AdminAuditLog.details,
        AdminAuditLog.ip_address,
        AdminAuditLog.created_at,
    ).join(User, User.id == AdminAuditLog.admin_id, isouter=True)

    # Apply filters
    if action is not None:
        base_query = base_query.where(AdminAuditLog.action == action)
    if admin_id is not None:
        base_query = base_query.where(AdminAuditLog.admin_id == admin_id)
    if target_type is not None:
        base_query = base_query.where(AdminAuditLog.target_type == target_type)
    if date_from is not None:
        base_query = base_query.where(AdminAuditLog.created_at >= date_from)
    if date_to is not None:
        base_query = base_query.where(AdminAuditLog.created_at <= date_to)

    # Count total matching entries
    count_query = select(func.count()).select_from(AdminAuditLog)
    if action is not None:
        count_query = count_query.where(AdminAuditLog.action == action)
    if admin_id is not None:
        count_query = count_query.where(AdminAuditLog.admin_id == admin_id)
    if target_type is not None:
        count_query = count_query.where(AdminAuditLog.target_type == target_type)
    if date_from is not None:
        count_query = count_query.where(AdminAuditLog.created_at >= date_from)
    if date_to is not None:
        count_query = count_query.where(AdminAuditLog.created_at <= date_to)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Fetch paginated results
    offset = (page - 1) * page_size
    data_query = (
        base_query.order_by(AdminAuditLog.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(data_query)
    rows = result.all()

    items = [
        AuditLogEntry(
            id=row.id,
            admin_id=row.admin_id,
            admin_email=row.admin_email,
            action=row.action,
            target_type=row.target_type,
            target_id=row.target_id,
            details=row.details,
            ip_address=row.ip_address,
            created_at=row.created_at,
        )
        for row in rows
    ]

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
