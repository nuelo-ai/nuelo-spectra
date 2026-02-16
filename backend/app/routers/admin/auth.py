from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Admin Authentication"])


@router.post("/login")
async def admin_login():
    """Placeholder -- implemented in plan 26-03."""
    return {"status": "not_implemented"}
