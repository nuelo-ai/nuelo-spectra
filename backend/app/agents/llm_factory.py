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
        provider: LLM provider name (anthropic, openai, google)
        model: Model name/ID (e.g., "claude-sonnet-4-20250514", "gpt-4", "gemini-pro")
        api_key: API key for the provider
        **kwargs: Additional model parameters (max_tokens, temperature, etc.)

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

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: anthropic, openai, google"
        )
