"""Tests for the rollback diff API endpoint.

Covers: TestDiffEndpoint, TestDiffEndpointRegistration, TestAllRollbackEndpointsRegistered.

[Source: docs/stories/18.5.story.md - AC 1-2]
[Source: docs/architecture/rollback-recovery-architecture.md:382-400]
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient



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
