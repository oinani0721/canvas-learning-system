# Story 33.10: P0 Runtime Defect Fixes (Adversarial Audit Round 2)
"""
Unit tests for 4 P0/P1 runtime defects:

Fix #1: ProgressMonitorModal URL (frontend - verified in test_poll_url_no_status_segment)
Fix #2: retry_single_node uses real node content
Fix #3: GroupProgress reflects actual session progress
Fix #4: WebSocket URL not hardcoded to localhost

[Source: docs/stories/33.10.story.md]
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.intelligent_parallel_models import (
    GroupProgress,
    GroupStatus,
    NodeResult,
    ParallelTaskStatus,
    SessionResponse,
    SingleAgentResponse,
    SingleAgentStatus,
)
from app.services.intelligent_parallel_service import IntelligentParallelService


# =============================================================================
# Fixtures
# =============================================================================

def _make_session_info(
    node_results: dict = None,
    metadata: dict = None,
    status_value: str = "running",
    completed_nodes: int = 0,
    failed_nodes: int = 0,
    node_count: int = 6,
):
    """Create a mock SessionInfo-like object."""
    from unittest.mock import MagicMock
    from enum import Enum

    class MockStatus(str, Enum):
        value_str = status_value

    session = MagicMock()
    session.status = MagicMock()
    session.status.value = status_value
    session.node_count = node_count
    session.completed_nodes = completed_nodes
    session.failed_nodes = failed_nodes
    session.metadata = metadata or {}
    session.node_results = node_results or {}
    session.created_at = datetime(2026, 2, 10, 12, 0, 0)
    session.started_at = datetime(2026, 2, 10, 12, 0, 1)
    session.completed_at = None
    return session


def _make_node_result(node_id: str, status: str = "success", result=None, error=None):
    """Create a mock NodeResult from session_models."""
    nr = MagicMock()
    nr.node_id = node_id
    nr.status = status
    nr.result = result
    nr.error = error
    nr.to_dict = MagicMock(return_value={
        "node_id": node_id,
        "status": status,
        "result": result,
        "error": error,
    })
    return nr


@pytest.fixture
def service_with_mocks():
    """Create IntelligentParallelService with all dependencies mocked."""
    session_manager = AsyncMock()
    agent_service = AsyncMock()
    canvas_service = AsyncMock()

    svc = IntelligentParallelService(
        session_manager=session_manager,
        agent_service=agent_service,
        canvas_service=canvas_service,
    )
    return svc, session_manager, agent_service, canvas_service


# =============================================================================
# Fix #3: GroupProgress reflects actual session progress
# =============================================================================

class TestGroupProgressComputation:
    """Story 33.10 AC-33.10.3: GroupProgress reflects actual session progress."""

    @pytest.mark.asyncio
    async def test_group_progress_all_pending(self, service_with_mocks):
        """No results yet → all groups pending with completed_nodes=0."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={},
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "comparison-table", "node_ids": ["n1", "n2", "n3"]},
                ]
            },
            status_value="running",
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        assert result is not None
        assert len(result.groups) == 1
        g = result.groups[0]
        assert g.completed_nodes == 0
        assert g.status == GroupStatus.pending
        assert g.total_nodes == 3

    @pytest.mark.asyncio
    async def test_group_progress_partial_completion(self, service_with_mocks):
        """2/3 nodes complete → running status, completed_nodes=2."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={
                "n1": _make_node_result("n1", "success", result="file1.md"),
                "n2": _make_node_result("n2", "success", result="file2.md"),
            },
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "oral-explanation", "node_ids": ["n1", "n2", "n3"]},
                ]
            },
            status_value="running",
            completed_nodes=2,
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        assert result is not None
        g = result.groups[0]
        assert g.completed_nodes == 2
        assert g.status == GroupStatus.running
        assert g.total_nodes == 3

    @pytest.mark.asyncio
    async def test_group_progress_all_completed(self, service_with_mocks):
        """3/3 nodes complete → completed status."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={
                "n1": _make_node_result("n1", "success"),
                "n2": _make_node_result("n2", "success"),
                "n3": _make_node_result("n3", "success"),
            },
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "comparison-table", "node_ids": ["n1", "n2", "n3"]},
                ]
            },
            status_value="completed",
            completed_nodes=3,
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        g = result.groups[0]
        assert g.completed_nodes == 3
        assert g.status == GroupStatus.completed

    @pytest.mark.asyncio
    async def test_group_progress_with_failures(self, service_with_mocks):
        """2 success + 1 failed → failed status (partial failure)."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={
                "n1": _make_node_result("n1", "success"),
                "n2": _make_node_result("n2", "failed", error="API timeout"),
                "n3": _make_node_result("n3", "success"),
            },
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "deep-decomposition", "node_ids": ["n1", "n2", "n3"]},
                ]
            },
            status_value="partial_failure",
            completed_nodes=2,
            failed_nodes=1,
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        g = result.groups[0]
        assert g.completed_nodes == 2
        assert g.status == GroupStatus.failed  # partial failure = failed
        assert len(g.errors) == 1
        assert g.errors[0].error_message == "API timeout"

    @pytest.mark.asyncio
    async def test_multiple_groups_independent_progress(self, service_with_mocks):
        """Two groups: group1 completed, group2 running."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={
                "n1": _make_node_result("n1", "success"),
                "n2": _make_node_result("n2", "success"),
                # n3 not yet processed
            },
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "comparison-table", "node_ids": ["n1", "n2"]},
                    {"group_id": "g2", "agent_type": "oral-explanation", "node_ids": ["n3"]},
                ]
            },
            status_value="running",
            completed_nodes=2,
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        assert len(result.groups) == 2
        assert result.groups[0].status == GroupStatus.completed
        assert result.groups[0].completed_nodes == 2
        assert result.groups[1].status == GroupStatus.pending
        assert result.groups[1].completed_nodes == 0

    @pytest.mark.asyncio
    async def test_empty_metadata_returns_no_groups(self, service_with_mocks):
        """Empty metadata {} → groups=[], total_groups=0."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={},
            metadata={},
            status_value="running",
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        assert result is not None
        assert result.groups == []
        assert result.total_groups == 0
        assert result.completed_groups == 0

    @pytest.mark.asyncio
    async def test_metadata_with_none_node_results(self, service_with_mocks):
        """Groups exist in metadata but node_results is empty → all groups pending."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={},
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "scoring", "node_ids": ["n1"]},
                    {"group_id": "g2", "agent_type": "hint", "node_ids": ["n2"]},
                ]
            },
            status_value="running",
            node_count=2,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")

        assert len(result.groups) == 2
        for g in result.groups:
            assert g.status == GroupStatus.pending
            assert g.completed_nodes == 0
            assert g.results == []
            assert g.errors == []

    @pytest.mark.asyncio
    async def test_completed_groups_counted(self, service_with_mocks):
        """completed_groups in ProgressResponse counts terminal groups."""
        svc, session_manager, _, _ = service_with_mocks

        session = _make_session_info(
            node_results={
                "n1": _make_node_result("n1", "success"),
                "n2": _make_node_result("n2", "success"),
            },
            metadata={
                "groups": [
                    {"group_id": "g1", "agent_type": "a", "node_ids": ["n1", "n2"]},
                    {"group_id": "g2", "agent_type": "b", "node_ids": ["n3"]},
                ]
            },
            status_value="running",
            completed_nodes=2,
            node_count=3,
        )
        session_manager.get_session = AsyncMock(return_value=session)

        result = await svc.get_session_status("test-session")
        assert result.completed_groups == 1  # Only g1 is completed


# =============================================================================
# Fix #2: retry_single_node uses real node content
# =============================================================================

class TestRetrySingleNodeRealContent:
    """Story 33.10 AC-33.10.2: retry_single_node uses real node content."""

    @pytest.mark.asyncio
    async def test_retry_uses_real_content_when_available(self, service_with_mocks):
        """When canvas_service returns content, agent gets real text."""
        svc, _, agent_service, canvas_service = service_with_mocks

        # Mock canvas_service to return real node content
        canvas_service.read_canvas = AsyncMock(return_value={
            "nodes": [
                {"id": "node-1", "type": "text", "text": "实数的完备性定义与性质"},
            ]
        })
        canvas_service.canvas_base_path = "/vault"

        # Mock get_node_content to return the text
        with patch(
            "app.services.context_enrichment_service.get_node_content",
            return_value="实数的完备性定义与性质",
        ):
            # Mock agent response
            agent_result = MagicMock()
            agent_result.success = True
            agent_result.file_path = "output/node-1.md"
            agent_service.call_agent = AsyncMock(return_value=agent_result)

            result = await svc.retry_single_node(
                node_id="node-1",
                agent_type="oral-explanation",
                canvas_path="test.canvas",
            )

        # Verify agent received real content, not placeholder
        call_args = agent_service.call_agent.call_args
        assert call_args.kwargs.get("prompt") == "实数的完备性定义与性质"
        assert result.status == SingleAgentStatus.success

    @pytest.mark.asyncio
    async def test_retry_falls_back_when_content_unavailable(self, service_with_mocks):
        """When canvas_service returns None, use fallback prompt."""
        svc, _, agent_service, canvas_service = service_with_mocks

        # Mock canvas_service to return empty
        canvas_service.read_canvas = AsyncMock(return_value=None)

        # Mock agent response
        agent_result = MagicMock()
        agent_result.success = True
        agent_result.file_path = None
        agent_service.call_agent = AsyncMock(return_value=agent_result)

        result = await svc.retry_single_node(
            node_id="node-1",
            agent_type="oral-explanation",
            canvas_path="test.canvas",
        )

        # Verify fallback prompt was used
        call_args = agent_service.call_agent.call_args
        prompt = call_args.kwargs.get("prompt")
        assert "Process node node-1" in prompt
        assert result.status == SingleAgentStatus.success

    @pytest.mark.asyncio
    async def test_retry_without_canvas_service_uses_fallback(self):
        """When canvas_service not injected, use fallback prompt."""
        agent_service = AsyncMock()
        svc = IntelligentParallelService(
            agent_service=agent_service,
            canvas_service=None,  # Not injected
        )

        agent_result = MagicMock()
        agent_result.success = True
        agent_result.file_path = None
        agent_service.call_agent = AsyncMock(return_value=agent_result)

        result = await svc.retry_single_node(
            node_id="node-1",
            agent_type="oral-explanation",
            canvas_path="test.canvas",
        )

        call_args = agent_service.call_agent.call_args
        prompt = call_args.kwargs.get("prompt")
        assert "Process node node-1" in prompt


# =============================================================================
# Fix #4: WebSocket URL not hardcoded
# =============================================================================

class TestWebSocketURLNotHardcoded:
    """Story 33.10 AC-33.10.4: WebSocket URL not hardcoded."""

    @pytest.mark.asyncio
    async def test_session_response_websocket_url_is_none(self, service_with_mocks):
        """start_batch_session returns websocket_url=None."""
        svc, session_manager, _, _ = service_with_mocks

        session_manager.create_session = AsyncMock(return_value="session-123")

        from app.models.intelligent_parallel_models import GroupExecuteConfig
        groups = [
            GroupExecuteConfig(
                group_id="g1",
                agent_type="comparison-table",
                node_ids=["n1", "n2"],
            )
        ]

        result = await svc.start_batch_session(
            canvas_path="test.canvas",
            groups=groups,
        )

        assert isinstance(result, SessionResponse)
        assert result.websocket_url is None
        assert result.task_id == "session-123"

    @pytest.mark.asyncio
    async def test_websocket_url_not_localhost(self, service_with_mocks):
        """Verify websocket_url does not contain localhost:8000."""
        svc, session_manager, _, _ = service_with_mocks

        session_manager.create_session = AsyncMock(return_value="session-456")

        from app.models.intelligent_parallel_models import GroupExecuteConfig
        groups = [
            GroupExecuteConfig(
                group_id="g1",
                agent_type="a",
                node_ids=["n1"],
            )
        ]

        result = await svc.start_batch_session(
            canvas_path="test.canvas",
            groups=groups,
        )

        # Must not contain hardcoded localhost
        if result.websocket_url is not None:
            assert "localhost:8000" not in result.websocket_url


# =============================================================================
# Fix #1: Frontend URL verification (backend route check)
# =============================================================================

class TestBackendRouteExists:
    """Story 33.10 AC-33.10.1: Backend route matches frontend expectation."""

    def test_get_progress_route_has_no_status_segment(self):
        """Verify backend route is /{session_id} not /status/{session_id}."""
        from app.api.v1.endpoints.intelligent_parallel import intelligent_parallel_router

        routes = [r.path for r in intelligent_parallel_router.routes]
        assert "/{session_id}" in routes
        assert "/status/{session_id}" not in routes
