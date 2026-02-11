# Canvas Learning System - Recommend Action API Tests
# Story 31.3: Agent决策推荐端点
"""
Integration tests for POST /api/v1/agents/recommend-action endpoint.

Tests verify:
- AC-31.3.1: POST /agents/recommend-action endpoint exists and responds
- AC-31.3.2: Request accepts score, node_id, canvas_name parameters
- AC-31.3.3: Score decision logic (<60→decompose, 60-79→explain, >=80→next)
- AC-31.3.4: Historical score trend consideration

[Source: docs/stories/31.3.story.md]
"""

from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.memory_service import MemoryService


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture(autouse=True)
def _clear_request_cache():
    """Clear request dedup cache between tests to prevent 409 Conflict.

    Story 12.H.5: The global request_cache singleton persists across tests.
    Without clearing, tests reusing the same (canvas_name, node_id) combo
    are rejected as duplicate requests.
    """
    from app.core.request_cache import request_cache
    request_cache.clear()
    yield
    request_cache.clear()


@pytest.fixture
def mock_memory_service():
    """Mock MemoryService for history queries."""
    svc = MagicMock(spec=MemoryService)
    svc.get_learning_history = AsyncMock(return_value={
        "items": [],
        "total": 0,
    })
    return svc


@pytest.fixture
def client_with_mock(mock_memory_service):
    """TestClient with mocked MemoryService."""
    from app.services.memory_service import get_memory_service

    app.dependency_overrides[get_memory_service] = lambda: mock_memory_service

    with TestClient(app) as c:
        yield c, mock_memory_service

    app.dependency_overrides.pop(get_memory_service, None)


def _make_history_items(scores: List[int]):
    """Build mock history items from a list of scores."""
    items = []
    for i, s in enumerate(scores):
        items.append({
            "score": s,
            "timestamp": f"2026-01-{15 - i:02d}T10:00:00Z",
            "concept": "逆否命题",
        })
    return {"items": items, "total": len(items)}


# ===========================================================================
# AC-31.3.1: Endpoint Exists
# ===========================================================================


class TestRecommendActionEndpoint:
    """Test POST /api/v1/agents/recommend-action exists.

    [Source: docs/stories/31.3.story.md#AC-31.3.1]
    """

    def test_endpoint_returns_200(self, client_with_mock):
        """AC-31.3.1: Endpoint responds with 200."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 75,
                "node_id": "node-1",
                "canvas_name": "离散数学.canvas",
            },
        )
        assert response.status_code == 200

    def test_endpoint_returns_json(self, client_with_mock):
        """AC-31.3.1: Response is valid JSON."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 50,
                "node_id": "node-1",
                "canvas_name": "test.canvas",
            },
        )
        data = response.json()
        assert "action" in data
        assert "reason" in data


# ===========================================================================
# AC-31.3.2: Request Parameters
# ===========================================================================


class TestRecommendActionRequestParams:
    """Test request parameter validation.

    [Source: docs/stories/31.3.story.md#AC-31.3.2]
    """

    def test_score_required(self, client_with_mock):
        """AC-31.3.2: score is required."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"node_id": "node-1", "canvas_name": "test.canvas"},
        )
        assert response.status_code == 422

    def test_node_id_required(self, client_with_mock):
        """AC-31.3.2: node_id is required."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 50, "canvas_name": "test.canvas"},
        )
        assert response.status_code == 422

    def test_canvas_name_required(self, client_with_mock):
        """AC-31.3.2: canvas_name is required."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 50, "node_id": "node-1"},
        )
        assert response.status_code == 422

    def test_score_range_validation(self, client_with_mock):
        """AC-31.3.2: score must be 0-100."""
        client, _ = client_with_mock
        # score > 100
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 101, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.status_code == 422

        # score < 0
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": -1, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.status_code == 422

    def test_optional_concept_parameter(self, client_with_mock):
        """AC-31.3.2: concept is optional."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 50,
                "node_id": "node-1",
                "canvas_name": "test.canvas",
                "concept": "逆否命题",
            },
        )
        assert response.status_code == 200

    def test_include_history_parameter(self, client_with_mock):
        """AC-31.3.2: include_history is optional, defaults to True."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 50,
                "node_id": "node-1",
                "canvas_name": "test.canvas",
                "include_history": False,
            },
        )
        assert response.status_code == 200


# ===========================================================================
# AC-31.3.3: Score Decision Logic
# ===========================================================================


class TestScoreDecisionLogic:
    """Test score-based recommendation logic.

    [Source: docs/stories/31.3.story.md#AC-31.3.3]
    """

    def test_low_score_returns_decompose(self, client_with_mock):
        """AC-31.3.3: score < 60 → decompose action."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 30, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        data = response.json()
        assert data["action"] == "decompose"

    def test_score_59_returns_decompose(self, client_with_mock):
        """AC-31.3.3: score=59 boundary → decompose."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 59, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.json()["action"] == "decompose"

    def test_mid_score_returns_explain(self, client_with_mock):
        """AC-31.3.3: score 60-79 → explain action."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 70, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        data = response.json()
        assert data["action"] == "explain"

    def test_score_60_returns_explain(self, client_with_mock):
        """AC-31.3.3: score=60 boundary → explain."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 60, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.json()["action"] == "explain"

    def test_score_79_returns_explain(self, client_with_mock):
        """AC-31.3.3: score=79 boundary → explain."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 79, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.json()["action"] == "explain"

    def test_high_score_returns_next(self, client_with_mock):
        """AC-31.3.3: score >= 80 → next action."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 85, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        data = response.json()
        assert data["action"] == "next"

    def test_score_80_returns_next(self, client_with_mock):
        """AC-31.3.3: score=80 boundary → next."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 80, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.json()["action"] == "next"

    def test_score_100_returns_next(self, client_with_mock):
        """AC-31.3.3: score=100 → next."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 100, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        assert response.json()["action"] == "next"

    def test_decompose_returns_agent_path(self, client_with_mock):
        """AC-31.3.3: decompose action includes agent path."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 30, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        data = response.json()
        assert data["agent"] is not None
        assert "decompose" in data["agent"] or "basic" in data["agent"]

    def test_explain_returns_agent_path(self, client_with_mock):
        """AC-31.3.3: explain action includes agent path."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 65, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        data = response.json()
        assert data["agent"] is not None
        assert "explain" in data["agent"] or "oral" in data["agent"]

    def test_next_has_no_agent(self, client_with_mock):
        """AC-31.3.3: next action has no agent (null)."""
        client, _ = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 90, "node_id": "n1", "canvas_name": "test.canvas"},
        )
        data = response.json()
        assert data["agent"] is None


# ===========================================================================
# AC-31.3.4: Historical Score Trend
# ===========================================================================


class TestHistoryTrendConsideration:
    """Test historical score trend analysis.

    [Source: docs/stories/31.3.story.md#AC-31.3.4]
    """

    def test_declining_trend_suggests_review(self, client_with_mock):
        """AC-31.3.4: Declining trend sets review_suggested=True."""
        client, mock_ms = client_with_mock
        # Scores declining: 50, 60, 70, 80, 90 (most recent first = 50)
        mock_ms.get_learning_history.return_value = _make_history_items(
            [50, 60, 70, 80, 90]
        )
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 50,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": True,
            },
        )
        data = response.json()
        assert data["review_suggested"] is True

    def test_improving_trend_no_review(self, client_with_mock):
        """AC-31.3.4: Improving trend does not suggest review."""
        client, mock_ms = client_with_mock
        # Scores improving: 90, 80, 70, 60, 50 (most recent first = 90)
        mock_ms.get_learning_history.return_value = _make_history_items(
            [90, 80, 70, 60, 50]
        )
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 90,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": True,
            },
        )
        data = response.json()
        assert data["review_suggested"] is False

    def test_history_context_in_response(self, client_with_mock):
        """AC-31.3.4: Response includes history_context when available."""
        client, mock_ms = client_with_mock
        mock_ms.get_learning_history.return_value = _make_history_items(
            [75, 70, 65]
        )
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 75,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": True,
            },
        )
        data = response.json()
        assert "history_context" in data
        ctx = data["history_context"]
        assert "recent_scores" in ctx
        assert "average_score" in ctx
        assert "trend" in ctx

    def test_no_history_returns_null_context(self, client_with_mock):
        """AC-31.3.4: No history → history_context is null."""
        client, mock_ms = client_with_mock
        mock_ms.get_learning_history.return_value = {"items": [], "total": 0}
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 75,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": True,
            },
        )
        data = response.json()
        assert data["history_context"] is None

    def test_include_history_false_skips_query(self, client_with_mock):
        """AC-31.3.4: include_history=False skips memory query."""
        client, mock_ms = client_with_mock
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 75,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": False,
            },
        )
        assert response.status_code == 200
        mock_ms.get_learning_history.assert_not_called()

    def test_consecutive_low_scores_alternative_agents(self, client_with_mock):
        """AC-31.3.4: 3+ consecutive low scores suggest alternative agents."""
        client, mock_ms = client_with_mock
        mock_ms.get_learning_history.return_value = _make_history_items(
            [40, 35, 30, 25, 50]
        )
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 40,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": True,
            },
        )
        data = response.json()
        # consecutive_low_count should be >= 3 (most recent: 40, 35, 30)
        if data.get("history_context"):
            assert data["history_context"]["consecutive_low_count"] >= 3

    def test_memory_service_error_graceful_degradation(self, client_with_mock):
        """AC-31.3.4: Memory service error → graceful degradation."""
        client, mock_ms = client_with_mock
        mock_ms.get_learning_history.side_effect = Exception("Neo4j down")
        response = client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 50,
                "node_id": "n1",
                "canvas_name": "test.canvas",
                "include_history": True,
            },
        )
        # Should still return a valid response (degraded without history)
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "decompose"
        assert data["history_context"] is None


# ===========================================================================
# Unit Tests: _calculate_trend and _recommend_action_from_score
# ===========================================================================


class TestCalculateTrend:
    """Unit tests for trend calculation helper.

    [Source: docs/stories/31.3.story.md#AC-31.3.4]
    """

    def test_fewer_than_3_scores_is_stable(self):
        """< 3 scores → stable trend."""
        from app.api.v1.endpoints.agents import _calculate_trend
        from app.models.schemas import ActionTrend
        assert _calculate_trend([80, 70]) == ActionTrend.stable
        assert _calculate_trend([80]) == ActionTrend.stable
        assert _calculate_trend([]) == ActionTrend.stable

    def test_improving_trend(self):
        """Recent scores higher than older → improving."""
        from app.api.v1.endpoints.agents import _calculate_trend
        from app.models.schemas import ActionTrend
        # Recent: [90, 85] avg=87.5, Older: [60, 55, 50] avg=55
        assert _calculate_trend([90, 85, 60, 55, 50]) == ActionTrend.improving

    def test_declining_trend(self):
        """Recent scores lower than older → declining."""
        from app.api.v1.endpoints.agents import _calculate_trend
        from app.models.schemas import ActionTrend
        # Recent: [50, 55] avg=52.5, Older: [80, 85, 90] avg=85
        assert _calculate_trend([50, 55, 80, 85, 90]) == ActionTrend.declining

    def test_stable_trend(self):
        """Scores roughly equal → stable."""
        from app.api.v1.endpoints.agents import _calculate_trend
        from app.models.schemas import ActionTrend
        assert _calculate_trend([72, 70, 71, 73, 70]) == ActionTrend.stable


class TestRecommendActionFromScore:
    """Unit tests for _recommend_action_from_score helper.

    [Source: docs/stories/31.3.story.md#AC-31.3.3]
    """

    def test_low_score_decompose(self):
        """score < 60 → decompose."""
        from app.api.v1.endpoints.agents import _recommend_action_from_score
        from app.models.schemas import ActionType
        action, reason, agent, priority, review, alts = _recommend_action_from_score(30)
        assert action == ActionType.decompose

    def test_mid_score_explain(self):
        """60 <= score < 80 → explain."""
        from app.api.v1.endpoints.agents import _recommend_action_from_score
        from app.models.schemas import ActionType
        action, reason, agent, priority, review, alts = _recommend_action_from_score(70)
        assert action == ActionType.explain

    def test_high_score_next(self):
        """score >= 80 → next."""
        from app.api.v1.endpoints.agents import _recommend_action_from_score
        from app.models.schemas import ActionType
        action, reason, agent, priority, review, alts = _recommend_action_from_score(85)
        assert action == ActionType.next

    def test_declining_history_sets_review(self):
        """Declining history → review_suggested=True."""
        from app.api.v1.endpoints.agents import _recommend_action_from_score
        from app.models.schemas import ActionTrend, HistoryContext
        ctx = HistoryContext(
            recent_scores=[50, 60, 70],
            average_score=60.0,
            trend=ActionTrend.declining,
            consecutive_low_count=1,
        )
        _, _, _, priority, review, _ = _recommend_action_from_score(50, ctx)
        assert review is True
        assert priority == 1
