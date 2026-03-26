from fastapi import APIRouter
from app.routers.admin import api_keys as admin_api_keys
from app.routers.admin import auth as admin_auth
from app.routers.admin import audit as admin_audit
from app.routers.admin import credits as admin_credits
from app.routers.admin import dashboard as admin_dashboard
from app.routers.admin import settings as admin_settings
from app.routers.admin import tiers as admin_tiers
from app.routers.admin import invitations as admin_invitations
from app.routers.admin import users as admin_users
from app.routers.admin import billing as admin_billing
from app.routers.admin import billing_settings as admin_billing_settings
from app.routers.admin import discount_codes as admin_discount_codes

admin_router = APIRouter()
admin_router.include_router(admin_api_keys.router)
admin_router.include_router(admin_auth.router)
admin_router.include_router(admin_audit.router)
admin_router.include_router(admin_billing.router)
admin_router.include_router(admin_billing_settings.router)
admin_router.include_router(admin_credits.router)
admin_router.include_router(admin_dashboard.router)
admin_router.include_router(admin_invitations.router)
admin_router.include_router(admin_settings.router)
admin_router.include_router(admin_tiers.router)
admin_router.include_router(admin_users.router)
admin_router.include_router(admin_discount_codes.router)
