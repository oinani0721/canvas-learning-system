# Canvas Learning System - Story 31.3 Tests
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: testing)
"""
Story 31.3 - Intelligent Action Recommendation Endpoint Tests

Tests for POST /api/v1/agents/recommend-action endpoint:
- AC-31.3.1: New endpoint POST /agents/recommend-action
- AC-31.3.2: Request params: score, node_id, canvas_name
- AC-31.3.3: Score-based recommendations (0-100 scale)
  - score < 60: decompose
  - score 60-79: explain
  - score >= 80: next
- AC-31.3.4: Consider history score trends
- AC-31.3.5: Frontend ScoringResultPanel integration (integration test)

[Source: docs/stories/31.3.story.md]
[Source: specs/data/recommend-action-request.schema.json]
[Source: specs/data/recommend-action-response.schema.json]
"""

from typing import Any, Dict, List, Optional

import pytest
from app.api.v1.endpoints.agents import (
    _calculate_trend,
    _recommend_action_from_score,
    recommend_action,
)
from app.models import (
    ActionTrend,
    ActionType,
    AlternativeAgent,
    HistoryContext,
    RecommendActionRequest,
    RecommendActionResponse,
)


class MockMemoryService:
    """Mock MemoryService for testing Story 31.3."""

    def __init__(
        self,
        history_items: Optional[List[Dict[str, Any]]] = None,
        should_raise: bool = False,
    ):
        """
        Initialize mock service.

        Args:
            history_items: List of history items to return (each with optional 'score' key)
            should_raise: Whether to raise an exception
        """
        self.history_items = history_items or []
        self.should_raise = should_raise
        self.call_count = 0
        self.last_params: Dict[str, Any] = {}

    async def get_learning_history(
        self,
        user_id: str,
        concept: Optional[str] = None,
        page: int = 1,
        page_size: int = 5,
    ) -> Dict[str, Any]:
        """Mock get_learning_history method."""
        self.call_count += 1
        self.last_params = {
            "user_id": user_id,
            "concept": concept,
            "page": page,
            "page_size": page_size,
        }

        if self.should_raise:
            raise Exception("Mock history query error")

        return {
            "items": self.history_items,
            "total": len(self.history_items),
            "page": page,
            "page_size": page_size,
            "pages": 1,
        }


class TestCalculateTrend:
    """Test _calculate_trend helper function (AC-31.3.4)."""

    def test_single_score_returns_stable(self):
        """Single score should return stable trend."""
        result = _calculate_trend([75])
        assert result == ActionTrend.stable

    def test_empty_scores_returns_stable(self):
        """Empty scores should return stable trend."""
        # Actually, with < 2 scores, it returns stable
        result = _calculate_trend([])
        assert result == ActionTrend.stable

    def test_improving_trend(self):
        """Recent scores higher than older scores = improving."""
        # Recent: [85, 80], avg=82.5; Older: [70, 65, 60], avg=65
        # diff = 82.5 - 65 = 17.5 > 5 -> improving
        result = _calculate_trend([85, 80, 70, 65, 60])
        assert result == ActionTrend.improving

    def test_declining_trend(self):
        """Recent scores lower than older scores = declining."""
        # Recent: [55, 50], avg=52.5; Older: [70, 75, 80], avg=75
        # diff = 52.5 - 75 = -22.5 < -5 -> declining
        result = _calculate_trend([55, 50, 70, 75, 80])
        assert result == ActionTrend.declining

    def test_stable_trend_small_diff(self):
        """Small difference between recent and older scores = stable."""
        # Recent: [72, 70], avg=71; Older: [70, 68, 69], avg=69
        # diff = 71 - 69 = 2, not > 5 and not < -5 -> stable
        result = _calculate_trend([72, 70, 70, 68, 69])
        assert result == ActionTrend.stable

    def test_two_scores_improving(self):
        """Two scores with improvement."""
        # mid = 1, recent: [80], older: [60]
        result = _calculate_trend([80, 60])
        assert result == ActionTrend.improving

    def test_two_scores_declining(self):
        """Two scores with decline."""
        result = _calculate_trend([50, 75])
        assert result == ActionTrend.declining


class TestRecommendActionFromScore:
    """Test _recommend_action_from_score helper function (AC-31.3.3)."""

    def test_low_score_recommends_decompose(self):
        """Score < 60 should recommend decompose."""
        action, reason, agent, priority, review, alts = _recommend_action_from_score(45)
        assert action == ActionType.decompose
        assert agent == "/agents/decompose/basic"
        assert "基础拆解" in reason
        assert priority == 1
        assert review is False

    def test_medium_score_recommends_explain(self):
        """Score 60-79 should recommend explain."""
        action, reason, agent, priority, review, alts = _recommend_action_from_score(70)
        assert action == ActionType.explain
        assert agent == "/agents/explain/oral"
        assert "解释" in reason
        assert priority == 2
        assert review is False

    def test_high_score_recommends_next(self):
        """Score >= 80 should recommend next."""
        action, reason, agent, priority, review, alts = _recommend_action_from_score(85)
        assert action == ActionType.next
        assert agent is None
        assert "继续" in reason
        assert priority == 3
        assert review is False

    def test_boundary_60_recommends_explain(self):
        """Score exactly 60 should recommend explain."""
        action, _, _, _, _, _ = _recommend_action_from_score(60)
        assert action == ActionType.explain

    def test_boundary_80_recommends_next(self):
        """Score exactly 80 should recommend next."""
        action, _, _, _, _, _ = _recommend_action_from_score(80)
        assert action == ActionType.next

    def test_boundary_59_recommends_decompose(self):
        """Score exactly 59 should recommend decompose."""
        action, _, _, _, _, _ = _recommend_action_from_score(59)
        assert action == ActionType.decompose

    def test_declining_trend_suggests_review(self):
        """Declining trend should suggest review."""
        history = HistoryContext(
            recent_scores=[55, 50, 45],
            average_score=50.0,
            trend=ActionTrend.declining,
            consecutive_low_count=3,
        )
        _, _, _, priority, review, _ = _recommend_action_from_score(45, history)
        assert review is True
        assert priority == 1

    def test_consecutive_low_scores_adds_alternatives(self):
        """Consecutive low scores should add memory anchor alternative."""
        history = HistoryContext(
            recent_scores=[45, 40, 35, 38, 42],
            average_score=40.0,
            trend=ActionTrend.declining,
            consecutive_low_count=5,
        )
        _, _, _, _, _, alts = _recommend_action_from_score(35, history)
        assert len(alts) >= 1
        assert any("/agents/explain/memory" in alt.agent for alt in alts)

    def test_high_score_ignores_history(self):
        """High score should not suggest review even with history."""
        history = HistoryContext(
            recent_scores=[85, 88, 90],
            average_score=87.67,
            trend=ActionTrend.improving,
            consecutive_low_count=0,
        )
        action, _, _, _, review, _ = _recommend_action_from_score(90, history)
        assert action == ActionType.next
        assert review is False

    def test_high_score_with_declining_trend_preserves_review(self):
        """[Bug fix] High score with declining trend should still suggest review.

        AC-31.3.4 requires considering historical trends even when current score is high.
        Scenario: Student scores 82 but trend is 90→85→60→50→40 (declining).
        """
        history = HistoryContext(
            recent_scores=[82, 60, 50, 40],
            average_score=58.0,
            trend=ActionTrend.declining,
            consecutive_low_count=0,
        )
        action, _, _, _, review, _ = _recommend_action_from_score(82, history)
        assert action == ActionType.next
        assert review is True  # Must preserve declining trend warning

    def test_high_score_with_consecutive_low_preserves_review(self):
        """[Bug fix] High score after 3+ consecutive lows should still suggest review."""
        history = HistoryContext(
            recent_scores=[40, 35, 30],
            average_score=35.0,
            trend=ActionTrend.declining,
            consecutive_low_count=3,
        )
        action, _, _, priority, review, alts = _recommend_action_from_score(85, history)
        assert action == ActionType.next
        assert review is True  # History concern persists
        assert len(alts) >= 1  # Memory anchor alternative should be present


class TestRecommendActionEndpoint:
    """Test recommend_action endpoint (AC-31.3.1, AC-31.3.2)."""

    @pytest.mark.asyncio
    async def test_basic_request_low_score(self):
        """Test basic request with low score."""
        mock_memory = MockMemoryService()
        request = RecommendActionRequest(
            score=45,
            node_id="node-001",
            canvas_name="test.canvas",
            include_history=False,
        )

        response = await recommend_action(request, mock_memory)

        assert isinstance(response, RecommendActionResponse)
        assert response.action == ActionType.decompose
        assert response.agent == "/agents/decompose/basic"
        assert response.reason is not None
        assert len(response.reason) > 0

    @pytest.mark.asyncio
    async def test_basic_request_medium_score(self):
        """Test basic request with medium score."""
        mock_memory = MockMemoryService()
        request = RecommendActionRequest(
            score=72,
            node_id="node-002",
            canvas_name="math.canvas",
            include_history=False,
        )

        response = await recommend_action(request, mock_memory)

        assert response.action == ActionType.explain
        assert response.agent == "/agents/explain/oral"

    @pytest.mark.asyncio
    async def test_basic_request_high_score(self):
        """Test basic request with high score."""
        mock_memory = MockMemoryService()
        request = RecommendActionRequest(
            score=88,
            node_id="node-003",
            canvas_name="physics.canvas",
            include_history=False,
        )

        response = await recommend_action(request, mock_memory)

        assert response.action == ActionType.next
        assert response.agent is None

    @pytest.mark.asyncio
    async def test_with_history_context(self):
        """Test request with history context enabled."""
        mock_memory = MockMemoryService(
            history_items=[
                {"score": 55, "concept": "test"},
                {"score": 50, "concept": "test"},
                {"score": 45, "concept": "test"},
            ]
        )
        request = RecommendActionRequest(
            score=48,
            node_id="node-004",
            canvas_name="test.canvas",
            include_history=True,
            concept="contrapositive",
        )

        response = await recommend_action(request, mock_memory)

        # Should have queried history
        assert mock_memory.call_count == 1
        assert mock_memory.last_params["concept"] == "contrapositive"

        # Response should include history context
        assert response.history_context is not None
        assert len(response.history_context.recent_scores) == 3
        assert response.history_context.average_score == 50.0

    @pytest.mark.asyncio
    async def test_history_query_failure_graceful_degradation(self):
        """Test graceful degradation when history query fails."""
        mock_memory = MockMemoryService(should_raise=True)
        request = RecommendActionRequest(
            score=65,
            node_id="node-005",
            canvas_name="test.canvas",
            include_history=True,
        )

        # Should not raise, should continue without history
        response = await recommend_action(request, mock_memory)

        assert response.action == ActionType.explain
        assert response.history_context is None

    @pytest.mark.asyncio
    async def test_empty_history_no_context(self):
        """Test with empty history returns no context."""
        mock_memory = MockMemoryService(history_items=[])
        request = RecommendActionRequest(
            score=75,
            node_id="node-006",
            canvas_name="test.canvas",
            include_history=True,
        )

        response = await recommend_action(request, mock_memory)

        # Should have queried but no context due to empty results
        assert mock_memory.call_count == 1
        assert response.history_context is None

    @pytest.mark.asyncio
    async def test_history_with_none_scores_filtered(self):
        """Test history items with None scores are filtered."""
        mock_memory = MockMemoryService(
            history_items=[
                {"score": 70, "concept": "test"},
                {"concept": "test"},  # Missing score
                {"score": None, "concept": "test"},  # None score
                {"score": 65, "concept": "test"},
            ]
        )
        request = RecommendActionRequest(
            score=68,
            node_id="node-007",
            canvas_name="test.canvas",
            include_history=True,
        )

        response = await recommend_action(request, mock_memory)

        # Only valid scores should be included
        assert response.history_context is not None
        assert len(response.history_context.recent_scores) == 2
        assert 70 in response.history_context.recent_scores
        assert 65 in response.history_context.recent_scores

    @pytest.mark.asyncio
    async def test_review_suggested_for_declining_trend(self):
        """Test review is suggested for declining trends."""
        mock_memory = MockMemoryService(
            history_items=[
                {"score": 40},
                {"score": 45},
                {"score": 55},
                {"score": 60},
                {"score": 70},
            ]
        )
        request = RecommendActionRequest(
            score=35,
            node_id="node-008",
            canvas_name="test.canvas",
            include_history=True,
        )

        response = await recommend_action(request, mock_memory)

        assert response.review_suggested is True
        assert response.history_context is not None
        assert response.history_context.trend == ActionTrend.declining

    @pytest.mark.asyncio
    async def test_history_with_timestamps_sorted_correctly(self):
        """[Bug fix] History items with timestamps should be sorted most-recent-first.

        Covers SORT-001 branch: when items have 'timestamp' field,
        they must be sorted by timestamp descending before extracting scores.
        """
        mock_memory = MockMemoryService(
            history_items=[
                # Deliberately out of order
                {"score": 60, "timestamp": "2026-02-07T10:00:00Z", "concept": "test"},
                {"score": 90, "timestamp": "2026-02-09T10:00:00Z", "concept": "test"},
                {"score": 70, "timestamp": "2026-02-08T10:00:00Z", "concept": "test"},
                {"score": 50, "timestamp": "2026-02-06T10:00:00Z", "concept": "test"},
            ]
        )
        request = RecommendActionRequest(
            score=75,
            node_id="node-sort-001",
            canvas_name="test.canvas",
            include_history=True,
        )

        response = await recommend_action(request, mock_memory)

        assert response.history_context is not None
        # Scores should be ordered by timestamp descending: 90, 70, 60, 50
        assert response.history_context.recent_scores == [90, 70, 60, 50]
        # Average: (90+70+60+50)/4 = 67.5
        assert response.history_context.average_score == 67.5

    @pytest.mark.asyncio
    async def test_history_without_timestamps_preserves_source_order(self):
        """History items without timestamps should preserve source order."""
        mock_memory = MockMemoryService(
            history_items=[
                {"score": 80, "concept": "test"},
                {"score": 60, "concept": "test"},
                {"score": 70, "concept": "test"},
            ]
        )
        request = RecommendActionRequest(
            score=72,
            node_id="node-sort-002",
            canvas_name="test.canvas",
            include_history=True,
        )

        response = await recommend_action(request, mock_memory)

        assert response.history_context is not None
        # Without timestamps, source order preserved: 80, 60, 70
        assert response.history_context.recent_scores == [80, 60, 70]


class TestRecommendActionModels:
    """Test Pydantic model validation."""

    def test_request_validation_valid(self):
        """Test valid request is accepted."""
        request = RecommendActionRequest(
            score=75,
            node_id="node-123",
            canvas_name="test.canvas",
        )
        assert request.score == 75
        assert request.include_history is True  # default

    def test_request_validation_score_bounds(self):
        """Test score validation bounds."""
        # Valid bounds
        RecommendActionRequest(score=0, node_id="n", canvas_name="c")
        RecommendActionRequest(score=100, node_id="n", canvas_name="c")

        # Invalid bounds should raise
        with pytest.raises(ValueError):
            RecommendActionRequest(score=-1, node_id="n", canvas_name="c")
        with pytest.raises(ValueError):
            RecommendActionRequest(score=101, node_id="n", canvas_name="c")

    def test_response_model_structure(self):
        """Test response model structure."""
        response = RecommendActionResponse(
            action=ActionType.decompose,
            agent="/agents/decompose/basic",
            reason="Test reason",
            priority=1,
            review_suggested=False,
        )
        assert response.action == ActionType.decompose
        assert response.agent == "/agents/decompose/basic"
        assert response.reason == "Test reason"
        assert response.history_context is None
        assert response.alternative_agents == []

    def test_history_context_model(self):
        """Test HistoryContext model."""
        context = HistoryContext(
            recent_scores=[80, 75, 70],
            average_score=75.0,
            trend=ActionTrend.improving,
            consecutive_low_count=0,
        )
        assert len(context.recent_scores) == 3
        assert context.trend == ActionTrend.improving

    def test_alternative_agent_model(self):
        """Test AlternativeAgent model."""
        alt = AlternativeAgent(
            agent="/agents/explain/memory",
            reason="Alternative reason",
        )
        assert alt.agent == "/agents/explain/memory"
        assert alt.reason == "Alternative reason"


# =============================================================================
# [Review fix TEST-001] HTTP Integration Tests
# Verify the endpoint works through the full FastAPI stack
# =============================================================================


class TestRecommendActionHTTP:
    """HTTP integration tests for POST /api/v1/agents/recommend-action.

    These tests use FastAPI TestClient to verify:
    - Route registration and URL correctness
    - Pydantic request/response serialization via HTTP
    - Dependency injection chain (MemoryServiceDep)
    - HTTP error codes (400, 500)
    """

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Set up TestClient with mocked MemoryService dependency."""
        from fastapi.testclient import TestClient
        from app.main import app
        from app.api.v1.endpoints.agents import get_memory_service_for_agents

        mock_service = MockMemoryService()

        async def override_memory_service():
            yield mock_service

        app.dependency_overrides[get_memory_service_for_agents] = override_memory_service
        self.client = TestClient(app)
        self.mock_service = mock_service
        yield
        app.dependency_overrides.pop(get_memory_service_for_agents, None)

    def test_http_low_score_returns_200_decompose(self):
        """HTTP POST with low score returns 200 and decompose action."""
        response = self.client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 45,
                "node_id": "node-http-001",
                "canvas_name": "test.canvas",
                "include_history": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "decompose"
        assert data["agent"] == "/agents/decompose/basic"
        assert "reason" in data
        assert isinstance(data["priority"], int)

    def test_http_high_score_returns_200_next(self):
        """HTTP POST with high score returns 200 and next action."""
        response = self.client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 92,
                "node_id": "node-http-002",
                "canvas_name": "math.canvas",
                "include_history": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "next"
        assert data["agent"] is None

    def test_http_invalid_score_returns_422(self):
        """HTTP POST with out-of-range score returns 422 validation error."""
        response = self.client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 150,
                "node_id": "node-http-003",
                "canvas_name": "test.canvas",
            },
        )
        assert response.status_code == 422

    def test_http_missing_required_field_returns_422(self):
        """HTTP POST missing required field returns 422."""
        response = self.client.post(
            "/api/v1/agents/recommend-action",
            json={"score": 50},  # missing node_id and canvas_name
        )
        assert response.status_code == 422

    def test_http_response_structure_complete(self):
        """HTTP response includes all expected fields."""
        response = self.client.post(
            "/api/v1/agents/recommend-action",
            json={
                "score": 70,
                "node_id": "node-http-004",
                "canvas_name": "physics.canvas",
                "include_history": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Verify all response fields exist
        assert "action" in data
        assert "agent" in data
        assert "reason" in data
        assert "priority" in data
        assert "review_suggested" in data
        assert "alternative_agents" in data
        # Verify types
        assert data["action"] in ["decompose", "explain", "next"]
        assert isinstance(data["review_suggested"], bool)
        assert isinstance(data["alternative_agents"], list)
