from fastapi import APIRouter
from app.routers.admin import auth as admin_auth
from app.routers.admin import credits as admin_credits
from app.routers.admin import settings as admin_settings
from app.routers.admin import tiers as admin_tiers
from app.routers.admin import invitations as admin_invitations
from app.routers.admin import users as admin_users

admin_router = APIRouter()
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_credits.router)
admin_router.include_router(admin_invitations.router)
admin_router.include_router(admin_settings.router)
admin_router.include_router(admin_tiers.router)
admin_router.include_router(admin_users.router)
