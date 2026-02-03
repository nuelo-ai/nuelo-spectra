"""Health check endpoint for deployment monitoring."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint for deployment verification.

    Returns:
        Status and version information
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }
