"""12-factor configuration for the samples integration, read from the environment."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration; every field is overridable via its upper-case env var."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    samples_api_base_url: str = (
        "https://raw.githubusercontent.com/cellsia/mini-nucleiq-code-challenge/main"
    )
    samples_api_timeout_seconds: float = 5.0
    samples_api_max_retries: int = 2
    samples_api_backoff_seconds: float = 0.2
