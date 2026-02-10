"""
Unit tests for Story 31.A.8: Mock 降级路径日志透明化

Tests verify that all mock scoring degradation paths are transparent:
- AC-31.A.8.1: Mock scoring logs upgraded to WARNING with [DEGRADED SCORING] prefix
- AC-31.A.8.2: API response includes degraded_reason and degraded_warning
- AC-31.A.8.3: _mock_evaluate_answer has comprehensive limitation docstring
- AC-31.A.8.4: _evaluate_answer_with_scoring_agent returns 4-tuple with reason

[Source: docs/stories/31.A.8.story.md]
"""

import asyncio
import json
import logging
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.verification_service import (
    VERIFICATION_AI_TIMEOUT,
    VerificationService,
)


# ===========================================================================
# Test Fixtures
# ===========================================================================


@pytest.fixture
def mock_canvas_service() -> MagicMock:
    """Mock canvas service for testing."""
    service = MagicMock()
    service.read_canvas = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_agent_service() -> MagicMock:
    """Mock agent service with successful scoring."""
    service = MagicMock()

    # Mock call_agent for question generation
    question_result = MagicMock()
    question_result.success = True
    question_result.data = {
        "questions": [{
            "source_node_id": "verification_test",
            "question_text": "请解释测试概念？",
            "question_type": "检验型",
            "difficulty": "基础",
            "guidance": "",
            "rationale": "测试"
        }]
    }
    service.call_agent = AsyncMock(return_value=question_result)

    # Mock call_scoring (successful AI scoring)
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
    """Mock RAG service."""
    service = MagicMock()
    service.query = AsyncMock(return_value={
        "learning_history": "之前学习过",
        "textbook_excerpts": "教材内容",
        "related_concepts": ["概念1"],
        "common_mistakes": "常见错误"
    })
    return service


@pytest.fixture
def verification_service(
    mock_canvas_service: MagicMock,
    mock_agent_service: MagicMock,
    mock_rag_service: MagicMock
) -> VerificationService:
    """Create VerificationService with mock dependencies (agent available)."""
    return VerificationService(
        rag_service=mock_rag_service,
        canvas_service=mock_canvas_service,
        agent_service=mock_agent_service,
        canvas_base_path=tempfile.gettempdir()
    )


@pytest.fixture
def verification_service_no_agent(
    mock_canvas_service: MagicMock,
    mock_rag_service: MagicMock
) -> VerificationService:
    """Create VerificationService without agent_service (simulates DI failure)."""
    return VerificationService(
        rag_service=mock_rag_service,
        canvas_service=mock_canvas_service,
        agent_service=None,
        canvas_base_path=tempfile.gettempdir()
    )


@pytest.fixture
def mock_canvas_data():
    """Sample Canvas data with red/purple nodes."""
    return {
        "nodes": [
            {"id": "node1", "text": "测试概念A", "color": "4"},
            {"id": "node2", "text": "测试概念B", "color": "3"},
        ],
        "edges": []
    }


@pytest.fixture
def temp_canvas_file(mock_canvas_data):
    """Create a temporary Canvas file."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.canvas', delete=False, encoding='utf-8'
    ) as f:
        json.dump(mock_canvas_data, f)
        yield f.name
    os.unlink(f.name)


async def _create_session_and_get_sid(service, temp_canvas_file):
    """Helper to create a session and return session_id."""
    result = await service.start_session(
        canvas_name="test_canvas",
        canvas_path=temp_canvas_file
    )
    return result["session_id"]


# ===========================================================================
# AC-31.A.8.1: Mock Scoring Logs Upgraded to WARNING
# ===========================================================================


class TestMockScoringWarningLogs:
    """AC-31.A.8.1: All mock scoring paths log WARNING with [DEGRADED SCORING]."""

    @pytest.mark.asyncio
    async def test_mock_mode_logs_warning(
        self, verification_service, temp_canvas_file, caplog
    ):
        """Mock mode (USE_MOCK_VERIFICATION=true) outputs WARNING."""
        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        with patch.dict(os.environ, {"USE_MOCK_VERIFICATION": "true"}), \
             patch("app.services.verification_service.USE_MOCK_VERIFICATION", True), \
             caplog.at_level(logging.WARNING):
            await verification_service.process_answer(sid, "这是一个测试回答")

        assert any("DEGRADED SCORING" in r.message for r in caplog.records)
        assert any("mock_mode_enabled" in r.message for r in caplog.records)
        assert any("NOT based on content quality" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_agent_timeout_logs_warning(
        self, verification_service, temp_canvas_file, caplog
    ):
        """Agent timeout outputs WARNING with agent_timeout reason."""
        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        async def slow_call(*args, **kwargs):
            raise asyncio.TimeoutError()

        with patch.object(
            verification_service, "_do_scoring_agent_call", side_effect=slow_call
        ), caplog.at_level(logging.WARNING):
            await verification_service.process_answer(sid, "这是一个测试回答" * 5)

        assert any("DEGRADED SCORING" in r.message for r in caplog.records)
        assert any("agent_timeout" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_agent_exception_logs_warning(
        self, verification_service, temp_canvas_file, caplog
    ):
        """Agent exception outputs WARNING with agent_exception reason."""
        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        async def failing_call(*args, **kwargs):
            raise RuntimeError("Connection refused")

        with patch.object(
            verification_service, "_do_scoring_agent_call", side_effect=failing_call
        ), caplog.at_level(logging.WARNING):
            await verification_service.process_answer(sid, "这是一个测试回答" * 5)

        assert any("DEGRADED SCORING" in r.message for r in caplog.records)
        assert any("agent_exception" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_agent_unavailable_logs_warning(
        self, verification_service_no_agent, temp_canvas_file, caplog
    ):
        """Agent unavailable (agent_service=None) outputs WARNING."""
        sid = await _create_session_and_get_sid(
            verification_service_no_agent, temp_canvas_file
        )

        with caplog.at_level(logging.WARNING):
            await verification_service_no_agent.process_answer(sid, "测试回答" * 5)

        assert any("DEGRADED SCORING" in r.message for r in caplog.records)
        assert any("agent_unavailable" in r.message for r in caplog.records)


# ===========================================================================
# AC-31.A.8.2: API Response Includes Degradation Info
# ===========================================================================


class TestDegradedResponseFields:
    """AC-31.A.8.2: degraded=True responses include reason and warning."""

    @pytest.mark.asyncio
    async def test_degraded_response_includes_reason_mock_mode(
        self, verification_service, temp_canvas_file
    ):
        """Mock mode response has degraded_reason='mock_mode_enabled'."""
        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        with patch("app.services.verification_service.USE_MOCK_VERIFICATION", True):
            result = await verification_service.process_answer(sid, "测试回答")

        assert result["degraded"] is True
        assert result["degraded_reason"] == "mock_mode_enabled"
        assert "仅供参考" in result["degraded_warning"]

    @pytest.mark.asyncio
    async def test_degraded_response_includes_reason_unavailable(
        self, verification_service_no_agent, temp_canvas_file
    ):
        """Agent unavailable response has degraded_reason='agent_unavailable'."""
        sid = await _create_session_and_get_sid(
            verification_service_no_agent, temp_canvas_file
        )
        result = await verification_service_no_agent.process_answer(sid, "测试回答" * 5)

        assert result["degraded"] is True
        assert result["degraded_reason"] == "agent_unavailable"
        assert "仅供参考" in result["degraded_warning"]

    @pytest.mark.asyncio
    async def test_normal_response_no_degradation_fields(
        self, verification_service, temp_canvas_file
    ):
        """Normal AI scoring response has no degradation markers."""
        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        result = await verification_service.process_answer(sid, "测试回答" * 5)

        assert result["degraded"] is False
        assert result["degraded_reason"] is None
        assert result["degraded_warning"] is None

    @pytest.mark.asyncio
    async def test_degraded_reason_enum_values(
        self, verification_service, temp_canvas_file
    ):
        """All degraded_reason values are from the expected enum."""
        valid_reasons = {
            "mock_mode_enabled", "agent_timeout",
            "agent_exception", "agent_unavailable"
        }

        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        # Test mock mode
        with patch("app.services.verification_service.USE_MOCK_VERIFICATION", True):
            result = await verification_service.process_answer(sid, "测试")
        assert result["degraded_reason"] in valid_reasons


# ===========================================================================
# AC-31.A.8.3: _mock_evaluate_answer Has Limitation Docstring
# ===========================================================================


class TestMockEvaluateDocstring:
    """AC-31.A.8.3: _mock_evaluate_answer has comprehensive docstring."""

    def test_docstring_exists_and_explains_limitations(self, verification_service):
        """Docstring explains character-length scoring limitations."""
        doc = verification_service._mock_evaluate_answer.__doc__
        assert doc is not None
        assert "DEGRADED FALLBACK" in doc
        assert "character length" in doc.lower() or "character-length" in doc.lower()

    def test_docstring_mentions_four_trigger_scenarios(self, verification_service):
        """Docstring lists all 4 trigger scenarios."""
        doc = verification_service._mock_evaluate_answer.__doc__
        assert "USE_MOCK_VERIFICATION" in doc
        assert "times out" in doc.lower() or "timeout" in doc.lower()
        assert "exception" in doc.lower()
        assert "not injected" in doc.lower() or "unavailable" in doc.lower()

    def test_docstring_mentions_known_issue(self, verification_service):
        """Docstring mentions the known scoring flaw."""
        doc = verification_service._mock_evaluate_answer.__doc__
        assert "KNOWN ISSUE" in doc


# ===========================================================================
# AC-31.A.8.4: 4-Tuple Return from _evaluate_answer_with_scoring_agent
# ===========================================================================


class TestFourTupleReturn:
    """AC-31.A.8.4: _evaluate_answer_with_scoring_agent returns 4-tuple."""

    @pytest.mark.asyncio
    async def test_mock_mode_returns_four_tuple(self, verification_service):
        """Mock mode returns (quality, score, True, 'mock_mode_enabled')."""
        with patch("app.services.verification_service.USE_MOCK_VERIFICATION", True):
            result = await verification_service._evaluate_answer_with_scoring_agent(
                concept="微积分",
                user_answer="这是一个测试" * 10,
                canvas_name="test_canvas"
            )

        assert len(result) == 4
        quality, score, degraded, reason = result
        assert isinstance(quality, str)
        assert isinstance(score, float)
        assert degraded is True
        assert reason == "mock_mode_enabled"

    @pytest.mark.asyncio
    async def test_normal_scoring_returns_four_tuple(self, verification_service):
        """Successful AI scoring returns (quality, score, False, None)."""
        result = await verification_service._evaluate_answer_with_scoring_agent(
            concept="微积分",
            user_answer="这是一个测试" * 10,
            canvas_name="test_canvas"
        )

        assert len(result) == 4
        quality, score, degraded, reason = result
        assert isinstance(quality, str)
        assert isinstance(score, float)
        assert degraded is False
        assert reason is None

    @pytest.mark.asyncio
    async def test_timeout_returns_four_tuple(self, verification_service):
        """Timeout returns (quality, score, True, 'agent_timeout')."""
        async def slow_call(*args, **kwargs):
            raise asyncio.TimeoutError()

        with patch.object(
            verification_service, "_do_scoring_agent_call", side_effect=slow_call
        ):
            result = await verification_service._evaluate_answer_with_scoring_agent(
                concept="微积分",
                user_answer="这是一个测试" * 10,
                canvas_name="test_canvas"
            )

        assert len(result) == 4
        _, _, degraded, reason = result
        assert degraded is True
        assert reason == "agent_timeout"

    @pytest.mark.asyncio
    async def test_exception_returns_four_tuple(self, verification_service):
        """Exception returns (quality, score, True, 'agent_exception')."""
        async def failing_call(*args, **kwargs):
            raise RuntimeError("Test error")

        with patch.object(
            verification_service, "_do_scoring_agent_call", side_effect=failing_call
        ):
            result = await verification_service._evaluate_answer_with_scoring_agent(
                concept="微积分",
                user_answer="这是一个测试" * 10,
                canvas_name="test_canvas"
            )

        assert len(result) == 4
        _, _, degraded, reason = result
        assert degraded is True
        assert reason == "agent_exception"

    @pytest.mark.asyncio
    async def test_agent_unavailable_returns_four_tuple(
        self, verification_service_no_agent
    ):
        """Agent unavailable returns (quality, score, True, 'agent_unavailable')."""
        result = await verification_service_no_agent._evaluate_answer_with_scoring_agent(
            concept="微积分",
            user_answer="这是一个测试" * 10,
            canvas_name="test_canvas"
        )

        assert len(result) == 4
        _, _, degraded, reason = result
        assert degraded is True
        assert reason == "agent_unavailable"
