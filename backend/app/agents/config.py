"""Configuration loader for agent prompts and allowlists."""

from functools import lru_cache
from pathlib import Path
import yaml


@lru_cache(maxsize=1)
def load_prompts() -> dict:
    """Load agent prompts from YAML configuration.

    Returns:
        dict: Parsed prompts configuration with structure:
            {
                "agents": {
                    "onboarding": {"system_prompt": str, "max_tokens": int},
                    "coding": {"system_prompt": str, "max_tokens": int},
                    ...
                }
            }

    Raises:
        FileNotFoundError: If prompts.yaml doesn't exist.
        yaml.YAMLError: If YAML is malformed.
    """
    config_dir = Path(__file__).parent.parent / "config"
    prompts_path = config_dir / "prompts.yaml"

    with open(prompts_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_provider_registry() -> dict:
    """Load LLM provider registry from YAML configuration.

    Returns:
        dict: Parsed provider registry with structure:
            {
                "providers": {
                    "anthropic": {"type": "anthropic", "default": true},
                    "ollama": {"type": "ollama", "base_url_env": "OLLAMA_BASE_URL"},
                    ...
                }
            }

    Raises:
        FileNotFoundError: If llm_providers.yaml doesn't exist.
        yaml.YAMLError: If YAML is malformed.
    """
    config_dir = Path(__file__).parent.parent / "config"
    providers_path = config_dir / "llm_providers.yaml"

    with open(providers_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_allowlist() -> dict:
    """Load library allowlist and unsafe operation lists from YAML.

    Returns:
        dict: Parsed allowlist configuration with structure:
            {
                "allowed_libraries": list[str],
                "unsafe_builtins": list[str],
                "unsafe_modules": list[str],
                "unsafe_operations": list[str]
            }

    Raises:
        FileNotFoundError: If allowlist.yaml doesn't exist.
        yaml.YAMLError: If YAML is malformed.
    """
    config_dir = Path(__file__).parent.parent / "config"
    allowlist_path = config_dir / "allowlist.yaml"

    with open(allowlist_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_agent_prompt(agent_name: str) -> str:
    """Get system prompt for a specific agent.

    Args:
        agent_name: Name of the agent (onboarding, coding, code_checker, data_analysis).

    Returns:
        str: System prompt for the agent.

    Raises:
        KeyError: If agent_name doesn't exist in configuration.
    """
    prompts = load_prompts()
    return prompts["agents"][agent_name]["system_prompt"]


def get_agent_max_tokens(agent_name: str) -> int:
    """Get max tokens configuration for a specific agent.

    Args:
        agent_name: Name of the agent.

    Returns:
        int: Maximum tokens for the agent's responses.

    Raises:
        KeyError: If agent_name doesn't exist in configuration.
    """
    prompts = load_prompts()
    return prompts["agents"][agent_name]["max_tokens"]


def get_allowed_libraries() -> set[str]:
    """Get set of allowed Python libraries.

    Returns:
        set[str]: Set of allowed library names (e.g., {'pandas', 'numpy', ...}).
    """
    allowlist = load_allowlist()
    return set(allowlist["allowed_libraries"])


def get_unsafe_builtins() -> set[str]:
    """Get set of unsafe builtin functions.

    Returns:
        set[str]: Set of unsafe builtin names (e.g., {'eval', 'exec', ...}).
    """
    allowlist = load_allowlist()
    return set(allowlist["unsafe_builtins"])


def get_unsafe_modules() -> set[str]:
    """Get set of unsafe modules.

    Returns:
        set[str]: Set of unsafe module names (e.g., {'os', 'sys', ...}).
    """
    allowlist = load_allowlist()
    return set(allowlist["unsafe_modules"])


def get_unsafe_operations() -> set[str]:
    """Get set of unsafe operations.

    Returns:
        set[str]: Set of unsafe operation names (e.g., {'open', 'file', ...}).
    """
    allowlist = load_allowlist()
    return set(allowlist["unsafe_operations"])


def get_default_provider() -> str:
    """Get default LLM provider from registry.

    Returns:
        str: Name of the default provider (e.g., "anthropic").

    Raises:
        ValueError: If no provider is marked as default in the registry.
    """
    registry = load_provider_registry()
    for provider_name, config in registry["providers"].items():
        if config.get("default", False):
            return provider_name
    raise ValueError("No default provider found in llm_providers.yaml")


def get_agent_provider(agent_name: str) -> str:
    """Get LLM provider for a specific agent.

    Args:
        agent_name: Name of the agent (onboarding, coding, code_checker, data_analysis).

    Returns:
        str: Provider name (e.g., "anthropic", "openai"). Falls back to default provider
             if agent doesn't specify a provider.

    Raises:
        KeyError: If agent_name doesn't exist in configuration.
    """
    prompts = load_prompts()
    agent_config = prompts["agents"][agent_name]
    return agent_config.get("provider", get_default_provider())


def get_agent_model(agent_name: str) -> str:
    """Get model name for a specific agent.

    Args:
        agent_name: Name of the agent.

    Returns:
        str: Model name/ID (e.g., "claude-sonnet-4-20250514", "gpt-4").

    Raises:
        KeyError: If agent_name doesn't exist or has no model field.
    """
    prompts = load_prompts()
    agent_config = prompts["agents"][agent_name]
    if "model" not in agent_config:
        raise KeyError(
            f"Agent '{agent_name}' has no 'model' field in prompts.yaml. "
            f"Please add a model configuration."
        )
    return agent_config["model"]


def get_agent_temperature(agent_name: str) -> float:
    """Get temperature setting for a specific agent.

    Args:
        agent_name: Name of the agent.

    Returns:
        float: Temperature value (0.0 = deterministic, higher = more creative).
               Defaults to 0.0 if not specified.

    Raises:
        KeyError: If agent_name doesn't exist in configuration.
    """
    prompts = load_prompts()
    agent_config = prompts["agents"][agent_name]
    return agent_config.get("temperature", 0.0)
