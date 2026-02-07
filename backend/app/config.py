from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # Frontend
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] | str = ["http://localhost:3000"]

    # Email
    email_service_api_key: str = ""
    email_from: str = "noreply@spectra.app"

    # File Upload
    upload_dir: str = "uploads"
    max_file_size_mb: int = 50

    # LLM Provider
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    openrouter_api_key: str = ""
    agent_model: str = "claude-sonnet-4-20250514"
    agent_max_retries: int = 3

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "spectra-agents"
    langsmith_tracing: bool = False

    # Streaming
    stream_timeout_seconds: int = 180
    stream_ping_interval: int = 30

    # Sandbox
    e2b_api_key: str = ""
    sandbox_timeout_seconds: int = 60
    sandbox_memory_mb: int = 1024
    sandbox_max_retries: int = 2

    model_config = SettingsConfigDict(env_file=".env")

    def get_cors_origins(self) -> list[str]:
        """Parse CORS origins from JSON string or return list directly."""
        if isinstance(self.cors_origins, str):
            try:
                return json.loads(self.cors_origins)
            except json.JSONDecodeError:
                # If not JSON, treat as single origin
                return [self.cors_origins]
        return self.cors_origins


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
