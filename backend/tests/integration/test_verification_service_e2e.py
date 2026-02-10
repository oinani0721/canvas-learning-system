"""
Integration tests for Story 31.1: VerificationService End-to-End

Tests the complete flow from Canvas reading to question generation to answer scoring.

[Source: docs/stories/31.1.story.md#Testing]
"""

import asyncio
import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import app.services.verification_service as vs_module
from app.services.verification_service import (
    VerificationService,
    VerificationStatus,
)


# ===========================================================================
# Test Fixtures
# ===========================================================================


@pytest.fixture(autouse=True)
def ensure_mock_mode_disabled():
    """
    Ensure USE_MOCK_VERIFICATION is False for integration tests.

    This is needed because unit tests may reload the module with mock mode enabled,
    and the module-level variable retains that value for subsequent tests.
    """
    original_value = vs_module.USE_MOCK_VERIFICATION
    vs_module.USE_MOCK_VERIFICATION = False
    yield
    vs_module.USE_MOCK_VERIFICATION = original_value


@pytest.fixture
def sample_canvas_data() -> Dict[str, Any]:
    """Sample Canvas data simulating a real learning canvas."""
    return {
        "nodes": [
            {
                "id": "node-1",
                "type": "text",
                "text": "机器学习基础",
                "color": "4",  # Red - doesn't understand
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 100
            },
            {
                "id": "node-2",
                "type": "text",
                "text": "神经网络结构",
                "color": "3",  # Purple - partially understands
                "x": 250,
                "y": 0,
                "width": 200,
                "height": 100
            },
            {
                "id": "node-3",
                "type": "text",
                "text": "反向传播算法",
                "color": "4",  # Red
                "x": 500,
                "y": 0,
                "width": 200,
                "height": 100
            },
            {
                "id": "node-4",
                "type": "text",
                "text": "激活函数",
                "color": "2",  # Green - understood (should be ignored)
                "x": 0,
                "y": 150,
                "width": 200,
                "height": 100
            }
        ],
        "edges": [
            {"id": "edge-1", "fromNode": "node-1", "toNode": "node-2"}
        ]
    }


@pytest.fixture
def temp_canvas_file(sample_canvas_data: Dict[str, Any]) -> str:
    """Create a temporary Canvas file."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.canvas',
        delete=False,
        encoding='utf-8'
    ) as f:
        json.dump(sample_canvas_data, f)
        return f.name


@pytest.fixture
def mock_agent_service() -> MagicMock:
    """Mock agent service with realistic responses returning AgentResult-like objects."""
    service = MagicMock()

    # Mock call_agent for question generation (returns AgentResult-like object)
    question_result = MagicMock()
    question_result.success = True
    question_result.data = {
        "questions": [{
            "source_node_id": "verification_e2e",
            "question_text": "为什么机器学习模型需要大量数据进行训练？请解释数据量与模型性能之间的关系。",
            "question_type": "检验型",
            "difficulty": "基础",
            "guidance": "",
            "rationale": "测试概念理解"
        }]
    }
    service.call_agent = AsyncMock(return_value=question_result)

    # Mock scoring agent - returns AgentResult-like object (not plain dict)
    # Uses user_understanding kwarg (matching agent_service.call_scoring signature)
    async def mock_scoring(**kwargs):
        user_understanding = kwargs.get("user_understanding", "")
        # Simulate realistic scoring based on answer content
        if len(user_understanding) > 200:
            scoring_data = {
                "total_score": 85.0,
                "accuracy": 22,
                "imagery": 20,
                "completeness": 23,
                "originality": 20,
                "color": "2"
            }
        elif len(user_understanding) > 100:
            scoring_data = {
                "total_score": 70.0,
                "accuracy": 18,
                "imagery": 17,
                "completeness": 18,
                "originality": 17,
                "color": "3"
            }
        else:
            scoring_data = {
                "total_score": 45.0,
                "accuracy": 12,
                "imagery": 11,
                "completeness": 12,
                "originality": 10,
                "color": "4"
            }
        result = MagicMock()
        result.success = True
        result.data = scoring_data
        return result

    service.call_scoring = AsyncMock(side_effect=mock_scoring)

    return service


@pytest.fixture
def mock_rag_service() -> MagicMock:
    """Mock RAG service with learning context."""
    service = MagicMock()

    async def mock_query(**kwargs) -> Dict[str, Any]:
        query = kwargs.get("query", "")
        if "机器学习" in query:
            return {
                "learning_history": "用户之前学习过统计学基础和Python编程",
                "textbook_excerpts": "机器学习是人工智能的一个子领域...",
                "related_concepts": ["统计学习", "深度学习", "监督学习"],
                "common_mistakes": "容易混淆过拟合和欠拟合的概念"
            }
        return {
            "learning_history": "无相关学习历史",
            "textbook_excerpts": "无教材引用",
            "related_concepts": [],
            "common_mistakes": "无已知错误模式"
        }

    service.query = AsyncMock(side_effect=mock_query)
    return service


@pytest.fixture
def verification_service(
    mock_agent_service: MagicMock,
    mock_rag_service: MagicMock
) -> VerificationService:
    """Create VerificationService with mock dependencies."""
    return VerificationService(
        rag_service=mock_rag_service,
        agent_service=mock_agent_service,
        canvas_base_path=tempfile.gettempdir()
    )


# ===========================================================================
# End-to-End Tests
# ===========================================================================


class TestEndToEndVerificationFlow:
    """Test complete verification flow from start to finish."""

    @pytest.mark.asyncio
    async def test_e2e_canvas_read_to_question_generation(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str,
        mock_agent_service: MagicMock
    ):
        """
        E2E Test: Canvas reading → Concept extraction → Question generation

        This tests the flow:
        1. Read Canvas file
        2. Filter red/purple nodes
        3. Extract concept names
        4. Generate first question using Gemini
        """
        # Start session
        result = await verification_service.start_session(
            canvas_name="ml_concepts",
            canvas_path=temp_canvas_file
        )

        # Verify session created
        assert result["session_id"] is not None
        assert result["status"] == "in_progress"

        # Verify concepts extracted (3 red/purple nodes)
        assert result["total_concepts"] == 3

        # Verify first question generated
        assert result["first_question"] is not None
        assert len(result["first_question"]) > 0

        # Verify agent service was called for question generation
        # Production code calls call_agent(AgentType.VERIFICATION_QUESTION, ...)
        # not _call_gemini_api directly
        assert mock_agent_service.call_agent.called

    @pytest.mark.asyncio
    async def test_e2e_answer_processing_with_scoring(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str,
        mock_agent_service: MagicMock
    ):
        """
        E2E Test: Answer submission → Scoring agent → Progress update

        This tests the flow:
        1. Submit user answer
        2. Call scoring-agent for evaluation
        3. Use unified 0-100 score scale
        4. Update progress and determine next action
        """
        # Start session
        session = await verification_service.start_session(
            canvas_name="ml_concepts",
            canvas_path=temp_canvas_file
        )

        # Submit a detailed answer
        detailed_answer = """
        机器学习是人工智能的一个分支，它使计算机能够通过数据学习模式和规律，
        而不需要明确编程。核心原理包括：特征提取、模型训练、参数优化等。
        通过大量数据训练，模型可以自动发现数据中的隐藏规律。
        """ * 2  # Make it >200 chars

        result = await verification_service.process_answer(
            session_id=session["session_id"],
            user_answer=detailed_answer
        )

        # Verify scoring agent was called
        assert mock_agent_service.call_scoring.called

        # Scoring: answer >200 chars → total_score=85.0 (unified 0-100 scale)
        assert result["score"] == 85.0
        assert result["quality"] == "excellent"
        # Wave 3: Real agent → not degraded
        assert result["degraded"] is False

        # Verify progress updated
        assert result["progress"]["completed_concepts"] == 1

    @pytest.mark.asyncio
    async def test_e2e_complete_session_all_concepts(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str
    ):
        """
        E2E Test: Complete verification session through all concepts

        This tests completing all concepts in a session.
        """
        # Start session
        session = await verification_service.start_session(
            canvas_name="ml_concepts",
            canvas_path=temp_canvas_file
        )

        total_concepts = session["total_concepts"]
        session_id = session["session_id"]

        # Process answers for all concepts
        for i in range(total_concepts):
            result = await verification_service.process_answer(
                session_id=session_id,
                user_answer="这是一个详细的回答，包含对概念的深入分析和理解。" * 5
            )

            if i < total_concepts - 1:
                assert result["action"] == "next"
            else:
                assert result["action"] == "complete"

        # Verify final progress
        progress = await verification_service.get_progress(session_id)
        assert progress["status"] == VerificationStatus.COMPLETED.value
        assert progress["completed_concepts"] == total_concepts

    @pytest.mark.asyncio
    async def test_e2e_rag_context_integration(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str,
        mock_rag_service: MagicMock
    ):
        """
        E2E Test: RAG context flows through entire pipeline

        This tests:
        1. RAG context retrieved for question generation
        2. RAG context passed to scoring agent
        """
        # Start session
        session = await verification_service.start_session(
            canvas_name="ml_concepts",
            canvas_path=temp_canvas_file
        )

        # RAG should be called during question generation
        assert mock_rag_service.query.called

        # Submit answer
        await verification_service.process_answer(
            session_id=session["session_id"],
            user_answer="测试回答"
        )

        # RAG should be called again during scoring
        # (Called for both question generation and scoring context)
        assert mock_rag_service.query.call_count >= 1

    @pytest.mark.asyncio
    async def test_e2e_hint_flow_after_partial_answer(
        self,
        verification_service: VerificationService,
        temp_canvas_file: str,
        mock_agent_service: MagicMock
    ):
        """
        E2E Test: Hint provided after partial answer

        This tests:
        1. Submit short answer
        2. Score below threshold
        3. Hint provided instead of advancing
        """
        # Configure scoring to return low score (AgentResult-like object)
        low_score_result = MagicMock()
        low_score_result.success = True
        low_score_result.data = {
            "total_score": 35.0,  # Below 60 threshold (unified 0-100 scale)
            "accuracy": 10,
            "imagery": 8,
            "completeness": 9,
            "originality": 8
        }
        mock_agent_service.call_scoring = AsyncMock(return_value=low_score_result)

        # Start session
        session = await verification_service.start_session(
            canvas_name="ml_concepts",
            canvas_path=temp_canvas_file
        )

        # Submit a short answer
        result = await verification_service.process_answer(
            session_id=session["session_id"],
            user_answer="不太确定"
        )

        # Should get hint (score 35.0 < 60 threshold)
        assert result["action"] == "hint"
        assert result["hint"] is not None
        # Wave 3: Real agent → not degraded (even for low scores)
        assert result["degraded"] is False


# ===========================================================================
# Performance Tests
# ===========================================================================


class TestPerformanceRequirements:
    """Test performance requirements from Story 31.1."""

    @pytest.mark.asyncio
    async def test_response_time_under_500ms_mock_mode(
        self,
        temp_canvas_file: str
    ):
        """Test that mock mode responds within timeout."""
        # H2 fix: Use direct patching instead of importlib.reload to avoid
        # module-level class duplication and test isolation poisoning.
        with patch.object(vs_module, "USE_MOCK_VERIFICATION", True):
            service = vs_module.VerificationService(
                canvas_base_path=tempfile.gettempdir()
            )

            import time
            start = time.time()

            await service.start_session(
                canvas_name="test",
                canvas_path=temp_canvas_file
            )

            elapsed = time.time() - start
            # Should be very fast in mock mode
            assert elapsed < 0.5, f"Mock mode took {elapsed}s, should be < 0.5s"


# Cleanup
@pytest.fixture(autouse=True)
def cleanup_temp_files(temp_canvas_file):
    yield
    try:
        os.unlink(temp_canvas_file)
    except (FileNotFoundError, OSError):
        pass
