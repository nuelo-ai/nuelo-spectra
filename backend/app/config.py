from functools import lru_cache
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App metadata
    app_version: str = "dev"

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

    # SMTP Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from_email: str = "noreply@spectra.app"
    smtp_from_name: str = "Spectra"

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

    # Session Memory
    context_window_tokens: int = 12000
    context_warning_threshold: float = 0.85

    # Suggestions
    suggestion_auto_send: bool = True

    # Web Search
    tavily_api_key: str = ""
    search_depth: str = "basic"
    search_max_per_query: int = 5
    search_daily_quota: int = 7
    search_num_results: int = 3
    search_timeout: float = 10.0

    # Admin / Split-Horizon
    spectra_mode: str = "dev"  # "public", "admin", "dev", or "api"
    admin_email: str = ""          # For seed-admin CLI
    admin_password: str = ""       # For seed-admin CLI
    admin_first_name: str = "Admin"  # For seed-admin CLI
    admin_last_name: str = "User"    # For seed-admin CLI

    @field_validator("spectra_mode")
    @classmethod
    def validate_spectra_mode(cls, v: str) -> str:
        """Reject unknown SPECTRA_MODE values at Settings construction."""
        allowed = ("public", "admin", "dev", "api")
        if v not in allowed:
            raise ValueError(
                f"SPECTRA_MODE must be one of {allowed}, got '{v}'"
            )
        return v

    @model_validator(mode="after")
    def validate_admin_credentials_for_admin_modes(self) -> "Settings":
        """Require ADMIN_EMAIL and ADMIN_PASSWORD when SPECTRA_MODE is dev or admin.

        This validator fires at Settings() construction (once, via lru_cache) so
        the process fails immediately at startup rather than at first admin request.
        """
        if self.spectra_mode in ("dev", "admin"):
            missing = []
            if not self.admin_email:
                missing.append("ADMIN_EMAIL")
            if not self.admin_password:
                missing.append("ADMIN_PASSWORD")
            if missing:
                raise ValueError(
                    f"{', '.join(missing)} must be set when SPECTRA_MODE is "
                    f"'{self.spectra_mode}'. Add "
                    f"{'them' if len(missing) > 1 else 'it'} to your .env file and restart."
                )
        return self

    admin_session_timeout_minutes: int = 30
    admin_cors_origin: str = "http://localhost:3001"  # Admin frontend origin

    # Scheduler
    enable_scheduler: bool = False  # Set ENABLE_SCHEDULER=true for credit reset job

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
