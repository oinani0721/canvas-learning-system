"""
Integration tests for Story 31.5: Difficulty Adaptive Algorithm Integration

Tests the integration of difficulty adaptation into VerificationService methods:
- _get_difficulty_for_concept() (memory service query + calculation)
- generate_question_with_rag() with return_difficulty_info=True
- _build_difficulty_aware_prompt() (prompt construction)
- _build_question_response_with_difficulty() (response building)
- start_session() with include_mastered=False (mastery filtering)

[Source: docs/stories/31.5.story.md#Task-7, Task-5.3, Task-5.4]
"""

import pytest
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import List

from app.services.verification_service import (
    VerificationService,
    DifficultyLevel,
    DifficultyResult,
    QuestionType,
    ForgettingStatus,
    calculate_full_difficulty_result,
    is_concept_mastered,
)


@dataclass
class MockScoreHistoryResponse:
    """Mock ScoreHistoryResponse for testing."""
    concept_id: str = "test-concept"
    canvas_name: str = "test.canvas"
    scores: List[int] = None
    timestamps: List[str] = None
    average: float = 0.0
    sample_size: int = 0

    def __post_init__(self):
        if self.scores is None:
            self.scores = []
        if self.timestamps is None:
            self.timestamps = []


def _make_service(**kwargs) -> VerificationService:
    """Create a VerificationService with mocked dependencies."""
    return VerificationService(
        rag_service=kwargs.get("rag_service"),
        cross_canvas_service=kwargs.get("cross_canvas_service"),
        textbook_context_service=kwargs.get("textbook_context_service"),
        canvas_service=kwargs.get("canvas_service"),
        agent_service=kwargs.get("agent_service"),
        canvas_base_path=kwargs.get("canvas_base_path"),
        graphiti_client=kwargs.get("graphiti_client"),
        memory_service=kwargs.get("memory_service"),
    )


class TestGetDifficultyForConcept:
    """Tests for VerificationService._get_difficulty_for_concept() integration."""

    @pytest.mark.asyncio
    async def test_returns_default_when_no_memory_service(self):
        """AC-31.5.2: Default to medium when memory service unavailable."""
        service = _make_service(memory_service=None)

        result = await service._get_difficulty_for_concept(
            concept="test-concept",
            canvas_name="test.canvas"
        )

        assert result.level == DifficultyLevel.MEDIUM
        assert result.average_score == 0.0
        assert result.sample_size == 0
        assert result.is_mastered is False

    @pytest.mark.asyncio
    async def test_returns_default_when_no_score_history(self):
        """AC-31.5.1: Default to medium when no history exists."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=MockScoreHistoryResponse(sample_size=0, scores=[])
        )
        service = _make_service(memory_service=mock_memory)

        result = await service._get_difficulty_for_concept(
            concept="new-concept",
            canvas_name="test.canvas"
        )

        assert result.level == DifficultyLevel.MEDIUM
        assert result.sample_size == 0

    @pytest.mark.asyncio
    async def test_calculates_easy_difficulty(self):
        """AC-31.5.2: avg < 60 returns EASY."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=MockScoreHistoryResponse(
                scores=[40, 50, 55],
                sample_size=3,
                average=48.3
            )
        )
        service = _make_service(memory_service=mock_memory)

        result = await service._get_difficulty_for_concept(
            concept="hard-concept",
            canvas_name="test.canvas"
        )

        assert result.level == DifficultyLevel.EASY
        assert result.question_type == QuestionType.BREAKTHROUGH

    @pytest.mark.asyncio
    async def test_calculates_hard_difficulty_with_mastery(self):
        """AC-31.5.2, AC-31.5.4: avg >= 80 with 3 consecutive = mastered."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=MockScoreHistoryResponse(
                scores=[85, 88, 92],
                sample_size=3,
                average=88.3
            )
        )
        service = _make_service(memory_service=mock_memory)

        result = await service._get_difficulty_for_concept(
            concept="mastered-concept",
            canvas_name="test.canvas"
        )

        assert result.level == DifficultyLevel.HARD
        assert result.is_mastered is True

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_timeout(self):
        """ADR-009: Timeout returns default medium."""
        import asyncio

        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        service = _make_service(memory_service=mock_memory)

        result = await service._get_difficulty_for_concept(
            concept="slow-concept",
            canvas_name="test.canvas"
        )

        assert result.level == DifficultyLevel.MEDIUM
        assert result.sample_size == 0

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_exception(self):
        """ADR-009: Exception returns default medium."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            side_effect=RuntimeError("DB connection failed")
        )
        service = _make_service(memory_service=mock_memory)

        result = await service._get_difficulty_for_concept(
            concept="error-concept",
            canvas_name="test.canvas"
        )

        assert result.level == DifficultyLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_uses_node_id_when_provided(self):
        """AC-31.5.1: Prefer node_id over concept name for lookup."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=MockScoreHistoryResponse(
                scores=[70, 75],
                sample_size=2,
                average=72.5
            )
        )
        service = _make_service(memory_service=mock_memory)

        await service._get_difficulty_for_concept(
            concept="Concept Name",
            canvas_name="test.canvas",
            node_id="node-123"
        )

        mock_memory.get_concept_score_history.assert_called_once_with(
            concept_id="node-123",
            canvas_name="test.canvas",
            limit=5
        )


class TestBuildQuestionResponseWithDifficulty:
    """Tests for _build_question_response_with_difficulty."""

    def test_builds_response_with_difficulty(self):
        """AC-31.5.4: Response includes difficulty_level and forgetting_status."""
        service = _make_service()
        difficulty = DifficultyResult(
            level=DifficultyLevel.HARD,
            average_score=88.0,
            sample_size=5,
            question_type=QuestionType.APPLICATION,
            forgetting_status=ForgettingStatus(needs_review=False, decay_percentage=5.0),
            is_mastered=True
        )

        result = service._build_question_response_with_difficulty(
            "What is X?", difficulty
        )

        assert result["question"] == "What is X?"
        assert result["difficulty_level"] == "hard"
        assert result["question_type"] == "application"
        assert result["is_mastered"] is True
        assert result["forgetting_status"]["needs_review"] is False

    def test_builds_response_without_difficulty(self):
        """Fallback when no difficulty available."""
        service = _make_service()

        result = service._build_question_response_with_difficulty(
            "What is X?", None
        )

        assert result["question"] == "What is X?"
        assert result["difficulty_level"] == "medium"
        assert result["is_mastered"] is False


class TestBuildDifficultyAwarePrompt:
    """Tests for _build_difficulty_aware_prompt."""

    def test_easy_prompt_mentions_breakthrough(self):
        """AC-31.5.3: Easy difficulty generates breakthrough-type prompt."""
        service = _make_service()
        difficulty = DifficultyResult(
            level=DifficultyLevel.EASY,
            average_score=45.0,
            sample_size=3,
            question_type=QuestionType.BREAKTHROUGH,
            is_mastered=False
        )

        prompt = service._build_difficulty_aware_prompt("微积分", difficulty)

        assert "突破型" in prompt
        assert "核心概念" in prompt

    def test_hard_prompt_mentions_application(self):
        """AC-31.5.3: Hard difficulty generates application-type prompt."""
        service = _make_service()
        difficulty = DifficultyResult(
            level=DifficultyLevel.HARD,
            average_score=88.0,
            sample_size=5,
            question_type=QuestionType.APPLICATION,
            is_mastered=True
        )

        prompt = service._build_difficulty_aware_prompt("微积分", difficulty)

        assert "应用型" in prompt or "挑战" in prompt

    def test_forgetting_prompt_includes_warning(self):
        """AC-31.5.5: Forgetting detected adds review guidance to prompt."""
        service = _make_service()
        difficulty = DifficultyResult(
            level=DifficultyLevel.MEDIUM,
            average_score=75.0,
            sample_size=5,
            question_type=QuestionType.VERIFICATION,
            forgetting_status=ForgettingStatus(needs_review=True, decay_percentage=35.0),
            is_mastered=False
        )

        prompt = service._build_difficulty_aware_prompt("微积分", difficulty)

        assert "遗忘" in prompt
        assert "35.0" in prompt


class TestStartSessionMasteryFilter:
    """Tests for start_session() with include_mastered parameter (Task 5.3, 5.4)."""

    @pytest.mark.asyncio
    async def test_include_mastered_true_includes_all(self):
        """AC-31.5.4 Task 5.4: include_mastered=True includes all concepts."""
        mock_memory = AsyncMock()
        mock_canvas = AsyncMock()
        mock_agent = AsyncMock()
        mock_agent.call_agent = AsyncMock(return_value="test question")

        service = _make_service(
            memory_service=mock_memory,
            canvas_service=mock_canvas,
            agent_service=mock_agent
        )

        # Mock _extract_concepts_from_canvas
        service._extract_concepts_from_canvas = AsyncMock(
            return_value=["concept-a", "concept-b", "concept-c"]
        )
        # Mock generate_question_with_rag
        service.generate_question_with_rag = AsyncMock(return_value="Question 1?")

        result = await service.start_session(
            canvas_name="test.canvas",
            include_mastered=True
        )

        assert result["total_concepts"] == 3
        # Memory service should NOT be called for mastery checks
        mock_memory.get_concept_score_history.assert_not_called()

    @pytest.mark.asyncio
    async def test_include_mastered_false_filters_mastered(self):
        """AC-31.5.4 Task 5.3: include_mastered=False filters mastered concepts."""
        mock_memory = AsyncMock()

        # concept-a: mastered (3 consecutive >= 80)
        # concept-b: not mastered
        # concept-c: mastered
        async def mock_get_history(concept_id, canvas_name, limit=5):
            if concept_id == "concept-a":
                return MockScoreHistoryResponse(scores=[85, 88, 92], sample_size=3)
            elif concept_id == "concept-b":
                return MockScoreHistoryResponse(scores=[60, 65, 70], sample_size=3)
            elif concept_id == "concept-c":
                return MockScoreHistoryResponse(scores=[80, 85, 90], sample_size=3)
            return MockScoreHistoryResponse(scores=[], sample_size=0)

        mock_memory.get_concept_score_history = AsyncMock(side_effect=mock_get_history)

        service = _make_service(memory_service=mock_memory)
        service._extract_concepts_from_canvas = AsyncMock(
            return_value=["concept-a", "concept-b", "concept-c"]
        )
        service.generate_question_with_rag = AsyncMock(return_value="Question?")

        result = await service.start_session(
            canvas_name="test.canvas",
            include_mastered=False
        )

        # Only concept-b should remain (not mastered)
        assert result["total_concepts"] == 1

    @pytest.mark.asyncio
    async def test_include_mastered_false_keeps_all_when_all_mastered(self):
        """AC-31.5.4: When all concepts mastered, include all for review."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=MockScoreHistoryResponse(scores=[85, 90, 92], sample_size=3)
        )

        service = _make_service(memory_service=mock_memory)
        service._extract_concepts_from_canvas = AsyncMock(
            return_value=["concept-a", "concept-b"]
        )
        service.generate_question_with_rag = AsyncMock(return_value="Question?")

        result = await service.start_session(
            canvas_name="test.canvas",
            include_mastered=False
        )

        # All mastered -> include all anyway
        assert result["total_concepts"] == 2

    @pytest.mark.asyncio
    async def test_include_mastered_false_no_memory_service(self):
        """AC-31.5.4: Without memory service, include all concepts."""
        service = _make_service(memory_service=None)
        service._extract_concepts_from_canvas = AsyncMock(
            return_value=["concept-a", "concept-b"]
        )
        service.generate_question_with_rag = AsyncMock(return_value="Question?")

        result = await service.start_session(
            canvas_name="test.canvas",
            include_mastered=False
        )

        assert result["total_concepts"] == 2

    @pytest.mark.asyncio
    async def test_include_mastered_default_is_true(self):
        """AC-31.5.4 Task 5.4: Default is backward compatible (include all)."""
        mock_memory = AsyncMock()
        mock_memory.get_concept_score_history = AsyncMock(
            return_value=MockScoreHistoryResponse(scores=[85, 90, 92], sample_size=3)
        )

        service = _make_service(memory_service=mock_memory)
        service._extract_concepts_from_canvas = AsyncMock(
            return_value=["concept-a"]
        )
        service.generate_question_with_rag = AsyncMock(return_value="Question?")

        # Default call without include_mastered
        result = await service.start_session(canvas_name="test.canvas")

        assert result["total_concepts"] == 1
        # Should NOT call memory service for mastery checks
        mock_memory.get_concept_score_history.assert_not_called()
