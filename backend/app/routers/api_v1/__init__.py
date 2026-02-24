"""API v1 router aggregator. Mounted at /api/v1 in api and dev modes.

The router is included via app.include_router(api_v1_router) with no
additional prefix in main.py, so the full /api/v1 prefix lives here.
"""

from fastapi import APIRouter

from app.routers.api_v1 import api_keys
from app.routers.api_v1 import health

api_v1_router = APIRouter(prefix="/api/v1", tags=["API v1"])
api_v1_router.include_router(api_keys.router)
api_v1_router.include_router(health.router)
