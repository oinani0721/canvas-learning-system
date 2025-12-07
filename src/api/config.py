"""
FastAPI Backend Configuration Module

Provides settings management using Pydantic Settings for environment variable
handling and configuration validation.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings)
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings)
    - Uses pydantic_settings.BaseSettings for environment variable loading
    - Supports .env file through model_config
    """

    # Application metadata
    PROJECT_NAME: str = Field(
        default="Canvas Learning System API",
        description="Application name shown in API docs"
    )
    PROJECT_DESCRIPTION: str = Field(
        default="FastAPI后端服务，提供Canvas操作、Agent调用和复习系统功能",
        description="Application description for OpenAPI docs"
    )
    VERSION: str = Field(
        default="1.0.0",
        description="API version"
    )

    # Server settings
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    PORT: int = Field(
        default=8000,
        description="Server port"
    )

    # API settings
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version 1 prefix"
    )

    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "app://obsidian.md"],
        description="Allowed CORS origins"
    )

    # Canvas settings
    CANVAS_BASE_PATH: str = Field(
        default="../笔记库",
        description="Base path for Canvas files"
    )

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings)
    Uses @lru_cache to ensure settings are only loaded once.

    Returns:
        Settings: Application settings instance
    """
    return Settings()


# Export settings instance for convenience
settings = get_settings()
