"""
Unit tests for Story 31.1: VerificationService核心逻辑激活

Tests verify the activation of real AI functionality in VerificationService:
- AC-31.1.1: start_session() reads Canvas file for red/purple nodes
- AC-31.1.2: generate_question_with_rag() calls Gemini API
- AC-31.1.3: process_answer() integrates scoring-agent (0-40 mapping)
- AC-31.1.4: RAG context injection for all methods
- AC-31.1.5: 500ms timeout protection and graceful degradation

[Source: docs/stories/31.1.story.md#Testing]
"""

import asyncio
import json
import os
import tempfile
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.verification_service import (
    VERIFICATION_AI_TIMEOUT,
    VerificationService,
    VerificationStatus,
)


# ===========================================================================
# Test Fixtures
# ===========================================================================


@pytest.fixture
def mock_canvas_data() -> Dict[str, Any]:
    """Sample Canvas data with nodes of different colors."""
    return {
        "nodes": [
            {"id": "node1", "text": "概念A - 测试", "color": "4"},  # Red
            {"id": "node2", "text": "概念B - 理解", "color": "3"},  # Purple
            {"id": "node3", "text": "概念C - 已掌握", "color": "2"},  # Green (ignored)
            {"id": "node4", "text": "概念D - 不理解", "color": "4"},  # Red
            {"id": "node5", "text": "概念E - 无颜色", "color": ""},  # No color (ignored)
        ],
        "edges": []
    }


@pytest.fixture
def mock_canvas_service() -> MagicMock:
    """Mock canvas service for testing."""
    service = MagicMock()
    service.read_canvas = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_agent_service() -> MagicMock:
    """Mock agent service for testing."""
    service = MagicMock()

    # Mock call_agent for question generation (returns AgentResult-like object)
    question_result = MagicMock()
    question_result.success = True
    question_result.data = {
        "questions": [{
            "source_node_id": "verification_test",
            "question_text": "这是一个测试问题：请解释概念A的核心含义？",
            "question_type": "检验型",
            "difficulty": "基础",
            "guidance": "",
            "rationale": "测试"
        }]
    }
    service.call_agent = AsyncMock(return_value=question_result)

    # Mock call_scoring (returns AgentResult-like object)
    scoring_result = MagicMock()
    scoring_result.success = True
    scoring_result.data = {
        "total_score": 75.0,
        "accuracy": 20,
        "imagery": 18,
        "completeness": 19,
        "originality": 18,
        "color": "2"
    }
    service.call_scoring = AsyncMock(return_value=scoring_result)
    return service


@pytest.fixture
def mock_rag_service() -> MagicMock:
    """Mock RAG service for testing."""
    service = MagicMock()
    service.query = AsyncMock(return_value={
        "learning_history": "用户之前学习过相关概念",
        "textbook_excerpts": "教材引用内容",
        "related_concepts": ["相关概念1", "相关概念2"],
        "common_mistakes": "常见错误模式"
    })
    return service


@pytest.fixture
def temp_canvas_file(mock_canvas_data: Dict[str, Any]) -> str:
    """Create a temporary Canvas file for testing."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.canvas',
        delete=False,
        encoding='utf-8'
    ) as f:
        json.dump(mock_canvas_data, f)
        return f.name


@pytest.fixture
def verification_service(
    mock_canvas_service: MagicMock,
    mock_agent_service: MagicMock,
    mock_rag_service: MagicMock
) -> VerificationService:
    """Create VerificationService with mock dependencies."""
    return VerificationService(
        rag_service=mock_rag_service,
        canvas_service=mock_canvas_service,
        agent_service=mock_agent_service,
        canvas_base_path=tempfile.gettempdir()
    )


# ===========================================================================
# AC-31.1.1: start_session() Canvas Reading Tests
# ===========================================================================


class TestStartSessionReadsCanvasFile:
    """Test AC-31.1.1: start_session() reads Canvas file."""

    @pytest.mark.asyncio
    async def test_start_session_reads_canvas_file(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str
    ):
        """Test that start_session reads Canvas file and extracts concepts."""
        # Given: A Canvas file with red/purple nodes
        # When: Starting a session with the canvas path
        result = await verification_service.start_session(
            canvas_name="test_canvas",
            canvas_path=temp_canvas_file
        )

        # Then: Session should be created with extracted concepts
        assert "session_id" in result
        assert result["status"] == "in_progress"
        assert result["total_concepts"] >= 1

    @pytest.mark.asyncio
    async def test_start_session_filters_red_purple_nodes(
        self,
        mock_canvas_data: Dict[str, Any]
    ):
        """Test that only color='3' (purple) and color='4' (red) nodes are selected."""
        # Given: A verification service with direct file reading
        service = VerificationService(canvas_base_path=tempfile.gettempdir())

        # Create temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.canvas', delete=False, encoding='utf-8'
        ) as f:
            json.dump(mock_canvas_data, f)
            canvas_path = f.name

        try:
            # When: Starting a session
            result = await service.start_session(
                canvas_name="test",
                canvas_path=canvas_path
            )

            # Then: Only red(4) and purple(3) nodes should be counted
            # mock_canvas_data has 3 qualifying nodes (2 red + 1 purple)
            assert result["total_concepts"] == 3
        finally:
            os.unlink(canvas_path)

    @pytest.mark.asyncio
    async def test_start_session_extracts_concepts(
        self,
        mock_canvas_data: Dict[str, Any]
    ):
        """Test that concept names are extracted from node text."""
        service = VerificationService(canvas_base_path=tempfile.gettempdir())

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.canvas', delete=False, encoding='utf-8'
        ) as f:
            json.dump(mock_canvas_data, f)
            canvas_path = f.name

        try:
            result = await service.start_session(
                canvas_name="test",
                canvas_path=canvas_path
            )

            # First concept should be extracted from text
            assert result["current_concept"] is not None
            assert len(result["current_concept"]) > 0
        finally:
            os.unlink(canvas_path)


# ===========================================================================
# AC-31.1.2: generate_question_with_rag() Gemini API Tests
# ===========================================================================


class TestGenerateQuestionCallsGemini:
    """Test AC-31.1.2: generate_question_with_rag() calls Gemini API."""

    @pytest.mark.asyncio
    async def test_generate_question_calls_gemini(
        self,
        verification_service: VerificationService,
        mock_agent_service: MagicMock
    ):
        """Test that generate_question_with_rag calls Gemini API."""
        # Given: A service with mock agent service
        # When: Generating a question
        question = await verification_service.generate_question_with_rag(
            concept="测试概念",
            canvas_name="test_canvas"
        )

        # Then: Agent service should be called via call_agent()
        assert mock_agent_service.call_agent.called
        assert question is not None
        assert len(question) > 0

    @pytest.mark.asyncio
    async def test_generate_question_includes_context(
        self,
        verification_service: VerificationService,
        mock_agent_service: MagicMock,
        mock_rag_service: MagicMock
    ):
        """Test that question generation includes RAG context."""
        # When: Generating a question
        await verification_service.generate_question_with_rag(
            concept="测试概念",
            canvas_name="test_canvas"
        )

        # Then: RAG context should be queried
        assert mock_rag_service.query.called


# ===========================================================================
# AC-31.1.3: process_answer() Scoring-Agent Tests
# ===========================================================================


class TestProcessAnswerCallsScoringAgent:
    """Test AC-31.1.3: process_answer() integrates scoring-agent."""

    @pytest.mark.asyncio
    async def test_process_answer_calls_scoring_agent(
        self,
        verification_service: VerificationService,
        mock_agent_service: MagicMock,
        temp_canvas_file: str
    ):
        """Test that process_answer calls scoring-agent."""
        # Given: A session is started
        session = await verification_service.start_session(
            canvas_name="test",
            canvas_path=temp_canvas_file
        )

        # When: Processing an answer
        result = await verification_service.process_answer(
            session_id=session["session_id"],
            user_answer="这是我对概念的理解，包含详细解释。"
        )

        # Then: Scoring agent should be called
        assert mock_agent_service.call_scoring.called
        assert "score" in result
        assert "quality" in result

    @pytest.mark.asyncio
    async def test_process_answer_maps_score_correctly(
        self,
        verification_service: VerificationService,
        mock_agent_service: MagicMock,
        temp_canvas_file: str
    ):
        """Test that 0-100 score is mapped to 0-40 range."""
        # Given: Scoring agent returns 75/100 (as AgentResult-like object)
        scoring_result = MagicMock()
        scoring_result.success = True
        scoring_result.data = {"total_score": 75.0}
        mock_agent_service.call_scoring.return_value = scoring_result

        session = await verification_service.start_session(
            canvas_name="test",
            canvas_path=temp_canvas_file
        )

        # When: Processing an answer
        result = await verification_service.process_answer(
            session_id=session["session_id"],
            user_answer="测试回答"
        )

        # Then: Score should be mapped to 0-40 range (75 * 0.4 = 30)
        assert result["score"] == 30.0

    @pytest.mark.asyncio
    async def test_score_to_quality_mapping(
        self,
        verification_service: VerificationService
    ):
        """Test score to quality level mapping."""
        # Test thresholds (0-40 range)
        assert verification_service._score_to_quality(40) == "excellent"
        assert verification_service._score_to_quality(32) == "excellent"
        assert verification_service._score_to_quality(31) == "good"
        assert verification_service._score_to_quality(24) == "good"
        assert verification_service._score_to_quality(23) == "partial"
        assert verification_service._score_to_quality(16) == "partial"
        assert verification_service._score_to_quality(15) == "wrong"
        assert verification_service._score_to_quality(0) == "wrong"


# ===========================================================================
# AC-31.1.4: RAG Context Injection Tests
# ===========================================================================


class TestRagContextInjection:
    """Test AC-31.1.4: RAG context injection."""

    @pytest.mark.asyncio
    async def test_rag_context_injection(
        self,
        verification_service: VerificationService,
        mock_rag_service: MagicMock
    ):
        """Test that RAG context is injected into question generation."""
        # When: Generating a question
        await verification_service.generate_question_with_rag(
            concept="测试概念",
            canvas_name="test_canvas"
        )

        # Then: RAG service should be queried for context
        mock_rag_service.query.assert_called_once()
        call_args = mock_rag_service.query.call_args
        assert "测试概念" in call_args[1]["query"]


# ===========================================================================
# AC-31.1.5: Timeout and Graceful Degradation Tests
# ===========================================================================


class TestTimeoutGracefulDegradation:
    """Test AC-31.1.5: 500ms timeout and graceful degradation."""

    @pytest.mark.asyncio
    async def test_timeout_graceful_degradation(
        self,
        mock_rag_service: MagicMock
    ):
        """Test that timeout triggers graceful degradation to mock."""
        # Given: Agent service that times out
        mock_agent_service = MagicMock()
        mock_agent_service.call_agent = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_agent_service.call_scoring = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        service = VerificationService(
            rag_service=mock_rag_service,
            agent_service=mock_agent_service,
            canvas_base_path=tempfile.gettempdir()
        )

        # When: Generating a question with timeout
        question = await service.generate_question_with_rag(
            concept="测试概念",
            canvas_name="test_canvas"
        )

        # Then: Should return fallback question
        assert question is not None
        assert "测试概念" in question

    @pytest.mark.asyncio
    async def test_timeout_15s_protection(self):
        """Test that timeout is set to 15 seconds (sufficient for Gemini API)."""
        # Verify the constant is set correctly (changed from 0.5 to 15 for real API calls)
        assert VERIFICATION_AI_TIMEOUT == 15.0

    @pytest.mark.asyncio
    async def test_mock_mode_returns_default_concepts(self):
        """Test that mock mode returns default concepts."""
        with patch.dict(os.environ, {"USE_MOCK_VERIFICATION": "true"}):
            # Need to reimport to pick up env var
            from importlib import reload
            import app.services.verification_service as vs
            reload(vs)

            service = vs.VerificationService()

            # Mock mode should return hardcoded concepts
            concepts = await service._extract_concepts_from_canvas(
                canvas_name="test",
                canvas_path=None,
                node_ids=None
            )

            assert concepts == ["概念1", "概念2", "概念3"]

            # Reset module
            reload(vs)


# ===========================================================================
# Score Mapping Tests
# ===========================================================================


class TestScoreMapping:
    """Test score mapping functions."""

    def test_map_score_to_verification_range(
        self,
        verification_service: VerificationService
    ):
        """Test 0-100 to 0-40 score mapping."""
        # Test various scores
        assert verification_service._map_score_to_verification_range(100) == 40.0
        assert verification_service._map_score_to_verification_range(75) == 30.0
        assert verification_service._map_score_to_verification_range(50) == 20.0
        assert verification_service._map_score_to_verification_range(25) == 10.0
        assert verification_service._map_score_to_verification_range(0) == 0.0

        # Test bounds
        assert verification_service._map_score_to_verification_range(150) == 40.0  # Clamped
        assert verification_service._map_score_to_verification_range(-10) == 0.0   # Clamped

    def test_mock_evaluate_answer(
        self,
        verification_service: VerificationService
    ):
        """Test mock evaluation based on answer length."""
        # Long answer (>100 chars)
        quality, score = verification_service._mock_evaluate_answer("a" * 101)
        assert quality == "excellent"
        assert score == 36.0

        # Medium answer (>50 chars)
        quality, score = verification_service._mock_evaluate_answer("a" * 51)
        assert quality == "good"
        assert score == 28.0

        # Short answer (>20 chars)
        quality, score = verification_service._mock_evaluate_answer("a" * 21)
        assert quality == "partial"
        assert score == 20.0

        # Very short answer
        quality, score = verification_service._mock_evaluate_answer("a" * 10)
        assert quality == "wrong"
        assert score == 8.0


# ===========================================================================
# Integration Tests
# ===========================================================================


class TestEndToEndFlow:
    """Integration tests for the full verification flow."""

    @pytest.mark.asyncio
    async def test_full_session_flow(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str
    ):
        """Test complete session flow: start -> answer -> complete."""
        # Start session
        session = await verification_service.start_session(
            canvas_name="test",
            canvas_path=temp_canvas_file
        )
        assert session["status"] == "in_progress"

        # Process answer
        result = await verification_service.process_answer(
            session_id=session["session_id"],
            user_answer="这是一个详细的回答，包含对概念的深入理解和分析。" * 3
        )
        assert "quality" in result
        assert "score" in result
        assert "progress" in result

    @pytest.mark.asyncio
    async def test_session_with_skip(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str
    ):
        """Test skipping a concept in a session."""
        session = await verification_service.start_session(
            canvas_name="test",
            canvas_path=temp_canvas_file
        )

        # Skip current concept
        result = await verification_service.skip_concept(
            session_id=session["session_id"]
        )
        assert "action" in result


# Cleanup temp files after tests
@pytest.fixture(autouse=True)
def cleanup_temp_files(temp_canvas_file):
    yield
    try:
        os.unlink(temp_canvas_file)
    except (FileNotFoundError, OSError):
        pass
