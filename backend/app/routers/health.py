"""Health check endpoints for deployment monitoring."""

import time
from datetime import datetime

import httpx
from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["Health"])
llm_router = APIRouter(tags=["Health"])

# Cache for LLM health check results (60-second TTL)
_health_cache = {"result": None, "timestamp": 0}
HEALTH_CACHE_TTL = 60  # seconds


@router.get("/health")
async def health_check():
    """Health check endpoint for deployment verification.

    Returns:
        Status and version information
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@llm_router.get("/health/llm")
async def llm_health_check():
    """LLM provider health check endpoint.

    Tests connectivity to each provider used by agents.
    Uses lightweight calls (model listing, not inference) to avoid consuming quota.
    Results cached for 60 seconds.

    Returns:
        Provider status dict with overall health and per-provider details.
    """
    # Check cache
    now = time.time()
    if _health_cache["result"] and (now - _health_cache["timestamp"]) < HEALTH_CACHE_TTL:
        return _health_cache["result"]

    from app.agents.config import get_agent_provider, load_prompts

    settings = get_settings()

    prompts = load_prompts()
    active_providers = {get_agent_provider(agent_name) for agent_name in prompts["agents"].keys()}

    provider_status = {}
    overall_status = "healthy"

    async with httpx.AsyncClient(timeout=5.0) as client:
        for provider in active_providers:
            start = time.time()
            try:
                if provider == "anthropic":
                    if not settings.anthropic_api_key:
                        raise ValueError("API key not configured")
                    response = await client.get(
                        "https://api.anthropic.com/v1/models",
                        headers={
                            "x-api-key": settings.anthropic_api_key,
                            "anthropic-version": "2023-06-01",
                        },
                    )
                    response.raise_for_status()

                elif provider == "openai":
                    if not settings.openai_api_key:
                        raise ValueError("API key not configured")
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                    )
                    response.raise_for_status()

                elif provider == "google":
                    if not settings.google_api_key:
                        raise ValueError("API key not configured")
                    response = await client.get(
                        f"https://generativelanguage.googleapis.com/v1/models?key={settings.google_api_key}"
                    )
                    response.raise_for_status()

                elif provider == "ollama":
                    response = await client.get(f"{settings.ollama_base_url}/api/tags")
                    response.raise_for_status()

                elif provider == "openrouter":
                    if not settings.openrouter_api_key:
                        raise ValueError("API key not configured")
                    response = await client.get(
                        "https://openrouter.ai/api/v1/models",
                        headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                    )
                    response.raise_for_status()

                latency_ms = round((time.time() - start) * 1000)
                provider_status[provider] = {"status": "healthy", "latency_ms": latency_ms}

            except Exception as e:
                overall_status = "degraded"
                error_msg = str(e)
                if isinstance(e, httpx.TimeoutException):
                    error_msg = "Request timeout"
                elif isinstance(e, httpx.ConnectError):
                    error_msg = "Connection refused"
                elif hasattr(e, "response") and e.response is not None:
                    error_msg = f"HTTP {e.response.status_code}"

                provider_status[provider] = {"status": "unhealthy", "error": error_msg}

    result = {
        "status": overall_status,
        "providers": provider_status,
        "checked_at": datetime.utcnow().isoformat() + "Z",
    }

    _health_cache["result"] = result
    _health_cache["timestamp"] = now

    return result
