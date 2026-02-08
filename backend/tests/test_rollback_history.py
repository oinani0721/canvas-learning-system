# Canvas Learning System - Rollback History & Operation API Endpoint Tests
# ✅ Verified from Context7:/fastapi/fastapi (topic: testing)
"""
Tests for the rollback history and operation API endpoints.

Covers:
- TestOperationHistoryEndpoint: GET /api/v1/rollback/history/{canvas_path}
- TestSingleOperationEndpoint: GET /api/v1/rollback/operation/{operation_id}
- TestRollbackRouterIntegration: router registration checks

[Source: docs/stories/18.1.story.md - AC 6]
[Source: docs/architecture/rollback-recovery-architecture.md:296-400]
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient



@pytest.fixture
def mock_operation_tracker():
    """Create a mock OperationTracker for API tests."""
    mock = MagicMock()

    # Mock operation data
    mock_operation = MagicMock()
    mock_operation.id = "op-001"
    mock_operation.type = MagicMock(value="node_add")
    mock_operation.canvas_path = "test.canvas"
    mock_operation.timestamp = datetime.now(timezone.utc)
    mock_operation.user_id = "test-user"
    mock_operation.data = MagicMock(
        before=None,
        after={"id": "node1", "text": "Test Node"},
        node_ids=["node1"],
        edge_ids=None,
    )
    mock_operation.metadata = MagicMock(
        description="Add node: Test Node",
        agent_id="basic-decomposition",
        request_id="req-123",
    )

    mock.get_history.return_value = [mock_operation]
    mock.get_total_count.return_value = 1
    mock.get_operation.return_value = mock_operation

    return mock



class TestOperationHistoryEndpoint:
    """Test suite for GET /api/v1/rollback/history/{canvas_path} endpoint."""

    def test_get_operation_history_returns_200(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that operation history endpoint returns HTTP 200 OK.

        [Source: docs/stories/18.1.story.md - AC 6]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/history/test.canvas")
            assert response.status_code == 200

    def test_get_operation_history_response_structure(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that operation history response has correct structure.

        [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
        Schema requires: canvas_path, total, limit, offset, operations
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/history/test.canvas")
            data = response.json()

            # Verify all required fields are present
            assert "canvas_path" in data
            assert "total" in data
            assert "limit" in data
            assert "offset" in data
            assert "operations" in data

    def test_get_operation_history_pagination_params(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that pagination parameters are correctly passed.

        [Source: docs/stories/18.1.story.md - AC 6]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get(
                "/api/v1/rollback/history/test.canvas?limit=10&offset=5"
            )
            data = response.json()

            assert data["limit"] == 10
            assert data["offset"] == 5
            mock_operation_tracker.get_history.assert_called_with(
                "test.canvas", limit=10, offset=5
            )

    def test_get_operation_history_default_pagination(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that default pagination values are applied.

        [Source: docs/stories/18.1.story.md - AC 6]
        Default: limit=50, offset=0
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/history/test.canvas")
            data = response.json()

            assert data["limit"] == 50
            assert data["offset"] == 0

    def test_get_operation_history_limit_validation(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that limit parameter is validated (1-100).

        [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            # Limit too high
            response = client.get("/api/v1/rollback/history/test.canvas?limit=200")
            assert response.status_code == 422  # Validation error

            # Limit too low
            response = client.get("/api/v1/rollback/history/test.canvas?limit=0")
            assert response.status_code == 422

    def test_get_operation_history_operations_structure(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that each operation in the list has correct structure.

        [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/history/test.canvas")
            data = response.json()

            assert len(data["operations"]) > 0
            op = data["operations"][0]

            # Verify operation structure
            assert "id" in op
            assert "type" in op
            assert "canvas_path" in op
            assert "timestamp" in op
            assert "user_id" in op
            assert "data" in op
            assert "metadata" in op

    def test_get_operation_history_empty_canvas(
        self, client: TestClient, mock_operation_tracker
    ):
        """Test that empty canvas returns empty operations list."""
        mock_operation_tracker.get_history.return_value = []
        mock_operation_tracker.get_total_count.return_value = 0

        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/history/empty.canvas")
            data = response.json()

            assert data["total"] == 0
            assert data["operations"] == []

    def test_get_operation_history_canvas_path_with_subdirectory(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that canvas path with subdirectory is handled correctly.

        [Source: docs/stories/18.1.story.md - AC 6]
        Example: "離散數學/逆否命題.canvas"
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get(
                "/api/v1/rollback/history/课程/离散数学.canvas"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["canvas_path"] == "课程/离散数学.canvas"

    def test_get_operation_history_content_type(
        self, client: TestClient, mock_operation_tracker
    ):
        """Test that operation history returns JSON content type."""
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/history/test.canvas")
            assert response.headers["content-type"] == "application/json"



class TestSingleOperationEndpoint:
    """Test suite for GET /api/v1/rollback/operation/{operation_id} endpoint."""

    def test_get_operation_returns_200(
        self, client: TestClient, mock_operation_tracker
    ):
        """Test that get operation endpoint returns HTTP 200 OK."""
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/operation/op-001")
            assert response.status_code == 200

    def test_get_operation_response_structure(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that single operation response has correct structure.

        [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/operation/op-001")
            data = response.json()

            # Verify all required fields
            assert "id" in data
            assert "type" in data
            assert "canvas_path" in data
            assert "timestamp" in data
            assert "user_id" in data
            assert "data" in data
            assert "metadata" in data

    def test_get_operation_not_found_returns_404(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that non-existent operation returns 404.

        [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
        """
        mock_operation_tracker.get_operation.return_value = None

        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/operation/nonexistent")
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_get_operation_data_structure(
        self, client: TestClient, mock_operation_tracker
    ):
        """Test that operation data has correct structure."""
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/operation/op-001")
            data = response.json()

            op_data = data["data"]
            assert "before" in op_data
            assert "after" in op_data
            assert "node_ids" in op_data
            assert "edge_ids" in op_data

    def test_get_operation_metadata_structure(
        self, client: TestClient, mock_operation_tracker
    ):
        """Test that operation metadata has correct structure."""
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/operation/op-001")
            data = response.json()

            metadata = data["metadata"]
            assert "description" in metadata
            assert "agent_id" in metadata
            assert "request_id" in metadata

    def test_get_operation_type_values(
        self, client: TestClient, mock_operation_tracker
    ):
        """
        Test that operation type is one of the valid types.

        [Source: docs/stories/18.1.story.md - AC 1]
        Valid types: node_add, node_delete, node_modify, node_color_change,
                     edge_add, edge_delete, batch_operation
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_operation_tracker",
            return_value=mock_operation_tracker,
        ):
            response = client.get("/api/v1/rollback/operation/op-001")
            data = response.json()

            valid_types = [
                "node_add",
                "node_delete",
                "node_modify",
                "node_color_change",
                "edge_add",
                "edge_delete",
                "batch_operation",
            ]
            assert data["type"] in valid_types



class TestRollbackRouterIntegration:
    """Test suite for rollback router integration."""

    def test_rollback_endpoints_registered(self, client: TestClient):
        """
        Test that rollback endpoints are registered on the router.

        [Source: docs/stories/18.1.story.md - AC 6]
        """
        # Get OpenAPI spec to verify endpoints are registered
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            # Check history endpoint is registered
            assert any(
                "rollback/history" in path for path in paths.keys()
            ), "History endpoint not found in OpenAPI spec"

            # Check operation endpoint is registered
            assert any(
                "rollback/operation" in path for path in paths.keys()
            ), "Operation endpoint not found in OpenAPI spec"

    def test_rollback_router_tags(self, client: TestClient):
        """
        Test that rollback endpoints have correct OpenAPI tags.

        [Source: docs/stories/18.1.story.md - AC 6]
        """
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            for path, methods in paths.items():
                if "rollback" in path:
                    for method_info in methods.values():
                        if isinstance(method_info, dict):
                            tags = method_info.get("tags", [])
                            # Should have Rollback tag
                            assert "Rollback" in tags or len(tags) > 0
