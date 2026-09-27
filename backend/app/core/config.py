"""Application configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_NAME: str = "CloudForge AI"
    APP_VERSION: str = "0.1.0"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    DATABASE_URL: str = (
        "postgresql+psycopg://cloudforge:cloudforge@localhost:5432/cloudforge"
    )
    JWT_SECRET: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AI_PROVIDER: Literal["demo", "azure_openai", "openai"] = "demo"
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-12-01-preview"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    LOG_LEVEL: str = "INFO"
    SEED_DEMO: bool = False
    COOKIE_SECURE: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        """Rewrite Render-style DB URL schemes to SQLAlchemy's explicit dialect.

        Render's ``connectionString`` uses ``postgres://``; SQLAlchemy 2.x with
        the installed psycopg v3 driver needs ``postgresql+psycopg://``.
        SQLite URLs (and anything else) pass through untouched.
        """
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+psycopg://" + value[len("postgres://") :]
            if value.startswith("postgresql://"):
                return "postgresql+psycopg://" + value[len("postgresql://") :]
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.APP_ENV == "production":
        if not settings.JWT_SECRET or settings.JWT_SECRET == "change-me-in-production":
            raise RuntimeError(
                "JWT_SECRET must be set to a non-default value when APP_ENV=production"
            )
        origins = [o.strip() for o in settings.FRONTEND_URL.split(",") if o.strip()]
        if "*" in origins:
            raise RuntimeError(
                "FRONTEND_URL must not contain '*' when APP_ENV=production"
            )
    return settings
