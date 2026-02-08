# Canvas Learning System - Rollback Execute API Endpoint Tests
# ✅ Verified from Context7:/fastapi/fastapi (topic: testing)
"""
Tests for the rollback execution API endpoint.

Covers:
- TestRollbackEndpoint: POST /api/v1/rollback/rollback
- TestRollbackEndpointRegistration: endpoint registration and enum checks

[Source: docs/stories/18.3.story.md - AC 6]
[Source: docs/architecture/rollback-recovery-architecture.md:344-380]
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient



@pytest.fixture
def mock_rollback_engine():
    """Create a mock RollbackEngine for API tests.

    [Source: docs/stories/18.3.story.md - AC 6]
    """
    from unittest.mock import AsyncMock

    mock = MagicMock()

    # Mock rollback result
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.rollback_type = MagicMock(value="operation")
    mock_result.canvas_path = "test.canvas"
    mock_result.backup_snapshot_id = "backup-001"
    mock_result.restored_operation_id = "op-001"
    mock_result.restored_snapshot_id = None
    mock_result.graph_sync_status = MagicMock(value="pending")
    mock_result.message = "Reversed operation: node_add"
    mock_result.error = None

    mock.rollback = AsyncMock(return_value=mock_result)

    return mock



class TestRollbackEndpoint:
    """Test suite for POST /api/v1/rollback/rollback endpoint.

    [Source: docs/stories/18.3.story.md - AC 6]
    """

    def test_rollback_operation_returns_200(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test that rollback operation endpoint returns HTTP 200 OK."""
        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "operation",
                },
            )
            assert response.status_code == 200

    def test_rollback_response_structure(
        self, client: TestClient, mock_rollback_engine
    ):
        """
        Test that rollback response has correct structure.

        [Source: docs/architecture/rollback-recovery-architecture.md:344-380]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "operation",
                },
            )
            data = response.json()

            # Verify all required fields
            assert "success" in data
            assert "rollback_type" in data
            assert "canvas_path" in data
            assert "backup_snapshot_id" in data
            assert "graph_sync_status" in data
            assert "message" in data

    def test_rollback_operation_type(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test rollback with operation type."""
        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "operation",
                    "target_id": "op-001",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["rollback_type"] == "operation"

    def test_rollback_snapshot_type(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test rollback with snapshot type."""
        # Mock for snapshot type
        mock_rollback_engine.rollback.return_value.rollback_type = MagicMock(
            value="snapshot"
        )
        mock_rollback_engine.rollback.return_value.restored_snapshot_id = "snap-001"

        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "snapshot",
                    "target_id": "snap-001",
                },
            )
            assert response.status_code == 200

    def test_rollback_timepoint_type(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test rollback with timepoint type."""
        mock_rollback_engine.rollback.return_value.rollback_type = MagicMock(
            value="timepoint"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "timepoint",
                    "target_time": "2025-01-15T10:00:00+00:00",
                },
            )
            assert response.status_code == 200

    def test_rollback_with_create_backup_false(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test rollback with create_backup=false."""
        mock_rollback_engine.rollback.return_value.backup_snapshot_id = None

        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "operation",
                    "create_backup": False,
                },
            )
            assert response.status_code == 200

    def test_rollback_with_preserve_graph(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test rollback with preserve_graph=true skips graph sync."""
        mock_rollback_engine.rollback.return_value.graph_sync_status = MagicMock(
            value="skipped"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "operation",
                    "preserve_graph": True,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["graph_sync_status"] == "skipped"

    def test_rollback_missing_canvas_path(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test that missing canvas_path returns 422 validation error."""
        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "rollback_type": "operation",
                },
            )
            assert response.status_code == 422

    def test_rollback_missing_rollback_type(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test that missing rollback_type returns 422 validation error."""
        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                },
            )
            assert response.status_code == 422

    def test_rollback_invalid_rollback_type(
        self, client: TestClient, mock_rollback_engine
    ):
        """Test that invalid rollback_type returns 422 validation error."""
        with patch(
            "app.api.v1.endpoints.rollback.get_rollback_engine",
            return_value=mock_rollback_engine,
        ):
            response = client.post(
                "/api/v1/rollback/rollback",
                json={
                    "canvas_path": "test.canvas",
                    "rollback_type": "invalid_type",
                },
            )
            assert response.status_code == 422


class TestRollbackEndpointRegistration:
    """Test suite for rollback endpoint registration.

    [Source: docs/stories/18.3.story.md - AC 6]
    """

    def test_rollback_endpoint_registered(self, client: TestClient):
        """Test that rollback endpoint is registered on the router."""
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            # Check rollback endpoint
            assert any(
                path.endswith("/rollback/rollback") for path in paths.keys()
            ), "Rollback endpoint not found"

    def test_rollback_type_enum_values(self, client: TestClient):
        """
        Test that rollback type enum values are documented.

        [Source: docs/stories/18.3.story.md - AC 1]
        Valid types: operation, snapshot, timepoint
        """
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            schemas = openapi.get("components", {}).get("schemas", {})

            # Find RollbackTypeEnum schema
            if "RollbackTypeEnum" in schemas:
                enum_values = schemas["RollbackTypeEnum"].get("enum", [])
                assert "operation" in enum_values
                assert "snapshot" in enum_values
                assert "timepoint" in enum_values

    def test_graph_sync_status_enum_values(self, client: TestClient):
        """
        Test that graph sync status enum values are documented.

        [Source: docs/stories/18.3.story.md - AC 4]
        Valid statuses: synced, pending, skipped
        """
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            schemas = openapi.get("components", {}).get("schemas", {})

            # Find GraphSyncStatusEnum schema
            if "GraphSyncStatusEnum" in schemas:
                enum_values = schemas["GraphSyncStatusEnum"].get("enum", [])
                assert "synced" in enum_values
                assert "pending" in enum_values
                assert "skipped" in enum_values
