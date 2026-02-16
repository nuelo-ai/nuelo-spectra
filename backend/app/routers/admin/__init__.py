from fastapi import APIRouter
from app.routers.admin import auth as admin_auth
from app.routers.admin import credits as admin_credits

admin_router = APIRouter()
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_credits.router)
