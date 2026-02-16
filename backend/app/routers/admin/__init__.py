from fastapi import APIRouter
from app.routers.admin import auth as admin_auth

admin_router = APIRouter()
admin_router.include_router(admin_auth.router)
