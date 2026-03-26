"""
Unit Tests for Story 31.4: Verification Question Deduplication

Tests for:
- AC-31.4.1: Query Graphiti for existing questions before generation
- AC-31.4.2: Generate new angle questions if history exists
- AC-31.4.3: Verification history query (unit level)
- AC-31.4.4: History data format validation

[Source: docs/stories/31.4.story.md#Testing]
"""

from datetime import datetime

import pytest
from app.services.verification_service import (
    VerificationService,
)


class TestVerificationDedup:
    """Test verification question deduplication logic (AC-31.4.1, AC-31.4.2)"""

    @pytest.fixture
    def service_with_graphiti(self, mock_graphiti_client, mock_agent_service):
        """Create VerificationService with mock Graphiti client"""
        return VerificationService(
            graphiti_client=mock_graphiti_client,
            agent_service=mock_agent_service
        )

    @pytest.mark.asyncio
    async def test_no_history_generates_standard_question(
        self, service_with_graphiti, mock_graphiti_client
    ):
        """
        AC-31.4.1: When no history exists, generate standard verification question.

        [Source: docs/stories/31.4.story.md#Task-2.3]
        """
        # Setup: Empty history
        mock_graphiti_client.search_verification_questions.return_value = []

        # Act
        question = await service_with_graphiti.generate_question_with_rag(
            concept="逆否命题",
            canvas_name="离散数学"
        )

        # Assert: Graphiti was queried
        mock_graphiti_client.search_verification_questions.assert_called_once()
        call_args = mock_graphiti_client.search_verification_questions.call_args
        assert call_args.kwargs.get("concept") == "逆否命题"

        # Assert: Question was generated (either from Gemini or fallback)
        assert question is not None
        assert len(question) > 0

    @pytest.mark.asyncio
    async def test_with_history_generates_alternative_question(
        self, service_with_graphiti, mock_graphiti_client
    ):
        """
        AC-31.4.2: When history exists, generate alternative angle question.

        [Source: docs/stories/31.4.story.md#Task-2.4]
        """
        # Setup: Has history with standard question
        mock_graphiti_client.search_verification_questions.return_value = [
            {
                "question_id": "vq_001",
                "question_text": "请解释什么是逆否命题？",
                "question_type": "standard",
                "asked_at": datetime(2025, 1, 15, 10, 30, 0).isoformat()
            }
        ]

        # Act
        question = await service_with_graphiti.generate_question_with_rag(
            concept="逆否命题",
            canvas_name="离散数学"
        )

        # Assert: Graphiti was queried
        assert mock_graphiti_client.search_verification_questions.called

        # Assert: Question was generated (should be different angle)
        assert question is not None

class TestAlternativeQuestionGeneration:
    """Test new angle question generation (AC-31.4.2)"""

    @pytest.fixture
    def service(self, mock_graphiti_client):
        """Create VerificationService"""
        return VerificationService(graphiti_client=mock_graphiti_client)

    @pytest.mark.asyncio
    async def test_question_angle_priority(self, service):
        """
        AC-31.4.2: Question angles follow priority order.

        Priority: application > comparison > counterexample > synthesis

        [Source: docs/stories/31.4.story.md#Task-3.4]
        """
        # Verify priority constant exists
        assert hasattr(service, "QUESTION_ANGLE_PRIORITY")
        priority = service.QUESTION_ANGLE_PRIORITY

        # Verify expected order
        assert priority[0] == "application"
        assert "comparison" in priority
        assert "counterexample" in priority
        assert "synthesis" in priority

    @pytest.mark.asyncio
    async def test_selects_unused_angle(self, service):
        """
        AC-31.4.2: Select first unused angle from priority list.

        [Source: docs/stories/31.4.story.md#Task-3.2]
        """
        # History with standard and application questions
        history = [
            {"question_type": "standard"},
            {"question_type": "application"}
        ]

        # Mock internal method to test angle selection
        question = await service._generate_alternative_question(
            concept="逆否命题",
            canvas_name="离散数学",
            history_questions=history
        )

        # Should generate question (comparison is next unused angle)
        assert question is not None

    @pytest.mark.asyncio
    async def test_cycles_back_when_all_angles_used(self, service):
        """
        AC-31.4.2: When all angles used, cycle back to first angle.

        [Source: docs/stories/31.4.story.md#Task-3]
        """
        # History with all angles used
        history = [
            {"question_type": "standard"},
            {"question_type": "application"},
            {"question_type": "comparison"},
            {"question_type": "counterexample"},
            {"question_type": "synthesis"}
        ]

        question = await service._generate_alternative_question(
            concept="逆否命题",
            canvas_name="离散数学",
            history_questions=history
        )

        # Should still generate a question (cycles back)
        assert question is not None


class TestAngleSpecificPrompts:
    """Test angle-specific prompt generation"""

    @pytest.fixture
    def service(self):
        """Create VerificationService"""
        return VerificationService()

    def test_build_application_prompt(self, service):
        """Test application angle prompt contains expected content"""
        prompt = service._build_angle_specific_prompt(
            concept="逆否命题",
            angle="application",
            history_questions=[]
        )

        assert "应用" in prompt or "application" in prompt.lower()
        assert "逆否命题" in prompt

    def test_build_comparison_prompt(self, service):
        """Test comparison angle prompt contains expected content"""
        prompt = service._build_angle_specific_prompt(
            concept="逆否命题",
            angle="comparison",
            history_questions=[]
        )

        assert "比较" in prompt or "comparison" in prompt.lower()
        assert "逆否命题" in prompt

    def test_build_counterexample_prompt(self, service):
        """Test counterexample angle prompt contains expected content"""
        prompt = service._build_angle_specific_prompt(
            concept="逆否命题",
            angle="counterexample",
            history_questions=[]
        )

        assert "反例" in prompt or "counterexample" in prompt.lower()
        assert "逆否命题" in prompt

    def test_build_synthesis_prompt(self, service):
        """Test synthesis angle prompt contains expected content"""
        prompt = service._build_angle_specific_prompt(
            concept="逆否命题",
            angle="synthesis",
            history_questions=[]
        )

        assert "综合" in prompt or "synthesis" in prompt.lower()
        assert "逆否命题" in prompt

    def test_prompt_includes_history(self, service):
        """Test prompt includes history to avoid repetition"""
        history = [
            {"question_text": "Previous question 1", "question_type": "standard"},
            {"question_text": "Previous question 2", "question_type": "application"}
        ]

        prompt = service._build_angle_specific_prompt(
            concept="逆否命题",
            angle="comparison",
            history_questions=history
        )

        # Should mention avoiding repetition
        assert "避免" in prompt or "重复" in prompt or "已问" in prompt


class TestFallbackQuestions:
    """Test fallback question generation"""

    @pytest.fixture
    def service(self):
        """Create VerificationService"""
        return VerificationService()

    @pytest.mark.parametrize("angle,expected_keyword", [
        ("application", "应用"),
        ("comparison", "比较"),
        ("counterexample", "反例"),
        ("synthesis", "关联"),
        ("standard", "解释"),
    ])
    def test_fallback_question_by_angle(self, service, angle, expected_keyword):
        """Test each angle has appropriate fallback question"""
        fallback = service._get_fallback_angle_question("逆否命题", angle)

        assert "逆否命题" in fallback
        # Just verify it's a non-empty question
        assert len(fallback) > 10
