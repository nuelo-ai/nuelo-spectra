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
