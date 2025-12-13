# Canvas Learning System - Memory API Integration Tests
# Story 22.4: 学习历史存储与查询API (AC-22.4.6)
# ✅ Verified from docs/stories/22.4.story.md#测试要求
"""
Integration tests for Memory API endpoints.

Test Coverage:
- POST /api/v1/memory/episodes - 记录学习事件 (AC-22.4.1)
- GET /api/v1/memory/episodes - 查询学习历史 (AC-22.4.2, AC-22.4.5)
- GET /api/v1/memory/concepts/{id}/history - 查询概念历史 (AC-22.4.3)
- GET /api/v1/memory/review-suggestions - 获取复习建议 (AC-22.4.4)

[Source: docs/stories/22.4.story.md#测试要求]
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import structlog

logger = structlog.get_logger(__name__)


# =============================================================================
# Test Fixtures
# ✅ Verified from ADR-008:294-336 - httpx AsyncClient pattern
# =============================================================================


@pytest.fixture
def mock_memory_service():
    """Mock MemoryService for API testing."""
    service = MagicMock()

    async def mock_initialize():
        return True

    async def mock_cleanup():
        pass

    async def mock_record_learning_event(**kwargs):
        return "episode-test123456"

    async def mock_get_learning_history(**kwargs):
        return {
            "items": [
                {
                    "episode_id": "episode-001",
                    "user_id": kwargs.get("user_id", "user-001"),
                    "canvas_path": "数学/离散数学.canvas",
                    "node_id": "node-001",
                    "concept": "逆否命题",
                    "agent_type": "scoring-agent",
                    "score": 85,
                    "duration_seconds": 300,
                    "timestamp": datetime.now().isoformat()
                }
            ],
            "total": 1,
            "page": kwargs.get("page", 1),
            "page_size": kwargs.get("page_size", 50),
            "pages": 1
        }

    async def mock_get_concept_history(**kwargs):
        return {
            "concept_id": kwargs.get("concept_id", "concept-001"),
            "timeline": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "score": 85,
                    "user_id": "user-001",
                    "concept": "逆否命题",
                    "review_count": 3
                }
            ],
            "score_trend": {
                "first": 75,
                "last": 85,
                "average": 80.0,
                "improvement": 10
            },
            "total_reviews": 1
        }

    async def mock_get_review_suggestions(**kwargs):
        return [
            {
                "concept": "逆否命题",
                "concept_id": "concept-001",
                "last_score": 75,
                "review_count": 2,
                "due_date": datetime.now().isoformat(),
                "priority": "high"
            }
        ]

    service.initialize = AsyncMock(side_effect=mock_initialize)
    service.cleanup = AsyncMock(side_effect=mock_cleanup)
    service.record_learning_event = AsyncMock(side_effect=mock_record_learning_event)
    service.get_learning_history = AsyncMock(side_effect=mock_get_learning_history)
    service.get_concept_history = AsyncMock(side_effect=mock_get_concept_history)
    service.get_review_suggestions = AsyncMock(side_effect=mock_get_review_suggestions)

    return service


@pytest.fixture
def test_client(mock_memory_service):
    """Create test client with mocked dependencies."""
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    # Create test app with memory router
    from app.api.v1.endpoints.memory import memory_router, get_memory_service

    app = FastAPI()
    app.include_router(memory_router, prefix="/api/v1/memory")

    # Override dependency
    async def override_get_memory_service():
        yield mock_memory_service

    app.dependency_overrides[get_memory_service] = override_get_memory_service

    return TestClient(app)


# =============================================================================
# Test: POST /episodes (AC-22.4.1)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


class TestPostEpisodes:
    """Tests for POST /api/v1/memory/episodes endpoint."""

    def test_create_episode_success(self, test_client, mock_memory_service):
        """Test successful episode creation."""
        # Arrange
        payload = {
            "user_id": "user-001",
            "canvas_path": "数学/离散数学.canvas",
            "node_id": "node-abc123",
            "concept": "逆否命题",
            "agent_type": "scoring-agent",
            "score": 85,
            "duration_seconds": 300
        }

        # Act
        response = test_client.post("/api/v1/memory/episodes", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "episode_id" in data
        assert data["status"] == "created"
        mock_memory_service.record_learning_event.assert_called_once()

    def test_create_episode_minimal_payload(self, test_client, mock_memory_service):
        """Test episode creation with minimal required fields."""
        # Arrange
        payload = {
            "user_id": "user-001",
            "canvas_path": "数学/离散数学.canvas",
            "node_id": "node-abc123",
            "concept": "命题逻辑",
            "agent_type": "basic-decomposition"
        }

        # Act
        response = test_client.post("/api/v1/memory/episodes", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"

    def test_create_episode_missing_required_field(self, test_client):
        """Test episode creation fails with missing required fields."""
        # Arrange - Missing user_id
        payload = {
            "canvas_path": "数学/离散数学.canvas",
            "node_id": "node-abc123",
            "concept": "逆否命题",
            "agent_type": "scoring-agent"
        }

        # Act
        response = test_client.post("/api/v1/memory/episodes", json=payload)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_episode_invalid_score(self, test_client):
        """Test episode creation fails with invalid score (>100)."""
        # Arrange
        payload = {
            "user_id": "user-001",
            "canvas_path": "数学/离散数学.canvas",
            "node_id": "node-abc123",
            "concept": "逆否命题",
            "agent_type": "scoring-agent",
            "score": 150  # Invalid: > 100
        }

        # Act
        response = test_client.post("/api/v1/memory/episodes", json=payload)

        # Assert
        assert response.status_code == 422


# =============================================================================
# Test: GET /episodes (AC-22.4.2, AC-22.4.5)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


class TestGetEpisodes:
    """Tests for GET /api/v1/memory/episodes endpoint."""

    def test_get_episodes_success(self, test_client, mock_memory_service):
        """Test successful episode retrieval."""
        # Act
        response = test_client.get("/api/v1/memory/episodes?user_id=user-001")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

    def test_get_episodes_with_pagination(self, test_client, mock_memory_service):
        """Test episode retrieval with pagination parameters (AC-22.4.5)."""
        # Act
        response = test_client.get(
            "/api/v1/memory/episodes?user_id=user-001&page=2&page_size=10"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10

    def test_get_episodes_with_concept_filter(self, test_client, mock_memory_service):
        """Test episode retrieval with concept filter."""
        # Act
        response = test_client.get(
            "/api/v1/memory/episodes?user_id=user-001&concept=逆否命题"
        )

        # Assert
        assert response.status_code == 200
        mock_memory_service.get_learning_history.assert_called_once()
        call_kwargs = mock_memory_service.get_learning_history.call_args.kwargs
        assert call_kwargs["concept"] == "逆否命题"

    def test_get_episodes_with_date_filter(self, test_client, mock_memory_service):
        """Test episode retrieval with date filters."""
        # Act
        response = test_client.get(
            "/api/v1/memory/episodes?user_id=user-001"
            "&start_date=2025-01-01T00:00:00"
            "&end_date=2025-12-31T23:59:59"
        )

        # Assert
        assert response.status_code == 200

    def test_get_episodes_missing_user_id(self, test_client):
        """Test episode retrieval fails without user_id."""
        # Act
        response = test_client.get("/api/v1/memory/episodes")

        # Assert
        assert response.status_code == 422

    def test_get_episodes_invalid_page_size(self, test_client):
        """Test episode retrieval fails with invalid page_size (>100)."""
        # Act
        response = test_client.get(
            "/api/v1/memory/episodes?user_id=user-001&page_size=200"
        )

        # Assert
        assert response.status_code == 422


# =============================================================================
# Test: GET /concepts/{id}/history (AC-22.4.3)
# ✅ Verified from AC-22.4.3
# =============================================================================


class TestGetConceptHistory:
    """Tests for GET /api/v1/memory/concepts/{id}/history endpoint."""

    def test_get_concept_history_success(self, test_client, mock_memory_service):
        """Test successful concept history retrieval."""
        # Act
        response = test_client.get("/api/v1/memory/concepts/concept-001/history")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "concept_id" in data
        assert "timeline" in data
        assert "score_trend" in data
        assert "total_reviews" in data

    def test_get_concept_history_with_user_filter(self, test_client, mock_memory_service):
        """Test concept history with user_id filter."""
        # Act
        response = test_client.get(
            "/api/v1/memory/concepts/concept-001/history?user_id=user-001"
        )

        # Assert
        assert response.status_code == 200
        mock_memory_service.get_concept_history.assert_called_once()
        call_kwargs = mock_memory_service.get_concept_history.call_args.kwargs
        assert call_kwargs["user_id"] == "user-001"

    def test_get_concept_history_with_limit(self, test_client, mock_memory_service):
        """Test concept history with limit parameter."""
        # Act
        response = test_client.get(
            "/api/v1/memory/concepts/concept-001/history?limit=20"
        )

        # Assert
        assert response.status_code == 200
        call_kwargs = mock_memory_service.get_concept_history.call_args.kwargs
        assert call_kwargs["limit"] == 20


# =============================================================================
# Test: GET /review-suggestions (AC-22.4.4)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


class TestGetReviewSuggestions:
    """Tests for GET /api/v1/memory/review-suggestions endpoint."""

    def test_get_review_suggestions_success(self, test_client, mock_memory_service):
        """Test successful review suggestions retrieval."""
        # Act
        response = test_client.get(
            "/api/v1/memory/review-suggestions?user_id=user-001"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["concept"] == "逆否命题"
        assert data[0]["priority"] == "high"

    def test_get_review_suggestions_with_limit(self, test_client, mock_memory_service):
        """Test review suggestions with custom limit."""
        # Act
        response = test_client.get(
            "/api/v1/memory/review-suggestions?user_id=user-001&limit=5"
        )

        # Assert
        assert response.status_code == 200
        call_kwargs = mock_memory_service.get_review_suggestions.call_args.kwargs
        assert call_kwargs["limit"] == 5

    def test_get_review_suggestions_missing_user_id(self, test_client):
        """Test review suggestions fails without user_id."""
        # Act
        response = test_client.get("/api/v1/memory/review-suggestions")

        # Assert
        assert response.status_code == 422

    def test_get_review_suggestions_invalid_limit(self, test_client):
        """Test review suggestions fails with invalid limit (>50)."""
        # Act
        response = test_client.get(
            "/api/v1/memory/review-suggestions?user_id=user-001&limit=100"
        )

        # Assert
        assert response.status_code == 422


# =============================================================================
# Test: Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for API error handling."""

    def test_service_error_returns_500(self, test_client, mock_memory_service):
        """Test that service errors return 500 status."""
        # Arrange
        mock_memory_service.record_learning_event = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        payload = {
            "user_id": "user-001",
            "canvas_path": "test.canvas",
            "node_id": "node-001",
            "concept": "Test",
            "agent_type": "test-agent"
        }

        # Act
        response = test_client.post("/api/v1/memory/episodes", json=payload)

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


# =============================================================================
# Test: Response Format Validation
# =============================================================================


class TestResponseFormat:
    """Tests for API response format compliance."""

    def test_episode_response_format(self, test_client, mock_memory_service):
        """Test episode response matches schema."""
        # Arrange
        payload = {
            "user_id": "user-001",
            "canvas_path": "test.canvas",
            "node_id": "node-001",
            "concept": "Test",
            "agent_type": "test-agent"
        }

        # Act
        response = test_client.post("/api/v1/memory/episodes", json=payload)

        # Assert
        data = response.json()
        assert isinstance(data.get("episode_id"), str)
        assert isinstance(data.get("status"), str)

    def test_history_response_format(self, test_client, mock_memory_service):
        """Test history response matches schema."""
        # Act
        response = test_client.get("/api/v1/memory/episodes?user_id=user-001")

        # Assert
        data = response.json()
        assert isinstance(data.get("items"), list)
        assert isinstance(data.get("total"), int)
        assert isinstance(data.get("page"), int)
        assert isinstance(data.get("page_size"), int)
        assert isinstance(data.get("pages"), int)

    def test_review_suggestion_response_format(self, test_client, mock_memory_service):
        """Test review suggestion response matches schema."""
        # Act
        response = test_client.get(
            "/api/v1/memory/review-suggestions?user_id=user-001"
        )

        # Assert
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            suggestion = data[0]
            assert "concept" in suggestion
            assert "concept_id" in suggestion
            assert "priority" in suggestion
            assert suggestion["priority"] in ["high", "medium", "low"]
