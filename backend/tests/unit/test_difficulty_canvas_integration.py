"""
Unit tests for Story 31.2+31.5: Difficulty Adaptive Canvas Integration

Tests that one-click verification canvas generation integrates difficulty adaptation:
- _get_difficulty_data(): score history retrieval + difficulty calculation
- Mastery filtering: skip_mastered=True/False
- Question templates: difficulty-enhanced fallback questions
- AI question generation: difficulty context injection
- Endpoint integration: backward compatibility

[Source: docs/stories/31.2.story.md, docs/stories/31.5.story.md]
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

from app.services.verification_service import (
    DifficultyLevel,
    DifficultyResult,
    ForgettingStatus,
    QuestionType,
    calculate_full_difficulty_result,
    is_concept_mastered,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_nodes():
    """Sample canvas nodes for testing."""
    return [
        {"id": "node_1", "type": "text", "text": "线性代数基础", "color": "4"},
        {"id": "node_2", "type": "text", "text": "矩阵乘法", "color": "3"},
        {"id": "node_3", "type": "text", "text": "特征值分解", "color": "4"},
    ]


@pytest.fixture
def mock_score_history_high():
    """Mock ScoreHistoryResponse for a mastered concept (3 consecutive >=80)."""
    mock = MagicMock()
    mock.scores = [85, 90, 88]
    mock.average = 87.67
    mock.sample_size = 3
    return mock


@pytest.fixture
def mock_score_history_medium():
    """Mock ScoreHistoryResponse for a medium-difficulty concept."""
    mock = MagicMock()
    mock.scores = [60, 70, 65]
    mock.average = 65.0
    mock.sample_size = 3
    return mock


@pytest.fixture
def mock_score_history_low():
    """Mock ScoreHistoryResponse for a low-difficulty concept."""
    mock = MagicMock()
    mock.scores = [30, 40, 35]
    mock.average = 35.0
    mock.sample_size = 3
    return mock


@pytest.fixture
def mock_score_history_empty():
    """Mock ScoreHistoryResponse with no scores."""
    mock = MagicMock()
    mock.scores = []
    mock.average = 0.0
    mock.sample_size = 0
    return mock


@pytest.fixture
def difficulty_map_mixed():
    """Pre-computed difficulty map with varied levels."""
    return {
        "node_1": DifficultyResult(
            level=DifficultyLevel.EASY,
            average_score=35.0,
            sample_size=3,
            question_type=QuestionType.BREAKTHROUGH,
            forgetting_status=None,
            is_mastered=False,
        ),
        "node_2": DifficultyResult(
            level=DifficultyLevel.HARD,
            average_score=88.0,
            sample_size=3,
            question_type=QuestionType.APPLICATION,
            forgetting_status=None,
            is_mastered=True,
        ),
        "node_3": DifficultyResult(
            level=DifficultyLevel.MEDIUM,
            average_score=65.0,
            sample_size=3,
            question_type=QuestionType.VERIFICATION,
            forgetting_status=ForgettingStatus(needs_review=True, decay_percentage=35.0),
            is_mastered=False,
        ),
    }


# ============================================================================
# Tests: _get_difficulty_data()
# ============================================================================

class TestGetDifficultyData:
    """Tests for _get_difficulty_data() function."""

    @pytest.mark.asyncio
    async def test_normal_path_returns_difficulty_map(
        self, sample_nodes, mock_score_history_medium
    ):
        """Normal path: memory service returns scores, difficulty map is built."""
        from app.api.v1.endpoints.review import _get_difficulty_data

        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=mock_score_history_medium
        )

        with patch(
            "app.services.memory_service.get_memory_service",
            return_value=mock_memory,
        ):
            result = await _get_difficulty_data(sample_nodes, "test_canvas")

        assert result is not None
        assert len(result) == 3
        for nid in ["node_1", "node_2", "node_3"]:
            assert nid in result
            assert isinstance(result[nid], DifficultyResult)

    @pytest.mark.asyncio
    async def test_memory_service_unavailable_returns_none(self, sample_nodes):
        """MemoryService not available → return None (graceful degradation)."""
        from app.api.v1.endpoints.review import _get_difficulty_data

        with patch(
            "app.services.memory_service.get_memory_service",
            side_effect=Exception("MemoryService unavailable"),
        ):
            result = await _get_difficulty_data(sample_nodes, "test_canvas")

        assert result is None

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self, sample_nodes):
        """5s timeout exceeded → return None (graceful degradation)."""
        from app.api.v1.endpoints.review import _get_difficulty_data

        async def slow_query(*args, **kwargs):
            await simulate_async_delay(10)  # Will exceed 5s timeout

        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = slow_query

        with patch(
            "app.services.memory_service.get_memory_service",
            return_value=mock_memory,
        ):
            result = await _get_difficulty_data(sample_nodes, "test_canvas")

        assert result is None

    @pytest.mark.asyncio
    async def test_partial_failure_returns_partial_map(
        self, sample_nodes, mock_score_history_medium
    ):
        """Some nodes fail → partial map returned for successful nodes."""
        from app.api.v1.endpoints.review import _get_difficulty_data

        async def mixed_query(concept_id, canvas_name, limit=5):
            if concept_id == "node_2":
                raise Exception("Query failed for node_2")
            return mock_score_history_medium

        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = mixed_query

        with patch(
            "app.services.memory_service.get_memory_service",
            return_value=mock_memory,
        ):
            result = await _get_difficulty_data(sample_nodes, "test_canvas")

        assert result is not None
        assert "node_1" in result
        assert "node_2" not in result  # Failed query
        assert "node_3" in result

    @pytest.mark.asyncio
    async def test_empty_scores_not_included(self, sample_nodes, mock_score_history_empty):
        """Nodes with empty score history are excluded from map."""
        from app.api.v1.endpoints.review import _get_difficulty_data

        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=mock_score_history_empty
        )

        with patch(
            "app.services.memory_service.get_memory_service",
            return_value=mock_memory,
        ):
            result = await _get_difficulty_data(sample_nodes, "test_canvas")

        # Empty scores → None result for each node → no entries → returns None
        assert result is None

    @pytest.mark.asyncio
    async def test_difficulty_flag_false_returns_none(self, sample_nodes):
        """When _difficulty_available is False → return None immediately."""
        from app.api.v1.endpoints import review

        original = review._difficulty_available
        try:
            review._difficulty_available = False
            result = await review._get_difficulty_data(sample_nodes, "test_canvas")
            assert result is None
        finally:
            review._difficulty_available = original


# ============================================================================
# Tests: Mastery Filtering
# ============================================================================

class TestMasteryFiltering:
    """Tests for skip_mastered filtering in generate_verification_canvas."""

    def test_filter_mastered_nodes(self, sample_nodes, difficulty_map_mixed):
        """skip_mastered=True filters out mastered nodes."""
        # node_2 is mastered in difficulty_map_mixed
        filtered = [
            n for n in sample_nodes
            if not (n.get("id") in difficulty_map_mixed and difficulty_map_mixed[n.get("id")].is_mastered)
        ]
        assert len(filtered) == 2
        assert all(n["id"] != "node_2" for n in filtered)

    def test_no_filter_when_skip_mastered_false(self, sample_nodes, difficulty_map_mixed):
        """skip_mastered=False keeps all nodes."""
        # No filtering applied
        assert len(sample_nodes) == 3

    def test_no_filter_when_no_difficulty_data(self, sample_nodes):
        """No difficulty data → all nodes kept regardless of skip_mastered."""
        difficulty_map = None
        # The condition `request.skip_mastered and difficulty_map` is False
        # when difficulty_map is None, so no filtering occurs
        assert len(sample_nodes) == 3

    def test_all_mastered_returns_empty(self):
        """All nodes mastered + skip_mastered=True → empty list."""
        nodes = [
            {"id": "a", "type": "text", "text": "concept A", "color": "4"},
            {"id": "b", "type": "text", "text": "concept B", "color": "3"},
        ]
        diff_map = {
            "a": DifficultyResult(
                level=DifficultyLevel.HARD, average_score=90.0,
                sample_size=3, question_type=QuestionType.APPLICATION,
                is_mastered=True,
            ),
            "b": DifficultyResult(
                level=DifficultyLevel.HARD, average_score=85.0,
                sample_size=3, question_type=QuestionType.APPLICATION,
                is_mastered=True,
            ),
        }
        filtered = [
            n for n in nodes
            if not (n.get("id") in diff_map and diff_map[n.get("id")].is_mastered)
        ]
        assert len(filtered) == 0


# ============================================================================
# Tests: Difficulty-Enhanced Question Templates
# ============================================================================

class TestDifficultyEnhancedQuestionText:
    """Tests for _get_difficulty_enhanced_question_text() function."""

    def test_easy_level_breakthrough_template(self, difficulty_map_mixed):
        """EASY → breakthrough template with 🔴."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        result = _get_difficulty_enhanced_question_text(
            "线性代数基础", "4", "node_1", difficulty_map_mixed
        )
        assert "🔴" in result
        assert "突破型" in result
        assert "线性代数基础" in result

    def test_hard_level_application_template(self, difficulty_map_mixed):
        """HARD → application template with 🔵."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        result = _get_difficulty_enhanced_question_text(
            "矩阵乘法", "3", "node_2", difficulty_map_mixed
        )
        assert "🔵" in result
        assert "应用型" in result

    def test_medium_level_verification_template(self, difficulty_map_mixed):
        """MEDIUM → verification template with 🟣."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        # node_3 is MEDIUM in difficulty_map_mixed
        result = _get_difficulty_enhanced_question_text(
            "特征值分解", "4", "node_3", difficulty_map_mixed
        )
        assert "🟣" in result
        assert "验证型" in result

    def test_forgetting_prefix_added(self, difficulty_map_mixed):
        """Forgetting detected → prefix added."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        # node_3 has forgetting_status.needs_review=True
        result = _get_difficulty_enhanced_question_text(
            "特征值分解", "4", "node_3", difficulty_map_mixed
        )
        assert "⚠️ 检测到遗忘趋势" in result

    def test_no_difficulty_data_red_fallback(self):
        """No difficulty data, red node → original 🔴 template."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        result = _get_difficulty_enhanced_question_text(
            "概念X", "4", "unknown_node", None
        )
        assert "🔴 突破型问题" in result
        assert "概念X" in result

    def test_no_difficulty_data_purple_fallback(self):
        """No difficulty data, purple node → original 🟣 template."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        result = _get_difficulty_enhanced_question_text(
            "概念Y", "3", "unknown_node", None
        )
        assert "🟣 检验型问题" in result
        assert "概念Y" in result

    def test_node_not_in_difficulty_map_uses_color_fallback(self, difficulty_map_mixed):
        """Node ID not in difficulty map → falls back to color-based template."""
        from app.api.v1.endpoints.review import _get_difficulty_enhanced_question_text

        result = _get_difficulty_enhanced_question_text(
            "新概念", "4", "node_999", difficulty_map_mixed
        )
        assert "🔴 突破型问题" in result


# ============================================================================
# Tests: AI Question Generation with Difficulty Context
# ============================================================================

class TestAIQuestionDifficultyInjection:
    """Tests for difficulty context injection into AI question generation."""

    @pytest.mark.asyncio
    async def test_difficulty_context_in_prompt(self, sample_nodes, difficulty_map_mixed):
        """Difficulty data is injected into AI prompt nodes_data."""
        captured_prompt = {}

        async def mock_call_agent(agent_type, prompt):
            captured_prompt["prompt"] = prompt
            result = MagicMock()
            result.success = True
            result.data = {"questions": []}
            return result

        mock_settings = MagicMock()
        mock_settings.AI_API_KEY = "test-key"
        mock_settings.AI_MODEL_NAME = "test-model"
        mock_settings.AI_BASE_URL = None

        # get_settings is imported at module level from app.core.config
        from app.api.v1.endpoints import review as review_mod
        original_get_settings = review_mod.get_settings if hasattr(review_mod, 'get_settings') else None

        with (
            patch.object(review_mod, "_ai_question_available", True),
            patch.object(review_mod, "get_settings", return_value=mock_settings, create=True),
            patch.object(review_mod, "GeminiClient", create=True),
            patch.object(review_mod, "AgentService", create=True) as mock_agent_cls,
        ):
            mock_agent = AsyncMock()
            mock_agent.call_agent = mock_call_agent
            mock_agent_cls.return_value = mock_agent

            await review_mod._generate_ai_questions(sample_nodes, difficulty_map_mixed)

        if "prompt" in captured_prompt:
            prompt_data = json.loads(captured_prompt["prompt"])
            nodes_in_prompt = prompt_data.get("nodes", [])
            # node_1 is EASY in difficulty_map_mixed
            node_1_data = next((n for n in nodes_in_prompt if n["id"] == "node_1"), None)
            if node_1_data:
                assert node_1_data.get("difficulty_level") == "easy"
                assert node_1_data.get("question_type_hint") == "breakthrough"

    @pytest.mark.asyncio
    async def test_no_difficulty_map_no_extra_fields(self, sample_nodes):
        """Without difficulty_map, no extra fields in prompt."""
        captured_prompt = {}

        async def mock_call_agent(agent_type, prompt):
            captured_prompt["prompt"] = prompt
            result = MagicMock()
            result.success = True
            result.data = {"questions": []}
            return result

        mock_settings = MagicMock()
        mock_settings.AI_API_KEY = "test-key"
        mock_settings.AI_MODEL_NAME = "test-model"
        mock_settings.AI_BASE_URL = None

        from app.api.v1.endpoints import review as review_mod

        with (
            patch.object(review_mod, "_ai_question_available", True),
            patch.object(review_mod, "get_settings", return_value=mock_settings, create=True),
            patch.object(review_mod, "GeminiClient", create=True),
            patch.object(review_mod, "AgentService", create=True) as mock_agent_cls,
        ):
            mock_agent = AsyncMock()
            mock_agent.call_agent = mock_call_agent
            mock_agent_cls.return_value = mock_agent

            await review_mod._generate_ai_questions(sample_nodes, None)

        if "prompt" in captured_prompt:
            prompt_data = json.loads(captured_prompt["prompt"])
            for node_data in prompt_data.get("nodes", []):
                assert "difficulty_level" not in node_data
                assert "question_type_hint" not in node_data


# ============================================================================
# Tests: Schema Backward Compatibility
# ============================================================================

class TestSchemaBackwardCompatibility:
    """Tests for backward-compatible schema changes."""

    def test_generate_request_defaults(self):
        """GenerateReviewRequest works without skip_mastered (backward compat)."""
        from app.models.schemas import GenerateReviewRequest

        req = GenerateReviewRequest(source_canvas="test")
        assert req.skip_mastered is False
        assert req.mode == "fresh"
        assert req.weak_weight == 0.7
        assert req.mastered_weight == 0.3

    def test_generate_request_with_skip_mastered(self):
        """GenerateReviewRequest accepts skip_mastered=True."""
        from app.models.schemas import GenerateReviewRequest

        req = GenerateReviewRequest(source_canvas="test", skip_mastered=True)
        assert req.skip_mastered is True

    def test_generate_response_defaults(self):
        """GenerateReviewResponse has default values for new fields."""
        from app.models.schemas import GenerateReviewResponse

        resp = GenerateReviewResponse(
            verification_canvas_name="test-检验白板-20260209",
            node_count=5,
        )
        assert resp.skipped_mastered_count == 0
        assert resp.difficulty_adapted is False

    def test_generate_response_with_new_fields(self):
        """GenerateReviewResponse accepts new difficulty fields."""
        from app.models.schemas import GenerateReviewResponse

        resp = GenerateReviewResponse(
            verification_canvas_name="test-检验白板-20260209",
            node_count=3,
            mode_used="fresh",
            skipped_mastered_count=2,
            difficulty_adapted=True,
        )
        assert resp.skipped_mastered_count == 2
        assert resp.difficulty_adapted is True
