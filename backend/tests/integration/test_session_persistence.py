# Canvas Learning System - Session Persistence Tests
# Story 31.10: 跨进程会话持久化
"""
Integration tests for session persistence and state management.

Tests verify:
- Session state transitions (in_progress → paused → in_progress → completed)
- State validation (invalid transitions raise errors)
- Session not found handling
- Progress tracking across session lifecycle
- Pause/resume timestamps and duration tracking

[Source: docs/stories/31.10.story.md]
"""

import json
import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.verification_service import (
    VerificationService,
    VerificationStatus,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def mock_canvas_data():
    """Canvas with 2 red/purple nodes for testing."""
    return {
        "nodes": [
            {"id": "n1", "type": "text", "text": "概念A", "color": "4",
             "x": 0, "y": 0, "width": 200, "height": 100},
            {"id": "n2", "type": "text", "text": "概念B", "color": "3",
             "x": 300, "y": 0, "width": 200, "height": 100},
        ],
        "edges": [],
    }


@pytest.fixture
def temp_canvas_file(mock_canvas_data):
    """Create a temporary Canvas file."""
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.canvas', delete=False, encoding='utf-8'
    ) as f:
        json.dump(mock_canvas_data, f)
        path = f.name
    yield path
    try:
        os.unlink(path)
    except (FileNotFoundError, OSError):
        pass


@pytest.fixture
def mock_agent_service():
    """Mock agent service for question generation and scoring."""
    svc = MagicMock()
    q_result = MagicMock()
    q_result.success = True
    q_result.data = {
        "questions": [{
            "source_node_id": "test",
            "question_text": "测试问题",
            "question_type": "检验型",
            "difficulty": "基础",
            "guidance": "",
            "rationale": "test",
        }]
    }
    svc.call_agent = AsyncMock(return_value=q_result)

    s_result = MagicMock()
    s_result.success = True
    s_result.data = {"total_score": 75.0, "color": "2"}
    svc.call_scoring = AsyncMock(return_value=s_result)
    return svc


@pytest.fixture
def verification_service(mock_agent_service):
    """VerificationService with mock dependencies."""
    return VerificationService(
        agent_service=mock_agent_service,
        canvas_base_path=tempfile.gettempdir(),
    )


# ===========================================================================
# Session State Transitions
# ===========================================================================


class TestSessionStateTransitions:
    """Test session state transitions.

    Story 31.10: Session state machine must enforce valid transitions.
    """

    @pytest.mark.asyncio
    async def test_session_starts_in_progress(
        self, verification_service, temp_canvas_file
    ):
        """New session starts in IN_PROGRESS state."""
        result = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        assert result["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_pause_sets_paused_state(
        self, verification_service, temp_canvas_file
    ):
        """Pausing session sets status to PAUSED."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        result = await verification_service.pause_session(session["session_id"])
        assert result["status"] == "paused"

    @pytest.mark.asyncio
    async def test_resume_sets_in_progress(
        self, verification_service, temp_canvas_file
    ):
        """Resuming paused session sets status back to IN_PROGRESS."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        await verification_service.pause_session(session["session_id"])
        result = await verification_service.resume_session(session["session_id"])
        assert result["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_cannot_pause_paused_session(
        self, verification_service, temp_canvas_file
    ):
        """Pausing an already paused session raises ValueError."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        await verification_service.pause_session(session["session_id"])

        with pytest.raises(ValueError, match="Cannot pause"):
            await verification_service.pause_session(session["session_id"])

    @pytest.mark.asyncio
    async def test_cannot_resume_in_progress_session(
        self, verification_service, temp_canvas_file
    ):
        """Resuming a non-paused session raises ValueError."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        with pytest.raises(ValueError, match="Cannot resume"):
            await verification_service.resume_session(session["session_id"])


# ===========================================================================
# Session Not Found
# ===========================================================================


class TestSessionNotFound:
    """Test handling of invalid session IDs.

    Story 31.10: Session persistence must handle missing sessions gracefully.
    """

    @pytest.mark.asyncio
    async def test_pause_nonexistent_session(self, verification_service):
        """Pausing nonexistent session raises ValueError."""
        with pytest.raises(ValueError, match="Session not found"):
            await verification_service.pause_session("nonexistent-id")

    @pytest.mark.asyncio
    async def test_resume_nonexistent_session(self, verification_service):
        """Resuming nonexistent session raises ValueError."""
        with pytest.raises(ValueError, match="Session not found"):
            await verification_service.resume_session("nonexistent-id")

    @pytest.mark.asyncio
    async def test_get_progress_nonexistent_session(self, verification_service):
        """Getting progress of nonexistent session raises ValueError."""
        with pytest.raises(ValueError, match="Session not found"):
            await verification_service.get_progress("nonexistent-id")

    @pytest.mark.asyncio
    async def test_process_answer_nonexistent_session(self, verification_service):
        """Processing answer for nonexistent session raises ValueError."""
        with pytest.raises(ValueError, match="Session not found"):
            await verification_service.process_answer("nonexistent-id", "answer")

    @pytest.mark.asyncio
    async def test_skip_concept_nonexistent_session(self, verification_service):
        """Skipping concept for nonexistent session raises ValueError."""
        with pytest.raises(ValueError, match="Session not found"):
            await verification_service.skip_concept("nonexistent-id")


# ===========================================================================
# Progress Tracking Across Lifecycle
# ===========================================================================


class TestProgressPersistence:
    """Test progress data persists across session operations.

    Story 31.10: Session state must be consistent across operations.
    """

    @pytest.mark.asyncio
    async def test_progress_after_start(
        self, verification_service, temp_canvas_file
    ):
        """Progress is available immediately after session start."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        progress = await verification_service.get_progress(session["session_id"])
        assert progress["total_concepts"] >= 1
        assert progress["completed_concepts"] == 0
        assert progress["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_progress_after_answer(
        self, verification_service, temp_canvas_file
    ):
        """Progress updates after answering a question."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        result = await verification_service.process_answer(
            session["session_id"],
            "这是一个详细的回答，包含对概念的深入理解和分析。" * 3,
        )
        assert "progress" in result
        assert result["progress"]["completed_concepts"] >= 1

    @pytest.mark.asyncio
    async def test_progress_survives_pause_resume(
        self, verification_service, temp_canvas_file
    ):
        """Progress data survives pause/resume cycle."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        sid = session["session_id"]

        # Answer first question
        await verification_service.process_answer(
            sid, "detailed answer " * 10,
        )

        # Pause → resume
        await verification_service.pause_session(sid)
        await verification_service.resume_session(sid)

        # Progress should still reflect the completed answer
        progress = await verification_service.get_progress(sid)
        assert progress["completed_concepts"] >= 1

    @pytest.mark.asyncio
    async def test_session_id_is_unique(
        self, verification_service, temp_canvas_file
    ):
        """Each session gets a unique ID."""
        s1 = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        s2 = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        assert s1["session_id"] != s2["session_id"]


# ===========================================================================
# Timestamp Tracking
# ===========================================================================


class TestTimestampTracking:
    """Test timestamp tracking for session operations.

    Story 31.10: Session timestamps must be tracked for persistence.
    """

    @pytest.mark.asyncio
    async def test_pause_records_timestamp(
        self, verification_service, temp_canvas_file
    ):
        """Pausing records paused_at timestamp."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        sid = session["session_id"]
        await verification_service.pause_session(sid)

        # Access internal progress to check timestamp
        progress = verification_service._progress[sid]
        assert progress.paused_at is not None
        assert isinstance(progress.paused_at, datetime)

    @pytest.mark.asyncio
    async def test_resume_clears_paused_at(
        self, verification_service, temp_canvas_file
    ):
        """Resuming clears paused_at timestamp."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        sid = session["session_id"]
        await verification_service.pause_session(sid)
        await verification_service.resume_session(sid)

        progress = verification_service._progress[sid]
        assert progress.paused_at is None

    @pytest.mark.asyncio
    async def test_resume_accumulates_pause_duration(
        self, verification_service, temp_canvas_file
    ):
        """Resume accumulates pause duration."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        sid = session["session_id"]

        # Set a past paused_at to simulate time passing
        await verification_service.pause_session(sid)
        progress = verification_service._progress[sid]
        # Manually backdate for testing
        from datetime import timedelta
        progress.paused_at = datetime.now() - timedelta(seconds=5)
        initial_duration = progress.total_pause_duration

        await verification_service.resume_session(sid)
        assert progress.total_pause_duration > initial_duration


# ===========================================================================
# In-Memory Storage Characteristics
# ===========================================================================


class TestInMemoryStorage:
    """Test in-memory session storage characteristics.

    Story 31.10: Current implementation uses TTLCache (1 hour TTL).
    These tests document the current storage behavior.
    """

    @pytest.mark.asyncio
    async def test_session_stored_in_memory(
        self, verification_service, temp_canvas_file
    ):
        """Session data stored in _sessions dict."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        assert session["session_id"] in verification_service._sessions

    @pytest.mark.asyncio
    async def test_progress_stored_in_memory(
        self, verification_service, temp_canvas_file
    ):
        """Progress data stored in _progress dict."""
        session = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        assert session["session_id"] in verification_service._progress

    @pytest.mark.asyncio
    async def test_multiple_sessions_isolated(
        self, verification_service, temp_canvas_file
    ):
        """Multiple sessions have isolated state."""
        s1 = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        s2 = await verification_service.start_session(
            canvas_name="test", canvas_path=temp_canvas_file
        )
        # Pause s1, s2 should remain in_progress
        await verification_service.pause_session(s1["session_id"])

        p1 = await verification_service.get_progress(s1["session_id"])
        p2 = await verification_service.get_progress(s2["session_id"])
        assert p1["status"] == "paused"
        assert p2["status"] == "in_progress"
