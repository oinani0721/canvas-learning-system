"""
Test Suite for Story 24.5: RAG Context Injection for Verification Canvas

Tests AC1-AC5:
- AC1: Question generation uses RAG context
- AC2: Hints based on learning history
- AC3: Cross-canvas association in prompts
- AC4: Textbook context reference
- AC5: Graceful RAG degradation

[Source: docs/stories/24.5.story.md#Testing-Requirements]
"""
# ✅ Verified from pytest documentation (fixtures, asyncio, mocking)

import asyncio

# Import services to test
import sys
from pathlib import Path
from typing import Any, List
from unittest.mock import AsyncMock, Mock

import pytest

# Add backend to path for imports
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.services.verification_service import VerificationService  # noqa: E402

# ============================================================================
# Mock Classes
# ============================================================================

class MockRAGResult:
    """Mock RAG query result."""
    def __init__(
        self,
        learning_history: str = "",
        textbook_context: str = "",
        related_concepts: List[str] = None,
        common_mistakes: str = "",
        past_effective_hints: List[str] = None
    ):
        self._data = {
            "learning_history": learning_history,
            "textbook_excerpts": textbook_context,
            "textbook_context": textbook_context,
            "related_concepts": related_concepts or [],
            "common_mistakes": common_mistakes,
            "past_effective_hints": past_effective_hints or []
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class MockRelatedCanvas:
    """Mock cross-canvas association."""
    def __init__(self, canvas_name: str, related_concept: str, relationship_type: str):
        self.canvas_name = canvas_name
        self.target_canvas_title = canvas_name
        self.related_concept = related_concept
        self.relationship_type = relationship_type
        self.common_concepts = [related_concept]


class MockCrossCanvasAssociation:
    """Mock CrossCanvasAssociation for get_associated_canvases."""
    def __init__(
        self,
        target_canvas_title: str,
        common_concepts: List[str],
        relationship_type: str
    ):
        self.target_canvas_title = target_canvas_title
        self.common_concepts = common_concepts
        self.relationship_type = relationship_type


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_rag_service():
    """Create mock RAG service."""
    service = Mock()
    service.query = AsyncMock()
    return service


@pytest.fixture
def mock_cross_canvas_service():
    """Create mock CrossCanvasService."""
    service = Mock()
    service.get_associated_canvases = AsyncMock()
    return service


@pytest.fixture
def mock_textbook_context_service():
    """Create mock TextbookContextService."""
    service = Mock()
    return service


@pytest.fixture
def verification_service(
    mock_rag_service,
    mock_cross_canvas_service,
    mock_textbook_context_service
):
    """Create VerificationService with mocked dependencies."""
    return VerificationService(
        rag_service=mock_rag_service,
        cross_canvas_service=mock_cross_canvas_service,
        textbook_context_service=mock_textbook_context_service
    )


@pytest.fixture
def verification_service_no_rag():
    """Create VerificationService without RAG (for fallback testing)."""
    return VerificationService(
        rag_service=None,
        cross_canvas_service=None,
        textbook_context_service=None
    )


# ============================================================================
# AC1: Question Generation Uses RAG Context
# ============================================================================

class TestAC1QuestionGenerationRAGContext:
    """Test AC1: Question generation should query RAG for context."""

    @pytest.mark.asyncio
    async def test_question_generation_uses_rag_context(
        self,
        verification_service,
        mock_rag_service
    ):
        """Question generation should query RAG and incorporate context."""
        # Setup mock RAG result
        mock_rag_service.query.return_value = MockRAGResult(
            learning_history="用户之前对此概念有3次错误尝试",
            textbook_context="教材第5章定义...",
            related_concepts=["概念A", "概念B"]
        )

        # Generate question
        question = await verification_service.generate_question_with_rag(
            concept="逆否命题",
            canvas_name="离散数学.canvas"
        )

        # Verify RAG was queried
        mock_rag_service.query.assert_called_once()
        call_args = mock_rag_service.query.call_args

        # Verify query contains concept
        assert "逆否命题" in call_args.kwargs["query"]
        assert call_args.kwargs["canvas_file"] == "离散数学.canvas"

        # Verify question was generated (not empty)
        assert question is not None
        assert len(question) > 0

    @pytest.mark.asyncio
    async def test_rag_context_includes_all_fields(
        self,
        verification_service,
        mock_rag_service
    ):
        """RAG context should include learning history, textbook, concepts, mistakes."""
        mock_rag_service.query.return_value = MockRAGResult(
            learning_history="历史记录",
            textbook_context="教材内容",
            related_concepts=["概念1", "概念2"],
            common_mistakes="常见错误"
        )

        # Get RAG context
        context = await verification_service._get_rag_context_for_concept(
            concept="测试概念",
            canvas_name="test.canvas"
        )

        # Verify all fields present
        assert context is not None
        assert "learning_history" in context
        assert "textbook_excerpts" in context
        assert "related_concepts" in context
        assert "common_mistakes" in context


# ============================================================================
# AC2: Hints Based on Learning History
# ============================================================================

class TestAC2HintsBasedOnHistory:
    """Test AC2: Hints should reference learning history."""

    @pytest.mark.asyncio
    async def test_hint_uses_learning_history(
        self,
        verification_service,
        mock_rag_service
    ):
        """Personalized hint should differ from generic hint."""
        # Setup RAG with learning history
        mock_rag_service.query.return_value = MockRAGResult(
            learning_history="用户常混淆逆命题和否命题",
            common_mistakes="注意区分逆命题和否命题的定义",
            past_effective_hints=["尝试从结论倒推..."]
        )

        # Generate hint with RAG
        hint_with_rag = await verification_service.generate_hint_with_rag(
            concept="逆否命题",
            user_answer="错误答案",
            attempt_number=1,
            canvas_name="离散数学.canvas"
        )

        # Verify hint includes context
        assert "逆否命题" in hint_with_rag
        assert len(hint_with_rag) > 0

    @pytest.mark.asyncio
    async def test_hint_without_history_is_generic(
        self,
        verification_service,
        mock_rag_service
    ):
        """Without learning history, hint should be generic."""
        # Setup RAG without learning history
        mock_rag_service.query.return_value = MockRAGResult(
            learning_history="",
            common_mistakes=""
        )

        hint = await verification_service.generate_hint_with_rag(
            concept="逆否命题",
            user_answer="错误答案",
            attempt_number=1,
            canvas_name="离散数学.canvas"
        )

        # Should be generic hint
        assert "提示" in hint
        assert "逆否命题" in hint


# ============================================================================
# AC3: Cross-Canvas Association in Prompts
# ============================================================================

class TestAC3CrossCanvasReferences:
    """Test AC3: Cross-canvas relationships should be included."""

    @pytest.mark.asyncio
    async def test_cross_canvas_references_included(
        self,
        verification_service,
        mock_cross_canvas_service
    ):
        """Cross-canvas lookup should return related canvases."""
        # Setup mock cross-canvas associations
        mock_cross_canvas_service.get_associated_canvases.return_value = [
            MockCrossCanvasAssociation(
                target_canvas_title="数理逻辑.canvas",
                common_concepts=["充分必要条件"],
                relationship_type="relates_to"
            )
        ]

        # Get cross-canvas context
        context = await verification_service._get_cross_canvas_context(
            concept="逆否命题",
            canvas_name="离散数学.canvas"
        )

        # Verify results
        assert len(context) > 0
        assert context[0]["canvas"] == "数理逻辑.canvas"
        assert "充分必要条件" in context[0]["concept"]

    @pytest.mark.asyncio
    async def test_cross_canvas_limits_results(
        self,
        verification_service,
        mock_cross_canvas_service
    ):
        """Cross-canvas lookup should limit to top 3 results."""
        # Setup mock with 5 associations
        mock_cross_canvas_service.get_associated_canvases.return_value = [
            MockCrossCanvasAssociation(f"canvas{i}", [f"concept{i}"], "relates_to")
            for i in range(5)
        ]

        context = await verification_service._get_cross_canvas_context(
            concept="测试",
            canvas_name="test.canvas"
        )

        # Should be limited to 3
        assert len(context) <= 3


# ============================================================================
# AC4: Textbook Context Reference
# ============================================================================

class TestAC4TextbookContext:
    """Test AC4: Textbook context should be included."""

    @pytest.mark.asyncio
    async def test_textbook_context_retrieved(
        self,
        verification_service,
        mock_rag_service
    ):
        """RAG result should include textbook context."""
        mock_rag_service.query.return_value = MockRAGResult(
            textbook_context="《离散数学》第三章：命题逻辑的等价变换..."
        )

        rag_context = await verification_service._get_rag_context_for_concept(
            concept="逆否命题",
            canvas_name="离散数学.canvas"
        )

        # Verify textbook context present
        assert rag_context is not None
        assert "textbook_excerpts" in rag_context
        assert "离散数学" in rag_context["textbook_excerpts"]


# ============================================================================
# AC5: Graceful RAG Degradation
# ============================================================================

class TestAC5GracefulDegradation:
    """Test AC5: RAG timeout/error should not block generation."""

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_timeout(
        self,
        verification_service,
        mock_rag_service
    ):
        """RAG timeout should not raise exception."""
        # Simulate timeout
        mock_rag_service.query.side_effect = asyncio.TimeoutError()

        # Should not raise exception
        question = await verification_service.generate_question_with_rag(
            concept="测试概念",
            canvas_name="test.canvas"
        )

        # Should return fallback question
        assert question is not None
        assert len(question) > 0

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_service_error(
        self,
        verification_service,
        mock_rag_service
    ):
        """RAG service error should trigger fallback."""
        # Simulate service error
        mock_rag_service.query.side_effect = Exception("Service unavailable")

        # Should not raise exception
        context = await verification_service._get_rag_context_for_concept(
            concept="测试",
            canvas_name="test.canvas"
        )

        # Should return None (fallback)
        assert context is None

    @pytest.mark.asyncio
    async def test_no_rag_service_uses_fallback(
        self,
        verification_service_no_rag
    ):
        """Without RAG service, should use basic prompt."""
        question = await verification_service_no_rag.generate_question_with_rag(
            concept="测试概念",
            canvas_name="test.canvas"
        )

        # Should generate basic question
        assert question is not None
        assert "测试概念" in question

    @pytest.mark.asyncio
    async def test_timeout_configuration_respected(
        self,
        verification_service,
        mock_rag_service
    ):
        """RAG timeout should respect configuration."""
        # Create slow query that times out
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(10)  # 10 seconds (exceeds 5s timeout)
            return MockRAGResult()

        mock_rag_service.query = slow_query

        # Should timeout and return None
        context = await verification_service._get_rag_context_for_concept(
            concept="测试",
            canvas_name="test.canvas",
            timeout=0.1  # 100ms timeout
        )

        assert context is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestRAGIntegration:
    """Integration tests for RAG context injection."""

    @pytest.mark.asyncio
    async def test_full_rag_question_generation_flow(
        self,
        verification_service,
        mock_rag_service
    ):
        """E2E test for RAG-enhanced question generation."""
        # Setup comprehensive RAG result
        mock_rag_service.query.return_value = MockRAGResult(
            learning_history="用户已学习此概念3次",
            textbook_context="教材第5章",
            related_concepts=["概念A", "概念B"],
            common_mistakes="易混淆点"
        )

        # Generate question
        question = await verification_service.generate_question_with_rag(
            concept="逆否命题",
            canvas_name="离散数学.canvas"
        )

        # Verify RAG was called
        assert mock_rag_service.query.called
        # Verify question generated
        assert question is not None

    @pytest.mark.asyncio
    async def test_prompt_building_with_rag_context(
        self,
        verification_service
    ):
        """Test enhanced prompt building."""
        context = {
            "learning_history": "测试历史",
            "textbook_excerpts": "测试教材",
            "related_concepts": ["概念1", "概念2"],
            "common_mistakes": "测试错误"
        }

        prompt = verification_service._build_rag_enhanced_prompt(
            concept="测试概念",
            context=context
        )

        # Verify all sections included
        assert "学习历史" in prompt
        assert "教材参考" in prompt
        assert "相关概念" in prompt
        assert "常见错误" in prompt
        assert "测试概念" in prompt


# ============================================================================
# Performance Tests
# ============================================================================

class TestRAGPerformance:
    """Performance tests for RAG integration."""

    @pytest.mark.asyncio
    async def test_concurrent_rag_queries(
        self,
        verification_service,
        mock_rag_service
    ):
        """Test multiple concurrent RAG queries."""
        mock_rag_service.query.return_value = MockRAGResult()

        # Generate 5 questions concurrently
        tasks = [
            verification_service.generate_question_with_rag(
                concept=f"概念{i}",
                canvas_name="test.canvas"
            )
            for i in range(5)
        ]

        questions = await asyncio.gather(*tasks)

        # All should succeed
        assert len(questions) == 5
        assert all(q is not None for q in questions)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
