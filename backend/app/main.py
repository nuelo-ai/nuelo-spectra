import logging

# Configure logging for development - ensures INFO messages are visible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from contextlib import asynccontextmanager
from pathlib import Path

from starlette.formparsers import MultiPartParser

# Override Starlette default 1MB limit for file uploads (50MB)
MultiPartParser.max_file_size = 1024 * 1024 * 50
MultiPartParser.max_part_size = 1024 * 1024 * 50

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine
from app.routers import auth, chat, files, health

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

    # (actual database connection happens on first request via get_db)
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
app.include_router(files.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Spectra API is running"}
