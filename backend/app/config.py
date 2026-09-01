"""Application configuration using Pydantic settings."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str

    # AI Provider Configuration
    ai_provider: Literal["openai", "anthropic", "gemini"] = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    openai_model: str = "gpt-4"
    ai_timeout_seconds: float = 45.0
    ai_max_retries: int = 2
    ai_max_calls_per_session: int = 30

    # Application Configuration
    environment: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    # CORS Configuration
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Rate Limiting
    rate_limit_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
