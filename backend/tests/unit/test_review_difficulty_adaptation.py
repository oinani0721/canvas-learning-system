"""
Unit tests for Story 31.2+31.5: Difficulty Adaptation in review.py

Tests the new difficulty-related functions added to the review router:
- _get_difficulty_enhanced_question_text(): Question text generation per difficulty level
- _get_difficulty_data(): Score history retrieval with graceful degradation
- skip_mastered filtering in generate_verification_canvas

[Source: Code Review H4 fix - 2026-02-09]
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ===========================================================================
# Local stubs for DifficultyResult/DifficultyLevel/ForgettingStatus
# (avoid importing from verification_service which has heavy deps)
# ===========================================================================


class _DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class _ForgettingStatus:
    needs_review: bool
    decay_percentage: float


@dataclass
class _DifficultyResult:
    level: _DifficultyLevel
    average_score: float
    sample_size: int
    question_type: str
    forgetting_status: Optional[_ForgettingStatus] = None
    is_mastered: bool = False


# ===========================================================================
# Tests for _get_difficulty_enhanced_question_text
# ===========================================================================


class TestGetDifficultyEnhancedQuestionText:
    """Test difficulty-enhanced question text generation."""

    @pytest.fixture(autouse=True)
    def patch_difficulty_imports(self):
        """Patch DifficultyLevel into review module for function to work."""
        with patch(
            "app.api.v1.endpoints.review.DifficultyLevel", _DifficultyLevel
        ), patch(
            "app.api.v1.endpoints.review._difficulty_available", True
        ):
            yield

    def _call(self, original_text, node_color, node_id, difficulty_map=None):
        from app.api.v1.endpoints.review import (
            _get_difficulty_enhanced_question_text,
        )
        return _get_difficulty_enhanced_question_text(
            original_text, node_color, node_id, difficulty_map
        )

    def test_easy_level_returns_breakthrough_question(self):
        diff = _DifficultyResult(
            level=_DifficultyLevel.EASY,
            average_score=90.0,
            sample_size=5,
            question_type="breakthrough",
        )
        result = self._call("微积分", "4", "node1", {"node1": diff})
        assert "突破型" in result
        assert "微积分" in result

    def test_medium_level_returns_verification_question(self):
        diff = _DifficultyResult(
            level=_DifficultyLevel.MEDIUM,
            average_score=65.0,
            sample_size=3,
            question_type="verification",
        )
        result = self._call("线性代数", "3", "node2", {"node2": diff})
        assert "验证型" in result
        assert "线性代数" in result

    def test_hard_level_returns_application_question(self):
        diff = _DifficultyResult(
            level=_DifficultyLevel.HARD,
            average_score=40.0,
            sample_size=4,
            question_type="application",
        )
        result = self._call("概率论", "4", "node3", {"node3": diff})
        assert "应用型" in result
        assert "概率论" in result

    def test_forgetting_prefix_added_when_needs_review(self):
        diff = _DifficultyResult(
            level=_DifficultyLevel.MEDIUM,
            average_score=60.0,
            sample_size=3,
            question_type="verification",
            forgetting_status=_ForgettingStatus(needs_review=True, decay_percentage=30.0),
        )
        result = self._call("统计", "3", "node4", {"node4": diff})
        assert "遗忘趋势" in result

    def test_no_forgetting_prefix_when_not_needed(self):
        diff = _DifficultyResult(
            level=_DifficultyLevel.EASY,
            average_score=85.0,
            sample_size=5,
            question_type="breakthrough",
            forgetting_status=_ForgettingStatus(needs_review=False, decay_percentage=5.0),
        )
        result = self._call("集合论", "4", "node5", {"node5": diff})
        assert "遗忘趋势" not in result

    def test_no_difficulty_data_red_node_fallback(self):
        result = self._call("机器学习", "4", "node6", None)
        assert "突破型问题" in result
        assert "机器学习" in result

    def test_no_difficulty_data_purple_node_fallback(self):
        result = self._call("深度学习", "3", "node7", None)
        assert "检验型问题" in result
        assert "深度学习" in result

    def test_node_id_not_in_difficulty_map_falls_back(self):
        diff = _DifficultyResult(
            level=_DifficultyLevel.EASY,
            average_score=90.0,
            sample_size=5,
            question_type="breakthrough",
        )
        # node_id "missing" is not in the map
        result = self._call("概念X", "4", "missing", {"other_node": diff})
        assert "突破型问题" in result  # Falls back to color-based

    def test_empty_difficulty_map_falls_back(self):
        result = self._call("概念Y", "3", "node8", {})
        assert "检验型问题" in result


# ===========================================================================
# Tests for _get_difficulty_data
# ===========================================================================


class TestGetDifficultyData:
    """Test difficulty data retrieval with graceful degradation."""

    @pytest.mark.asyncio
    async def test_returns_none_when_difficulty_unavailable(self):
        with patch("app.api.v1.endpoints.review._difficulty_available", False):
            from app.api.v1.endpoints.review import _get_difficulty_data
            result = await _get_difficulty_data([], "test_canvas")
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_neo4j_not_configured(self):
        """H1 test: memory_service.neo4j is None should return None gracefully."""
        mock_memory = MagicMock()
        mock_memory.neo4j = None  # Neo4j not configured

        with patch("app.api.v1.endpoints.review._difficulty_available", True), \
             patch("app.services.memory_service.get_memory_service", return_value=mock_memory):
            from app.api.v1.endpoints.review import _get_difficulty_data
            result = await _get_difficulty_data(
                [{"id": "n1", "text": "test"}], "canvas"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_history(self):
        """When nodes have no score history, returns None."""
        mock_memory = MagicMock()
        mock_memory.neo4j = MagicMock()  # Neo4j is configured
        mock_memory.get_concept_score_history = AsyncMock(return_value=None)

        with patch("app.api.v1.endpoints.review._difficulty_available", True), \
             patch("app.services.memory_service.get_memory_service", return_value=mock_memory):
            from app.api.v1.endpoints.review import _get_difficulty_data
            result = await _get_difficulty_data(
                [{"id": "n1", "text": "test"}], "canvas"
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_node_list(self):
        """Empty node list returns None without calling memory service."""
        with patch("app.api.v1.endpoints.review._difficulty_available", True):
            from app.api.v1.endpoints.review import _get_difficulty_data
            result = await _get_difficulty_data([], "canvas")
            # Should return None since no nodes to query
            assert result is None

    @pytest.mark.asyncio
    async def test_skips_nodes_without_id(self):
        """Nodes without id field should be skipped."""
        mock_memory = MagicMock()
        mock_memory.neo4j = MagicMock()
        mock_memory.get_concept_score_history = AsyncMock(return_value=None)

        with patch("app.api.v1.endpoints.review._difficulty_available", True), \
             patch("app.services.memory_service.get_memory_service", return_value=mock_memory):
            from app.api.v1.endpoints.review import _get_difficulty_data
            result = await _get_difficulty_data(
                [{"text": "no id node"}], "canvas"
            )
            assert result is None


# ===========================================================================
# Tests for skip_mastered filtering logic
# ===========================================================================


class TestSkipMasteredFiltering:
    """Test the skip_mastered logic in generate_verification_canvas."""

    def test_skip_mastered_filters_mastered_nodes(self):
        """Mastered nodes should be removed when skip_mastered=True."""
        nodes = [
            {"id": "n1", "type": "text", "color": "4", "text": "A"},
            {"id": "n2", "type": "text", "color": "3", "text": "B"},
            {"id": "n3", "type": "text", "color": "4", "text": "C"},
        ]

        # n1 and n3 are mastered
        difficulty_map = {
            "n1": _DifficultyResult(
                level=_DifficultyLevel.EASY, average_score=90,
                sample_size=5, question_type="breakthrough", is_mastered=True
            ),
            "n2": _DifficultyResult(
                level=_DifficultyLevel.MEDIUM, average_score=65,
                sample_size=3, question_type="verification", is_mastered=False
            ),
            "n3": _DifficultyResult(
                level=_DifficultyLevel.EASY, average_score=95,
                sample_size=5, question_type="breakthrough", is_mastered=True
            ),
        }

        # Simulate the filtering logic from review.py Step 3.6
        filtered = [
            n for n in nodes
            if not (n.get("id") in difficulty_map and difficulty_map[n.get("id")].is_mastered)
        ]

        assert len(filtered) == 1
        assert filtered[0]["id"] == "n2"

    def test_skip_mastered_keeps_all_when_none_mastered(self):
        """When no nodes are mastered, all should remain."""
        nodes = [
            {"id": "n1", "type": "text", "color": "4", "text": "A"},
            {"id": "n2", "type": "text", "color": "3", "text": "B"},
        ]

        difficulty_map = {
            "n1": _DifficultyResult(
                level=_DifficultyLevel.HARD, average_score=40,
                sample_size=2, question_type="application", is_mastered=False
            ),
            "n2": _DifficultyResult(
                level=_DifficultyLevel.MEDIUM, average_score=60,
                sample_size=3, question_type="verification", is_mastered=False
            ),
        }

        filtered = [
            n for n in nodes
            if not (n.get("id") in difficulty_map and difficulty_map[n.get("id")].is_mastered)
        ]

        assert len(filtered) == 2

    def test_skip_mastered_handles_missing_difficulty_data(self):
        """Nodes not in difficulty_map should be kept."""
        nodes = [
            {"id": "n1", "type": "text", "color": "4", "text": "A"},
            {"id": "n2", "type": "text", "color": "3", "text": "B"},
        ]

        # Only n1 has difficulty data, n2 does not
        difficulty_map = {
            "n1": _DifficultyResult(
                level=_DifficultyLevel.EASY, average_score=90,
                sample_size=5, question_type="breakthrough", is_mastered=True
            ),
        }

        filtered = [
            n for n in nodes
            if not (n.get("id") in difficulty_map and difficulty_map[n.get("id")].is_mastered)
        ]

        assert len(filtered) == 1
        assert filtered[0]["id"] == "n2"
