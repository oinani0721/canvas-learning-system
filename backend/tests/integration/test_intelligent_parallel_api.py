# Canvas Learning System - Intelligent Parallel API Integration Tests
# Story 33.1: Backend REST Endpoints
# Source: Story 33.1 Task 6 - Integration Tests
"""
Integration tests for intelligent parallel batch processing API.

Test Workflows:
- Full workflow: analyze → confirm → progress → complete
- Cancellation workflow
- Retry workflow after partial failure

[Source: docs/stories/33.1.story.md - Task 6]
[Source: specs/api/parallel-api.openapi.yml]
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.intelligent_parallel_models import ParallelTaskStatus


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def async_client():
    """Provide async client for integration tests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# =============================================================================
# Test: Full Workflow (analyze → confirm → progress → complete)
# =============================================================================

class TestFullWorkflow:
    """Integration tests for complete batch processing workflow."""

    @pytest.mark.asyncio
    async def test_full_workflow_success(self, async_client):
        """
        Test complete workflow: analyze → confirm → check progress.

        Steps:
        1. Analyze canvas to get groupings
        2. Confirm groupings to start batch
        3. Check progress status
        """
        # Step 1: Analyze canvas
        analyze_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/",
            json={
                "canvas_path": "test.canvas",
                "target_color": "3",
            }
        )

        assert analyze_response.status_code == 200
        analyze_data = analyze_response.json()
        assert len(analyze_data["groups"]) > 0

        # Step 2: Confirm groupings
        groups_config = [
            {
                "group_id": group["group_id"],
                "agent_type": group["recommended_agent"],
                "node_ids": [node["node_id"] for node in group["nodes"]],
            }
            for group in analyze_data["groups"]
        ]

        confirm_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/confirm",
            json={
                "canvas_path": "test.canvas",
                "groups": groups_config,
            }
        )

        assert confirm_response.status_code == 202
        confirm_data = confirm_response.json()
        session_id = confirm_data["session_id"]
        assert session_id is not None
        assert confirm_data["status"] == "pending"

        # Step 3: Check progress
        progress_response = await async_client.get(
            f"/api/v1/canvas/intelligent-parallel/{session_id}"
        )

        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["session_id"] == session_id
        assert progress_data["total_groups"] == len(groups_config)
        assert "progress_percent" in progress_data

    @pytest.mark.asyncio
    async def test_workflow_with_agent_override(self, async_client):
        """
        Test workflow where user overrides recommended agent.
        """
        # Analyze canvas
        analyze_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/",
            json={"canvas_path": "test.canvas"}
        )
        analyze_data = analyze_response.json()

        # Override all agents to use oral-explanation
        groups_config = [
            {
                "group_id": group["group_id"],
                "agent_type": "oral-explanation",  # Override
                "node_ids": [node["node_id"] for node in group["nodes"]],
            }
            for group in analyze_data["groups"]
        ]

        confirm_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/confirm",
            json={
                "canvas_path": "test.canvas",
                "groups": groups_config,
            }
        )

        assert confirm_response.status_code == 202
        session_id = confirm_response.json()["session_id"]

        # Check progress - groups should show overridden agent type
        progress_response = await async_client.get(
            f"/api/v1/canvas/intelligent-parallel/{session_id}"
        )

        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        for group in progress_data["groups"]:
            assert group["agent_type"] == "oral-explanation"


# =============================================================================
# Test: Cancellation Workflow
# =============================================================================

class TestCancellationWorkflow:
    """Integration tests for session cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_pending_session(self, async_client):
        """
        Test cancellation of a pending session.

        Steps:
        1. Create session
        2. Cancel immediately
        3. Verify cancelled status
        """
        # Create session
        analyze_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/",
            json={"canvas_path": "test.canvas"}
        )
        analyze_data = analyze_response.json()

        groups_config = [
            {
                "group_id": analyze_data["groups"][0]["group_id"],
                "agent_type": analyze_data["groups"][0]["recommended_agent"],
                "node_ids": [n["node_id"] for n in analyze_data["groups"][0]["nodes"]],
            }
        ]

        confirm_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/confirm",
            json={
                "canvas_path": "test.canvas",
                "groups": groups_config,
            }
        )
        session_id = confirm_response.json()["session_id"]

        # Cancel session
        cancel_response = await async_client.post(
            f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
        )

        assert cancel_response.status_code == 200
        cancel_data = cancel_response.json()
        assert cancel_data["success"] is True

        # Verify status is cancelled
        progress_response = await async_client.get(
            f"/api/v1/canvas/intelligent-parallel/{session_id}"
        )

        assert progress_response.status_code == 200
        assert progress_response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cannot_cancel_twice(self, async_client):
        """
        Test that cancelling an already cancelled session returns 409.
        """
        # Create and cancel session
        analyze_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/",
            json={"canvas_path": "test.canvas"}
        )
        groups_config = [
            {
                "group_id": analyze_response.json()["groups"][0]["group_id"],
                "agent_type": "comparison-table",
                "node_ids": ["node-001"],
            }
        ]

        confirm_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/confirm",
            json={
                "canvas_path": "test.canvas",
                "groups": groups_config,
            }
        )
        session_id = confirm_response.json()["session_id"]

        # First cancel
        await async_client.post(
            f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
        )

        # Second cancel should fail
        second_cancel = await async_client.post(
            f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
        )

        assert second_cancel.status_code == 409


# =============================================================================
# Test: Retry Workflow (Single Agent)
# =============================================================================

class TestRetryWorkflow:
    """Integration tests for single agent retry."""

    @pytest.mark.asyncio
    async def test_retry_single_node(self, async_client):
        """
        Test retrying a single node with single-agent endpoint.

        This endpoint is independent of batch sessions.
        """
        response = await async_client.post(
            "/api/v1/canvas/single-agent",
            json={
                "node_id": "node-001",
                "agent_type": "oral-explanation",
                "canvas_path": "test.canvas",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "node-001"
        assert data["status"] == "success"
        assert data["file_path"] is not None

    @pytest.mark.asyncio
    async def test_retry_with_different_agent(self, async_client):
        """
        Test retrying a node with different agent types.
        """
        agent_types = [
            "comparison-table",
            "four-level-explanation",
            "example-teaching",
            "oral-explanation",
        ]

        for agent_type in agent_types:
            response = await async_client.post(
                "/api/v1/canvas/single-agent",
                json={
                    "node_id": "node-001",
                    "agent_type": agent_type,
                    "canvas_path": "test.canvas",
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert agent_type in data["file_path"]


# =============================================================================
# Test: Error Handling Across Workflow
# =============================================================================

class TestWorkflowErrorHandling:
    """Integration tests for error handling across workflow."""

    @pytest.mark.asyncio
    async def test_invalid_canvas_throughout_workflow(self, async_client):
        """
        Test that nonexistent canvas returns 404 at each step.
        """
        # Analyze with nonexistent canvas
        analyze_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/",
            json={"canvas_path": "nonexistent.canvas"}
        )
        assert analyze_response.status_code == 404

        # Confirm with nonexistent canvas
        confirm_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/confirm",
            json={
                "canvas_path": "nonexistent.canvas",
                "groups": [
                    {
                        "group_id": "g1",
                        "agent_type": "test",
                        "node_ids": ["n1"],
                    }
                ],
            }
        )
        assert confirm_response.status_code == 404

        # Single agent with nonexistent canvas
        single_response = await async_client.post(
            "/api/v1/canvas/single-agent",
            json={
                "node_id": "node-001",
                "agent_type": "oral-explanation",
                "canvas_path": "nonexistent.canvas",
            }
        )
        assert single_response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_session_id(self, async_client):
        """
        Test that invalid session ID returns 404.
        """
        # Get progress with invalid session
        progress_response = await async_client.get(
            "/api/v1/canvas/intelligent-parallel/invalid-session-id"
        )
        assert progress_response.status_code == 404

        # Cancel invalid session
        cancel_response = await async_client.post(
            "/api/v1/canvas/intelligent-parallel/cancel/invalid-session-id"
        )
        assert cancel_response.status_code == 404


# =============================================================================
# Test: Multiple Sessions
# =============================================================================

class TestMultipleSessions:
    """Integration tests for handling multiple concurrent sessions."""

    @pytest.mark.asyncio
    async def test_create_multiple_sessions(self, async_client):
        """
        Test creating multiple independent sessions.
        """
        session_ids = []

        # Create 3 sessions
        for i in range(3):
            analyze_response = await async_client.post(
                "/api/v1/canvas/intelligent-parallel/",
                json={"canvas_path": f"test{i}.canvas"}
            )
            groups_config = [
                {
                    "group_id": analyze_response.json()["groups"][0]["group_id"],
                    "agent_type": "comparison-table",
                    "node_ids": ["node-001"],
                }
            ]

            confirm_response = await async_client.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": f"test{i}.canvas",
                    "groups": groups_config,
                }
            )
            session_ids.append(confirm_response.json()["session_id"])

        # Verify all sessions are unique
        assert len(set(session_ids)) == 3

        # Verify each session can be queried independently
        for session_id in session_ids:
            response = await async_client.get(
                f"/api/v1/canvas/intelligent-parallel/{session_id}"
            )
            assert response.status_code == 200
            assert response.json()["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_sessions_isolated(self, async_client):
        """
        Test that cancelling one session doesn't affect others.
        """
        # Create 2 sessions
        sessions = []
        for i in range(2):
            analyze_response = await async_client.post(
                "/api/v1/canvas/intelligent-parallel/",
                json={"canvas_path": f"test{i}.canvas"}
            )
            groups_config = [
                {
                    "group_id": analyze_response.json()["groups"][0]["group_id"],
                    "agent_type": "comparison-table",
                    "node_ids": ["node-001"],
                }
            ]

            confirm_response = await async_client.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": f"test{i}.canvas",
                    "groups": groups_config,
                }
            )
            sessions.append(confirm_response.json()["session_id"])

        # Cancel first session
        await async_client.post(
            f"/api/v1/canvas/intelligent-parallel/cancel/{sessions[0]}"
        )

        # Verify first session is cancelled
        first_response = await async_client.get(
            f"/api/v1/canvas/intelligent-parallel/{sessions[0]}"
        )
        assert first_response.json()["status"] == "cancelled"

        # Verify second session is still pending
        second_response = await async_client.get(
            f"/api/v1/canvas/intelligent-parallel/{sessions[1]}"
        )
        assert second_response.json()["status"] == "pending"
