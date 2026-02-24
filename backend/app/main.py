import logging

# Configure logging for development - ensures INFO messages are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from contextlib import asynccontextmanager
from pathlib import Path

from starlette.formparsers import MultiPartParser
from starlette.requests import Request

# Override Starlette default 1MB limit for file uploads (50MB)
MultiPartParser.max_file_size = 1024 * 1024 * 50
MultiPartParser.max_part_size = 1024 * 1024 * 50

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import auth, chat, chat_sessions, files, health, search, version

# Get settings
settings = get_settings()


async def validate_llm_configuration():
    """Validate LLM provider configuration at startup.

    Performs two-phase validation:
    1. Config validation: Verify all agent-referenced providers exist in registry
    2. Connectivity validation: Test active providers with lightweight calls

    Raises:
        ValueError: If any agent references unknown provider
        Exception: If any active provider fails connectivity test (invalid credentials, unreachable)
    """
    import httpx
    from app.agents.config import (
        load_provider_registry,
        load_prompts,
        get_agent_provider,
    )

    logger = logging.getLogger("spectra.llm")

    # Step 1: Config validation
    registry = load_provider_registry()
    prompts = load_prompts()
    available_providers = set(registry["providers"].keys())

    # Check all agent provider references
    for agent_name in prompts["agents"].keys():
        provider = get_agent_provider(agent_name)
        if provider not in available_providers:
            raise ValueError(
                f"LLM Configuration Error: Agent '{agent_name}' configured with "
                f"provider '{provider}' which is not in llm_providers.yaml. "
                f"Available providers: {', '.join(sorted(available_providers))}"
            )

    # Step 2: Collect active providers (only test providers actually used)
    active_providers = {get_agent_provider(agent_name) for agent_name in prompts["agents"].keys()}

    # Step 3: Connectivity validation per active provider
    async with httpx.AsyncClient(timeout=5.0) as client:
        for provider in active_providers:
            agents_using = [
                name for name in prompts["agents"].keys()
                if get_agent_provider(name) == provider
            ]

            try:
                if provider == "anthropic":
                    if not settings.anthropic_api_key:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: ANTHROPIC_API_KEY is not set. Get an API key from https://console.anthropic.com/"
                        )
                    response = await client.get(
                        "https://api.anthropic.com/v1/models",
                        headers={
                            "x-api-key": settings.anthropic_api_key,
                            "anthropic-version": "2023-06-01"
                        }
                    )
                    if response.status_code == 401:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: Invalid ANTHROPIC_API_KEY. Check your ANTHROPIC_API_KEY setting or get a new key from https://console.anthropic.com/"
                        )
                    response.raise_for_status()

                elif provider == "openai":
                    if not settings.openai_api_key:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: OPENAI_API_KEY is not set. Get an API key from https://platform.openai.com/"
                        )
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"}
                    )
                    if response.status_code == 401:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: Invalid OPENAI_API_KEY. Check your OPENAI_API_KEY setting or get a new key from https://platform.openai.com/"
                        )
                    response.raise_for_status()

                elif provider == "google":
                    if not settings.google_api_key:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: GOOGLE_API_KEY is not set. Get an API key from https://makersuite.google.com/app/apikey"
                        )
                    response = await client.get(
                        f"https://generativelanguage.googleapis.com/v1/models?key={settings.google_api_key}"
                    )
                    if response.status_code in (400, 403):
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: Invalid GOOGLE_API_KEY. Check your GOOGLE_API_KEY setting or get a new key from https://makersuite.google.com/app/apikey"
                        )
                    response.raise_for_status()

                elif provider == "ollama":
                    response = await client.get(f"{settings.ollama_base_url}/api/tags")
                    response.raise_for_status()

                elif provider == "openrouter":
                    if not settings.openrouter_api_key:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: OPENROUTER_API_KEY is not set. Get an API key from https://openrouter.ai/keys"
                        )
                    response = await client.get(
                        "https://openrouter.ai/api/v1/models",
                        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"}
                    )
                    if response.status_code == 401:
                        raise ValueError(
                            f"LLM Configuration Error: {provider} provider failed validation\n"
                            f"Agent(s) affected: {', '.join(agents_using)}\n"
                            f"Error: Invalid OPENROUTER_API_KEY. Check your OPENROUTER_API_KEY setting or get a new key from https://openrouter.ai/keys"
                        )
                    response.raise_for_status()

            except httpx.TimeoutException:
                logger.error(
                    f"LLM validation failed",
                    extra={"provider": provider, "error_type": "timeout", "agents": agents_using}
                )
                raise ValueError(
                    f"LLM Configuration Error: {provider} provider failed validation\n"
                    f"Agent(s) affected: {', '.join(agents_using)}\n"
                    f"Error: Request timeout. Check network connectivity or that {provider} service is accessible."
                )
            except httpx.ConnectError as e:
                logger.error(
                    f"LLM validation failed",
                    extra={"provider": provider, "error_type": "connection", "agents": agents_using}
                )
                if provider == "ollama":
                    raise ValueError(
                        f"LLM Configuration Error: {provider} provider failed validation\n"
                        f"Agent(s) affected: {', '.join(agents_using)}\n"
                        f"Error: Cannot connect to Ollama at {settings.ollama_base_url}. Check that Ollama is running and OLLAMA_BASE_URL is correct."
                    )
                else:
                    raise ValueError(
                        f"LLM Configuration Error: {provider} provider failed validation\n"
                        f"Agent(s) affected: {', '.join(agents_using)}\n"
                        f"Error: Connection failed - {str(e)}. Check network connectivity."
                    )
            except ValueError:
                # Re-raise our own error messages (auth/config errors)
                raise
            except Exception as e:
                logger.error(
                    f"LLM validation failed",
                    extra={
                        "provider": provider,
                        "error_type": type(e).__name__,
                        "agents": agents_using,
                        "error_message": str(e)
                    }
                )
                raise ValueError(
                    f"LLM Configuration Error: {provider} provider failed validation\n"
                    f"Agent(s) affected: {', '.join(agents_using)}\n"
                    f"Error: {type(e).__name__}: {str(e)}"
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup: create uploads directory if it doesn't exist
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)

    # NEW: Validate LLM provider configuration
    await validate_llm_configuration()
    logging.getLogger("spectra.llm").info("All LLM providers validated successfully")

    # Validate SMTP email configuration
    from app.services.email import validate_smtp_connection, is_smtp_configured
    smtp_configured = await validate_smtp_connection(settings)
    if smtp_configured:
        logging.getLogger("spectra.smtp").info("SMTP connection validated - email delivery active")
    elif is_smtp_configured(settings):
        logging.getLogger("spectra.smtp").warning("SMTP configured but validation failed - emails may fail")
    else:
        logging.getLogger("spectra.smtp").info("SMTP not configured - using dev mode (console logging)")

    # Initialize PostgreSQL checkpointer for session memory
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool
    from psycopg.rows import dict_row

    # Convert SQLAlchemy URL to psycopg format if needed
    db_url = settings.database_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    async with AsyncConnectionPool(
        conninfo=db_url,
        max_size=10,
        kwargs={"autocommit": True, "row_factory": dict_row}
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()  # Idempotent - creates tables if needed
        app.state.checkpointer = checkpointer
        logging.getLogger("spectra").info("PostgreSQL checkpointer initialized")

        # Start credit reset scheduler if enabled
        # Scheduler only makes sense in public or dev mode (processes user credits)
        # but we rely on the env var toggle rather than mode check
        if settings.enable_scheduler:
            from app.scheduler import setup_scheduler
            sched = setup_scheduler()
            sched.start()
            logging.getLogger("spectra.scheduler").info(
                "Credit reset scheduler started (15-min interval)"
            )

        yield

        # Shutdown scheduler if it was started
        if settings.enable_scheduler:
            from app.scheduler import scheduler
            scheduler.shutdown(wait=False)
            logging.getLogger("spectra.scheduler").info("Credit reset scheduler stopped")

    # Shutdown: dispose of database engine
    await engine.dispose()


# Create FastAPI application
app = FastAPI(
    title="Spectra API",
    version="0.1.0",
    description="AI-powered data analytics platform backend",
    lifespan=lifespan,
    redirect_slashes=False,
)


@app.middleware("http")
async def strip_trailing_slash(request: Request, call_next):
    """Normalize paths by stripping trailing slashes so the API works
    regardless of whether the caller includes one. Required because
    the Next.js route-handler proxy may or may not preserve them."""
    if request.url.path != "/" and request.url.path.endswith("/"):
        request.scope["path"] = request.url.path.rstrip("/")
    return await call_next(request)


# Determine operational mode
mode = settings.spectra_mode
if mode not in ("public", "admin", "dev", "api"):
    raise ValueError(f"Invalid SPECTRA_MODE: '{mode}'. Must be 'public', 'admin', 'dev', or 'api'")

logger = logging.getLogger("spectra.mode")
logger.info(f"Starting Spectra in {mode.upper()} mode")

# Add CORS middleware (mode-aware)
# IMPORTANT: Must use explicit origins (not wildcard) with allow_credentials=True
cors_origins = settings.get_cors_origins()
if mode in ("admin", "dev") and settings.admin_cors_origin:
    if settings.admin_cors_origin not in cors_origins:
        cors_origins.append(settings.admin_cors_origin)

if mode == "api":
    # API mode: Bearer token auth, no cookies needed, allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Admin-Token"],  # For sliding window token reissue
    )

# Health is always available (all modes)
app.include_router(health.router)
app.include_router(version.router)           # GET /version — for public frontend proxy
app.include_router(version.router, prefix="/api")  # GET /api/version — for admin frontend proxy

# Public routes (public and dev modes)
if mode in ("public", "dev"):
    app.include_router(auth.router)
    app.include_router(files.router)
    app.include_router(chat.router)
    app.include_router(chat_sessions.router)
    app.include_router(search.router)

    from app.routers import credits
    app.include_router(credits.router)

# Admin routes (admin and dev modes) -- lazy import to avoid loading admin code in public mode
if mode in ("admin", "dev"):
    from app.routers.admin import admin_router
    from app.middleware.admin_token import AdminTokenReissueMiddleware

    app.include_router(admin_router, prefix="/api/admin")
    app.add_middleware(AdminTokenReissueMiddleware)

# API v1 routes (api and dev modes) — external API access and API key management
if mode in ("api", "dev"):
    from app.routers.api_v1 import api_v1_router
    from app.middleware.api_usage import ApiUsageMiddleware

    app.include_router(api_v1_router)                    # /v1/* — public frontend proxy strips /api
    app.include_router(api_v1_router, prefix="/api")     # /api/v1/* — direct access and admin frontend
    app.add_middleware(ApiUsageMiddleware)                # Structured logging for all /v1/ requests

# In public mode, catch-all for /api/admin/* to log warnings and return 404
if mode == "public":
    from fastapi import HTTPException

    @app.api_route("/api/admin/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    async def admin_route_not_found(path: str):
        logging.getLogger("spectra.security").warning(
            f"Request to admin route /api/admin/{path} in public mode"
        )
        raise HTTPException(status_code=404, detail="Not Found")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Spectra API is running"}
