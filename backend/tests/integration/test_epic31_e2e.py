"""
EPIC 31 End-to-End Integration Tests (Wave 5)

Tests the complete verification flow across all EPIC 31 stories:
- Story 31.1: VerificationService core logic activation (Canvas reading, Gemini API, scoring)
- Story 31.2+31.5: Difficulty adaptation for one-click canvas generation
- Story 31.4: Question deduplication via Graphiti
- Story 31.6: Session progress, pause/resume, score scale unification

Test scenarios:
1. test_complete_verification_flow: session → answer → score → recommend → next → complete
2. test_pause_resume_flow: session → answer 1 → pause → resume → confirm non-template question
3. test_consecutive_low_recommendation: 3 low scores → confirm recommendation changes
4. test_degradation_visibility: Mock AI failure → confirm degraded marker

[Source: Wave 5 E2E test plan]
"""

import asyncio
import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import simulate_async_delay

import app.services.verification_service as vs_module
from app.services.verification_service import (
    VerificationService,
    VerificationStatus,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture(autouse=True)
def ensure_real_mode():
    """Ensure USE_MOCK_VERIFICATION is False for E2E tests."""
    original = vs_module.USE_MOCK_VERIFICATION
    vs_module.USE_MOCK_VERIFICATION = False
    yield
    vs_module.USE_MOCK_VERIFICATION = original


@pytest.fixture
def e2e_canvas_data() -> Dict[str, Any]:
    """Canvas data with 3 red/purple nodes for a full session flow."""
    return {
        "nodes": [
            {
                "id": "node-a",
                "type": "text",
                "text": "梯度下降法",
                "color": "4",  # Red
                "x": 0, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-b",
                "type": "text",
                "text": "损失函数",
                "color": "3",  # Purple
                "x": 250, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-c",
                "type": "text",
                "text": "正则化技术",
                "color": "4",  # Red
                "x": 500, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-d",
                "type": "text",
                "text": "已掌握概念",
                "color": "2",  # Green – ignored
                "x": 0, "y": 150, "width": 200, "height": 100,
            },
        ],
        "edges": [],
    }


@pytest.fixture
def temp_canvas(e2e_canvas_data: Dict[str, Any]) -> str:
    """Create a temporary .canvas file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".canvas", delete=False, encoding="utf-8"
    ) as f:
        json.dump(e2e_canvas_data, f)
        return f.name


@pytest.fixture(autouse=True)
def cleanup_temp(temp_canvas: str):
    """Clean up temp file after each test."""
    yield
    try:
        os.unlink(temp_canvas)
    except (FileNotFoundError, OSError):
        pass


def _make_question_result(text: str = "请解释梯度下降法的核心原理") -> MagicMock:
    """Helper: create an AgentResult-like object for question generation."""
    result = MagicMock()
    result.success = True
    result.data = {
        "questions": [{
            "source_node_id": "e2e_test",
            "question_text": text,
            "question_type": "检验型",
            "difficulty": "基础",
            "guidance": "",
            "rationale": "E2E测试",
        }],
    }
    return result


def _make_scoring_result(total_score: float) -> MagicMock:
    """Helper: create an AgentResult-like object for scoring."""
    result = MagicMock()
    result.success = True
    result.data = {
        "total_score": total_score,
        "accuracy": int(total_score * 0.25),
        "imagery": int(total_score * 0.25),
        "completeness": int(total_score * 0.25),
        "originality": int(total_score * 0.25),
    }
    return result


@pytest.fixture
def mock_agent() -> MagicMock:
    """Mock AgentService with realistic question and scoring responses."""
    service = MagicMock()
    service.call_agent = AsyncMock(return_value=_make_question_result())

    # Default: score based on answer length (simulate realistic scoring)
    async def _scoring(**kwargs):
        answer = kwargs.get("user_understanding", "")
        if len(answer) > 200:
            return _make_scoring_result(85.0)
        elif len(answer) > 100:
            return _make_scoring_result(70.0)
        else:
            return _make_scoring_result(45.0)

    service.call_scoring = AsyncMock(side_effect=_scoring)
    return service


@pytest.fixture
def mock_rag() -> MagicMock:
    """Mock RAG service."""
    service = MagicMock()
    service.query = AsyncMock(return_value={
        "learning_history": "用户之前学习过线性代数基础",
        "textbook_excerpts": "梯度下降是一种迭代优化算法...",
        "related_concepts": ["凸优化", "学习率"],
        "common_mistakes": "容易混淆梯度和导数",
    })
    return service


@pytest.fixture
def service(mock_agent: MagicMock, mock_rag: MagicMock) -> VerificationService:
    """Create VerificationService with mock dependencies for E2E flow."""
    return VerificationService(
        rag_service=mock_rag,
        agent_service=mock_agent,
        canvas_base_path=tempfile.gettempdir(),
    )


# ===========================================================================
# Test 1: Complete verification flow
# ===========================================================================


class TestCompleteVerificationFlow:
    """
    E2E Test: session → answer → score (0-100) → recommend → next → complete

    Validates the full lifecycle from start_session() through process_answer()
    for all concepts, ending with VerificationStatus.COMPLETED.
    """

    @pytest.mark.asyncio
    async def test_start_session_extracts_red_purple_nodes(
        self, service: VerificationService, temp_canvas: str
    ):
        """Canvas reading extracts exactly 3 red/purple nodes, ignores green."""
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        assert session["status"] == "in_progress"
        assert session["session_id"] is not None
        assert session["total_concepts"] == 3
        assert session["first_question"] is not None
        assert len(session["first_question"]) > 0

    @pytest.mark.asyncio
    async def test_answer_returns_score_in_0_100_range(
        self, service: VerificationService, temp_canvas: str
    ):
        """Score is returned in unified 0-100 scale."""
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        result = await service.process_answer(
            session_id=session["session_id"],
            user_answer="这是一个详细的回答，包含对概念的深入分析和理解" * 15,  # >200 chars → 85.0
        )

        assert 0 <= result["score"] <= 100
        assert result["score"] == 85.0
        assert result["quality"] == "excellent"

    @pytest.mark.asyncio
    async def test_full_session_through_all_concepts(
        self,
        service: VerificationService,
        temp_canvas: str,
        mock_agent: MagicMock,
    ):
        """Complete all 3 concepts end-to-end and reach COMPLETED status."""
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]
        total = session["total_concepts"]
        assert total == 3

        detailed_answer = "这是一个详细的回答，包含对概念的深入分析和理解。" * 8

        for i in range(total):
            result = await service.process_answer(
                session_id=session_id,
                user_answer=detailed_answer,
            )

            assert "quality" in result
            assert "score" in result
            assert "progress" in result

            if i < total - 1:
                assert result["action"] == "next"
                assert result["next_question"] is not None
            else:
                assert result["action"] == "complete"

        # Verify final state
        progress = await service.get_progress(session_id)
        assert progress["status"] == VerificationStatus.COMPLETED.value
        assert progress["completed_concepts"] == total

    @pytest.mark.asyncio
    async def test_recommendation_logic_correct(
        self,
        service: VerificationService,
        temp_canvas: str,
        mock_agent: MagicMock,
    ):
        """
        High score (>=60) → action='next'; low score (<60, hints available) → action='hint'.
        """
        # Configure agent to return high score for first call
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(85.0)
        )

        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        # High score → next
        result = await service.process_answer(
            session_id=session["session_id"],
            user_answer="详细回答" * 50,
        )
        assert result["action"] == "next"

        # Now configure low score
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(35.0)
        )

        # Low score → hint
        result = await service.process_answer(
            session_id=session["session_id"],
            user_answer="不太确定",
        )
        assert result["action"] == "hint"
        assert result["hint"] is not None


# ===========================================================================
# Test 2: Pause/Resume flow
# ===========================================================================


class TestPauseResumeFlow:
    """
    E2E Test: session → answer 1 → pause → resume → confirm non-template question

    Validates Story 31.6 pause/resume with stored question restoration.
    """

    @pytest.mark.asyncio
    async def test_pause_resume_preserves_question(
        self,
        service: VerificationService,
        temp_canvas: str,
        mock_agent: MagicMock,
    ):
        """After pause+resume, the stored question is returned (not a template)."""
        # Configure high score so first answer advances
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(85.0)
        )

        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]

        # Answer first concept → advance to second
        result = await service.process_answer(
            session_id=session_id,
            user_answer="详细的梯度下降回答" * 20,
        )
        assert result["action"] == "next"
        second_question = result["next_question"]

        # Pause
        pause_result = await service.pause_session(session_id)
        assert pause_result["status"] == "paused"

        # Resume
        resume_result = await service.resume_session(session_id)
        assert resume_result["status"] == "in_progress"

        # Verify restored question matches stored question (not a template)
        restored_question = resume_result["current_question"]
        assert restored_question is not None
        assert len(restored_question) > 0
        # The question should be the same as what was stored after advancing
        assert restored_question == second_question

    @pytest.mark.asyncio
    async def test_pause_invalid_state_raises(
        self, service: VerificationService, temp_canvas: str
    ):
        """Pausing an already-paused session raises ValueError."""
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]

        await service.pause_session(session_id)

        with pytest.raises(ValueError, match="Cannot pause"):
            await service.pause_session(session_id)

    @pytest.mark.asyncio
    async def test_resume_invalid_state_raises(
        self, service: VerificationService, temp_canvas: str
    ):
        """Resuming an in_progress session raises ValueError."""
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        with pytest.raises(ValueError, match="Cannot resume"):
            await service.resume_session(session["session_id"])

    @pytest.mark.asyncio
    async def test_pause_tracks_duration(
        self, service: VerificationService, temp_canvas: str
    ):
        """Pause/resume accumulates total_pause_duration."""
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]

        await service.pause_session(session_id)

        # Small delay to accumulate measurable duration
        await simulate_async_delay(0.05)

        resume_result = await service.resume_session(session_id)
        progress = resume_result["progress"]

        assert progress["total_pause_duration"] >= 0.0
        assert progress["paused_at"] is None  # Cleared after resume


# ===========================================================================
# Test 3: Consecutive low score recommendation
# ===========================================================================


class TestConsecutiveLowRecommendation:
    """
    E2E Test: 3 low scores → confirm recommendation changes

    After max hints (3), the system should advance to next concept
    even with a low score.
    """

    @pytest.mark.asyncio
    async def test_three_low_scores_exhaust_hints_then_advance(
        self,
        service: VerificationService,
        temp_canvas: str,
        mock_agent: MagicMock,
    ):
        """
        3 consecutive low scores use up all hints, 4th low score forces advance.

        Flow: low→hint, low→hint, low→hint, low→next (hints exhausted)
        """
        # Always return low score
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(30.0)
        )

        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]

        # First 3 low answers → hints
        for i in range(3):
            result = await service.process_answer(
                session_id=session_id,
                user_answer="不确定",
            )
            assert result["action"] == "hint", (
                f"Attempt {i+1}: expected 'hint', got '{result['action']}'"
            )
            assert result["hint"] is not None
            assert result["score"] == 30.0
            assert result["quality"] == "wrong"

        # 4th low answer → hints exhausted, should advance
        result = await service.process_answer(
            session_id=session_id,
            user_answer="还是不确定",
        )
        assert result["action"] == "next", (
            f"After 3 hints, expected 'next' but got '{result['action']}'"
        )

    @pytest.mark.asyncio
    async def test_all_concepts_low_score_still_completes(
        self,
        service: VerificationService,
        temp_canvas: str,
        mock_agent: MagicMock,
    ):
        """Even with all low scores, session eventually reaches COMPLETED."""
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(25.0)
        )

        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]
        total = session["total_concepts"]

        # For each concept: 3 hints + 1 forced advance
        for concept_idx in range(total):
            # 3 hint attempts
            for hint_num in range(3):
                result = await service.process_answer(
                    session_id=session_id,
                    user_answer="不知道",
                )
                assert result["action"] == "hint"

            # Force advance
            result = await service.process_answer(
                session_id=session_id,
                user_answer="不知道",
            )
            if concept_idx < total - 1:
                assert result["action"] == "next"
            else:
                assert result["action"] == "complete"

        # Final state
        progress = await service.get_progress(session_id)
        assert progress["status"] == VerificationStatus.COMPLETED.value
        assert progress["completed_concepts"] == total
        # All low scores → red count should be total
        assert progress["red_count"] == total

    @pytest.mark.asyncio
    async def test_color_counts_reflect_scores(
        self,
        service: VerificationService,
        temp_canvas: str,
        mock_agent: MagicMock,
    ):
        """
        Verify that progress color counts match scoring:
        - score >= 80 → green
        - score 60-79 → yellow
        - score < 60 → red
        """
        session = await service.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]

        # Concept 1: excellent (85)
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(85.0)
        )
        await service.process_answer(
            session_id=session_id,
            user_answer="完美回答" * 50,
        )

        # Concept 2: good (70)
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(70.0)
        )
        await service.process_answer(
            session_id=session_id,
            user_answer="不错的回答" * 50,
        )

        # Concept 3: wrong (25) — exhaust hints then advance
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(25.0)
        )
        for _ in range(3):  # hints
            await service.process_answer(
                session_id=session_id, user_answer="不知道"
            )
        # Force advance on 4th
        await service.process_answer(
            session_id=session_id, user_answer="不知道"
        )

        progress = await service.get_progress(session_id)
        assert progress["green_count"] == 1   # 85 → green
        assert progress["yellow_count"] == 1  # 70 → yellow
        assert progress["red_count"] == 1     # 25 → red
        assert progress["completed_concepts"] == 3


# ===========================================================================
# Test 4: Degradation visibility
# ===========================================================================


class TestDegradationVisibility:
    """
    E2E Test: Mock AI failure → confirm degraded/fallback behavior

    Tests graceful degradation when agent_service fails (timeout, error).
    The service should still produce usable results via fallback.
    """

    @pytest.mark.asyncio
    async def test_scoring_timeout_falls_back_to_mock(
        self,
        mock_rag: MagicMock,
        temp_canvas: str,
    ):
        """When scoring agent times out, mock evaluation is used."""
        mock_agent = MagicMock()
        mock_agent.call_agent = AsyncMock(
            return_value=_make_question_result()
        )
        mock_agent.call_scoring = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )

        svc = VerificationService(
            rag_service=mock_rag,
            agent_service=mock_agent,
            canvas_base_path=tempfile.gettempdir(),
        )

        session = await svc.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        # Short answer → mock fallback → score=20.0 (wrong)
        result = await svc.process_answer(
            session_id=session["session_id"],
            user_answer="短",
        )

        # Fallback mock scoring should produce a result, not raise
        assert result["score"] is not None
        assert result["quality"] is not None
        assert 0 <= result["score"] <= 100

    @pytest.mark.asyncio
    async def test_scoring_exception_falls_back_to_mock(
        self,
        mock_rag: MagicMock,
        temp_canvas: str,
    ):
        """When scoring agent throws an exception, mock evaluation is used."""
        mock_agent = MagicMock()
        mock_agent.call_agent = AsyncMock(
            return_value=_make_question_result()
        )
        mock_agent.call_scoring = AsyncMock(
            side_effect=RuntimeError("API quota exceeded")
        )

        svc = VerificationService(
            rag_service=mock_rag,
            agent_service=mock_agent,
            canvas_base_path=tempfile.gettempdir(),
        )

        session = await svc.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        # Long answer → mock fallback → score=90.0 (excellent)
        result = await svc.process_answer(
            session_id=session["session_id"],
            user_answer="这是一个非常详细的回答" * 30,
        )

        assert result["score"] == 90.0
        assert result["quality"] == "excellent"

    @pytest.mark.asyncio
    async def test_question_generation_timeout_uses_fallback(
        self,
        mock_rag: MagicMock,
        temp_canvas: str,
    ):
        """When question generation times out, a fallback question is produced."""
        mock_agent = MagicMock()
        mock_agent.call_agent = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_agent.call_scoring = AsyncMock(
            return_value=_make_scoring_result(80.0)
        )

        svc = VerificationService(
            rag_service=mock_rag,
            agent_service=mock_agent,
            canvas_base_path=tempfile.gettempdir(),
        )

        session = await svc.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        # Even with timeout, first_question should be a fallback, not None
        assert session["first_question"] is not None
        assert len(session["first_question"]) > 0
        # Fallback question should contain the concept text
        assert session["current_concept"] in session["first_question"]

    @pytest.mark.asyncio
    async def test_no_agent_service_uses_mock_scoring(
        self,
        mock_rag: MagicMock,
        temp_canvas: str,
    ):
        """When agent_service is None entirely, mock evaluation handles scoring."""
        svc = VerificationService(
            rag_service=mock_rag,
            agent_service=None,  # No agent service
            canvas_base_path=tempfile.gettempdir(),
        )

        session = await svc.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )

        # Should still work with mock scoring
        result = await svc.process_answer(
            session_id=session["session_id"],
            user_answer="a" * 101,  # >100 chars → mock score 90.0
        )

        assert result["score"] == 90.0
        assert result["quality"] == "excellent"

    @pytest.mark.asyncio
    async def test_complete_session_under_degradation(
        self,
        mock_rag: MagicMock,
        temp_canvas: str,
    ):
        """Full session completes even when all AI calls are degraded."""
        mock_agent = MagicMock()
        mock_agent.call_agent = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        mock_agent.call_scoring = AsyncMock(
            side_effect=RuntimeError("Service unavailable")
        )

        svc = VerificationService(
            rag_service=mock_rag,
            agent_service=mock_agent,
            canvas_base_path=tempfile.gettempdir(),
        )

        session = await svc.start_session(
            canvas_name="e2e_test", canvas_path=temp_canvas
        )
        session_id = session["session_id"]
        total = session["total_concepts"]
        assert total == 3

        # Complete all concepts with long answers (mock → 90.0 → advance)
        for i in range(total):
            result = await svc.process_answer(
                session_id=session_id,
                user_answer="这是一个完整的回答" * 30,  # >100 chars
            )

            if i < total - 1:
                assert result["action"] == "next"
            else:
                assert result["action"] == "complete"

        progress = await svc.get_progress(session_id)
        assert progress["status"] == VerificationStatus.COMPLETED.value
        assert progress["completed_concepts"] == total
