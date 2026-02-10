"""Provider-agnostic LLM factory for multi-provider support."""

from langchain_core.language_models import BaseChatModel
from typing import Any
import logging
import json
import time

logger = logging.getLogger("spectra.llm")


def classify_llm_error(error: Exception, provider: str) -> str:
    """Classify LLM error into error categories.

    Args:
        error: Exception raised during LLM call
        provider: Provider name (for context-specific classification)

    Returns:
        str: Error classification (network_error, auth_error, rate_limit,
             model_not_found, provider_error)
    """
    error_msg = str(error).lower()
    error_type = type(error).__name__.lower()

    # Network/connection errors
    if any(x in error_type for x in ["connecterror", "timeout", "connectionerror"]):
        return "network_error"

    # Authentication errors
    if any(x in error_msg for x in ["401", "403", "unauthorized", "invalid api key", "authentication"]):
        return "auth_error"

    # Rate limit errors
    if any(x in error_msg for x in ["429", "rate limit", "quota", "too many requests"]):
        return "rate_limit"

    # Model not found errors
    if any(x in error_msg for x in ["404", "model not found", "not found", "model_not_found"]):
        return "model_not_found"

    # Default to provider error
    return "provider_error"


class EmptyLLMResponseError(Exception):
    """Raised when an LLM returns empty content."""
    def __init__(self, provider: str, model: str, agent: str):
        self.provider = provider
        self.model = model
        self.agent = agent
        super().__init__(
            f"LLM returned empty response (provider={provider}, model={model}, agent={agent}). "
            f"This often happens with reasoning models that exhaust token budget on internal reasoning. "
            f"Try increasing max_tokens or using a non-reasoning model."
        )


def validate_llm_response(response, provider: str, model: str, agent: str) -> str:
    """Validate that an LLM response has non-empty content.

    Args:
        response: LangChain LLM response object
        provider: Provider name (for error context)
        model: Model name (for error context)
        agent: Agent name (for error context)

    Returns:
        str: The validated, non-empty response content

    Raises:
        EmptyLLMResponseError: If response.content is empty or whitespace-only
    """
    content = getattr(response, "content", None)
    if content is None or (isinstance(content, str) and not content.strip()):
        logger.error(json.dumps({
            "event": "llm_empty_response",
            "agent": agent,
            "provider": provider,
            "model": model,
            "has_content_attr": content is not None,
            "content_repr": repr(content)[:100] if content is not None else "None",
        }))
        raise EmptyLLMResponseError(provider, model, agent)
    return content if isinstance(content, str) else str(content)


async def invoke_with_logging(
    llm: BaseChatModel,
    messages: list,
    agent_name: str,
    provider: str,
    model: str,
):
    """Invoke LLM with structured metadata logging.

    Logs: timestamp, provider, model, agent, latency, status.
    Does NOT log: full prompts or responses (LangSmith handles that).

    Args:
        llm: LangChain chat model instance
        messages: List of messages to send
        agent_name: Name of the calling agent (for logging context)
        provider: Provider name (for logging)
        model: Model name (for logging)

    Returns:
        LLM response

    Raises:
        Exception: Re-raises any exception from LLM call after logging
    """
    start_time = time.time()

    try:
        response = await llm.ainvoke(messages)
        latency = time.time() - start_time

        # Log successful call metadata (NOT full content)
        logger.info(json.dumps({
            "event": "llm_call",
            "agent": agent_name,
            "provider": provider,
            "model": model,
            "status": "success",
            "latency_seconds": round(latency, 3),
        }))

        return response

    except Exception as e:
        latency = time.time() - start_time

        # Classify error type
        error_class = classify_llm_error(e, provider)

        # Log error metadata
        logger.error(json.dumps({
            "event": "llm_call",
            "agent": agent_name,
            "provider": provider,
            "model": model,
            "status": "error",
            "error_type": type(e).__name__,
            "error_class": error_class,
            "latency_seconds": round(latency, 3),
        }))

        raise


def get_llm(
    provider: str,
    model: str,
    api_key: str,
    **kwargs: Any
) -> BaseChatModel:
    """Create LLM instance based on provider.

    This factory function creates LangChain chat models for different providers,
    enabling agent code to be provider-agnostic. All providers return the same
    BaseChatModel interface.

    Args:
        provider: LLM provider name (anthropic, openai, google, ollama, openrouter)
        model: Model name/ID (e.g., "claude-sonnet-4-20250514", "gpt-4", "gemini-pro")
        api_key: API key for the provider (not required for ollama)
        **kwargs: Additional model parameters (max_tokens, temperature, etc.)
                 For ollama: include base_url kwarg for custom endpoint

    Returns:
        LangChain BaseChatModel instance

    Raises:
        ValueError: If provider is not supported

    Examples:
        >>> # Anthropic Claude
        >>> llm = get_llm("anthropic", "claude-sonnet-4-20250514", api_key)
        >>> # OpenAI GPT
        >>> llm = get_llm("openai", "gpt-4", api_key)
        >>> # Google Gemini
        >>> llm = get_llm("google", "gemini-pro", api_key)
        >>> # Ollama (local or remote)
        >>> llm = get_llm("ollama", "llama3.1", "", base_url="http://localhost:11434")
        >>> # OpenRouter (routes through OpenAI-compatible API)
        >>> llm = get_llm("openrouter", "anthropic/claude-3.5-sonnet", api_key)
    """
    provider = provider.lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, api_key=api_key, **kwargs)

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        # Detect OpenAI reasoning models and configure reasoning_effort
        # Reasoning models (o1, o3, o4-mini, gpt-5-nano, gpt-5-mini, etc.) use
        # internal chain-of-thought that consumes token budget. Without
        # reasoning_effort, they may exhaust budget on reasoning and return
        # empty content. Set reasoning_effort=low as default for these models.
        _reasoning_patterns = ("o1", "o3", "o4-mini", "gpt-5-nano", "gpt-5-mini")
        model_lower = model.lower()
        is_reasoning_model = any(model_lower.startswith(p) for p in _reasoning_patterns)
        if is_reasoning_model and "model_kwargs" not in kwargs:
            kwargs.setdefault("model_kwargs", {})
        if is_reasoning_model and "reasoning_effort" not in kwargs.get("model_kwargs", {}):
            kwargs.setdefault("model_kwargs", {})
            kwargs["model_kwargs"]["reasoning_effort"] = "low"
            logger.info(json.dumps({
                "event": "reasoning_model_config",
                "model": model,
                "reasoning_effort": "low",
            }))
        return ChatOpenAI(model=model, api_key=api_key, **kwargs)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, **kwargs)

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        # Ollama doesn't use api_key parameter - only model and base_url
        # Extract base_url from kwargs to avoid duplicate keyword argument
        base_url = kwargs.pop("base_url", None)
        return ChatOllama(model=model, base_url=base_url, **kwargs)

    elif provider == "openrouter":
        from langchain_openai import ChatOpenAI
        # OpenRouter uses OpenAI-compatible API with custom base_url
        # HTTP-Referer and X-Title headers are optional attribution fields
        # The URL https://spectra.app doesn't need to be registered - it's for analytics/leaderboard display
        # Update the URL if production domain changes. See: https://openrouter.ai/docs/api-reference/overview
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://spectra.app",
                "X-Title": "Spectra"
            },
            **kwargs
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: anthropic, openai, google, ollama, openrouter"
        )
