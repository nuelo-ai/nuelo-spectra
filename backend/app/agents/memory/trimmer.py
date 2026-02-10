"""Message trimming utilities for context window management."""
from langchain_core.messages import BaseMessage, trim_messages
from app.agents.memory.token_counter import TokenCounter


async def trim_if_needed(
    messages: list[BaseMessage],
    max_tokens: int,
    token_counter: TokenCounter,
    user_confirmed: bool = False
) -> tuple[list[BaseMessage], bool]:
    """Trim messages if token limit exceeded.

    Two-phase flow:
    1. First call (user_confirmed=False): Returns (messages, True) if trimming needed
    2. Second call (user_confirmed=True): Performs trimming, returns (trimmed, False)

    Args:
        messages: Current conversation messages
        max_tokens: Maximum allowed tokens
        token_counter: Provider-specific token counter
        user_confirmed: Whether user has confirmed trimming

    Returns:
        Tuple of (messages, needs_confirmation):
        - If needs_confirmation is True, frontend should show confirmation dialog
        - If needs_confirmation is False, messages are ready to use (possibly trimmed)
    """
    current_tokens = token_counter.count_messages(messages)

    if current_tokens <= max_tokens:
        return messages, False

    if not user_confirmed:
        return messages, True  # Signal frontend to show confirmation

    # User confirmed - trim to 90% of limit for headroom
    target_tokens = int(max_tokens * 0.9)

    trimmed = trim_messages(
        messages,
        max_tokens=target_tokens,
        strategy="last",
        token_counter=lambda msgs: token_counter.count_messages(msgs),
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
    )

    return trimmed, False
