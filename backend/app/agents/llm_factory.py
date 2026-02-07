"""Provider-agnostic LLM factory for multi-provider support."""

from langchain_core.language_models import BaseChatModel
from typing import Any


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
