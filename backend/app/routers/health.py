"""Health check endpoint for deployment monitoring."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for deployment verification.

    Returns:
        Status and version information
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.app_version,
    }
