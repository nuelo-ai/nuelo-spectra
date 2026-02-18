"""Admin audit logging utility.

Creates audit log entries within the caller's transaction.
Does NOT commit -- the caller's transaction includes the audit entry.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_audit_log import AdminAuditLog


async def log_admin_action(
    db: AsyncSession,
    admin_id: UUID,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Create an audit log entry. Do NOT commit -- let caller's transaction handle it.

    Args:
        db: Database session (caller manages transaction)
        admin_id: UUID of the admin performing the action
        action: Action identifier (e.g., "admin_login", "update_user")
        target_type: Type of entity being acted on (e.g., "session", "user")
        target_id: Optional ID of the target entity
        details: Optional dict with before/after values for mutations
        ip_address: Optional client IP address
    """
    entry = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
