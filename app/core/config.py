"""Typed application configuration loaded from environment variables."""

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported application runtime environments."""

    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings with environment-variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NCCP_",
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    app_name: str = Field(
        default="Network Compliance Control Plane",
        min_length=1,
    )
    app_version: str = Field(default="0.1.0", min_length=1)
    environment: Environment = Environment.LOCAL
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return one immutable settings object for the process lifetime."""
    return Settings()
