# Canvas Learning System - Configuration Tests
"""
Tests for the configuration module.

These tests verify that the configuration system correctly loads
and validates settings from environment variables.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#配置管理]
"""


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
