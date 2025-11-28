# Canvas Learning System - Configuration Management
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings pydantic-settings)
"""
Application configuration using Pydantic Settings.

This module provides centralized configuration management for the Canvas Learning System
backend API. Settings are loaded from environment variables and .env files.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#配置管理]
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

from functools import lru_cache
from typing import List

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings)
# Source: "from pydantic_settings import BaseSettings, SettingsConfigDict"
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings)
    Pattern: Pydantic v2 BaseSettings with model_config for .env file loading.

    Attributes:
        PROJECT_NAME: Application name displayed in API responses
        PROJECT_DESCRIPTION: Application description for documentation
        VERSION: Application version (semver format)
        DEBUG: Enable debug mode (Swagger/ReDoc docs, detailed errors)
        LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        CORS_ORIGINS: Allowed CORS origins as comma-separated string
        CANVAS_BASE_PATH: Base path to Canvas files directory
        API_V1_PREFIX: API version prefix path
        MAX_CONCURRENT_REQUESTS: Maximum concurrent requests limit
    """

    # ═══════════════════════════════════════════════════════════════════════════
    # Application Settings
    # ═══════════════════════════════════════════════════════════════════════════

    PROJECT_NAME: str = Field(
        default="Canvas Learning System API",
        description="Application name displayed in API responses and Swagger UI"
    )

    PROJECT_DESCRIPTION: str = Field(
        default="Multi-agent learning system backend using Feynman method",
        description="Application description for API documentation"
    )

    VERSION: str = Field(
        default="1.0.0",
        description="Application version (semver format)"
    )

    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (Swagger/ReDoc docs, detailed errors)"
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CORS Settings
    # ═══════════════════════════════════════════════════════════════════════════

    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,app://obsidian.md",
        description="Allowed CORS origins (comma-separated)"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Canvas Settings
    # ═══════════════════════════════════════════════════════════════════════════

    CANVAS_BASE_PATH: str = Field(
        default="../笔记库",
        description="Base path to Canvas files directory"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # API Settings
    # ═══════════════════════════════════════════════════════════════════════════

    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version prefix path"
    )

    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100,
        description="Maximum concurrent requests limit"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Computed Properties
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS_ORIGINS string into a list of origins.

        Returns:
            List of allowed CORS origin strings.
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # ═══════════════════════════════════════════════════════════════════════════
    # Configuration
    # ═══════════════════════════════════════════════════════════════════════════

    # ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings .env file)
    # Pattern: model_config = SettingsConfigDict(env_file=".env")
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lru_cache Depends settings)
# Pattern: @lru_cache decorator ensures Settings is initialized only once
@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.

    Uses @lru_cache to ensure the Settings object is instantiated only once,
    preventing repeated reads from the .env file.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lru_cache settings)

    Returns:
        Settings: Cached application settings instance.
    """
    return Settings()


# Create default settings instance for direct import
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings module pattern)
settings = get_settings()
