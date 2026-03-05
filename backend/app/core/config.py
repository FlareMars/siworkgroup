"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Annotated, Any

from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    APP_NAME: str = "SiWorkGroup"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    VERSION: str = "0.1.0"

    # ---------------------------------------------------------------------------
    # Security / JWT
    # ---------------------------------------------------------------------------
    SECRET_KEY: str = Field(
        default="change-me-in-production-must-be-at-least-32-chars",
        min_length=32,
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24h
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://siuser:sipass@localhost:5432/siworkgroup"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://siuser:sipass@localhost:5432/siworkgroup"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ---------------------------------------------------------------------------
    # Redis
    # ---------------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ---------------------------------------------------------------------------
    # CORS
    # ---------------------------------------------------------------------------
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # ---------------------------------------------------------------------------
    # OpenAI / Model Service
    # ---------------------------------------------------------------------------
    OPENAI_API_KEY: str = "sk-placeholder"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-4o"

    # ---------------------------------------------------------------------------
    # Docker / Sandbox
    # ---------------------------------------------------------------------------
    DOCKER_HOST: str = "unix:///var/run/docker.sock"
    SANDBOX_IMAGE: str = "siworkgroup/claw-sandbox:latest"
    SANDBOX_NETWORK: str = "siworkgroup_sandbox"
    SANDBOX_CPU_DEFAULT: str = "1.0"
    SANDBOX_MEMORY_DEFAULT: str = "2g"
    SANDBOX_DISK_DEFAULT: str = "10g"

    # ---------------------------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------------------------
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()