"""API v1 router aggregator. Mounted at /v1 on the backend.

Public frontend reaches these routes via proxy: /api/v1/* → strip /api → /v1/*
Direct backend access (e.g. SPECTRA_MODE=api) uses /v1/* directly.
"""

from fastapi import APIRouter

from app.routers.api_v1 import api_keys
from app.routers.api_v1 import health

api_v1_router = APIRouter(prefix="/v1", tags=["API v1"])
api_v1_router.include_router(api_keys.router)
api_v1_router.include_router(health.router)
