from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration."""

    openai_api_key: str = "YOUR_OPENAI_API_KEY"

    default_model: str = "gpt-5"

    app_name: str = "Enterprise Agent Platform"

    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
