"""Application configuration using pydantic-settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
