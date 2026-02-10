"""
Integration tests for EPIC-31: Interactive Verification Session Endpoints

Tests the end-to-end flow:
  POST /review/session/start → session_id + first_question
  POST /review/session/{id}/answer → score + action + progress

[Source: docs/epics/EPIC-31-VERIFICATION-CANVAS-INTELLIGENT-GUIDANCE.md]
"""

import json
import os
import tempfile
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture(autouse=True)
def _reset_verification_singleton():
    """Reset verification service singleton between tests."""
    import app.services.verification_service as vs_module
    original = vs_module._verification_service
    vs_module._verification_service = None
    yield
    vs_module._verification_service = original


@pytest.fixture
def sample_canvas_data() -> Dict[str, Any]:
    """Sample Canvas JSON with red + purple nodes."""
    return {
        "nodes": [
            {
                "id": "node-red-1",
                "type": "text",
                "text": "逆否命题",
                "color": "4",
                "x": 0, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-purple-1",
                "type": "text",
                "text": "充分必要条件",
                "color": "3",
                "x": 300, "y": 0, "width": 200, "height": 100,
            },
            {
                "id": "node-green-1",
                "type": "text",
                "text": "命题逻辑",
                "color": "1",
                "x": 600, "y": 0, "width": 200, "height": 100,
            },
        ],
        "edges": [],
    }


@pytest.fixture
def canvas_temp_dir(sample_canvas_data):
    """Create a temp directory with a sample .canvas file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        canvas_path = os.path.join(tmpdir, "离散数学.canvas")
        with open(canvas_path, "w", encoding="utf-8") as f:
            json.dump(sample_canvas_data, f, ensure_ascii=False)
        yield tmpdir


@pytest.fixture
def mock_verification_service():
    """Create a mock VerificationService with realistic responses."""
    mock_svc = MagicMock()

    # start_session returns session data
    mock_svc.start_session = AsyncMock(return_value={
        "session_id": "test-session-001",
        "total_concepts": 2,
        "first_question": "请用自己的话解释什么是「逆否命题」？",
        "current_concept": "逆否命题",
        "status": "in_progress",
    })

    # process_answer returns scoring + progress
    mock_svc.process_answer = AsyncMock(return_value={
        "quality": "good",
        "score": 72.0,
        "degraded": False,
        "action": "next",
        "hint": None,
        "next_question": "请解释「充分必要条件」的定义和判断方法",
        "current_concept": "充分必要条件",
        "progress": {
            "session_id": "test-session-001",
            "canvas_name": "离散数学",
            "total_concepts": 2,
            "completed_concepts": 1,
            "current_concept": "充分必要条件",
            "current_concept_idx": 1,
            "green_count": 0,
            "yellow_count": 1,
            "purple_count": 0,
            "red_count": 0,
            "status": "in_progress",
            "progress_percentage": 50.0,
            "mastery_percentage": 0.0,
            "hints_given": 0,
            "max_hints": 3,
            "started_at": "2026-02-09T10:00:00",
            "updated_at": "2026-02-09T10:01:00",
        },
    })

    # pause/resume
    mock_svc.pause_session = AsyncMock(return_value=True)
    mock_svc.resume_session = AsyncMock(return_value=True)

    # get_progress
    mock_progress = MagicMock()
    mock_progress.to_dict.return_value = {
        "session_id": "test-session-001",
        "canvas_name": "离散数学",
        "total_concepts": 2,
        "completed_concepts": 1,
        "current_concept": "充分必要条件",
        "current_concept_idx": 1,
        "green_count": 0,
        "yellow_count": 1,
        "purple_count": 0,
        "red_count": 0,
        "status": "in_progress",
        "progress_percentage": 50.0,
        "mastery_percentage": 0.0,
        "hints_given": 0,
        "max_hints": 3,
    }
    from datetime import datetime
    mock_progress.started_at = datetime(2026, 2, 9, 10, 0, 0)
    mock_progress.updated_at = datetime(2026, 2, 9, 10, 1, 0)
    mock_svc.get_progress = AsyncMock(return_value=mock_progress)

    return mock_svc


@pytest.fixture
def client_with_mock_vs(mock_verification_service):
    """TestClient with mocked VerificationService singleton.

    Patches both the new _get_vs_singleton() and the original
    get_verification_service() used by existing pause/resume/progress endpoints.
    """
    # Code Review Fix: _get_vs_singleton was renamed to _get_or_create_verification_service
    with patch(
        "app.api.v1.endpoints.review._get_or_create_verification_service",
        return_value=mock_verification_service,
    ), patch(
        "app.services.verification_service.get_verification_service",
        return_value=mock_verification_service,
    ):
        with TestClient(app) as c:
            yield c, mock_verification_service


# ===========================================================================
# Tests
# ===========================================================================


class TestStartSession:
    """Tests for POST /api/v1/review/session/start"""

    def test_start_session_returns_question(self, client_with_mock_vs):
        """EPIC-31: Start session returns session_id and first_question."""
        client, mock_svc = client_with_mock_vs

        response = client.post(
            "/api/v1/review/session/start",
            json={"canvas_name": "离散数学"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-001"
        assert data["total_concepts"] == 2
        assert "逆否命题" in data["first_question"]
        assert data["current_concept"] == "逆否命题"
        assert data["status"] == "in_progress"

        # Verify service was called with correct args
        mock_svc.start_session.assert_called_once()
        call_kwargs = mock_svc.start_session.call_args[1]
        assert call_kwargs["canvas_name"] == "离散数学"
        assert call_kwargs["include_mastered"] is True

    def test_start_session_with_node_ids(self, client_with_mock_vs):
        """Start session with specific node IDs."""
        client, mock_svc = client_with_mock_vs

        response = client.post(
            "/api/v1/review/session/start",
            json={
                "canvas_name": "离散数学",
                "node_ids": ["node-red-1"],
                "include_mastered": False,
            },
        )

        assert response.status_code == 200
        call_kwargs = mock_svc.start_session.call_args[1]
        assert call_kwargs["node_ids"] == ["node-red-1"]
        assert call_kwargs["include_mastered"] is False

    def test_start_session_no_concepts_returns_404(self, client_with_mock_vs):
        """404 when canvas has no verifiable concepts."""
        client, mock_svc = client_with_mock_vs
        mock_svc.start_session = AsyncMock(return_value={
            "session_id": "empty",
            "total_concepts": 0,
            "first_question": "",
            "current_concept": "",
            "status": "completed",
        })

        response = client.post(
            "/api/v1/review/session/start",
            json={"canvas_name": "空白Canvas"},
        )

        assert response.status_code == 404
        assert "No verifiable concepts" in response.json()["detail"]

    def test_start_session_value_error_returns_404(self, client_with_mock_vs):
        """ValueError (invalid canvas) maps to 404."""
        client, mock_svc = client_with_mock_vs
        mock_svc.start_session = AsyncMock(side_effect=ValueError("Canvas not found"))

        response = client.post(
            "/api/v1/review/session/start",
            json={"canvas_name": "不存在的Canvas"},
        )

        assert response.status_code == 404


class TestSubmitAnswer:
    """Tests for POST /api/v1/review/session/{id}/answer"""

    def test_submit_answer_returns_score(self, client_with_mock_vs):
        """EPIC-31: Submit answer returns quality, score, and progress."""
        client, mock_svc = client_with_mock_vs

        response = client.post(
            "/api/v1/review/session/test-session-001/answer",
            json={"user_answer": "逆否命题就是将原命题的条件和结论同时取反再交换"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quality"] == "good"
        assert 0 <= data["score"] <= 100
        assert data["action"] == "next"
        assert data["current_concept"] == "充分必要条件"
        assert data["next_question"] is not None

        # Verify progress is included
        progress = data["progress"]
        assert progress["session_id"] == "test-session-001"
        assert progress["completed_concepts"] == 1
        assert progress["total_concepts"] == 2
        assert progress["progress_percentage"] == 50.0

    def test_submit_answer_invalid_session_returns_404(self, client_with_mock_vs):
        """404 when session_id doesn't exist."""
        client, mock_svc = client_with_mock_vs
        mock_svc.process_answer = AsyncMock(
            side_effect=ValueError("Session not found: nonexistent")
        )

        response = client.post(
            "/api/v1/review/session/nonexistent/answer",
            json={"user_answer": "test"},
        )

        assert response.status_code == 404

    def test_submit_answer_empty_string_rejected(self, client_with_mock_vs):
        """Empty answer string should be rejected by validation."""
        client, _ = client_with_mock_vs

        response = client.post(
            "/api/v1/review/session/test-session-001/answer",
            json={"user_answer": ""},
        )

        # Pydantic min_length=1 validation
        assert response.status_code == 422


class TestFullInteractiveFlow:
    """End-to-end interactive verification flow test."""

    def test_full_flow_start_answer_pause_resume(self, client_with_mock_vs):
        """EPIC-31: Complete flow - start → answer → pause → resume."""
        client, mock_svc = client_with_mock_vs

        # Step 1: Start session
        start_resp = client.post(
            "/api/v1/review/session/start",
            json={"canvas_name": "离散数学"},
        )
        assert start_resp.status_code == 200
        session_id = start_resp.json()["session_id"]
        assert session_id == "test-session-001"

        # Step 2: Submit first answer
        answer_resp = client.post(
            f"/api/v1/review/session/{session_id}/answer",
            json={"user_answer": "逆否命题是原命题条件结论同时否定再交换"},
        )
        assert answer_resp.status_code == 200
        assert answer_resp.json()["action"] == "next"
        assert answer_resp.json()["progress"]["completed_concepts"] == 1

        # Step 3: Pause session
        pause_resp = client.post(f"/api/v1/review/session/{session_id}/pause")
        assert pause_resp.status_code == 200
        assert pause_resp.json()["status"] == "paused"

        # Step 4: Resume session
        resume_resp = client.post(f"/api/v1/review/session/{session_id}/resume")
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "in_progress"

        # Step 5: Get progress
        progress_resp = client.get(f"/api/v1/review/session/{session_id}/progress")
        assert progress_resp.status_code == 200
        assert progress_resp.json()["completed_concepts"] == 1


# ===========================================================================
# Story 31.A.8 Code Review Fix: API-level degraded field verification
# ===========================================================================


class TestDegradedFieldsInApiResponse:
    """Story 31.A.8 Code Review: Verify degraded fields pass through API layer.

    These tests ensure that degraded, degraded_reason, and degraded_warning
    are present in the HTTP response (not just the service-layer dict).
    This catches the critical bug where SubmitAnswerResponse model was
    missing these fields, causing FastAPI to silently strip them.
    """

    def test_normal_response_includes_degraded_false(self, client_with_mock_vs):
        """API response includes degraded=False for normal scoring."""
        client, _ = client_with_mock_vs

        response = client.post(
            "/api/v1/review/session/test-session-001/answer",
            json={"user_answer": "逆否命题是原命题条件结论取反再交换"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "degraded" in data, "degraded field missing from API response"
        assert data["degraded"] is False
        assert data["degraded_reason"] is None
        assert data["degraded_warning"] is None

    def test_degraded_response_includes_reason_and_warning(self, client_with_mock_vs):
        """API response includes degraded_reason and degraded_warning when degraded."""
        client, mock_svc = client_with_mock_vs

        # Override mock to return degraded response
        mock_svc.process_answer = AsyncMock(return_value={
            "quality": "partial",
            "score": 50.0,
            "degraded": True,
            "degraded_reason": "agent_unavailable",
            "degraded_warning": "评分基于答案长度而非内容质量，仅供参考",
            "action": "hint",
            "hint": "请考虑逆否命题的定义",
            "next_question": None,
            "current_concept": "逆否命题",
            "progress": {
                "session_id": "test-session-001",
                "canvas_name": "离散数学",
                "total_concepts": 2,
                "completed_concepts": 0,
                "current_concept": "逆否命题",
                "current_concept_idx": 0,
                "green_count": 0,
                "yellow_count": 0,
                "purple_count": 1,
                "red_count": 1,
                "status": "in_progress",
                "progress_percentage": 0.0,
                "mastery_percentage": 0.0,
                "hints_given": 1,
                "max_hints": 3,
                "started_at": "2026-02-10T10:00:00",
                "updated_at": "2026-02-10T10:01:00",
            },
        })

        response = client.post(
            "/api/v1/review/session/test-session-001/answer",
            json={"user_answer": "不知道"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["degraded"] is True
        assert data["degraded_reason"] == "agent_unavailable"
        assert "仅供参考" in data["degraded_warning"]
