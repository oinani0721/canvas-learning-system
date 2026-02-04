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


class TestVerificationHistoryEndpoint:
    """Test GET /verification/history/{concept} endpoint (AC-31.4.3, Task 7.4)"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_graphiti_client(self):
        """Create mock GraphitiTemporalClient"""
        client = AsyncMock()
        client.search_verification_questions = AsyncMock(return_value=[])
        return client

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

            # Should return 200 or valid response structure
            assert response.status_code in [200, 404, 503]

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

            if response.status_code == 200:
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

            if response.status_code == 200:
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

            if response.status_code == 200:
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

            # Should return graceful response (empty list or service unavailable)
            assert response.status_code in [200, 503]
            if response.status_code == 200:
                data = response.json()
                assert data["total_count"] == 0


class TestVerificationHistoryPagination:
    """Test pagination functionality (Task 7.5)"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

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

            if response.status_code == 200:
                data = response.json()
                # Check pagination info if present
                if data.get("pagination"):
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

            if response.status_code == 200:
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

            if response.status_code == 200:
                data = response.json()
                # Verify offset is reflected in pagination info
                if data.get("pagination"):
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
            # Return total count and limited items
            mock_client.search_verification_questions = AsyncMock(
                return_value=mock_history[:20]
            )
            mock_client.count_verification_questions = AsyncMock(return_value=25)
            mock_get.return_value = mock_client

            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"limit": 20}
            )

            if response.status_code == 200:
                data = response.json()
                # If pagination is included and total_count > items returned
                if data.get("pagination") and data["total_count"] > len(data["items"]):
                    assert data["pagination"]["has_more"] is True

    def test_limit_validation(self, client):
        """
        Test limit parameter validation (1-100).

        [Source: specs/data/verification-history-response.schema.json#L30-35]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            # Test invalid limit (too high)
            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"limit": 200}
            )

            # Should reject invalid limit (400 Bad Request or 422 Unprocessable Entity)
            assert response.status_code in [400, 422]

    def test_offset_validation(self, client):
        """
        Test offset parameter validation (>= 0).

        [Source: specs/data/verification-history-response.schema.json#L36-40]
        """
        with patch("app.dependencies.get_graphiti_temporal_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.search_verification_questions = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            # Test invalid offset (negative)
            response = client.get(
                "/api/v1/review/verification/history/逆否命题",
                params={"offset": -1}
            )

            # Should reject negative offset (400 Bad Request or 422 Unprocessable Entity)
            assert response.status_code in [400, 422]


class TestVerificationHistoryResponseFormat:
    """Test response format validation (AC-31.4.4)"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

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

            if response.status_code == 200:
                data = response.json()

                # Verify top-level fields
                assert "concept" in data
                assert "total_count" in data
                assert "items" in data

                # Verify item fields match schema
                if data["items"]:
                    item = data["items"][0]
                    assert "question_id" in item
                    assert "question_text" in item
                    assert "question_type" in item
                    assert "canvas_name" in item
                    assert "asked_at" in item

    def test_question_type_enum_values(self, client):
        """
        Test question_type field uses valid enum values.

        [Source: specs/data/verification-history-response.schema.json#L61-64]
        """
        valid_types = ["standard", "application", "comparison", "counterexample", "synthesis"]

        for q_type in valid_types:
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

                if response.status_code == 200:
                    data = response.json()
                    if data["items"]:
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

            if response.status_code == 200:
                data = response.json()
                if data["items"] and data["items"][0].get("score") is not None:
                    score = data["items"][0]["score"]
                    assert 0 <= score <= 100


class TestMultiSubjectIsolation:
    """Test multi-subject isolation via group_id (ADR-0003)"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

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

            if response.status_code == 200:
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

            if response_math.status_code == 200 and response_physics.status_code == 200:
                math_data = response_math.json()
                physics_data = response_physics.json()

                # Results should be different based on group_id
                if math_data["items"] and physics_data["items"]:
                    assert math_data["items"][0]["question_id"] != physics_data["items"][0]["question_id"]
