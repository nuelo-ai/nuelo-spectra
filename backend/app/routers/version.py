from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(tags=["Version"])


@router.get("/version")
async def get_version():
    """Returns application version and deployment environment."""
    settings = get_settings()
    return {
        "version": settings.app_version,
        "environment": settings.spectra_mode,
    }
