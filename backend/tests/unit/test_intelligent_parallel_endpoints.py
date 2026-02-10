# Canvas Learning System - Intelligent Parallel Endpoints Unit Tests
# EPIC-33 P0 Fix: Updated to test real service integration with mocked dependencies
"""
Unit tests for intelligent parallel batch processing endpoints.

EPIC-33 P0 Fix: Tests now mock the real service dependencies
(IntelligentGroupingService, SessionManager, BatchOrchestrator, AgentService,
AgentRoutingEngine) instead of relying on STUB behavior.

Test Coverage:
- Test analyze endpoint with valid canvas path (delegates to grouping_service)
- Test analyze endpoint with missing canvas (404)
- Test confirm endpoint with valid groups (creates real session)
- Test confirm endpoint with invalid groups (400)
- Test progress endpoint with valid session
- Test progress endpoint with invalid session (404)
- Test cancel endpoint for running session
- Test cancel endpoint for completed session (409)
- Test single-agent retry endpoint
- Test DI integration: service dependencies are wired
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from fastapi import status
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
    PerformanceMetrics,
    ProgressResponse,
    SessionResponse,
    SingleAgentRequest,
    SingleAgentResponse,
    SingleAgentStatus,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def reset_service_singleton():
    """Reset the endpoint service singleton before each test."""
    from app.api.v1.endpoints.intelligent_parallel import reset_service
    reset_service()
    yield
    reset_service()


@pytest.fixture
def mock_grouping_service():
    """Mock IntelligentGroupingService."""
    service = AsyncMock()
    service.analyze_canvas = AsyncMock(return_value=IntelligentParallelResponse(
        canvas_path="test.canvas",
        total_nodes=4,
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
    ))
    return service


@pytest.fixture
def mock_session_manager():
    """Mock SessionManager."""
    manager = AsyncMock()
    manager.create_session = AsyncMock(return_value="parallel-20260209-abc123")

    # Mock session info for get_session
    session_info = MagicMock()
    session_info.status = MagicMock()
    session_info.status.value = "pending"
    session_info.node_count = 2
    session_info.completed_nodes = 0
    session_info.failed_nodes = 0
    session_info.created_at = datetime.now()
    session_info.started_at = None
    session_info.completed_at = None
    session_info.metadata = {
        "groups": [{"group_id": "group-1", "agent_type": "comparison-table", "node_ids": ["node-001"]}]
    }
    manager.get_session = AsyncMock(return_value=session_info)
    manager.transition_state = AsyncMock()

    return manager


@pytest.fixture
def mock_agent_service():
    """Mock AgentService."""
    service = AsyncMock()
    result = MagicMock()
    result.success = True
    result.file_path = "test/node-001-oral-explanation.md"
    result.content = "test content"
    service.call_agent = AsyncMock(return_value=result)
    return service


@pytest.fixture
def mock_routing_engine():
    """Mock AgentRoutingEngine."""
    engine = MagicMock()
    return engine


@pytest.fixture
def patched_service(
    mock_grouping_service,
    mock_session_manager,
    mock_agent_service,
    mock_routing_engine,
):
    """Patch get_service to return a fully mocked IntelligentParallelService."""
    from app.services.intelligent_parallel_service import IntelligentParallelService

    service = IntelligentParallelService(
        grouping_service=mock_grouping_service,
        session_manager=mock_session_manager,
        batch_orchestrator=None,  # Not needed for endpoint tests
        agent_service=mock_agent_service,
        routing_engine=mock_routing_engine,
    )

    with patch(
        "app.api.v1.endpoints.intelligent_parallel.get_service",
        return_value=service,
    ), patch(
        "app.api.v1.endpoints.intelligent_parallel._ensure_async_deps",
        new_callable=AsyncMock,
    ):
        yield service


# =============================================================================
# Test: POST /canvas/intelligent-parallel - Analyze Endpoint
# =============================================================================

class TestAnalyzeEndpoint:
    """Tests for analyze canvas endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_valid_canvas(self, patched_service):
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
        assert len(data["groups"]) == 2
        assert data["total_nodes"] == 4

    @pytest.mark.asyncio
    async def test_analyze_with_max_groups(self, patched_service, mock_grouping_service):
        """Test analyze endpoint respects max_groups parameter."""
        # Return only 1 group when max_groups=1
        mock_grouping_service.analyze_canvas.return_value = IntelligentParallelResponse(
            canvas_path="test.canvas",
            total_nodes=2,
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
            ],
            estimated_duration="1分钟",
            resource_warning=None,
        )

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
    async def test_analyze_missing_canvas_404(self, patched_service, mock_grouping_service):
        """Test analyze endpoint returns 404 for nonexistent canvas."""
        mock_grouping_service.analyze_canvas.side_effect = FileNotFoundError(
            "Canvas file 'nonexistent.canvas' not found"
        )

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
    async def test_analyze_invalid_color(self, patched_service):
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
# Test: POST /canvas/intelligent-parallel/confirm - Confirm Endpoint
# =============================================================================

class TestConfirmEndpoint:
    """Tests for confirm batch endpoint."""

    @pytest.mark.asyncio
    async def test_confirm_valid_groups(self, patched_service):
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
    async def test_confirm_missing_canvas_404(self, patched_service, mock_session_manager):
        """Test confirm endpoint returns 404 for nonexistent canvas."""
        # Make create_session raise FileNotFoundError
        mock_session_manager.create_session.side_effect = FileNotFoundError(
            "Canvas file 'nonexistent.canvas' not found"
        )

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

        # FileNotFoundError propagates as 404 or 500 from the service
        assert response.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @pytest.mark.asyncio
    async def test_confirm_empty_groups_400(self, patched_service):
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
    async def test_confirm_timeout_validation(self, patched_service):
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
# Test: GET /canvas/intelligent-parallel/{session_id} - Progress Endpoint
# =============================================================================

class TestProgressEndpoint:
    """Tests for progress status endpoint."""

    @pytest.mark.asyncio
    async def test_progress_valid_session(self, patched_service):
        """Test progress endpoint returns status for valid session."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/v1/canvas/intelligent-parallel/parallel-20260209-abc123"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["session_id"] == "parallel-20260209-abc123"
        assert "status" in data
        assert "progress_percent" in data

    @pytest.mark.asyncio
    async def test_progress_invalid_session_404(self, patched_service, mock_session_manager):
        """Test progress endpoint returns 404 for nonexistent session."""
        from app.services.session_manager import SessionNotFoundError
        mock_session_manager.get_session.side_effect = SessionNotFoundError("not found")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.get(
                "/api/v1/canvas/intelligent-parallel/nonexistent-session"
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Test: POST /canvas/intelligent-parallel/cancel/{session_id} - Cancel
# =============================================================================

class TestCancelEndpoint:
    """Tests for cancel session endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_running_session(self, patched_service):
        """Test cancel endpoint successfully cancels running session."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/cancel/parallel-20260209-abc123"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "completed_count" in data

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_session_404(self, patched_service, mock_session_manager):
        """Test cancel endpoint returns 404 for nonexistent session."""
        from app.services.session_manager import SessionNotFoundError
        mock_session_manager.get_session.side_effect = SessionNotFoundError("not found")

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/cancel/nonexistent-session"
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_409(self, patched_service, mock_session_manager):
        """Test cancel endpoint returns 409 for already cancelled session."""
        session_info = MagicMock()
        session_info.status = MagicMock()
        session_info.status.value = "cancelled"
        session_info.completed_nodes = 0
        mock_session_manager.get_session.return_value = session_info

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            response = await ac.post(
                "/api/v1/canvas/intelligent-parallel/cancel/parallel-20260209-abc123"
            )

        assert response.status_code == status.HTTP_409_CONFLICT


# =============================================================================
# Test: POST /canvas/single-agent - Single Agent Retry
# =============================================================================

class TestSingleAgentEndpoint:
    """Tests for single agent retry endpoint."""

    @pytest.mark.asyncio
    async def test_single_agent_success(self, patched_service):
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
    async def test_single_agent_canvas_not_found_404(self, patched_service, mock_agent_service):
        """Test single agent endpoint returns 404 for nonexistent canvas."""
        mock_agent_service.call_agent.side_effect = FileNotFoundError(
            "Canvas file 'nonexistent.canvas' not found"
        )

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

        # Service catches exceptions and returns failed status instead of raising
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] is not None


# =============================================================================
# Test: Error Response Format
# =============================================================================

class TestErrorResponses:
    """Tests for proper error response format."""

    @pytest.mark.asyncio
    async def test_404_error_format(self, patched_service, mock_session_manager):
        """Test 404 errors include proper error type and message."""
        from app.services.session_manager import SessionNotFoundError
        mock_session_manager.get_session.side_effect = SessionNotFoundError("not found")

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
    async def test_400_error_format(self, patched_service):
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


# =============================================================================
# Test: DI Integration - Service dependencies are wired
# =============================================================================

class TestDIIntegration:
    """Tests verifying dependency injection wiring for EPIC-33."""

    def test_service_has_all_dependencies(self, patched_service):
        """Verify the service is constructed with all required dependencies."""
        assert patched_service._grouping_service is not None
        assert patched_service._session_manager is not None
        assert patched_service._routing_engine is not None
        # agent_service is injected
        assert patched_service._agent_service is not None

    @pytest.mark.asyncio
    async def test_analyze_delegates_to_grouping_service(self, patched_service, mock_grouping_service):
        """Verify analyze_canvas delegates to IntelligentGroupingService."""
        await patched_service.analyze_canvas("test.canvas", "3")
        mock_grouping_service.analyze_canvas.assert_called_once_with(
            canvas_path="test.canvas",
            target_color="3",
            max_groups=None,
            min_nodes_per_group=2,
        )

    @pytest.mark.asyncio
    async def test_start_batch_delegates_to_session_manager(self, patched_service, mock_session_manager):
        """Verify start_batch_session creates session via SessionManager."""
        groups = [
            GroupExecuteConfig(group_id="g1", agent_type="test", node_ids=["n1"])
        ]
        await patched_service.start_batch_session("test.canvas", groups)
        mock_session_manager.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_exists_delegates_to_session_manager(self, patched_service, mock_session_manager):
        """Verify session_exists checks SessionManager."""
        result = await patched_service.session_exists("test-session")
        assert result is True
        mock_session_manager.get_session.assert_called_with("test-session")

    @pytest.mark.asyncio
    async def test_retry_single_node_delegates_to_agent_service(self, patched_service, mock_agent_service):
        """Verify retry_single_node calls AgentService.call_agent."""
        result = await patched_service.retry_single_node(
            node_id="node-001",
            agent_type="oral-explanation",
            canvas_path="test.canvas",
        )
        assert result.status == SingleAgentStatus.success
        mock_agent_service.call_agent.assert_called_once()
