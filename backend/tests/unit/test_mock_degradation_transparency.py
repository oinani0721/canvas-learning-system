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
        "questions": [
            {
                "source_node_id": "verification_test",
                "question_text": "请解释测试概念？",
                "question_type": "检验型",
                "difficulty": "基础",
                "guidance": "",
                "rationale": "测试",
            }
        ]
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
        "color": "2",
    }
    service.call_scoring = AsyncMock(return_value=scoring_result)
    return service


@pytest.fixture
def mock_rag_service() -> MagicMock:
    """Mock RAG service."""
    service = MagicMock()
    service.query = AsyncMock(
        return_value={
            "learning_history": "之前学习过",
            "related_excerpts": "相关内容",
            "related_concepts": ["概念1"],
            "common_mistakes": "常见错误",
        }
    )
    return service


@pytest.fixture
def verification_service(
    mock_canvas_service: MagicMock,
    mock_agent_service: MagicMock,
    mock_rag_service: MagicMock,
) -> VerificationService:
    """Create VerificationService with mock dependencies (agent available)."""
    return VerificationService(
        rag_service=mock_rag_service,
        canvas_service=mock_canvas_service,
        agent_service=mock_agent_service,
        canvas_base_path=tempfile.gettempdir(),
    )


@pytest.fixture
def verification_service_no_agent(
    mock_canvas_service: MagicMock, mock_rag_service: MagicMock
) -> VerificationService:
    """Create VerificationService without agent_service (simulates DI failure)."""
    return VerificationService(
        rag_service=mock_rag_service,
        canvas_service=mock_canvas_service,
        agent_service=None,
        canvas_base_path=tempfile.gettempdir(),
    )


@pytest.fixture
def mock_canvas_data():
    """Sample Canvas data with red/purple nodes."""
    return {
        "nodes": [
            {"id": "node1", "text": "测试概念A", "color": "4"},
            {"id": "node2", "text": "测试概念B", "color": "3"},
        ],
        "edges": [],
    }


@pytest.fixture
def temp_canvas_file(mock_canvas_data):
    """Create a temporary Canvas file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        json.dump(mock_canvas_data, f)
        yield f.name
    os.unlink(f.name)


async def _create_session_and_get_sid(service, temp_canvas_file):
    """Helper to create a session and return session_id."""
    result = await service.start_session(
        canvas_name="test_canvas", canvas_path=temp_canvas_file
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

        with (
            patch.dict(os.environ, {"USE_MOCK_VERIFICATION": "true"}),
            patch("app.services.verification_service.USE_MOCK_VERIFICATION", True),
            caplog.at_level(logging.WARNING),
        ):
            await verification_service.process_answer(sid, "这是一个测试回答")

        assert any("DEGRADED SCORING" in r.message for r in caplog.records)
        assert any("mock_mode_enabled" in r.message for r in caplog.records)
        # FR-KG-04 P1-4: fail-closed 设计 — 不再按长度判分
        assert any(
            "mastery state will NOT be updated" in r.message for r in caplog.records
        )

    @pytest.mark.asyncio
    async def test_agent_timeout_logs_warning(
        self, verification_service, temp_canvas_file, caplog
    ):
        """Agent timeout outputs WARNING with agent_timeout reason."""
        sid = await _create_session_and_get_sid(verification_service, temp_canvas_file)

        async def slow_call(*args, **kwargs):
            raise asyncio.TimeoutError()

        with (
            patch.object(
                verification_service, "_do_scoring_agent_call", side_effect=slow_call
            ),
            caplog.at_level(logging.WARNING),
        ):
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

        with (
            patch.object(
                verification_service, "_do_scoring_agent_call", side_effect=failing_call
            ),
            caplog.at_level(logging.WARNING),
        ):
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
        # FR-KG-04 P1-4: fail-closed warning 文案
        assert "不计分" in result["degraded_warning"]
        assert "不更新掌握度" in result["degraded_warning"]

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
        # FR-KG-04 P1-4: fail-closed warning 文案
        assert "不计分" in result["degraded_warning"]
        assert "不更新掌握度" in result["degraded_warning"]

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
            "mock_mode_enabled",
            "agent_timeout",
            "agent_exception",
            "agent_unavailable",
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
    """AC-31.A.8.3: _mock_evaluate_answer has comprehensive docstring.

    FR-KG-04 P1-4: Updated to verify fail-closed design (was: character-length scoring).
    """

    def test_docstring_exists_and_explains_fail_closed_design(
        self, verification_service
    ):
        """Docstring explains fail-closed neutral return design."""
        doc = verification_service._mock_evaluate_answer.__doc__
        assert doc is not None
        assert "DEGRADED FALLBACK" in doc
        assert "fail-closed" in doc.lower()

    def test_docstring_mentions_four_trigger_scenarios(self, verification_service):
        """Docstring lists all 4 trigger scenarios."""
        doc = verification_service._mock_evaluate_answer.__doc__
        assert "USE_MOCK_VERIFICATION" in doc
        assert "times out" in doc.lower() or "timeout" in doc.lower()
        assert "exception" in doc.lower()
        assert "not injected" in doc.lower() or "unavailable" in doc.lower()

    def test_docstring_explains_mastery_protection(self, verification_service):
        """Docstring explains why fail-closed protects mastery state."""
        doc = verification_service._mock_evaluate_answer.__doc__
        assert "mastery" in doc.lower()
        assert "neutral" in doc.lower() or "unknown" in doc.lower()


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
                canvas_name="test_canvas",
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
            concept="微积分", user_answer="这是一个测试" * 10, canvas_name="test_canvas"
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
                canvas_name="test_canvas",
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
                canvas_name="test_canvas",
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
        result = (
            await verification_service_no_agent._evaluate_answer_with_scoring_agent(
                concept="微积分",
                user_answer="这是一个测试" * 10,
                canvas_name="test_canvas",
            )
        )

        assert len(result) == 4
        _, _, degraded, reason = result
        assert degraded is True
        assert reason == "agent_unavailable"


# ===========================================================================
# FR-KG-04 P1-4: Fail-Closed Degraded Scoring
# ===========================================================================


class TestFailClosedDegradedScoring:
    """FR-KG-04 P1-4: degraded mode must NOT score by length and MUST NOT
    update mastery state. Adversarial inputs (long noise) must not produce
    high scores."""

    def test_mock_evaluate_returns_unknown_for_short_input(self, verification_service):
        """Short answer in degraded mode returns ('unknown', 0.0)."""
        quality, score = verification_service._mock_evaluate_answer("hi")
        assert quality == "unknown"
        assert score == 0.0

    def test_mock_evaluate_returns_unknown_for_long_input(self, verification_service):
        """Long answer in degraded mode also returns ('unknown', 0.0)."""
        long_answer = "x" * 200
        quality, score = verification_service._mock_evaluate_answer(long_answer)
        assert quality == "unknown"
        assert score == 0.0

    def test_adversarial_101_char_noise_does_not_score_high(self, verification_service):
        """REGRESSION: 101-character noise must NOT outscore 19-char correct answer.

        Before P1-4 fix, "x"*101 → score=90, while "正确答案是力等于质量乘加速度" (~16 chars) → score=20.
        After fix, both must return ("unknown", 0.0).
        """
        long_noise = "x" * 101
        short_correct = "F=ma"

        q1, s1 = verification_service._mock_evaluate_answer(long_noise)
        q2, s2 = verification_service._mock_evaluate_answer(short_correct)

        assert q1 == q2 == "unknown"
        assert s1 == s2 == 0.0

    def test_mock_evaluate_returns_unknown_for_empty_input(self, verification_service):
        """Empty answer in degraded mode also returns ('unknown', 0.0)."""
        quality, score = verification_service._mock_evaluate_answer("")
        assert quality == "unknown"
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_degraded_mode_does_not_update_mastery_counts(
        self, verification_service_no_agent, temp_canvas_file
    ):
        """In degraded mode, _advance_concept must NOT increment color counts."""
        sid = await _create_session_and_get_sid(
            verification_service_no_agent, temp_canvas_file
        )

        # Capture progress before
        progress_before = verification_service_no_agent._progress[sid]
        green_before = progress_before.green_count
        yellow_before = progress_before.yellow_count
        red_before = progress_before.red_count
        purple_before = progress_before.purple_count

        # Submit an answer in degraded mode (agent_service=None)
        result = await verification_service_no_agent.process_answer(
            sid,
            "x" * 200,  # Long noise — would have scored 90 before fix
        )

        # Verify degraded flag set
        assert result["degraded"] is True
        assert result["score"] == 0.0
        assert result["quality"] == "unknown"

        # Verify mastery counts UNCHANGED (fail-closed)
        progress_after = verification_service_no_agent._progress[sid]
        assert progress_after.green_count == green_before
        assert progress_after.yellow_count == yellow_before
        assert progress_after.red_count == red_before
        assert progress_after.purple_count == purple_before

    @pytest.mark.asyncio
    async def test_degraded_mode_still_advances_to_next_concept(
        self, verification_service_no_agent, temp_canvas_file
    ):
        """In degraded mode, completed_concepts MUST still advance to avoid blocking UX."""
        sid = await _create_session_and_get_sid(
            verification_service_no_agent, temp_canvas_file
        )

        progress_before = verification_service_no_agent._progress[sid]
        completed_before = progress_before.completed_concepts

        result = await verification_service_no_agent.process_answer(sid, "anything")

        assert result["degraded"] is True
        # Action should advance (not block on hint loop)
        assert result["action"] in ("next", "complete")

        progress_after = verification_service_no_agent._progress[sid]
        assert progress_after.completed_concepts == completed_before + 1


# ===========================================================================
# FR-KG-04 P0-3: Path Traversal Hardening
# ===========================================================================


class TestPathTraversalHardening:
    """FR-KG-04 P0-3: _resolve_safe_canvas_path must reject all traversal
    attempts (../, absolute paths, null bytes, paths outside base, non-.canvas
    files). Defense-in-depth alongside CanvasService._validate_canvas_name."""

    def test_resolve_rejects_dotdot_in_canvas_name(self, verification_service):
        """canvas_name with '..' must be rejected."""
        result = verification_service._resolve_safe_canvas_path(
            "../../etc/passwd", None
        )
        assert result is None

    def test_resolve_rejects_absolute_canvas_name(self, verification_service):
        """canvas_name starting with '/' must be rejected."""
        result = verification_service._resolve_safe_canvas_path("/etc/passwd", None)
        assert result is None

    def test_resolve_rejects_null_byte_in_canvas_name(self, verification_service):
        """canvas_name with null byte must be rejected."""
        result = verification_service._resolve_safe_canvas_path("test\0.canvas", None)
        assert result is None

    def test_resolve_rejects_canvas_path_outside_base(
        self, verification_service, tmp_path
    ):
        """canvas_path that resolves outside _canvas_base_path must be rejected."""
        # Pin base to a fresh subdirectory inside tmp_path to ensure we have
        # control over what's "inside" vs "outside" the base.
        base = tmp_path / "vault"
        base.mkdir()
        verification_service._canvas_base_path = str(base)

        # canvas_path points OUTSIDE the base (sibling directory)
        outside = str(tmp_path / "evil.canvas")
        result = verification_service._resolve_safe_canvas_path("test", outside)
        assert result is None

    def test_resolve_rejects_non_canvas_suffix(self, verification_service, tmp_path):
        """Resolved file must end with .canvas, not .py/.sh/etc."""
        # Use a path inside base but with wrong suffix
        verification_service._canvas_base_path = str(tmp_path)
        evil = str(tmp_path / "evil.sh")
        result = verification_service._resolve_safe_canvas_path("evil", evil)
        assert result is None

    def test_resolve_accepts_valid_relative_canvas_name(
        self, verification_service, tmp_path
    ):
        """Normal canvas_name with subfolder should resolve safely."""
        verification_service._canvas_base_path = str(tmp_path)
        # Create a fake canvas file inside base
        sub = tmp_path / "Math"
        sub.mkdir()
        (sub / "Lecture5.canvas").write_text("{}")

        result = verification_service._resolve_safe_canvas_path("Math/Lecture5", None)
        assert result is not None
        assert result.endswith("Lecture5.canvas")
        # Must be inside base
        assert str(tmp_path) in result

    def test_resolve_strips_double_canvas_suffix(self, verification_service, tmp_path):
        """canvas_name with .canvas suffix should not produce .canvas.canvas."""
        verification_service._canvas_base_path = str(tmp_path)
        (tmp_path / "test.canvas").write_text("{}")

        result = verification_service._resolve_safe_canvas_path("test.canvas", None)
        assert result is not None
        assert result.endswith("test.canvas")
        assert not result.endswith(".canvas.canvas")

    @pytest.mark.asyncio
    async def test_extract_concepts_rejects_traversal_falls_back(
        self, verification_service_no_agent
    ):
        """End-to-end: canvas_name with traversal returns fallback concepts.

        REGRESSION for P0-3: Previously the fallback open() would have
        successfully read /etc/passwd.canvas if it existed.
        """
        # Use the no-agent fixture so canvas_service is available but
        # we test the safe path resolution rather than CanvasService
        result = await verification_service_no_agent._do_extract_concepts(
            canvas_name="../../etc/passwd",
            canvas_path=None,
        )
        # Should return fallback, never read traversal target
        assert result == ["默认概念"]
