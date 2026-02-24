"""API v1 router aggregator. Mounted at /api/v1 in api and dev modes."""

from fastapi import APIRouter

from app.routers.api_v1 import api_keys

api_v1_router = APIRouter(prefix="/v1", tags=["API v1"])
api_v1_router.include_router(api_keys.router)
