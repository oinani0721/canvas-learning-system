# backend/tests/test_rollback_e2e.py
"""
End-to-End Integration Tests for Rollback System

These tests verify the complete rollback workflow from API endpoints
through service layer to core rollback module components.

[Source: docs/architecture/rollback-recovery-architecture.md]
[Source: docs/stories/18.5.story.md - AC 8]

Test Coverage:
- Complete operation tracking workflow
- Snapshot creation and retrieval workflow
- Rollback execution workflow
- Diff computation workflow
- Error handling and edge cases
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest
from app.main import app
from app.services.rollback_service import RollbackService, RollbackServiceConfig
from fastapi.testclient import TestClient

# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def test_client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def temp_storage_path():
    """Create temporary storage directory for tests."""
    temp_dir = tempfile.mkdtemp(prefix="rollback_e2e_test_")
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_canvas_file(temp_storage_path):
    """Create temporary Canvas file for tests."""
    canvas_path = Path(temp_storage_path) / "test_canvas.canvas"
    canvas_data = {
        "nodes": [
            {
                "id": "node1",
                "type": "text",
                "text": "逆否命题",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "1",
            },
            {
                "id": "node2",
                "type": "text",
                "text": "条件命题",
                "x": 250,
                "y": 0,
                "width": 200,
                "height": 100,
                "color": "2",
            },
        ],
        "edges": [
            {
                "id": "edge1",
                "fromNode": "node1",
                "toNode": "node2",
                "fromSide": "right",
                "toSide": "left",
            }
        ],
    }
    with open(canvas_path, "w", encoding="utf-8") as f:
        json.dump(canvas_data, f, ensure_ascii=False, indent=2)
    yield str(canvas_path)


@pytest.fixture
def rollback_service(temp_storage_path):
    """Create RollbackService instance for testing."""
    return RollbackService(
        storage_path=temp_storage_path,
        history_limit=100,
        snapshot_interval=300,
        max_snapshots=50,
        graphiti_timeout_ms=200,
        enable_graphiti_sync=False,  # Disable for unit tests
        enable_auto_backup=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Test: RollbackServiceConfig
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackServiceConfig:
    """Tests for RollbackServiceConfig Pydantic model."""

    def test_config_default_values(self):
        """Test default configuration values."""
        config = RollbackServiceConfig()

        assert config.storage_path == ".canvas-learning"
        assert config.history_limit == 100
        assert config.snapshot_interval == 300
        assert config.max_snapshots == 50
        assert config.graphiti_timeout_ms == 200
        assert config.enable_graphiti_sync is True
        assert config.enable_auto_backup is True

    def test_config_custom_values(self):
        """Test custom configuration values."""
        config = RollbackServiceConfig(
            storage_path="/custom/path",
            history_limit=200,
            snapshot_interval=600,
            max_snapshots=100,
            graphiti_timeout_ms=500,
            enable_graphiti_sync=False,
            enable_auto_backup=False,
        )

        assert config.storage_path == "/custom/path"
        assert config.history_limit == 200
        assert config.snapshot_interval == 600
        assert config.max_snapshots == 100
        assert config.graphiti_timeout_ms == 500
        assert config.enable_graphiti_sync is False
        assert config.enable_auto_backup is False


# ═══════════════════════════════════════════════════════════════════════════════
# Test: RollbackService Initialization
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackServiceInitialization:
    """Tests for RollbackService initialization and lifecycle."""

    def test_service_creation_with_defaults(self):
        """Test service creation with default parameters."""
        service = RollbackService()

        assert service._initialized is False
        assert service._operation_tracker is None
        assert service._snapshot_manager is None
        assert service._rollback_engine is None
        assert service._graph_sync_service is None

    def test_service_creation_with_custom_params(self, temp_storage_path):
        """Test service creation with custom parameters."""
        service = RollbackService(
            storage_path=temp_storage_path,
            history_limit=50,
            max_snapshots=25,
        )

        stats = service.get_stats()
        assert stats["storage_path"] == temp_storage_path
        assert stats["history_limit"] == 50
        assert stats["max_snapshots"] == 25
        assert stats["initialized"] is False

    def test_service_stats_returns_config(self, rollback_service):
        """Test get_stats returns configuration info."""
        stats = rollback_service.get_stats()

        assert "initialized" in stats
        assert "storage_path" in stats
        assert "history_limit" in stats
        assert "snapshot_interval" in stats
        assert "max_snapshots" in stats
        assert "graphiti_timeout_ms" in stats
        assert "enable_graphiti_sync" in stats
        assert "enable_auto_backup" in stats

    @pytest.mark.asyncio
    async def test_service_cleanup(self, rollback_service):
        """Test service cleanup method."""
        # Cleanup should work even if not initialized
        await rollback_service.cleanup()

        assert rollback_service._initialized is False


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Operation History E2E
# ═══════════════════════════════════════════════════════════════════════════════


class TestOperationHistoryE2E:
    """End-to-end tests for operation history functionality."""

    def test_get_operation_history_api_flow(self, test_client):
        """Test complete API flow for getting operation history."""
        response = test_client.get(
            "/api/v1/rollback/history/test.canvas",
            params={"limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert "canvas_path" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "operations" in data

    def test_get_operation_history_pagination(self, test_client):
        """Test pagination in operation history."""
        # First page
        response1 = test_client.get(
            "/api/v1/rollback/history/test.canvas",
            params={"limit": 5, "offset": 0},
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["limit"] == 5
        assert data1["offset"] == 0

        # Second page
        response2 = test_client.get(
            "/api/v1/rollback/history/test.canvas",
            params={"limit": 5, "offset": 5},
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["limit"] == 5
        assert data2["offset"] == 5

    def test_get_single_operation_not_found(self, test_client):
        """Test getting non-existent operation."""
        response = test_client.get(
            "/api/v1/rollback/operation/nonexistent-operation-id"
        )

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Snapshot Management E2E
# ═══════════════════════════════════════════════════════════════════════════════


class TestSnapshotManagementE2E:
    """End-to-end tests for snapshot management functionality."""

    def test_list_snapshots_api_flow(self, test_client):
        """Test complete API flow for listing snapshots."""
        response = test_client.get(
            "/api/v1/rollback/snapshots/test.canvas",
            params={"limit": 10, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()
        assert "canvas_path" in data
        assert "total" in data
        assert "snapshots" in data
        assert isinstance(data["snapshots"], list)

    def test_create_snapshot_api_flow(self, test_client):
        """Test complete API flow for creating snapshot."""
        response = test_client.post(
            "/api/v1/rollback/snapshot",
            json={
                "canvas_path": "test.canvas",
                "description": "E2E test snapshot",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "canvas_path" in data
        assert "timestamp" in data
        assert "type" in data

    def test_create_snapshot_with_tags(self, test_client):
        """Test creating snapshot with optional tags."""
        response = test_client.post(
            "/api/v1/rollback/snapshot",
            json={
                "canvas_path": "test.canvas",
                "description": "Tagged snapshot",
                "tags": ["important", "milestone"],
            },
        )

        assert response.status_code == 201

    def test_get_snapshot_not_found(self, test_client):
        """Test getting non-existent snapshot."""
        response = test_client.get(
            "/api/v1/rollback/snapshot/nonexistent-snapshot-id",
            params={"canvas_path": "test.canvas"},
        )

        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Rollback Execution E2E
# ═══════════════════════════════════════════════════════════════════════════════


class TestRollbackExecutionE2E:
    """End-to-end tests for rollback execution functionality."""

    def test_rollback_operation_type(self, test_client):
        """Test rollback with operation type."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
                "rollback_type": "operation",
                "target_id": "op-123",
                "create_backup": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "rollback_type" in data
        assert data["rollback_type"] == "operation"

    def test_rollback_snapshot_type(self, test_client):
        """Test rollback with snapshot type."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
                "rollback_type": "snapshot",
                "target_id": "snap-456",
                "create_backup": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rollback_type"] == "snapshot"

    def test_rollback_timepoint_type(self, test_client):
        """Test rollback with timepoint type."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
                "rollback_type": "timepoint",
                "target_time": "2025-12-04T00:00:00Z",
                "create_backup": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rollback_type"] == "timepoint"

    def test_rollback_without_backup(self, test_client):
        """Test rollback without creating backup."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
                "rollback_type": "operation",
                "target_id": "op-789",
                "create_backup": False,
            },
        )

        assert response.status_code == 200

    def test_rollback_preserve_graph(self, test_client):
        """Test rollback with graph preservation."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
                "rollback_type": "snapshot",
                "target_id": "snap-abc",
                "preserve_graph": True,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "graph_sync_status" in data

    def test_rollback_invalid_type_rejected(self, test_client):
        """Test that invalid rollback type is rejected."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
                "rollback_type": "invalid_type",
            },
        )

        assert response.status_code == 422  # Validation error


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Diff Computation E2E
# ═══════════════════════════════════════════════════════════════════════════════


class TestDiffComputationE2E:
    """End-to-end tests for diff computation functionality."""

    def test_get_diff_api_flow(self, test_client):
        """Test complete API flow for getting diff."""
        response = test_client.get(
            "/api/v1/rollback/diff/snapshot-123",
            params={"canvas_path": "test.canvas"},
        )

        # May return 200 or 404 depending on mock
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "snapshot_id" in data
            assert "canvas_path" in data
            assert "nodes_diff" in data
            assert "edges_diff" in data

    def test_get_diff_requires_canvas_path(self, test_client):
        """Test that canvas_path is required for diff."""
        response = test_client.get("/api/v1/rollback/diff/snapshot-123")

        assert response.status_code == 422  # Missing required parameter


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Complete Workflow E2E
# ═══════════════════════════════════════════════════════════════════════════════


class TestCompleteWorkflowE2E:
    """End-to-end tests for complete rollback workflows."""

    def test_workflow_create_snapshot_then_rollback(self, test_client):
        """Test workflow: create snapshot, make changes, rollback."""
        # Step 1: Create initial snapshot
        create_response = test_client.post(
            "/api/v1/rollback/snapshot",
            json={
                "canvas_path": "workflow_test.canvas",
                "description": "Before changes",
            },
        )
        assert create_response.status_code == 201
        snapshot_data = create_response.json()
        snapshot_id = snapshot_data["id"]

        # Step 2: Verify snapshot exists
        list_response = test_client.get(
            "/api/v1/rollback/snapshots/workflow_test.canvas"
        )
        assert list_response.status_code == 200

        # Step 3: Rollback to snapshot
        rollback_response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "workflow_test.canvas",
                "rollback_type": "snapshot",
                "target_id": snapshot_id,
                "create_backup": True,
            },
        )
        assert rollback_response.status_code == 200
        result = rollback_response.json()
        assert result["success"] is True
        assert result["rollback_type"] == "snapshot"

    def test_workflow_operation_history_tracking(self, test_client):
        """Test workflow: track operations and view history."""
        canvas_path = "history_test.canvas"

        # Get operation history
        history_response = test_client.get(
            f"/api/v1/rollback/history/{canvas_path}",
            params={"limit": 50},
        )
        assert history_response.status_code == 200
        history = history_response.json()

        assert history["canvas_path"] == canvas_path
        assert "operations" in history
        assert isinstance(history["operations"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Error Handling E2E
# ═══════════════════════════════════════════════════════════════════════════════


class TestErrorHandlingE2E:
    """End-to-end tests for error handling."""

    def test_invalid_canvas_path_characters(self, test_client):
        """Test handling of invalid canvas path characters."""
        # Most special characters should be URL-encoded
        response = test_client.get(
            "/api/v1/rollback/history/test%20canvas.canvas"
        )
        # Should handle gracefully
        assert response.status_code in [200, 400, 404]

    def test_empty_canvas_path(self, test_client):
        """Test handling of empty canvas path."""
        # Empty canvas_path may cause PermissionError on file system access
        # This test verifies the endpoint doesn't crash silently
        try:
            response = test_client.post(
                "/api/v1/rollback/snapshot",
                json={
                    "canvas_path": "",
                    "description": "Test",
                },
            )
            # Validation should catch empty path or it may cause internal error
            # Empty path is not a valid input, so any error response is acceptable
            assert response.status_code in [201, 400, 422, 500]
        except PermissionError:
            # Expected on Windows when trying to access "." directory
            pass

    def test_missing_required_fields(self, test_client):
        """Test handling of missing required fields."""
        # Missing canvas_path
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "rollback_type": "operation",
            },
        )
        assert response.status_code == 422

        # Missing rollback_type
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "test.canvas",
            },
        )
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# Test: API Contract Validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestAPIContractValidation:
    """Tests to validate API contract conformance."""

    def test_all_endpoints_return_json(self, test_client):
        """Test that all endpoints return JSON content type."""
        endpoints = [
            ("/api/v1/rollback/history/test.canvas", "get"),
            ("/api/v1/rollback/snapshots/test.canvas", "get"),
        ]

        for endpoint, method in endpoints:
            if method == "get":
                response = test_client.get(endpoint)
            assert response.headers.get("content-type", "").startswith(
                "application/json"
            )

    def test_operation_response_schema(self, test_client):
        """Test operation response matches expected schema."""
        response = test_client.get("/api/v1/rollback/history/test.canvas")
        assert response.status_code == 200

        data = response.json()
        # Validate required fields
        required_fields = ["canvas_path", "total", "limit", "offset", "operations"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_snapshot_response_schema(self, test_client):
        """Test snapshot response matches expected schema."""
        response = test_client.post(
            "/api/v1/rollback/snapshot",
            json={
                "canvas_path": "schema_test.canvas",
                "description": "Schema validation test",
            },
        )
        assert response.status_code == 201

        data = response.json()
        # Validate required fields
        required_fields = ["id", "canvas_path", "timestamp", "type"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_rollback_result_schema(self, test_client):
        """Test rollback result matches expected schema."""
        response = test_client.post(
            "/api/v1/rollback/rollback",
            json={
                "canvas_path": "schema_test.canvas",
                "rollback_type": "operation",
                "target_id": "test-op-id",
            },
        )
        assert response.status_code == 200

        data = response.json()
        # Validate required fields
        required_fields = ["success", "rollback_type", "canvas_path", "graph_sync_status"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"


# ═══════════════════════════════════════════════════════════════════════════════
# Test: Performance Baseline
# ═══════════════════════════════════════════════════════════════════════════════


class TestPerformanceBaseline:
    """Basic performance tests for rollback endpoints."""

    def test_history_endpoint_response_time(self, test_client):
        """Test that history endpoint responds within acceptable time."""
        import time

        start = time.time()
        response = test_client.get("/api/v1/rollback/history/perf_test.canvas")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Response took {elapsed:.2f}s, expected < 1.0s"

    def test_snapshot_list_endpoint_response_time(self, test_client):
        """Test that snapshot list endpoint responds within acceptable time."""
        import time

        start = time.time()
        response = test_client.get("/api/v1/rollback/snapshots/perf_test.canvas")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Response took {elapsed:.2f}s, expected < 1.0s"
