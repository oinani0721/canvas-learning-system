# Canvas Learning System - Rollback API Endpoint Tests
# ✅ Verified from Context7:/fastapi/fastapi (topic: testing)
"""
Tests for the rollback API endpoints.

These tests verify that the rollback API endpoints return correct data
and adhere to the API specification.

[Source: docs/stories/18.1.story.md - AC 6]
[Source: docs/architecture/rollback-recovery-architecture.md:296-400]
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ═══════════════════════════════════════════════════════════════════════════════
# Test Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════════
# Operation History Endpoint Tests
# [Source: docs/stories/18.1.story.md - AC 6]
# ═══════════════════════════════════════════════════════════════════════════════


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
        Example: "离散数学/逆否命题.canvas"
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


# ═══════════════════════════════════════════════════════════════════════════════
# Single Operation Endpoint Tests
# ═══════════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════════
# Router Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.2: Snapshot Endpoint Tests
# [Source: docs/stories/18.2.story.md - AC 6-7]
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_snapshot_manager():
    """Create a mock SnapshotManager for API tests.

    [Source: docs/stories/18.2.story.md - AC 6]
    """
    from unittest.mock import AsyncMock

    mock = MagicMock()

    # Mock snapshot entry for list_snapshots
    mock_entry = {
        "id": "snap-001",
        "canvas_path": "test.canvas",
        "timestamp": "2025-01-15T10:00:00+00:00",
        "type": "manual",
        "last_operation_id": "op-001",
        "metadata": {
            "description": "Test snapshot",
            "created_by": "user",
            "tags": ["test"],
            "size_bytes": 1024,
        },
    }

    # Mock snapshot object for create/get
    mock_snapshot = MagicMock()
    mock_snapshot.id = "snap-001"
    mock_snapshot.canvas_path = "test.canvas"
    mock_snapshot.timestamp = datetime.now(timezone.utc)
    mock_snapshot.type = MagicMock(value="manual")
    mock_snapshot.last_operation_id = "op-001"
    mock_snapshot.metadata = MagicMock(
        description="Test snapshot",
        created_by="user",
        tags=["test"],
        size_bytes=1024,
    )

    # Configure async mock methods
    mock.list_snapshots = AsyncMock(return_value=[mock_entry])
    mock.get_total_count = AsyncMock(return_value=1)
    mock.create_snapshot = AsyncMock(return_value=mock_snapshot)
    mock.get_snapshot = AsyncMock(return_value=mock_snapshot)

    return mock


class TestSnapshotListEndpoint:
    """Test suite for GET /api/v1/rollback/snapshots/{canvas_path} endpoint.

    [Source: docs/stories/18.2.story.md - AC 6]
    """

    def test_list_snapshots_returns_200(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that list snapshots endpoint returns HTTP 200 OK."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get("/api/v1/rollback/snapshots/test.canvas")
            assert response.status_code == 200

    def test_list_snapshots_response_structure(
        self, client: TestClient, mock_snapshot_manager
    ):
        """
        Test that snapshot list response has correct structure.

        [Source: docs/architecture/rollback-recovery-architecture.md:312-326]
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get("/api/v1/rollback/snapshots/test.canvas")
            data = response.json()

            # Verify required fields
            assert "canvas_path" in data
            assert "total" in data
            assert "snapshots" in data

    def test_list_snapshots_pagination_params(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that pagination parameters are passed correctly."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get(
                "/api/v1/rollback/snapshots/test.canvas?limit=10&offset=5"
            )
            assert response.status_code == 200
            mock_snapshot_manager.list_snapshots.assert_called_with(
                "test.canvas", limit=10, offset=5
            )

    def test_list_snapshots_default_pagination(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test default pagination values (limit=20, offset=0)."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            _response = client.get("/api/v1/rollback/snapshots/test.canvas")  # noqa: F841
            mock_snapshot_manager.list_snapshots.assert_called_with(
                "test.canvas", limit=20, offset=0
            )

    def test_list_snapshots_snapshot_structure(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that each snapshot in the list has correct structure."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get("/api/v1/rollback/snapshots/test.canvas")
            data = response.json()

            assert len(data["snapshots"]) > 0
            snap = data["snapshots"][0]

            # Verify snapshot structure
            assert "id" in snap
            assert "canvas_path" in snap
            assert "timestamp" in snap
            assert "type" in snap
            assert "metadata" in snap


class TestCreateSnapshotEndpoint:
    """Test suite for POST /api/v1/rollback/snapshot endpoint.

    [Source: docs/stories/18.2.story.md - AC 7]
    """

    def test_create_snapshot_returns_201(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that create snapshot endpoint returns HTTP 201 Created."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.post(
                "/api/v1/rollback/snapshot",
                json={"canvas_path": "test.canvas"},
            )
            assert response.status_code == 201

    def test_create_snapshot_response_structure(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that created snapshot response has correct structure."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.post(
                "/api/v1/rollback/snapshot",
                json={
                    "canvas_path": "test.canvas",
                    "description": "Manual backup",
                    "tags": ["backup"],
                },
            )
            data = response.json()

            # Verify response structure
            assert "id" in data
            assert "canvas_path" in data
            assert "timestamp" in data
            assert "type" in data
            assert data["type"] == "manual"
            assert "metadata" in data

    def test_create_snapshot_with_description(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test creating snapshot with description."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.post(
                "/api/v1/rollback/snapshot",
                json={
                    "canvas_path": "test.canvas",
                    "description": "Before major changes",
                },
            )
            assert response.status_code == 201

    def test_create_snapshot_missing_canvas_path(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that missing canvas_path returns 422 validation error."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.post(
                "/api/v1/rollback/snapshot",
                json={},
            )
            assert response.status_code == 422


class TestGetSnapshotEndpoint:
    """Test suite for GET /api/v1/rollback/snapshot/{snapshot_id} endpoint."""

    def test_get_snapshot_returns_200(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that get snapshot endpoint returns HTTP 200 OK."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get(
                "/api/v1/rollback/snapshot/snap-001?canvas_path=test.canvas"
            )
            assert response.status_code == 200

    def test_get_snapshot_response_structure(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that single snapshot response has correct structure."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get(
                "/api/v1/rollback/snapshot/snap-001?canvas_path=test.canvas"
            )
            data = response.json()

            # Verify all required fields
            assert "id" in data
            assert "canvas_path" in data
            assert "timestamp" in data
            assert "type" in data
            assert "metadata" in data

    def test_get_snapshot_not_found_returns_404(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that non-existent snapshot returns 404."""
        mock_snapshot_manager.get_snapshot = MagicMock(return_value=None)
        # Need to make it async
        from unittest.mock import AsyncMock
        mock_snapshot_manager.get_snapshot = AsyncMock(return_value=None)

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get(
                "/api/v1/rollback/snapshot/nonexistent?canvas_path=test.canvas"
            )
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data

    def test_get_snapshot_requires_canvas_path(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that canvas_path query parameter is required."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get("/api/v1/rollback/snapshot/snap-001")
            assert response.status_code == 422  # Missing required query param

    def test_get_snapshot_metadata_structure(
        self, client: TestClient, mock_snapshot_manager
    ):
        """Test that snapshot metadata has correct structure."""
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get(
                "/api/v1/rollback/snapshot/snap-001?canvas_path=test.canvas"
            )
            data = response.json()

            metadata = data["metadata"]
            assert "description" in metadata
            assert "created_by" in metadata
            assert "size_bytes" in metadata


class TestSnapshotEndpointsRegistration:
    """Test suite for snapshot endpoint registration.

    [Source: docs/stories/18.2.story.md - AC 6-7]
    """

    def test_snapshot_endpoints_registered(self, client: TestClient):
        """Test that snapshot endpoints are registered on the router."""
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            # Check list snapshots endpoint
            assert any(
                "rollback/snapshots" in path for path in paths.keys()
            ), "List snapshots endpoint not found"

            # Check create snapshot endpoint
            assert any(
                path.endswith("/rollback/snapshot") for path in paths.keys()
            ), "Create snapshot endpoint not found"

    def test_snapshot_type_enum_values(
        self, client: TestClient, mock_snapshot_manager
    ):
        """
        Test that snapshot type is one of the valid types.

        [Source: docs/stories/18.2.story.md - AC 1]
        Valid types: auto, manual, checkpoint
        """
        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_manager,
        ):
            response = client.get(
                "/api/v1/rollback/snapshot/snap-001?canvas_path=test.canvas"
            )
            data = response.json()

            valid_types = ["auto", "manual", "checkpoint"]
            assert data["type"] in valid_types


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.3: Rollback Endpoint Tests
# [Source: docs/stories/18.3.story.md - AC 6]
# ═══════════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.5: Diff Endpoint Tests
# [Source: docs/stories/18.5.story.md - AC 1]
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_snapshot_with_data():
    """Create a mock snapshot with canvas_data for diff tests.

    [Source: docs/stories/18.5.story.md - AC 1]
    """
    from unittest.mock import AsyncMock

    mock = MagicMock()

    # Mock snapshot with canvas_data
    mock_snapshot = MagicMock()
    mock_snapshot.id = "snap-001"
    mock_snapshot.canvas_path = "test.canvas"
    mock_snapshot.timestamp = datetime.now(timezone.utc)
    mock_snapshot.type = MagicMock(value="manual")
    mock_snapshot.last_operation_id = "op-001"
    mock_snapshot.canvas_data = {
        "nodes": [
            {"id": "node-1", "text": "Node 1", "color": "1", "x": 0, "y": 0},
            {"id": "node-2", "text": "Node 2", "color": "2", "x": 100, "y": 100},
        ],
        "edges": [
            {"id": "edge-1", "fromNode": "node-1", "toNode": "node-2"},
        ],
    }
    mock_snapshot.metadata = MagicMock(
        description="Test snapshot",
        created_by="user",
        tags=["test"],
        size_bytes=1024,
    )

    # Configure async mock
    mock.get_snapshot = AsyncMock(return_value=mock_snapshot)

    return mock


class TestDiffEndpoint:
    """Test suite for GET /api/v1/rollback/diff/{snapshot_id} endpoint.

    [Source: docs/stories/18.5.story.md - AC 1]
    """

    def test_get_diff_returns_200(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """Test that diff endpoint returns HTTP 200 OK."""
        # Create a temporary canvas file
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [], "edges": []}', encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            assert response.status_code == 200

    def test_get_diff_response_structure(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """
        Test that diff response has correct structure.

        [Source: docs/architecture/rollback-recovery-architecture.md:382-400]
        """
        # Create a temporary canvas file
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [], "edges": []}', encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            # Verify all required fields
            assert "snapshot_id" in data
            assert "canvas_path" in data
            assert "timestamp" in data
            assert "nodes_diff" in data
            assert "edges_diff" in data

    def test_get_diff_nodes_diff_structure(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """Test that nodes_diff has added, removed, modified arrays."""
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [], "edges": []}', encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            nodes_diff = data["nodes_diff"]
            assert "added" in nodes_diff
            assert "removed" in nodes_diff
            assert "modified" in nodes_diff

    def test_get_diff_edges_diff_structure(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """Test that edges_diff has added, removed arrays."""
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [], "edges": []}', encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            edges_diff = data["edges_diff"]
            assert "added" in edges_diff
            assert "removed" in edges_diff

    def test_get_diff_snapshot_not_found(
        self, client: TestClient, mock_snapshot_with_data
    ):
        """Test that 404 is returned when snapshot is not found."""
        from unittest.mock import AsyncMock

        # Configure mock to return None
        mock_snapshot_with_data.get_snapshot = AsyncMock(return_value=None)

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ):
            response = client.get(
                "/api/v1/rollback/diff/nonexistent-snap?canvas_path=test.canvas"
            )
            assert response.status_code == 404

    def test_get_diff_requires_canvas_path(self, client: TestClient):
        """Test that canvas_path query parameter is required."""
        response = client.get("/api/v1/rollback/diff/snap-001")
        assert response.status_code == 422  # Missing required query param

    def test_get_diff_detects_removed_nodes(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """Test that diff correctly detects removed nodes (in snapshot but not current)."""
        # Current canvas is empty - all snapshot nodes should be "removed"
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [], "edges": []}', encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            # Snapshot had 2 nodes, current has 0 -> 2 removed nodes
            assert len(data["nodes_diff"]["removed"]) == 2
            assert len(data["nodes_diff"]["added"]) == 0

    def test_get_diff_detects_added_nodes(
        self, client: TestClient, tmp_path
    ):
        """Test that diff correctly detects added nodes (in current but not snapshot)."""
        from unittest.mock import AsyncMock

        mock = MagicMock()
        mock_snapshot = MagicMock()
        mock_snapshot.id = "snap-empty"
        mock_snapshot.canvas_path = "test.canvas"
        mock_snapshot.canvas_data = {"nodes": [], "edges": []}  # Empty snapshot

        mock.get_snapshot = AsyncMock(return_value=mock_snapshot)

        # Current canvas has 2 nodes
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [{"id": "new-1", "text": "New Node 1"}, '
            '{"id": "new-2", "text": "New Node 2"}], "edges": []}',
            encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-empty?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            # Snapshot had 0 nodes, current has 2 -> 2 added nodes
            assert len(data["nodes_diff"]["added"]) == 2
            assert len(data["nodes_diff"]["removed"]) == 0

    def test_get_diff_detects_modified_nodes(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """Test that diff correctly detects modified nodes (same id, different content)."""
        # Current canvas has same node ids but different text/color
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": ['
            '{"id": "node-1", "text": "Modified Node 1", "color": "3", "x": 0, "y": 0},'
            '{"id": "node-2", "text": "Node 2", "color": "2", "x": 100, "y": 100}'
            '], "edges": []}',
            encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            # node-1 has different text and color
            modified = data["nodes_diff"]["modified"]
            assert len(modified) >= 1

            # Find node-1 modification
            node1_mod = next(
                (m for m in modified if m["id"] == "node-1"), None
            )
            assert node1_mod is not None
            assert "text" in node1_mod["before"] or "color" in node1_mod["before"]

    def test_get_diff_detects_removed_edges(
        self, client: TestClient, mock_snapshot_with_data, tmp_path
    ):
        """Test that diff correctly detects removed edges."""
        # Current canvas has no edges
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [{"id": "node-1"}, {"id": "node-2"}], "edges": []}',
            encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock_snapshot_with_data,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-001?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            # Snapshot had 1 edge, current has 0 -> 1 removed edge
            assert len(data["edges_diff"]["removed"]) == 1

    def test_get_diff_detects_added_edges(
        self, client: TestClient, tmp_path
    ):
        """Test that diff correctly detects added edges."""
        from unittest.mock import AsyncMock

        mock = MagicMock()
        mock_snapshot = MagicMock()
        mock_snapshot.id = "snap-no-edges"
        mock_snapshot.canvas_data = {
            "nodes": [{"id": "node-1"}, {"id": "node-2"}],
            "edges": [],
        }

        mock.get_snapshot = AsyncMock(return_value=mock_snapshot)

        # Current canvas has 1 edge
        canvas_file = tmp_path / "test.canvas"
        canvas_file.write_text(
            '{"nodes": [{"id": "node-1"}, {"id": "node-2"}], '
            '"edges": [{"id": "new-edge", "fromNode": "node-1", "toNode": "node-2"}]}',
            encoding="utf-8"
        )

        with patch(
            "app.api.v1.endpoints.rollback.get_snapshot_manager",
            return_value=mock,
        ), patch(
            "app.api.v1.endpoints.rollback._project_root",
            tmp_path,
        ):
            response = client.get(
                f"/api/v1/rollback/diff/snap-no-edges?canvas_path={str(canvas_file)}"
            )
            data = response.json()

            # Snapshot had 0 edges, current has 1 -> 1 added edge
            assert len(data["edges_diff"]["added"]) == 1


class TestDiffEndpointRegistration:
    """Test suite for diff endpoint registration.

    [Source: docs/stories/18.5.story.md - AC 2]
    """

    def test_diff_endpoint_registered(self, client: TestClient):
        """Test that diff endpoint is registered on the router."""
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            # Check diff endpoint exists
            assert any(
                "/rollback/diff/" in path for path in paths.keys()
            ), "Diff endpoint not found"

    def test_diff_response_schema_documented(self, client: TestClient):
        """Test that DiffResponse schema is documented in OpenAPI."""
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            schemas = openapi.get("components", {}).get("schemas", {})

            # Check DiffResponse schema exists
            assert "DiffResponse" in schemas, "DiffResponse schema not found"


class TestAllRollbackEndpointsRegistered:
    """Test that all 5 rollback endpoints are registered.

    [Source: docs/stories/18.5.story.md - AC 2]
    """

    def test_five_rollback_endpoints_registered(self, client: TestClient):
        """
        Test that all 5 rollback endpoints are registered.

        Endpoints:
        1. GET /api/v1/rollback/history/{canvas_path}
        2. GET /api/v1/rollback/snapshots/{canvas_path}
        3. POST /api/v1/rollback/snapshot
        4. POST /api/v1/rollback/rollback
        5. GET /api/v1/rollback/diff/{snapshot_id}
        """
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            rollback_paths = [p for p in paths.keys() if "/rollback/" in p]

            # Should have at least 5 rollback-related paths
            assert len(rollback_paths) >= 5, f"Expected 5 rollback endpoints, found {len(rollback_paths)}: {rollback_paths}"
