from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import auth, health

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup: verify database connection is configured
    # (actual connection happens on first request via get_db)
    yield
    # Shutdown: dispose of database engine
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Spectra API",
    version="0.1.0",
    description="AI-powered data analytics platform backend",
    lifespan=lifespan
)

# Add CORS middleware
# IMPORTANT: Must use explicit origins (not wildcard) with allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),  # Use method to parse JSON/list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Spectra API is running"}
