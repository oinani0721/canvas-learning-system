# Canvas Learning System - Rollback Snapshot API Endpoint Tests
# ✅ Verified from Context7:/fastapi/fastapi (topic: testing)
"""
Tests for the rollback snapshot API endpoints.

Covers:
- TestSnapshotListEndpoint: GET /api/v1/rollback/snapshots/{canvas_path}
- TestCreateSnapshotEndpoint: POST /api/v1/rollback/snapshot
- TestGetSnapshotEndpoint: GET /api/v1/rollback/snapshot/{snapshot_id}
- TestSnapshotEndpointsRegistration: endpoint registration checks

[Source: docs/stories/18.2.story.md - AC 6-7]
[Source: docs/architecture/rollback-recovery-architecture.md:312-326]
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient



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
