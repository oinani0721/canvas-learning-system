# Canvas Learning System - Configuration Tests
"""
Tests for the configuration module.

These tests verify that the configuration system correctly loads
and validates settings from environment variables.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#配置管理]
[Source: docs/stories/21.5.2.story.md - AC-5 Unit Tests]
"""

import pytest

from app.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration class."""

    def test_settings_default_values(self):
        """Test that Settings has correct default values."""
        settings = Settings()

        assert settings.PROJECT_NAME == "Canvas Learning System API"
        assert settings.VERSION == "1.0.0"
        assert settings.DEBUG is False
        assert settings.LOG_LEVEL == "INFO"
        assert settings.API_V1_PREFIX == "/api/v1"
        assert settings.MAX_CONCURRENT_REQUESTS == 100

    def test_settings_cors_origins_list(self):
        """Test that CORS origins are correctly parsed to list."""
        settings = Settings(
            CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,app://obsidian.md"
        )

        origins = settings.cors_origins_list
        assert isinstance(origins, list)
        assert len(origins) == 3
        assert "http://localhost:3000" in origins
        assert "http://127.0.0.1:3000" in origins
        assert "app://obsidian.md" in origins

    def test_settings_cors_origins_with_whitespace(self):
        """Test that CORS origins handles whitespace correctly."""
        settings = Settings(
            CORS_ORIGINS="http://localhost:3000 , http://127.0.0.1:3000"
        )

        origins = settings.cors_origins_list
        assert len(origins) == 2
        assert "http://localhost:3000" in origins
        assert "http://127.0.0.1:3000" in origins

    def test_settings_cors_origins_empty_values(self):
        """Test that empty CORS origin values are filtered out."""
        settings = Settings(
            CORS_ORIGINS="http://localhost:3000,,http://127.0.0.1:3000,"
        )

        origins = settings.cors_origins_list
        assert len(origins) == 2

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self):
        """
        Test that get_settings returns the same cached instance.

        ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: lru_cache settings)
        """
        settings1 = get_settings()
        settings2 = get_settings()

        # Should be the exact same object (cached)
        assert settings1 is settings2


class TestSettingsOverride:
    """Test suite for settings override functionality."""

    def test_settings_can_be_overridden(self):
        """Test that settings can be created with custom values."""
        custom_settings = Settings(
            PROJECT_NAME="Test App",
            VERSION="2.0.0",
            DEBUG=True,
            LOG_LEVEL="DEBUG"
        )

        assert custom_settings.PROJECT_NAME == "Test App"
        assert custom_settings.VERSION == "2.0.0"
        assert custom_settings.DEBUG is True
        assert custom_settings.LOG_LEVEL == "DEBUG"

    def test_settings_partial_override(self):
        """Test that partial overrides preserve defaults."""
        custom_settings = Settings(DEBUG=True)

        # Overridden value
        assert custom_settings.DEBUG is True
        # Default values preserved
        assert custom_settings.PROJECT_NAME == "Canvas Learning System API"
        assert custom_settings.VERSION == "1.0.0"


# ============================================================================
# Story 21.5.2: AI_MODEL_NAME Validator Tests
# [Source: docs/stories/21.5.2.story.md - AC-1, AC-2, AC-5]
# ============================================================================


class TestAIModelNameValidator:
    """
    Test suite for AI_MODEL_NAME field validator.

    验证 AI_MODEL_NAME 字段验证器能正确检测并清理异常前缀。
    某些终端或配置工具可能在模型名称前添加前缀（如 [K1], [K2]），
    这会导致 API 调用失败。

    [Source: docs/stories/21.5.2.story.md - Task 1]
    [Source: backend/app/config.py:147-176 - validate_model_name]
    """

    def test_model_name_normal(self):
        """
        正常模型名称不应被修改。

        Given: AI_MODEL_NAME 设置为正常值 "gemini-2.0-flash-exp"
        When: Settings 实例化
        Then: AI_MODEL_NAME 保持不变
        """
        settings = Settings(AI_MODEL_NAME="gemini-2.0-flash-exp")
        assert settings.AI_MODEL_NAME == "gemini-2.0-flash-exp"

    def test_model_name_normal_gpt4(self):
        """
        GPT-4 模型名称不应被修改。

        Given: AI_MODEL_NAME 设置为 "gpt-4o"
        When: Settings 实例化
        Then: AI_MODEL_NAME 保持不变
        """
        settings = Settings(AI_MODEL_NAME="gpt-4o")
        assert settings.AI_MODEL_NAME == "gpt-4o"

    def test_model_name_normal_claude(self):
        """
        Claude 模型名称不应被修改。

        Given: AI_MODEL_NAME 设置为 "claude-3-5-sonnet-20241022"
        When: Settings 实例化
        Then: AI_MODEL_NAME 保持不变
        """
        settings = Settings(AI_MODEL_NAME="claude-3-5-sonnet-20241022")
        assert settings.AI_MODEL_NAME == "claude-3-5-sonnet-20241022"

    def test_model_name_with_k1_prefix(self):
        """
        [K1] 前缀应被自动清理。

        Given: AI_MODEL_NAME 设置为 "[K1]gemini-2.0-flash-exp"
        When: Settings 实例化
        Then: AI_MODEL_NAME 被清理为 "gemini-2.0-flash-exp"
        """
        settings = Settings(AI_MODEL_NAME="[K1]gemini-2.0-flash-exp")
        assert settings.AI_MODEL_NAME == "gemini-2.0-flash-exp"

    def test_model_name_with_k2_prefix(self):
        """
        [K2] 前缀应被自动清理。

        Given: AI_MODEL_NAME 设置为 "[K2]gpt-4o"
        When: Settings 实例化
        Then: AI_MODEL_NAME 被清理为 "gpt-4o"
        """
        settings = Settings(AI_MODEL_NAME="[K2]gpt-4o")
        assert settings.AI_MODEL_NAME == "gpt-4o"

    @pytest.mark.parametrize(
        "prefixed_name,expected_clean_name",
        [
            ("[K1]gemini-2.0-flash-exp", "gemini-2.0-flash-exp"),
            ("[K2]gpt-4o", "gpt-4o"),
            ("[TEST]claude-3-5-sonnet", "claude-3-5-sonnet"),
            ("[DEBUG]llama-3.1-70b", "llama-3.1-70b"),
            ("[PROD]mixtral-8x7b", "mixtral-8x7b"),
            ("[ENV]qwen-72b-chat", "qwen-72b-chat"),
        ],
        ids=[
            "K1_prefix_gemini",
            "K2_prefix_gpt4",
            "TEST_prefix_claude",
            "DEBUG_prefix_llama",
            "PROD_prefix_mixtral",
            "ENV_prefix_qwen",
        ],
    )
    def test_model_name_various_prefixes(self, prefixed_name: str, expected_clean_name: str):
        """
        各种方括号前缀都应被正确清理。

        此参数化测试验证多种常见的异常前缀格式都能被正确处理。

        [Source: docs/stories/21.5.2.story.md - AC-2 多种前缀测试]
        """
        settings = Settings(AI_MODEL_NAME=prefixed_name)
        assert settings.AI_MODEL_NAME == expected_clean_name

    def test_model_name_no_closing_bracket(self):
        """
        没有闭合方括号的名称不应被修改。

        Given: AI_MODEL_NAME 设置为 "[K1gemini-2.0-flash-exp" (无闭合括号)
        When: Settings 实例化
        Then: AI_MODEL_NAME 保持不变 (不匹配清理规则)
        """
        settings = Settings(AI_MODEL_NAME="[K1gemini-2.0-flash-exp")
        assert settings.AI_MODEL_NAME == "[K1gemini-2.0-flash-exp"

    def test_model_name_bracket_in_middle(self):
        """
        方括号在中间的名称不应被错误清理。

        Given: AI_MODEL_NAME 设置为 "gemini[K1]-2.0-flash"
        When: Settings 实例化
        Then: AI_MODEL_NAME 保持不变 (不以 [ 开头)
        """
        settings = Settings(AI_MODEL_NAME="gemini[K1]-2.0-flash")
        assert settings.AI_MODEL_NAME == "gemini[K1]-2.0-flash"

    def test_model_name_empty_prefix(self):
        """
        空方括号前缀应被清理。

        Given: AI_MODEL_NAME 设置为 "[]gemini-2.0-flash-exp"
        When: Settings 实例化
        Then: AI_MODEL_NAME 被清理为 "gemini-2.0-flash-exp"
        """
        settings = Settings(AI_MODEL_NAME="[]gemini-2.0-flash-exp")
        assert settings.AI_MODEL_NAME == "gemini-2.0-flash-exp"
