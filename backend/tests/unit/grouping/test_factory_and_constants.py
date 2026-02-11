# Canvas Learning System - Factory & Constants Tests
# Split from test_intelligent_grouping_service.py (EPIC-33 P1-6)
"""Tests for factory function, constants, and path resolution."""

import platform
from pathlib import Path

import pytest

from app.services.intelligent_grouping_service import (
    AGENT_KEYWORD_MAPPING,
    AVERAGE_AGENT_PROCESSING_SECONDS,
    DEFAULT_AGENT,
    GROUP_EMOJI_MAPPING,
    HIGH_KEYWORDS,
    SILHOUETTE_QUALITY_THRESHOLD,
    URGENT_KEYWORDS,
    IntelligentGroupingService,
    get_intelligent_grouping_service,
)


class TestFactoryFunction:
    """Tests for factory function."""

    def test_get_intelligent_grouping_service(self):
        """Test factory function creates service instance."""
        service = get_intelligent_grouping_service("/test/path")
        assert isinstance(service, IntelligentGroupingService)
        assert service.canvas_base_path == Path("/test/path")

    def test_get_intelligent_grouping_service_default_path(self):
        """Test factory function with default path."""
        service = get_intelligent_grouping_service()
        assert isinstance(service, IntelligentGroupingService)


class TestConstants:
    """Tests for service constants."""

    def test_average_agent_processing_seconds(self):
        """Verify AVERAGE_AGENT_PROCESSING_SECONDS is configured."""
        assert AVERAGE_AGENT_PROCESSING_SECONDS == 10

    def test_silhouette_quality_threshold(self):
        """Verify SILHOUETTE_QUALITY_THRESHOLD is configured."""
        assert SILHOUETTE_QUALITY_THRESHOLD == 0.3

    def test_agent_keyword_mapping_contains_all_agents(self):
        """Verify AGENT_KEYWORD_MAPPING has all expected agents."""
        expected_agents = [
            "comparison-table",
            "oral-explanation",
            "example-teaching",
            "clarification-path",
            "memory-anchor",
            "deep-decomposition",
        ]
        for agent in expected_agents:
            assert agent in AGENT_KEYWORD_MAPPING

    def test_default_agent_configured(self):
        """Verify DEFAULT_AGENT is configured."""
        assert DEFAULT_AGENT == "four-level-explanation"

    def test_priority_keywords_configured(self):
        """Verify priority keywords are configured."""
        assert "错误" in URGENT_KEYWORDS
        assert "复习" in HIGH_KEYWORDS

    def test_group_emoji_mapping_configured(self):
        """Verify GROUP_EMOJI_MAPPING is configured."""
        assert GROUP_EMOJI_MAPPING["comparison-table"] == "📊"
        assert GROUP_EMOJI_MAPPING["oral-explanation"] == "📖"


class TestPathResolution:
    """Tests for canvas path resolution."""

    def test_resolve_relative_path(self, service: IntelligentGroupingService):
        """Test resolving relative path."""
        result = service._resolve_canvas_path("test.canvas")
        assert result == Path("/test/path/test.canvas")

    def test_resolve_absolute_path(self, service: IntelligentGroupingService):
        """Test resolving absolute path (unchanged)."""
        result = service._resolve_canvas_path("/absolute/path/test.canvas")
        assert result == Path("/absolute/path/test.canvas")

    def test_resolve_nested_path(self, service: IntelligentGroupingService):
        """Test resolving nested relative path."""
        result = service._resolve_canvas_path("数学/离散数学.canvas")
        assert result == Path("/test/path/数学/离散数学.canvas")


class TestAbsolutePathCoverage:
    """Additional tests for absolute path handling in _resolve_canvas_path."""

    def test_resolve_windows_absolute_path(self, service: IntelligentGroupingService):
        """Test resolving Windows-style absolute path."""
        result = service._resolve_canvas_path("C:\\Users\\test\\canvas.canvas")
        assert "canvas.canvas" in str(result)

    def test_resolve_unix_absolute_path(self):
        """Test resolving Unix-style absolute path on any platform."""
        service = IntelligentGroupingService("/base/path")
        result = service._resolve_canvas_path("/absolute/test.canvas")
        if platform.system() == "Windows":
            assert "absolute" in str(result) and "test.canvas" in str(result)
        else:
            assert str(result) == "/absolute/test.canvas"
