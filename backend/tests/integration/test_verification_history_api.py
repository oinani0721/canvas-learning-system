"""
Integration Tests for Story 31.4: Verification History API

Tests for:
- AC-31.4.3: GET /verification/history/{concept} endpoint
- AC-31.4.4: Response format with question, answer, score, timestamp
- Task 7.4: Test endpoint functionality
- Task 7.5: Test pagination functionality

[Source: docs/stories/31.4.story.md#Testing]
"""

import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.models import (
    QuestionType,
    VerificationHistoryItem,
    VerificationHistoryResponse,
)


@pytest.fixture
def client():
    """Create test client for verification history API tests"""
    return TestClient(app)


class TestVerificationHistoryEndpoint:
    """Test GET /verification/history/{concept} endpoint (AC-31.4.3, Task 7.4)"""

    def test_endpoint_exists(self, client):
        """
        AC-31.4.3: Verify endpoint exists and returns valid response.

        [Source: docs/stories/31.4.story.md#Task-4]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/逆否命题")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_returns_empty_list_when_no_history(self, client):
        """
        Test endpoint returns empty list when no history exists.

        [Source: docs/stories/31.4.story.md#Task-4.1]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/新概念")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert data["concept"] == "新概念"
            assert data["total_count"] == 0
            assert data["items"] == []

    def test_returns_history_items(self, client):
        """
        AC-31.4.4: Test history data includes question, answer, score, timestamp.

        [Source: docs/stories/31.4.story.md#Task-4.2]
        """
        mock_history = [
            {
                "question_id": "vq_001",
                "question_text": "请解释什么是逆否命题？",
                "question_type": "standard",
                "user_answer": "逆否命题是...",
                "score": 85,
                "canvas_name": "离散数学",
                "asked_at": datetime.now().isoformat()
            },
            {
                "question_id": "vq_002",
                "question_text": "逆否命题在日常生活中有哪些应用？",
                "question_type": "application",
                "user_answer": None,
                "score": None,
                "canvas_name": "离散数学",
                "asked_at": (datetime.now() - timedelta(days=1)).isoformat()
            }
        ]

        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=mock_history)
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/逆否命题")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert data["concept"] == "逆否命题"
            assert data["total_count"] == 2
            assert len(data["items"]) == 2

            # Verify first item has all required fields
            item = data["items"][0]
            assert "question_id" in item
            assert "question_text" in item
            assert "question_type" in item
            assert "asked_at" in item

    def test_filters_by_canvas_name(self, client):
        """
        Test endpoint filters by canvas_name query parameter.

        [Source: docs/stories/31.4.story.md#Task-4.3]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"canvas_name": "离散数学"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            # Verify the client was called with canvas_name filter
            mock_client.search_verification_questions.assert_called()
            call_kwargs = mock_client.search_verification_questions.call_args.kwargs
            assert call_kwargs.get("canvas_name") == "离散数学"

    def test_handles_graphiti_unavailable(self, client):
        """
        ADR-009: Graceful degradation when Graphiti is unavailable.

        [Source: docs/stories/31.4.story.md#Dev-Notes - ADR-009]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/v1/review/verification/history/逆否命题")

            # Graceful degradation: should return 200 with empty list
            assert response.status_code == 200, f"Graceful degradation should return 200, got {response.status_code}"
            data = response.json()
            assert data["total_count"] == 0


class TestVerificationHistoryPagination:
    """Test pagination functionality (Task 7.5)"""

    def test_default_pagination(self, client):
        """
        Test default pagination values (limit=20, offset=0).

        [Source: docs/stories/31.4.story.md#Task-4.4]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/逆否命题")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "pagination" in data, "Response should include pagination info"
            assert data["pagination"]["limit"] == 20
            assert data["pagination"]["offset"] == 0

    def test_custom_limit(self, client):
        """
        Test custom limit parameter.

        Note: Endpoint fetches limit+1 to check has_more.

        [Source: docs/stories/31.4.story.md#Task-4.5]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"limit": 5}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            mock_client.search_verification_questions.assert_called()
            call_kwargs = mock_client.search_verification_questions.call_args.kwargs
            # Endpoint fetches limit+1 to detect has_more
            assert call_kwargs.get("limit") == 6

    def test_custom_offset(self, client):
        """
        Test custom offset parameter for pagination.

        Note: Verifies offset is included in response pagination info.
        The actual offset handling may vary by implementation.

        [Source: docs/stories/31.4.story.md#Task-4.6]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"offset": 10}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "pagination" in data, "Response should include pagination info"
            assert data["pagination"]["offset"] == 10

    def test_has_more_indicator(self, client):
        """
        Test has_more field indicates more records exist.

        [Source: docs/stories/31.4.story.md#Task-4.7]
        """
        # Create mock history with more items than limit
        mock_history = [
            {
                "question_id": f"vq_{i:03d}",
                "question_text": f"Question {i}",
                "question_type": "standard",
                "user_answer": None,
                "score": None,
                "canvas_name": "离散数学",
                "asked_at": datetime.now().isoformat()
            }
            for i in range(25)  # More than default limit of 20
        ]

        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            # Endpoint fetches limit+1 to detect has_more, so return 21 items
            mock_client.search_verification_questions = AsyncMock(
                return_value=mock_history[:21]
            )
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"limit": 20}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert "pagination" in data, "Response should include pagination info"
            assert data["pagination"]["has_more"] is True

    @pytest.mark.parametrize("params,description", [
        ({"limit": 200}, "invalid limit (too high, max 100)"),
        ({"offset": -1}, "invalid offset (negative)"),
    ])
    def test_invalid_pagination_params(self, client, params, description):
        """
        Test pagination parameter validation rejects invalid values.

        [Source: specs/data/verification-history-response.schema.json#L30-40]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params=params
            )

            assert response.status_code in [400, 422], (
                f"Expected 400/422 for {description}, got {response.status_code}"
            )


class TestVerificationHistoryResponseFormat:
    """Test response format validation (AC-31.4.4)"""

    def test_response_matches_schema(self, client):
        """
        AC-31.4.4: Response matches verification-history-response.schema.json.

        [Source: specs/data/verification-history-response.schema.json]
        """
        mock_history = [
            {
                "question_id": "vq_001",
                "question_text": "请解释什么是逆否命题？",
                "question_type": "standard",
                "user_answer": "逆否命题是将原命题的条件和结论同时取否并交换位置",
                "score": 90,
                "canvas_name": "离散数学",
                "asked_at": "2025-01-15T10:30:00Z"
            }
        ]

        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=mock_history)
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/逆否命题")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()

            # Verify top-level fields
            assert "concept" in data
            assert "total_count" in data
            assert "items" in data

            # Verify item fields match schema
            assert len(data["items"]) > 0, "Expected non-empty items list"
            item = data["items"][0]
            assert "question_id" in item
            assert "question_text" in item
            assert "question_type" in item
            assert "canvas_name" in item
            assert "asked_at" in item

    @pytest.mark.parametrize("q_type", [
        "standard", "application", "comparison", "counterexample", "synthesis"
    ])
    def test_question_type_enum_values(self, client, q_type):
        """
        Test question_type field uses valid enum values.

        [Source: specs/data/verification-history-response.schema.json#L61-64]
        """
        mock_history = [
            {
                "question_id": "vq_test",
                "question_text": "Test question",
                "question_type": q_type,
                "user_answer": None,
                "score": None,
                "canvas_name": "测试",
                "asked_at": datetime.now().isoformat()
            }
        ]

        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=mock_history)
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/测试概念")

            assert response.status_code == 200, f"Expected 200 for type {q_type}, got {response.status_code}: {response.text}"
            data = response.json()
            assert len(data["items"]) > 0, f"Expected non-empty items for type {q_type}"
            assert data["items"][0]["question_type"] == q_type

    def test_score_range_validation(self, client):
        """
        Test score field is within valid range (0-100).

        [Source: specs/data/verification-history-response.schema.json#L75-80]
        """
        mock_history = [
            {
                "question_id": "vq_001",
                "question_text": "Test question",
                "question_type": "standard",
                "user_answer": "Answer",
                "score": 75,
                "canvas_name": "测试",
                "asked_at": datetime.now().isoformat()
            }
        ]

        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=mock_history)
            mock_get.return_value = mock_client

            response = client.get("/api/v1/review/verification/history/测试概念")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            data = response.json()
            assert len(data["items"]) > 0, "Expected non-empty items list"
            assert data["items"][0].get("score") is not None, "Expected score to be present"
            score = data["items"][0]["score"]
            assert 0 <= score <= 100


class TestMultiSubjectIsolation:
    """Test multi-subject isolation via group_id (ADR-0003)"""

    def test_group_id_filter(self, client):
        """
        ADR-0003: Test group_id parameter for multi-subject isolation.

        [Source: docs/stories/31.4.story.md#Dev-Notes - ADR-0003 约束3]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"group_id": "math_subject"}
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
            mock_client.search_verification_questions.assert_called()
            call_kwargs = mock_client.search_verification_questions.call_args.kwargs
            assert call_kwargs.get("group_id") == "math_subject"

    def test_different_groups_isolated(self, client):
        """
        ADR-0003: Verify different groups return different results.

        [Source: docs/stories/31.4.story.md#Dev-Notes - ADR-0003]
        """
        math_history = [
            {
                "question_id": "vq_math_001",
                "question_text": "数学问题",
                "question_type": "standard",
                "user_answer": None,
                "score": None,
                "canvas_name": "离散数学",
                "asked_at": datetime.now().isoformat()
            }
        ]

        physics_history = [
            {
                "question_id": "vq_physics_001",
                "question_text": "物理问题",
                "question_type": "standard",
                "user_answer": None,
                "score": None,
                "canvas_name": "量子物理",
                "asked_at": datetime.now().isoformat()
            }
        ]

        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()

            # Configure different responses based on group_id
            def mock_search(**kwargs):
                if kwargs.get("group_id") == "math_subject":
                    return math_history
                elif kwargs.get("group_id") == "physics_subject":
                    return physics_history
                return []

            mock_client.search_verification_questions = AsyncMock(side_effect=mock_search)
            mock_get.return_value = mock_client

            # Query math subject
            response_math = client.get(
                "/api/v1/review/verification/history/概念",
                params={"group_id": "math_subject"}
            )

            # Query physics subject
            response_physics = client.get(
                "/api/v1/review/verification/history/概念",
                params={"group_id": "physics_subject"}
            )

            assert response_math.status_code == 200, f"Math query: expected 200, got {response_math.status_code}"
            assert response_physics.status_code == 200, f"Physics query: expected 200, got {response_physics.status_code}"
            math_data = response_math.json()
            physics_data = response_physics.json()

            # Results should be different based on group_id
            assert len(math_data["items"]) > 0, "Expected non-empty math items"
            assert len(physics_data["items"]) > 0, "Expected non-empty physics items"
            assert math_data["items"][0]["question_id"] != physics_data["items"][0]["question_id"]
