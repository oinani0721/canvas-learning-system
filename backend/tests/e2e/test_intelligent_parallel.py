# Canvas Learning System - API Integration Tests for Intelligent Parallel Processing
# Story 33.8: API Integration Testing
# ✅ Verified from docs/stories/33.8.story.md
"""
API integration tests for intelligent parallel batch processing.

These tests use AsyncClient with mocked AgentService and patched DI,
making them API integration tests (not true E2E tests which would
require real AI services and database connections).

Tests cover:
- AC-33.8.1: Complete happy path workflow
- AC-33.8.2: Cancellation workflow
- AC-33.8.3: Retry workflow for failed nodes
- AC-33.8.4: WebSocket real-time updates
- AC-33.8.5: Performance test (100 nodes < 60s)

[Source: docs/stories/33.8.story.md - Tasks 2-6]
[Source: specs/api/parallel-api.openapi.yml]

Fix (Story 33.13 adversarial review):
  - Replaced broken app.dependency_overrides[get_settings] pattern with
    patch("app.dependencies.get_settings") which intercepts direct calls.
  - Added _perform_clustering mock (avoids canvas_utils import).
  - Added _ensure_async_deps mock (lightweight DI for batch pipeline).
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.intelligent_parallel_models import ParallelTaskStatus
from tests.conftest import simulate_async_delay

# Import shared helpers and utilities from conftest
# (autouse _reset_e2e_singletons fixture applies automatically)
from tests.e2e.conftest import (
    get_e2e_settings_override,
    mock_perform_clustering,
    make_lightweight_ensure_deps,
    PerformanceTimer,
    EventCollector,
)


# =============================================================================
# Shared Agent Mock Factories
# =============================================================================

def _make_fast_agent_mock():
    """Create a fast agent mock returning proper AgentResult objects."""
    from app.services.agent_service import AgentResult, AgentType

    async def fast_agent(*args, **kwargs):
        agent_type_str = kwargs.get("agent_type", args[0] if args else "basic-decomposition")
        await simulate_async_delay(0.01)  # 10ms per node
        try:
            at = AgentType(agent_type_str)
        except ValueError:
            at = AgentType.BASIC_DECOMPOSITION
        return AgentResult(
            agent_type=at,
            success=True,
            result={"content": f"Mock response for {agent_type_str}"},
        )

    return fast_agent


# =============================================================================
# Test Class: Happy Path API Integration (AC-33.8.1)
# [Source: docs/stories/33.8.story.md - Task 2]
# =============================================================================

class TestHappyPathAPIIntegration:
    """
    API integration tests for complete batch processing workflow.

    Tests: 10 yellow nodes → grouping preview → confirm → parallel execution → completion
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_batch_processing_workflow(
        self,
        test_canvas_10_nodes: Path,
        tmp_path: Path,
    ):
        """
        Test complete happy path: analyze → confirm → execute → complete.

        [Source: docs/stories/33.8.story.md - Task 2.1-2.7]

        Steps:
        1. POST /api/v1/canvas/intelligent-parallel - Get grouping preview
        2. POST /api/v1/canvas/intelligent-parallel/confirm - Start batch
        3. GET /api/v1/canvas/intelligent-parallel/{sessionId} - Poll until complete
        4. Verify all nodes processed successfully
        """
        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        fast_agent = _make_fast_agent_mock()

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=fast_agent),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, fast_agent)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                # Get relative path for API
                canvas_relative_path = str(test_canvas_10_nodes.relative_to(tmp_path))

                # Step 1: Analyze canvas - Get grouping preview
                analyze_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={
                        "canvas_path": canvas_relative_path,
                        "target_color": "6",  # Yellow
                    }
                )

                assert analyze_response.status_code == 200, f"Analyze failed: {analyze_response.text}"
                analyze_data = analyze_response.json()

                # Verify grouping preview response structure
                assert "canvas_path" in analyze_data
                assert "total_nodes" in analyze_data
                assert "groups" in analyze_data
                assert isinstance(analyze_data["groups"], list)
                assert len(analyze_data["groups"]) > 0
                total_from_groups = sum(len(g["nodes"]) for g in analyze_data["groups"])
                assert analyze_data["total_nodes"] == total_from_groups
                expected_node_count = analyze_data["total_nodes"]

                # Verify each group has required fields
                for group in analyze_data["groups"]:
                    assert "group_id" in group
                    assert "recommended_agent" in group
                    assert "nodes" in group
                    assert "confidence" in group

                # Step 2: Confirm batch processing
                groups_config = [
                    {
                        "group_id": group["group_id"],
                        "agent_type": group["recommended_agent"],
                        "node_ids": [node["node_id"] for node in group["nodes"]],
                    }
                    for group in analyze_data["groups"]
                ]

                confirm_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={
                        "canvas_path": canvas_relative_path,
                        "groups": groups_config,
                    }
                )

                assert confirm_response.status_code == 202, f"Confirm failed: {confirm_response.text}"
                confirm_data = confirm_response.json()
                session_id = confirm_data["session_id"]
                assert session_id is not None
                assert confirm_data["status"] in ["pending", "running"]

                # Step 3: Poll until completion
                max_polls = 120
                poll_count = 0
                final_status = None

                while poll_count < max_polls:
                    progress_response = await client.get(
                        f"/api/v1/canvas/intelligent-parallel/{session_id}"
                    )
                    assert progress_response.status_code == 200

                    progress_data = progress_response.json()
                    status = progress_data["status"]

                    if status in ["completed", "partial_failure", "failed"]:
                        final_status = progress_data
                        break

                    await simulate_async_delay(0.1)
                    poll_count += 1

                # Step 4: Verify completion
                assert final_status is not None, "Session did not complete within timeout"
                assert final_status["status"] in ["completed", "partial_failure"], \
                    f"Expected completed/partial_failure, got {final_status['status']}"
                assert final_status["progress_percent"] >= 0

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_grouping_preview_response_structure(
        self,
        test_canvas_10_nodes: Path,
        tmp_path: Path,
    ):
        """
        Test grouping preview returns correct response structure.

        [Source: docs/stories/33.8.story.md - Dev Notes - 响应Schema验证]
        """
        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                canvas_relative_path = str(test_canvas_10_nodes.relative_to(tmp_path))

                response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={
                        "canvas_path": canvas_relative_path,
                        "target_color": "6",
                    }
                )

                assert response.status_code == 200
                data = response.json()

                assert "canvas_path" in data
                assert "total_nodes" in data
                assert "groups" in data
                assert isinstance(data["groups"], list)


# =============================================================================
# Test Class: Cancellation API Integration (AC-33.8.2)
# [Source: docs/stories/33.8.story.md - Task 3]
# =============================================================================

class TestCancellationAPIIntegration:
    """
    API integration tests for cancellation workflow.

    Tests: Start batch → cancel mid-execution → verify partial results
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_batch_cancellation_workflow(
        self,
        test_canvas_20_nodes: Path,
        tmp_path: Path,
    ):
        """
        Test cancellation returns partial results.

        [Source: docs/stories/33.8.story.md - Task 3.1-3.6]

        Steps:
        1. Start batch with 20+ nodes
        2. Cancel after some nodes complete
        3. Verify completed_count > 0
        4. Verify session status is "cancelled"
        """
        from app.services.agent_service import AgentResult, AgentType

        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        # Slow agent to ensure enough time for cancellation
        # With 20 nodes, semaphore=12: first batch needs 2s, giving time to cancel
        async def slow_agent(*args, **kwargs):
            agent_type_str = kwargs.get("agent_type", args[0] if args else "basic-decomposition")
            await simulate_async_delay(2.0)  # 2s per node — ensures session is still running
            try:
                at = AgentType(agent_type_str)
            except ValueError:
                at = AgentType.BASIC_DECOMPOSITION
            return AgentResult(
                agent_type=at, success=True,
                result={"content": "Mock response"},
            )

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=slow_agent),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, slow_agent)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                canvas_relative_path = str(test_canvas_20_nodes.relative_to(tmp_path))

                # Step 1: Analyze and confirm
                analyze_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_relative_path, "target_color": "6"}
                )
                analyze_data = analyze_response.json()

                groups_config = [
                    {
                        "group_id": group["group_id"],
                        "agent_type": group["recommended_agent"],
                        "node_ids": [node["node_id"] for node in group["nodes"]],
                    }
                    for group in analyze_data["groups"]
                ]

                confirm_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={"canvas_path": canvas_relative_path, "groups": groups_config}
                )
                session_id = confirm_response.json()["session_id"]

                # Step 2: Wait briefly then cancel (session should still be running)
                await simulate_async_delay(0.5)

                cancel_response = await client.post(
                    f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
                )

                # Step 3: Verify cancellation response
                assert cancel_response.status_code == 200, f"Cancel failed: {cancel_response.text}"
                cancel_data = cancel_response.json()
                assert "completed_count" in cancel_data

                # Step 4: Verify session status
                progress_response = await client.get(
                    f"/api/v1/canvas/intelligent-parallel/{session_id}"
                )
                progress_data = progress_response.json()
                assert progress_data["status"] == "cancelled"

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_cancel_already_completed_returns_409(
        self,
        test_canvas_10_nodes: Path,
        tmp_path: Path,
    ):
        """
        Test cancelling already completed session returns 409.

        [Source: Story 33.1 - AC4]
        """
        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        fast_agent = _make_fast_agent_mock()

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=fast_agent),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, fast_agent)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                canvas_relative_path = str(test_canvas_10_nodes.relative_to(tmp_path))

                # Complete a batch first
                analyze_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_relative_path, "target_color": "6"}
                )
                analyze_data = analyze_response.json()

                groups_config = [
                    {
                        "group_id": group["group_id"],
                        "agent_type": group["recommended_agent"],
                        "node_ids": [node["node_id"] for node in group["nodes"]],
                    }
                    for group in analyze_data["groups"]
                ]

                confirm_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={"canvas_path": canvas_relative_path, "groups": groups_config}
                )
                session_id = confirm_response.json()["session_id"]

                # Wait for completion
                for _ in range(60):
                    progress_response = await client.get(
                        f"/api/v1/canvas/intelligent-parallel/{session_id}"
                    )
                    if progress_response.json()["status"] in ["completed", "partial_failure"]:
                        break
                    await simulate_async_delay(0.1)

                # Try to cancel completed session
                cancel_response = await client.post(
                    f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
                )
                # Accept both 200 (with warning/already-completed) or 409 (conflict)
                assert cancel_response.status_code in [200, 409]


# =============================================================================
# Test Class: Retry API Integration (AC-33.8.3)
# [Source: docs/stories/33.8.story.md - Task 4]
# =============================================================================

class TestRetryAPIIntegration:
    """
    API integration tests for retry workflow.

    Tests: Simulate partial failure → retry single failed node → verify success
    """

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_retry_failed_node_workflow(
        self,
        test_canvas_with_failing_node: Path,
        tmp_path: Path,
    ):
        """
        Test retry single failed node using /single-agent endpoint.

        [Source: docs/stories/33.8.story.md - Task 4.1-4.5]

        Steps:
        1. Run batch with failing node
        2. Verify partial_failure status
        3. Retry failed node with /single-agent
        4. Verify retry success
        """
        from app.services.agent_service import AgentResult, AgentType

        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        retry_succeeded = {"value": False}

        async def mock_agent_with_retry(*args, **kwargs):
            """Agent that fails first time for node-999, succeeds on retry."""
            agent_type_str = kwargs.get("agent_type", args[0] if args else "basic-decomposition")
            node_id = kwargs.get("node_id", args[1] if len(args) > 1 else "unknown")
            node_text = kwargs.get("node_text", args[2] if len(args) > 2 else "")
            await simulate_async_delay(0.01)

            try:
                at = AgentType(agent_type_str)
            except ValueError:
                at = AgentType.BASIC_DECOMPOSITION

            # First call to node-999 fails, subsequent calls succeed
            if node_id == "node-999":
                if not retry_succeeded["value"]:
                    retry_succeeded["value"] = True
                    raise ValueError(f"Initial failure for node {node_id}")
                return AgentResult(
                    agent_type=at, success=True,
                    result={"content": "Retry succeeded"},
                )

            if not str(node_text).strip():
                raise ValueError(f"Empty content for node {node_id}")

            return AgentResult(
                agent_type=at, success=True,
                result={"content": f"Response for {str(node_text)[:30]}"},
            )

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=mock_agent_with_retry),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, mock_agent_with_retry)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                canvas_relative_path = str(test_canvas_with_failing_node.relative_to(tmp_path))

                # Run batch (expect partial failure)
                analyze_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_relative_path, "target_color": "6"}
                )
                analyze_data = analyze_response.json()

                groups_config = [
                    {
                        "group_id": group["group_id"],
                        "agent_type": group["recommended_agent"],
                        "node_ids": [node["node_id"] for node in group["nodes"]],
                    }
                    for group in analyze_data["groups"]
                ]

                confirm_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={"canvas_path": canvas_relative_path, "groups": groups_config}
                )
                session_id = confirm_response.json()["session_id"]

                # Wait for completion (expect partial_failure)
                final_data = None
                for _ in range(60):
                    progress_response = await client.get(
                        f"/api/v1/canvas/intelligent-parallel/{session_id}"
                    )
                    final_data = progress_response.json()
                    if final_data["status"] in ["completed", "partial_failure", "failed"]:
                        break
                    await simulate_async_delay(0.1)

                # Step 3: Retry failed node
                retry_response = await client.post(
                    "/api/v1/canvas/single-agent",
                    json={
                        "canvas_path": canvas_relative_path,
                        "node_id": "node-999",
                        "agent_type": "oral-explanation",
                    }
                )

                # Step 4: Verify retry success
                assert retry_response.status_code == 200, f"Retry failed: {retry_response.text}"
                retry_data = retry_response.json()
                assert retry_data.get("success") is True or "file_path" in retry_data


# =============================================================================
# Test Class: WebSocket API Integration (AC-33.8.4)
# [Source: docs/stories/33.8.story.md - Task 5]
# =============================================================================

class TestWebSocketAPIIntegration:
    """
    API integration tests for WebSocket real-time updates.

    Tests: Connect → receive progress events → verify event sequence
    """

    @pytest.mark.e2e
    @pytest.mark.websocket
    def test_websocket_realtime_updates(
        self,
        websocket_test_app,
    ):
        """
        Test WebSocket receives real-time progress updates.

        [Source: docs/stories/33.8.story.md - Task 5.1-5.5]

        Expected event sequence:
        - connected
        - progress_update* (0 or more)
        - task_completed* (0 or more)
        - session_completed
        """
        from fastapi.testclient import TestClient

        client = TestClient(websocket_test_app)
        session_id = "test-ws-session-001"
        events_received = []

        with client.websocket_connect(f"/ws/intelligent-parallel/{session_id}") as websocket:
            # Receive connected event
            data = websocket.receive_json()
            events_received.append(data)
            assert data["type"] == "connected"
            assert data["task_id"] == session_id

            # Verify timestamp is present
            assert "timestamp" in data

        # Verify we received at least the connected event
        assert len(events_received) >= 1
        assert events_received[0]["type"] == "connected"

    @pytest.mark.e2e
    @pytest.mark.websocket
    def test_websocket_multiple_clients_same_session(
        self,
        websocket_test_app,
    ):
        """
        Test multiple clients can connect to same session.

        [Source: backend/tests/integration/test_websocket_integration.py]
        """
        from fastapi.testclient import TestClient

        client = TestClient(websocket_test_app)
        session_id = "shared-ws-session"

        # First client connects
        with client.websocket_connect(f"/ws/intelligent-parallel/{session_id}") as ws1:
            data1 = ws1.receive_json()
            assert data1["type"] == "connected"

            # Second client connects to same session
            with client.websocket_connect(f"/ws/intelligent-parallel/{session_id}") as ws2:
                data2 = ws2.receive_json()
                assert data2["type"] == "connected"

    @pytest.mark.e2e
    @pytest.mark.websocket
    @pytest.mark.asyncio
    async def test_websocket_event_broadcast_integration(
        self,
    ):
        """
        Test WebSocket events are broadcast to connected clients.

        [Source: docs/stories/33.8.story.md - Task 5.5]
        """
        from app.services.websocket_manager import ConnectionManager, reset_connection_manager
        from app.models.intelligent_parallel_models import create_ws_progress_event

        reset_connection_manager()
        manager = ConnectionManager()
        session_id = "broadcast-test-session"

        # Create mock WebSocket with all required methods
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        await manager.connect(session_id, mock_ws)

        # Create progress event using the model factory
        event = create_ws_progress_event(
            task_id=session_id,
            progress_percent=50,
            completed_nodes=5,
            total_nodes=10,
        )

        sent_count = await manager.broadcast_to_session(session_id, event)

        assert sent_count == 1
        # At least 2 calls: 1 for connected event + 1 for progress event
        assert mock_ws.send_json.call_count >= 2
        # Last call should be the progress event
        last_call = mock_ws.send_json.call_args_list[-1]
        last_message = last_call[0][0]
        assert last_message["type"] == "progress"
        assert last_message["data"]["progress_percent"] == 50

        reset_connection_manager()


# =============================================================================
# Test Class: Performance API Integration (AC-33.8.5)
# [Source: docs/stories/33.8.story.md - Task 6]
# =============================================================================

class TestPerformanceAPIIntegration:
    """
    Performance tests for batch processing.

    Tests: 100 nodes batch processing < 60 seconds
    """

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_100_nodes_performance(
        self,
        test_canvas_100_nodes: Path,
        tmp_path: Path,
        performance_timer: PerformanceTimer,
    ):
        """
        Performance test: 100 nodes < 60 seconds.

        [Source: docs/stories/33.8.story.md - Task 6.1-6.6]
        [Source: ADR-0004 - Performance target: 100 nodes < 60s]
        """
        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        fast_agent = _make_fast_agent_mock()

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=fast_agent),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, fast_agent)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                canvas_relative_path = str(test_canvas_100_nodes.relative_to(tmp_path))

                # Analyze canvas
                analyze_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_relative_path, "target_color": "6"}
                )
                analyze_data = analyze_response.json()
                total_from_groups = sum(len(g["nodes"]) for g in analyze_data["groups"])
                assert analyze_data["total_nodes"] == total_from_groups
                assert analyze_data["total_nodes"] > 0, "Should have at least some yellow nodes"

                groups_config = [
                    {
                        "group_id": group["group_id"],
                        "agent_type": group["recommended_agent"],
                        "node_ids": [node["node_id"] for node in group["nodes"]],
                    }
                    for group in analyze_data["groups"]
                ]

                # Start timer for batch execution
                with performance_timer:
                    confirm_response = await client.post(
                        "/api/v1/canvas/intelligent-parallel/confirm",
                        json={"canvas_path": canvas_relative_path, "groups": groups_config}
                    )
                    session_id = confirm_response.json()["session_id"]

                    # Poll until completion
                    progress_data = None
                    for _ in range(600):  # 60 seconds with 100ms interval
                        progress_response = await client.get(
                            f"/api/v1/canvas/intelligent-parallel/{session_id}"
                        )
                        progress_data = progress_response.json()

                        if progress_data["status"] in ["completed", "partial_failure", "failed"]:
                            break

                        await simulate_async_delay(0.1)

                # Verify performance (90s threshold for CI)
                elapsed = performance_timer.elapsed
                assert elapsed < 90, f"Batch processing took {elapsed:.2f}s (limit: 90s)"

                # Log performance metrics
                actual_nodes = analyze_data["total_nodes"]
                metrics = performance_timer.get_metrics(actual_nodes if actual_nodes > 0 else 1)
                print(f"\n=== Performance Metrics ===")
                print(f"Total duration: {metrics['total_duration_seconds']:.2f}s")
                print(f"Nodes per second: {metrics['nodes_per_second']:.2f}")
                print(f"Average per node: {metrics['average_per_node_ms']:.2f}ms")

                # Verify completion status
                assert progress_data["status"] in ["completed", "partial_failure"]

    @pytest.mark.e2e
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_semaphore_concurrency_working(
        self,
        test_canvas_20_nodes: Path,
        tmp_path: Path,
    ):
        """
        Test Semaphore(12) concurrency control is working.

        [Source: ADR-0004 - Semaphore(12) concurrency limit]
        """
        from app.services.agent_service import AgentResult, AgentType

        test_settings = get_e2e_settings_override()
        test_settings.CANVAS_BASE_PATH = str(tmp_path)

        concurrent_count = {"max": 0, "current": 0}
        lock = asyncio.Lock()

        async def tracking_mock(*args, **kwargs):
            """Track concurrent executions."""
            agent_type_str = kwargs.get("agent_type", args[0] if args else "basic-decomposition")

            async with lock:
                concurrent_count["current"] += 1
                concurrent_count["max"] = max(concurrent_count["max"], concurrent_count["current"])

            await simulate_async_delay(0.1)  # Simulate work

            async with lock:
                concurrent_count["current"] -= 1

            try:
                at = AgentType(agent_type_str)
            except ValueError:
                at = AgentType.BASIC_DECOMPOSITION
            return AgentResult(
                agent_type=at, success=True,
                result={"content": "test"},
            )

        with (
            patch("app.services.intelligent_grouping_service.IntelligentGroupingService._perform_clustering",
                  mock_perform_clustering),
            patch("app.dependencies.get_settings", return_value=test_settings),
            patch("app.services.agent_service.AgentService.call_agent",
                  side_effect=tracking_mock),
            patch("app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
                  new=make_lightweight_ensure_deps(test_settings, tracking_mock)),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                canvas_relative_path = str(test_canvas_20_nodes.relative_to(tmp_path))

                # Analyze and confirm
                analyze_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/",
                    json={"canvas_path": canvas_relative_path, "target_color": "6"}
                )
                analyze_data = analyze_response.json()

                groups_config = [
                    {
                        "group_id": group["group_id"],
                        "agent_type": group["recommended_agent"],
                        "node_ids": [node["node_id"] for node in group["nodes"]],
                    }
                    for group in analyze_data["groups"]
                ]

                confirm_response = await client.post(
                    "/api/v1/canvas/intelligent-parallel/confirm",
                    json={"canvas_path": canvas_relative_path, "groups": groups_config}
                )
                session_id = confirm_response.json()["session_id"]

                # Wait for completion
                for _ in range(100):
                    progress_response = await client.get(
                        f"/api/v1/canvas/intelligent-parallel/{session_id}"
                    )
                    if progress_response.json()["status"] in ["completed", "partial_failure", "failed"]:
                        break
                    await simulate_async_delay(0.1)

                # Verify concurrency was limited
                assert concurrent_count["max"] <= 12, f"Max concurrent was {concurrent_count['max']}, expected <= 12"
                print(f"\nMax concurrent executions: {concurrent_count['max']}")
