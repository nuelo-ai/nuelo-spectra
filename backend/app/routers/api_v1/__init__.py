"""API v1 router aggregator. Mounted at /v1 on the backend.

Public frontend reaches these routes via proxy: /api/v1/* → strip /api → /v1/*
Direct backend access (e.g. SPECTRA_MODE=api) uses /v1/* directly.

Note: api_keys router is intentionally excluded here. It is registered separately
in main.py only for public/dev modes — not exposed in SPECTRA_MODE=api.
"""

from fastapi import APIRouter

from app.routers.api_v1 import context, files, health, query

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(files.router)
api_v1_router.include_router(context.router)
api_v1_router.include_router(query.router)
