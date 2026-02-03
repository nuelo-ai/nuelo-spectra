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
