"""Application configuration, loaded from environment / .env via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Values are read from environment variables and an optional `.env` file.
    Field names are case-insensitive (APP_NAME, app_name, ... all work).
    """

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "NexusSSD"
    version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    # ---- Database ----
    # Defaults match docker-compose; override with DATABASE_URL for local/SQLite runs.
    database_url: str = "postgresql+psycopg://nexus:nexus@localhost:5432/nexus"

    # ---- CORS ----
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # ---- AI providers (used from Phase 4 onward) ----
    openai_api_key: str | None = None
    llm_provider: str = "auto"  # auto | openai | local
    embedding_dim: int = 1536

    # ---- ML ----
    model_artifact_dir: str = "ml/artifacts"
    prediction_horizon_days: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, value: object) -> object:
        """Allow CORS_ORIGINS to be a comma-separated string in the environment."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (one per process)."""
    return Settings()


settings = get_settings()
