"""
Review Endpoint Tests for Canvas Learning System API

Tests for Ebbinghaus review system endpoints (3 endpoints total).

Story 15.6: API文档和测试框架
✅ Verified from Context7:/websites/fastapi_tiangolo (topic: TestClient testing)
"""

import pytest
from datetime import date, timedelta


@pytest.mark.api
class TestGetReviewSchedule:
    """Tests for GET /api/v1/review/schedule endpoint."""

    def test_get_review_schedule_success(self, client, api_v1_prefix):
        """
        Test getting review schedule returns items.

        AC: GET /api/v1/review/schedule returns 200 with ReviewScheduleResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.get(f"{api_v1_prefix}/review/schedule")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total_count" in data
        assert isinstance(data["items"], list)
        assert data["total_count"] >= 0

    def test_get_review_schedule_with_days_param(self, client, api_v1_prefix):
        """
        Test getting review schedule with days parameter.

        AC: Query parameter 'days' filters results.
        """
        response = client.get(f"{api_v1_prefix}/review/schedule?days=3")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        # All items should have due_date within 3 days
        today = date.today()
        max_date = today + timedelta(days=3)

        for item in data["items"]:
            assert "due_date" in item
            due_date = date.fromisoformat(item["due_date"])
            assert due_date <= max_date

    def test_get_review_schedule_item_structure(self, client, api_v1_prefix):
        """
        Test review schedule items have correct structure.

        AC: Each item has required fields.
        """
        response = client.get(f"{api_v1_prefix}/review/schedule")

        assert response.status_code == 200
        data = response.json()

        if data["items"]:
            item = data["items"][0]
            assert "canvas_name" in item
            assert "node_id" in item
            assert "concept" in item
            assert "due_date" in item
            assert "interval_days" in item


@pytest.mark.api
class TestGenerateVerificationCanvas:
    """Tests for POST /api/v1/review/generate endpoint."""

    def test_generate_review_success(self, client, api_v1_prefix, valid_generate_review_request):
        """
        Test generating verification canvas returns 201.

        AC: POST /api/v1/review/generate returns 201 with GenerateReviewResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        response = client.post(
            f"{api_v1_prefix}/review/generate",
            json=valid_generate_review_request()
        )

        assert response.status_code == 201
        data = response.json()

        assert "verification_canvas_name" in data
        assert "node_count" in data
        assert data["node_count"] >= 0

    def test_generate_review_with_node_ids(self, client, api_v1_prefix, valid_generate_review_request):
        """
        Test generating verification canvas with specific nodes.

        AC: Optional node_ids parameter specifies nodes to include.
        """
        request_data = valid_generate_review_request(
            node_ids=["a1b2c3d4", "e5f6g7h8"]
        )
        response = client.post(
            f"{api_v1_prefix}/review/generate",
            json=request_data
        )

        assert response.status_code == 201
        data = response.json()

        assert data["node_count"] == len(request_data["node_ids"])

    def test_generate_review_canvas_not_found(self, client, api_v1_prefix):
        """
        Test generating from non-existent canvas returns 404.

        AC: Returns 404 when source canvas doesn't exist.
        """
        response = client.post(
            f"{api_v1_prefix}/review/generate",
            json={"source_canvas": "nonexistent-canvas"}
        )

        assert response.status_code == 404

    def test_generate_review_validation_error(self, client, api_v1_prefix):
        """
        Test generating with missing fields returns 422.

        AC: Returns 422 validation error for invalid data.
        """
        response = client.post(
            f"{api_v1_prefix}/review/generate",
            json={}
        )

        assert response.status_code == 422


@pytest.mark.api
class TestRecordReviewResult:
    """Tests for PUT /api/v1/review/record endpoint."""

    def test_record_review_high_score(self, client, api_v1_prefix, valid_record_review_request):
        """
        Test recording high score extends interval.

        AC: PUT /api/v1/review/record returns 200 with RecordReviewResponse.
        Source: specs/api/fastapi-backend-api.openapi.yml
        """
        request_data = valid_record_review_request(score=35.0)  # High score
        response = client.put(
            f"{api_v1_prefix}/review/record",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert "next_review_date" in data
        assert "new_interval" in data
        # High score should give longer interval
        assert data["new_interval"] == 30

    def test_record_review_medium_score(self, client, api_v1_prefix, valid_record_review_request):
        """
        Test recording medium score gives standard interval.

        AC: Score 24-31 gives 7-day interval.
        """
        request_data = valid_record_review_request(score=28.0)
        response = client.put(
            f"{api_v1_prefix}/review/record",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["new_interval"] == 7

    def test_record_review_low_score(self, client, api_v1_prefix, valid_record_review_request):
        """
        Test recording low score gives short interval.

        AC: Score <24 gives 1-day interval.
        """
        request_data = valid_record_review_request(score=18.0)
        response = client.put(
            f"{api_v1_prefix}/review/record",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["new_interval"] == 1

    def test_record_review_validation_error(self, client, api_v1_prefix):
        """
        Test recording with invalid score returns 422.

        AC: Returns 422 for score outside 0-40 range.
        """
        response = client.put(
            f"{api_v1_prefix}/review/record",
            json={
                "canvas_name": "test",
                "node_id": "node1",
                "score": 50.0  # Invalid: > 40
            }
        )

        assert response.status_code == 422

    def test_record_review_missing_fields(self, client, api_v1_prefix):
        """
        Test recording with missing required fields returns 422.

        AC: Returns 422 validation error for missing fields.
        """
        response = client.put(
            f"{api_v1_prefix}/review/record",
            json={"canvas_name": "test"}  # Missing node_id and score
        )

        assert response.status_code == 422
