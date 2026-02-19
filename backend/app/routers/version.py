import os
from fastapi import APIRouter

router = APIRouter(tags=["Version"])


@router.get("/version")
async def get_version():
    """Returns application version and deployment environment."""
    return {
        "version": os.getenv("APP_VERSION", "dev"),
        "environment": os.getenv("SPECTRA_MODE", "dev"),
    }
