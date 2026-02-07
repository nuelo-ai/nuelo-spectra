"""Provider-agnostic token counting for context management."""
import logging
from typing import Protocol
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)


class TokenCounter(Protocol):
    """Protocol for token counting implementations."""
    def count_messages(self, messages: list[BaseMessage]) -> int: ...


class TiktokenCounter:
    """Token counter using OpenAI's tiktoken library.

    Works as a reasonable approximation for all providers.
    For Anthropic models, applies a 1.1x scaling factor (Claude tokenizer
    tends to produce ~10% more tokens than tiktoken for the same text).
    """

    def __init__(self, model: str = "gpt-4", scale_factor: float = 1.0):
        import tiktoken
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoding = tiktoken.get_encoding("cl100k_base")
        self.scale_factor = scale_factor

    def count_messages(self, messages: list[BaseMessage]) -> int:
        """Count tokens in a list of messages."""
        total = 0
        for msg in messages:
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            # Count content tokens + message overhead (role, formatting)
            total += len(self.encoding.encode(f"{msg.type}: {content}"))
            total += 4  # Message formatting overhead per OpenAI spec
        return int(total * self.scale_factor)


def get_token_counter(provider: str, model: str) -> TokenCounter:
    """Factory function for provider-specific token counters.

    Args:
        provider: LLM provider name (anthropic, openai, google, ollama, openrouter)
        model: Model name/ID

    Returns:
        TokenCounter implementation appropriate for the provider
    """
    if provider == "openai":
        return TiktokenCounter(model=model, scale_factor=1.0)
    elif provider == "anthropic":
        # Anthropic uses slightly different tokenization - apply 1.1x scaling
        return TiktokenCounter(model="gpt-4", scale_factor=1.1)
    elif provider == "google":
        return TiktokenCounter(model="gpt-4", scale_factor=1.05)
    else:
        # Ollama, OpenRouter, etc. - use base approximation
        logger.info(f"Using approximate token counter for provider '{provider}'")
        return TiktokenCounter(model="gpt-4", scale_factor=1.0)
