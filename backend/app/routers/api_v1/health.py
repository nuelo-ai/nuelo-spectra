"""API v1 health endpoint for service monitoring.

Used by Dokploy health checks when running in SPECTRA_MODE=api.
Returns service status with database connectivity check.
"""

from sqlalchemy import text

from app.config import get_settings
from app.dependencies import DbSession

from fastapi import APIRouter

router = APIRouter(tags=["API v1 Health"])


@router.get("/health")
async def api_v1_health(db: DbSession) -> dict:
    """Health check endpoint returning service status and DB connectivity.

    Returns:
        JSON with status, service name, version, and database connectivity.
    """
    settings = get_settings()
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    status = "healthy" if db_status == "connected" else "degraded"
    return {
        "status": status,
        "service": "spectra-api",
        "version": settings.app_version,
        "database": db_status,
    }
