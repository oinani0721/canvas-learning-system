# Canvas Learning System - Configuration Management
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings pydantic-settings)
"""
Application configuration using Pydantic Settings.

This module provides centralized configuration management for the Canvas Learning System
backend API. Settings are loaded from environment variables and .env files.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#配置管理]
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

import json
import logging
import os
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: settings BaseSettings)
# Source: "from pydantic_settings import BaseSettings, SettingsConfigDict"
from pydantic_settings import BaseSettings, SettingsConfigDict

# Logger for config validation warnings
# [Source: docs/stories/21.5.2.story.md - AC-1]
logger = logging.getLogger(__name__)

# Calculate absolute project root path for reliable path resolution
# This ensures paths work regardless of where the backend is started from
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/app/
_BACKEND_DIR = os.path.dirname(_CONFIG_DIR)  # backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)  # Canvas/


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

    # FIX-4.0: Use absolute path to avoid encoding issues with Chinese characters
    # The relative path "../笔记库" was causing 404 errors due to path resolution issues
    CANVAS_BASE_PATH: str = Field(
        default=os.path.join(_PROJECT_ROOT, "笔记库"),
        description="Absolute path to Canvas files directory"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # API Settings
    # ═══════════════════════════════════════════════════════════════════════════

    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="API version prefix path"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Field Validators
    # ═══════════════════════════════════════════════════════════════════════════

    @field_validator("API_V1_PREFIX")
    @classmethod
    def validate_api_prefix(cls, v: str) -> str:
        """
        Fix MSYS/Git Bash path conversion issue.

        On Windows with Git Bash, paths starting with '/' get converted to
        Windows paths (e.g., '/api/v1' becomes 'C:/Program Files/Git/api/v1').
        This validator detects and corrects such conversions.

        Args:
            v: The API prefix value (possibly converted by MSYS)

        Returns:
            Corrected API prefix starting with '/'
        """
        if v.startswith("/"):
            return v

        # Detect MSYS path conversion - look for /api/ in the converted path
        if "/api/" in v:
            # Extract the API path portion
            idx = v.find("/api/")
            return v[idx:]

        # Fallback: return default if path is completely invalid
        return "/api/v1"

    # ✅ Verified from Context7:/websites/pydantic_dev (topic: field_validator)
    # [Source: docs/stories/21.5.2.story.md - AC-1, AC-2]
    @field_validator("AI_MODEL_NAME")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """
        检测并清理AI模型名称中的异常前缀。

        某些终端或配置工具可能会在模型名称前添加前缀（如 [K1], [K2]），
        这会导致 API 调用失败。此验证器自动检测并清理这些前缀。

        异常前缀示例: [K1], [K2], [TEST]

        Args:
            v: 原始 AI_MODEL_NAME 值

        Returns:
            清理后的模型名称

        [Source: docs/prd/EPIC-21.5-AGENT-RELIABILITY-FIX.md#story-21-5-2]
        """
        # 检测方括号前缀模式
        if v.startswith("[") and "]" in v:
            bracket_end = v.index("]") + 1
            prefix = v[:bracket_end]
            clean_name = v[bracket_end:]
            logger.warning(
                f"AI_MODEL_NAME contains abnormal prefix '{prefix}', "
                f"auto-cleaned to '{clean_name}'"
            )
            return clean_name
        return v

    MAX_CONCURRENT_REQUESTS: int = Field(
        default=100,
        description="Maximum concurrent requests limit"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Rollback Settings (Story 18.5)
    # [Source: docs/architecture/rollback-recovery-architecture.md:100-150]
    # ═══════════════════════════════════════════════════════════════════════════

    ROLLBACK_HISTORY_LIMIT: int = Field(
        default=100,
        description="Maximum operation history records per Canvas"
    )

    ROLLBACK_SNAPSHOT_INTERVAL: int = Field(
        default=300,
        description="Auto snapshot interval in seconds (default: 5 minutes)"
    )

    ROLLBACK_MAX_SNAPSHOTS: int = Field(
        default=50,
        description="Maximum snapshots per Canvas before auto-cleanup"
    )

    ROLLBACK_GRAPHITI_TIMEOUT_MS: int = Field(
        default=200,
        description="Graphiti sync timeout in milliseconds"
    )

    ROLLBACK_ENABLE_GRAPHITI_SYNC: bool = Field(
        default=True,
        description="Enable Graphiti knowledge graph synchronization"
    )

    ROLLBACK_STORAGE_PATH: str = Field(
        default=".canvas-learning",
        description="Base path for rollback data storage (history/snapshots)"
    )

    ROLLBACK_ENABLE_AUTO_BACKUP: bool = Field(
        default=True,
        description="Create backup snapshot before rollback operations"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # AI Model Configuration (Multi-Provider Support)
    # Supports: google, openai, anthropic, openrouter, custom
    # [Source: Multi-Provider AI Architecture - flexible model configuration]
    # ═══════════════════════════════════════════════════════════════════════════

    AI_PROVIDER: str = Field(
        default="google",
        description="AI provider: google, openai, anthropic, openrouter, custom"
    )

    AI_MODEL_NAME: str = Field(
        default="gemini-2.0-flash-exp",
        description="AI model name (e.g., gemini-2.0-flash-exp, gpt-4o, claude-3-5-sonnet)"
    )

    AI_BASE_URL: str = Field(
        default="",
        description="AI API base URL (leave empty to use provider's default)"
    )

    AI_API_KEY: str = Field(
        default="",
        description="AI API key for the selected provider"
    )

    AGENT_MAX_TOKENS: int = Field(
        default=4000,
        description="Maximum tokens per Agent response"
    )

    AGENT_PROMPT_PATH: str = Field(
        default=os.path.join(_PROJECT_ROOT, ".claude", "agents"),
        description="Path to Agent prompt templates directory (absolute path)"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Legacy Settings (Deprecated - kept for backward compatibility)
    # ═══════════════════════════════════════════════════════════════════════════

    GEMINI_MODEL: str = Field(
        default="gemini-2.0-flash-exp",
        description="[DEPRECATED] Use AI_MODEL_NAME instead"
    )

    GOOGLE_API_KEY: str = Field(
        default="",
        description="[DEPRECATED] Use AI_API_KEY instead"
    )

    AGENT_MODEL: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="[DEPRECATED] Use AI_MODEL_NAME instead"
    )

    ANTHROPIC_API_KEY: str = Field(
        default="",
        description="[DEPRECATED] Use AI_API_KEY instead"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # Computed Properties
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Parse CORS_ORIGINS string into a list of origins.

        Supports two formats:
        1. Comma-separated: "http://localhost:3000,http://127.0.0.1:3000"
        2. JSON array: '["http://localhost:3000","http://127.0.0.1:3000"]'

        Returns:
            List of allowed CORS origin strings.
        """
        cors_value = self.CORS_ORIGINS.strip()

        # Try JSON array format first (handles system env variable override)
        if cors_value.startswith("["):
            try:
                origins = json.loads(cors_value)
                if isinstance(origins, list):
                    return [str(o).strip() for o in origins if o]
            except json.JSONDecodeError:
                pass  # Fall through to comma-separated parsing

        # Comma-separated format (from .env file)
        return [origin.strip() for origin in cors_value.split(",") if origin.strip()]

    # ═══════════════════════════════════════════════════════════════════════════
    # Lowercase Property Aliases (for convenience)
    # ═══════════════════════════════════════════════════════════════════════════

    @property
    def canvas_base_path(self) -> str:
        """Alias for CANVAS_BASE_PATH (lowercase for convenience)."""
        return self.CANVAS_BASE_PATH

    @property
    def api_v1_prefix(self) -> str:
        """Alias for API_V1_PREFIX (lowercase for convenience)."""
        return self.API_V1_PREFIX

    @property
    def max_concurrent_requests(self) -> int:
        """Alias for MAX_CONCURRENT_REQUESTS (lowercase for convenience)."""
        return self.MAX_CONCURRENT_REQUESTS

    @property
    def project_name(self) -> str:
        """Alias for PROJECT_NAME (lowercase for convenience)."""
        return self.PROJECT_NAME

    @property
    def debug(self) -> bool:
        """Alias for DEBUG (lowercase for convenience)."""
        return self.DEBUG

    @property
    def log_level(self) -> str:
        """Alias for LOG_LEVEL (lowercase for convenience)."""
        return self.LOG_LEVEL

    @property
    def rollback_history_limit(self) -> int:
        """Alias for ROLLBACK_HISTORY_LIMIT (lowercase for convenience)."""
        return self.ROLLBACK_HISTORY_LIMIT

    @property
    def rollback_snapshot_interval(self) -> int:
        """Alias for ROLLBACK_SNAPSHOT_INTERVAL (lowercase for convenience)."""
        return self.ROLLBACK_SNAPSHOT_INTERVAL

    @property
    def rollback_max_snapshots(self) -> int:
        """Alias for ROLLBACK_MAX_SNAPSHOTS (lowercase for convenience)."""
        return self.ROLLBACK_MAX_SNAPSHOTS

    @property
    def rollback_graphiti_timeout_ms(self) -> int:
        """Alias for ROLLBACK_GRAPHITI_TIMEOUT_MS (lowercase for convenience)."""
        return self.ROLLBACK_GRAPHITI_TIMEOUT_MS

    @property
    def rollback_enable_graphiti_sync(self) -> bool:
        """Alias for ROLLBACK_ENABLE_GRAPHITI_SYNC (lowercase for convenience)."""
        return self.ROLLBACK_ENABLE_GRAPHITI_SYNC

    @property
    def rollback_storage_path(self) -> str:
        """Alias for ROLLBACK_STORAGE_PATH (lowercase for convenience)."""
        return self.ROLLBACK_STORAGE_PATH

    @property
    def rollback_enable_auto_backup(self) -> bool:
        """Alias for ROLLBACK_ENABLE_AUTO_BACKUP (lowercase for convenience)."""
        return self.ROLLBACK_ENABLE_AUTO_BACKUP

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
