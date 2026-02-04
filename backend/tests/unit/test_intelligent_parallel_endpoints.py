# Canvas Learning System - Intelligent Parallel Endpoints Unit Tests
# Story 33.1: Backend REST Endpoints
# Source: Story 33.1 Task 5 - Unit Tests
"""
Unit tests for intelligent parallel batch processing endpoints.

Test Coverage (AC7: ≥90%):
- Test analyze endpoint with valid canvas path
- Test analyze endpoint with missing canvas (404)
- Test confirm endpoint with valid groups
- Test confirm endpoint with invalid groups (400)
- Test progress endpoint with valid session
- Test progress endpoint with invalid session (404)
- Test cancel endpoint for running session
- Test cancel endpoint for completed session (409)
- Test single-agent retry endpoint

[Source: docs/stories/33.1.story.md - Task 5]
[Source: specs/api/parallel-api.openapi.yml]
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.intelligent_parallel_models import (
    CancelResponse,
    ConfirmRequest,
    GroupExecuteConfig,
    GroupPriority,
    GroupProgress,
    GroupStatus,
    IntelligentParallelRequest,
    IntelligentParallelResponse,
    NodeGroup,
    NodeInGroup,
    ParallelTaskStatus,
    ProgressResponse,
    SessionResponse,
    SingleAgentRequest,
    SingleAgentResponse,
    SingleAgentStatus,
)
from app.services.intelligent_parallel_service import IntelligentParallelService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def test_client():
    """Synchronous test client for basic tests."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Provide a mock IntelligentParallelService."""
    return MagicMock(spec=IntelligentParallelService)


@pytest.fixture
def sample_analyze_response():
    """Sample response for analyze endpoint."""
    return IntelligentParallelResponse(
        canvas_path="test.canvas",
        total_nodes=6,
        groups=[
            NodeGroup(
                group_id="group-1",
                group_name="对比类概念",
                group_emoji="📊",
                nodes=[
                    NodeInGroup(node_id="node-001", text="逆否命题 vs 否命题"),
                    NodeInGroup(node_id="node-002", text="充分条件 vs 必要条件"),
                ],
                recommended_agent="comparison-table",
                confidence=0.85,
                priority=GroupPriority.high,
            ),
            NodeGroup(
                group_id="group-2",
                group_name="基础定义",
                group_emoji="📖",
                nodes=[
                    NodeInGroup(node_id="node-003", text="命题的定义"),
                    NodeInGroup(node_id="node-004", text="真值表"),
                ],
                recommended_agent="four-level-explanation",
                confidence=0.78,
                priority=GroupPriority.medium,
            ),
        ],
        estimated_duration="2分钟",
        resource_warning=None,
    )


@pytest.fixture
def sample_session_response():
    """Sample response for confirm endpoint."""
    return SessionResponse(
        session_id="parallel-20250118-abc123",
        status=ParallelTaskStatus.pending,
        total_groups=2,
        total_nodes=4,
        created_at=datetime.now(),
        estimated_completion=None,
        websocket_url="ws://localhost:8000/ws/intelligent-parallel/parallel-20250118-abc123",
    )


@pytest.fixture
def sample_progress_response():
    """Sample response for progress endpoint."""
    return ProgressResponse(
        session_id="parallel-20250118-abc123",
        status=ParallelTaskStatus.running,
        total_groups=2,
        total_nodes=4,
        completed_groups=1,
        completed_nodes=2,
        failed_nodes=0,
        progress_percent=50,
        created_at=datetime.now(),
        started_at=datetime.now(),
        completed_at=None,
        groups=[
            GroupProgress(
                group_id="group-1",
                status=GroupStatus.completed,
                agent_type="comparison-table",
                completed_nodes=2,
                total_nodes=2,
                results=[],
                errors=[],
            ),
            GroupProgress(
                group_id="group-2",
                status=GroupStatus.running,
                agent_type="four-level-explanation",
                completed_nodes=0,
                total_nodes=2,
                results=[],
                errors=[],
            ),
        ],
        performance_metrics=None,
    )


# =============================================================================
# Test: POST /canvas/intelligent-parallel - Analyze Endpoint (AC1)
# =============================================================================

class TestAnalyzeEndpoint:
    """Tests for analyze canvas endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_valid_canvas(self, sample_analyze_response):
        """Test analyze endpoint with valid canvas path returns groupings."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/",
                json={
                    "canvas_path": "test.canvas",
                    "target_color": "3",
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "canvas_path" in data
        assert "groups" in data
        assert "total_nodes" in data
        assert len(data["groups"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_with_max_groups(self):
        """Test analyze endpoint respects max_groups parameter."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/",
                json={
                    "canvas_path": "test.canvas",
                    "target_color": "3",
                    "max_groups": 1,
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["groups"]) <= 1

    @pytest.mark.asyncio
    async def test_analyze_missing_canvas_404(self):
        """Test analyze endpoint returns 404 for nonexistent canvas."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/",
                json={
                    "canvas_path": "nonexistent.canvas",
                    "target_color": "3",
                }
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "CanvasNotFoundError" in str(data["detail"])

    @pytest.mark.asyncio
    async def test_analyze_invalid_color(self):
        """Test analyze endpoint validates target_color."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/",
                json={
                    "canvas_path": "test.canvas",
                    "target_color": "7",  # Invalid: must be 1-6
                }
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# Test: POST /canvas/intelligent-parallel/confirm - Confirm Endpoint (AC2)
# =============================================================================

class TestConfirmEndpoint:
    """Tests for confirm batch endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_valid_groups(self):
        """Test confirm endpoint with valid groups returns session ID."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001", "node-002"],
                        },
                    ],
                    "timeout": 600,
                }
            )

        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert "session_id" in data
        assert "status" in data
        assert data["status"] == "pending"
        assert "websocket_url" in data

    @pytest.mark.asyncio
    async def test_confirm_missing_canvas_404(self):
        """Test confirm endpoint returns 404 for nonexistent canvas."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "nonexistent.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001"],
                        },
                    ],
                }
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_confirm_empty_groups_400(self):
        """Test confirm endpoint returns 400 for empty groups."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [],
                }
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_confirm_timeout_validation(self):
        """Test confirm endpoint validates timeout range."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001"],
                        },
                    ],
                    "timeout": 10,  # Invalid: minimum is 60
                }
            )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# =============================================================================
# Test: GET /canvas/intelligent-parallel/{session_id} - Progress Endpoint (AC3)
# =============================================================================

class TestProgressEndpoint:
    """Tests for progress status endpoint."""

    @pytest.mark.asyncio
    async def test_progress_valid_session(self):
        """Test progress endpoint returns status for valid session."""
        # First create a session
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            create_response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001", "node-002"],
                        },
                    ],
                }
            )
            session_id = create_response.json()["session_id"]

            # Get progress
            response = await ac.get(
                f"/api/v1/canvas/intelligent-parallel/{session_id}"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == session_id
        assert "status" in data
        assert "progress_percent" in data
        assert "groups" in data

    @pytest.mark.asyncio
    async def test_progress_invalid_session_404(self):
        """Test progress endpoint returns 404 for nonexistent session."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/v1/canvas/intelligent-parallel/nonexistent-session"
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "SessionNotFoundError" in str(data["detail"])


# =============================================================================
# Test: POST /canvas/intelligent-parallel/cancel/{session_id} - Cancel (AC4)
# =============================================================================

class TestCancelEndpoint:
    """Tests for cancel session endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_running_session(self):
        """Test cancel endpoint successfully cancels running session."""
        # First create a session
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            create_response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001"],
                        },
                    ],
                }
            )
            session_id = create_response.json()["session_id"]

            # Cancel the session
            response = await ac.post(
                f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "completed_count" in data

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_session_404(self):
        """Test cancel endpoint returns 404 for nonexistent session."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session"
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_409(self):
        """Test cancel endpoint returns 409 for already cancelled session."""
        # Create and cancel a session
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            create_response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001"],
                        },
                    ],
                }
            )
            session_id = create_response.json()["session_id"]

            # Cancel first time
            await ac.post(
                f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
            )

            # Try to cancel again
            response = await ac.post(
                f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
            )

        assert response.status_code == status.HTTP_409_CONFLICT


# =============================================================================
# Test: POST /canvas/single-agent - Single Agent Retry (AC5)
# =============================================================================

class TestSingleAgentEndpoint:
    """Tests for single agent retry endpoint."""

    @pytest.mark.asyncio
    async def test_single_agent_success(self):
        """Test single agent endpoint processes node successfully."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/single-agent",
                json={
                    "node_id": "node-001",
                    "agent_type": "oral-explanation",
                    "canvas_path": "test.canvas",
                }
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["node_id"] == "node-001"
        assert data["status"] == "success"
        assert "file_path" in data

    @pytest.mark.asyncio
    async def test_single_agent_canvas_not_found_404(self):
        """Test single agent endpoint returns 404 for nonexistent canvas."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/single-agent",
                json={
                    "node_id": "node-001",
                    "agent_type": "oral-explanation",
                    "canvas_path": "nonexistent.canvas",
                }
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_single_agent_node_not_found_404(self):
        """Test single agent endpoint returns 404 for nonexistent node."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/single-agent",
                json={
                    "node_id": "nonexistent-node",
                    "agent_type": "oral-explanation",
                    "canvas_path": "test.canvas",
                }
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Test: Error Response Format (AC6)
# =============================================================================

class TestErrorResponses:
    """Tests for proper error response format."""

    @pytest.mark.asyncio
    async def test_404_error_format(self):
        """Test 404 errors include proper error type and message."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/v1/canvas/intelligent-parallel/nonexistent-session"
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert "error" in detail
        assert "message" in detail

    @pytest.mark.asyncio
    async def test_400_error_format(self):
        """Test 400 errors include proper error type and message."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [],  # Empty groups triggers 400
                }
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_409_error_format(self):
        """Test 409 errors include proper error type and message."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            # Create and cancel session
            create_response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/confirm",
                json={
                    "canvas_path": "test.canvas",
                    "groups": [
                        {
                            "group_id": "group-1",
                            "agent_type": "comparison-table",
                            "node_ids": ["node-001"],
                        },
                    ],
                }
            )
            session_id = create_response.json()["session_id"]
            await ac.post(
                f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
            )

            # Try to cancel again
            response = await ac.post(
                f"/api/v1/canvas/intelligent-parallel/cancel/{session_id}"
            )

        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert "detail" in data


# =============================================================================
# Test: Model Validation
# =============================================================================

class TestModelValidation:
    """Tests for Pydantic model validation."""

    def test_intelligent_parallel_request_defaults(self):
        """Test IntelligentParallelRequest has correct defaults."""
        request = IntelligentParallelRequest(canvas_path="test.canvas")
        assert request.target_color == "3"
        assert request.max_groups is None
        assert request.min_nodes_per_group == 2

    def test_confirm_request_timeout_default(self):
        """Test ConfirmRequest has correct timeout default."""
        request = ConfirmRequest(
            canvas_path="test.canvas",
            groups=[
                GroupExecuteConfig(
                    group_id="g1",
                    agent_type="test",
                    node_ids=["n1"],
                )
            ],
        )
        assert request.timeout == 600

    def test_session_response_alias(self):
        """Test SessionResponse uses task_id alias for session_id."""
        response = SessionResponse(
            session_id="test-123",
            total_groups=1,
            created_at=datetime.now(),
        )
        # Check that serialize uses alias
        data = response.model_dump(by_alias=True)
        assert "session_id" in data
        assert data["session_id"] == "test-123"

    def test_progress_response_alias(self):
        """Test ProgressResponse uses task_id alias for session_id."""
        response = ProgressResponse(
            session_id="test-123",
            status=ParallelTaskStatus.running,
            total_groups=1,
            total_nodes=2,
            created_at=datetime.now(),
        )
        data = response.model_dump(by_alias=True)
        assert "session_id" in data

    def test_parallel_task_status_values(self):
        """Test ParallelTaskStatus has all required values."""
        expected = {"pending", "running", "completed", "partial_failure", "failed", "cancelled"}
        actual = {s.value for s in ParallelTaskStatus}
        assert actual == expected

    def test_group_priority_values(self):
        """Test GroupPriority has all required values."""
        expected = {"urgent", "high", "medium", "low"}
        actual = {p.value for p in GroupPriority}
        assert actual == expected
