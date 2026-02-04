# Canvas Learning System - Intelligent Parallel Service
# Story 33.1: Backend REST Endpoints - Service Layer Stubs
# Story 33.2: WebSocket Integration for Real-time Updates
# ✅ Verified from specs/api/parallel-api.openapi.yml
# ✅ Verified from specs/data/parallel-task.schema.json
"""
IntelligentParallelService - Service layer for parallel batch processing.

Story 33.1: STUB implementations for REST endpoints.
Story 33.2: WebSocket integration for real-time progress updates.

Service Methods:
- analyze_canvas(): Returns mock groupings (stub)
- start_batch_session(): Creates session, returns ID (stub)
- get_session_status(): Returns progress (stub)
- cancel_session(): Cancels and returns count (stub)
- retry_single_node(): Calls single agent (stub)
- notify_progress(): Broadcast progress via WebSocket (Story 33.2)
- session_exists(): Check if session exists (Story 33.2)

[Source: docs/stories/33.1.story.md - Task 4]
[Source: docs/stories/33.2.story.md - Task 4]
[Source: specs/api/parallel-api.openapi.yml]
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.intelligent_parallel_models import (
    CancelResponse,
    GroupExecuteConfig,
    GroupPriority,
    GroupProgress,
    GroupStatus,
    IntelligentParallelResponse,
    NodeGroup,
    NodeInGroup,
    NodeResult,
    ParallelTaskStatus,
    PerformanceMetrics,
    ProgressResponse,
    SessionResponse,
    SingleAgentResponse,
    SingleAgentStatus,
    WebSocketMessage,
    create_ws_complete_event,
    create_ws_error_event,
    create_ws_group_complete_event,
    create_ws_node_complete_event,
    create_ws_progress_event,
)
from app.services.websocket_manager import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)


class IntelligentParallelService:
    """
    Service for intelligent parallel batch processing.

    Story 33.1: STUB implementations for REST endpoints.
    Story 33.2: WebSocket integration for real-time progress updates.

    [Source: docs/stories/33.1.story.md - Task 4]
    [Source: docs/stories/33.2.story.md - Task 4]
    """

    def __init__(
        self,
        connection_manager: Optional[ConnectionManager] = None,
    ) -> None:
        """
        Initialize service with in-memory session storage and WebSocket manager.

        [Source: docs/stories/33.2.story.md - Task 4]

        Args:
            connection_manager: Optional ConnectionManager for WebSocket broadcasting
        """
        # In-memory session storage (Redis adapter in Story 33.2)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        # WebSocket connection manager (Story 33.2)
        self._connection_manager = connection_manager or get_connection_manager()
        logger.info("IntelligentParallelService initialized with WebSocket support")

    async def analyze_canvas(
        self,
        canvas_path: str,
        target_color: str = "3",
        max_groups: Optional[int] = None,
        min_nodes_per_group: int = 2,
    ) -> IntelligentParallelResponse:
        """
        Analyze canvas and return node groupings with agent recommendations.

        STUB: Returns mock data. Full TF-IDF + K-Means implementation in Story 33.2.

        [Source: docs/stories/33.1.story.md - AC1]
        [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel/post]

        Args:
            canvas_path: Path to canvas file
            target_color: Target node color (1-6, default "3" for purple)
            max_groups: Maximum number of groups (optional)
            min_nodes_per_group: Minimum nodes per group

        Returns:
            IntelligentParallelResponse with grouped nodes

        Raises:
            FileNotFoundError: If canvas file not found
        """
        logger.info(
            f"analyze_canvas called: path={canvas_path}, color={target_color}"
        )

        # STUB: Check if canvas exists (mock check for testing)
        if canvas_path.startswith("nonexistent"):
            raise FileNotFoundError(f"Canvas file '{canvas_path}' not found")

        # STUB: Return mock groupings
        mock_groups = [
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
            NodeGroup(
                group_id="group-3",
                group_name="证明技巧",
                group_emoji="🔍",
                nodes=[
                    NodeInGroup(node_id="node-005", text="反证法"),
                    NodeInGroup(node_id="node-006", text="数学归纳法"),
                ],
                recommended_agent="example-teaching",
                confidence=0.72,
                priority=GroupPriority.medium,
            ),
        ]

        # Apply max_groups limit if specified
        if max_groups is not None and max_groups < len(mock_groups):
            mock_groups = mock_groups[:max_groups]

        return IntelligentParallelResponse(
            canvas_path=canvas_path,
            total_nodes=sum(len(g.nodes) for g in mock_groups),
            groups=mock_groups,
            estimated_duration="2分钟",
            resource_warning=None,
        )

    async def start_batch_session(
        self,
        canvas_path: str,
        groups: List[GroupExecuteConfig],
        max_concurrent: Optional[int] = None,
        timeout: int = 600,
    ) -> SessionResponse:
        """
        Start batch processing session.

        STUB: Creates session in memory. Full async execution in Story 33.2.

        [Source: docs/stories/33.1.story.md - AC2]
        [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel~1confirm/post]

        Args:
            canvas_path: Path to canvas file
            groups: Confirmed groups with agent assignments
            max_concurrent: Maximum concurrent executions
            timeout: Total timeout in seconds

        Returns:
            SessionResponse with session ID

        Raises:
            FileNotFoundError: If canvas not found
            ValueError: If groups configuration invalid
        """
        logger.info(
            f"start_batch_session called: path={canvas_path}, groups={len(groups)}"
        )

        # STUB: Validate canvas exists
        if canvas_path.startswith("nonexistent"):
            raise FileNotFoundError(f"Canvas file '{canvas_path}' not found")

        # STUB: Validate groups
        if not groups:
            raise ValueError("At least one group must be specified")

        # Generate session ID
        session_id = f"parallel-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
        now = datetime.now()

        # Calculate totals
        total_nodes = sum(len(g.node_ids) for g in groups)

        # Store session
        self._sessions[session_id] = {
            "canvas_path": canvas_path,
            "groups": groups,
            "status": ParallelTaskStatus.pending,
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "total_groups": len(groups),
            "total_nodes": total_nodes,
            "completed_groups": 0,
            "completed_nodes": 0,
            "failed_nodes": 0,
            "max_concurrent": max_concurrent or 12,
            "timeout": timeout,
        }

        logger.info(f"Session created: {session_id}")

        return SessionResponse(
            session_id=session_id,
            status=ParallelTaskStatus.pending,
            total_groups=len(groups),
            total_nodes=total_nodes,
            created_at=now,
            estimated_completion=now + timedelta(seconds=timeout // 2),
            websocket_url=f"ws://localhost:8000/ws/intelligent-parallel/{session_id}",
        )

    async def get_session_status(
        self,
        session_id: str,
    ) -> Optional[ProgressResponse]:
        """
        Get current progress status for a batch session.

        STUB: Returns stored session data. Real progress tracking in Story 33.2.

        [Source: docs/stories/33.1.story.md - AC3]
        [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel~1{sessionId}/get]

        Args:
            session_id: Session ID

        Returns:
            ProgressResponse or None if session not found
        """
        logger.info(f"get_session_status called: session_id={session_id}")

        session = self._sessions.get(session_id)
        if session is None:
            return None

        # STUB: Calculate progress
        total_nodes = session["total_nodes"]
        completed_nodes = session["completed_nodes"]
        progress_percent = (
            int(completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
        )

        # STUB: Build group progress
        groups_progress = []
        for i, group in enumerate(session["groups"]):
            groups_progress.append(
                GroupProgress(
                    group_id=group.group_id,
                    status=GroupStatus.pending,  # STUB: always pending
                    agent_type=group.agent_type,
                    completed_nodes=0,
                    total_nodes=len(group.node_ids),
                    results=[],
                    errors=[],
                )
            )

        return ProgressResponse(
            session_id=session_id,
            status=session["status"],
            total_groups=session["total_groups"],
            total_nodes=total_nodes,
            completed_groups=session["completed_groups"],
            completed_nodes=completed_nodes,
            failed_nodes=session["failed_nodes"],
            progress_percent=progress_percent,
            created_at=session["created_at"],
            started_at=session["started_at"],
            completed_at=session["completed_at"],
            groups=groups_progress,
            performance_metrics=None,  # STUB: metrics only after completion
        )

    async def cancel_session(
        self,
        session_id: str,
    ) -> Optional[CancelResponse]:
        """
        Cancel an in-progress batch processing session.

        STUB: Updates session status. Real task cancellation in Story 33.2.

        [Source: docs/stories/33.1.story.md - AC4]
        [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel~1cancel~1{sessionId}/post]

        Args:
            session_id: Session ID to cancel

        Returns:
            CancelResponse or None if session not found

        Raises:
            ValueError: If session already completed or cancelled
        """
        logger.info(f"cancel_session called: session_id={session_id}")

        session = self._sessions.get(session_id)
        if session is None:
            return None

        # Check if already completed or cancelled
        if session["status"] in [
            ParallelTaskStatus.completed,
            ParallelTaskStatus.cancelled,
        ]:
            raise ValueError(
                f"Session already {session['status'].value}, cannot cancel"
            )

        # STUB: Cancel session
        completed_count = session["completed_nodes"]
        session["status"] = ParallelTaskStatus.cancelled
        session["completed_at"] = datetime.now()

        logger.info(
            f"Session cancelled: {session_id}, completed_count={completed_count}"
        )

        return CancelResponse(
            success=True,
            message="Task cancelled successfully",
            completed_count=completed_count,
        )

    async def retry_single_node(
        self,
        node_id: str,
        agent_type: str,
        canvas_path: str,
    ) -> SingleAgentResponse:
        """
        Execute single agent on a specific node.

        STUB: Returns mock success. Real agent invocation in Story 33.2.

        [Source: docs/stories/33.1.story.md - AC5]

        Args:
            node_id: Node ID to process
            agent_type: Agent type to use
            canvas_path: Canvas file path

        Returns:
            SingleAgentResponse with result

        Raises:
            FileNotFoundError: If node or canvas not found
        """
        logger.info(
            f"retry_single_node called: node={node_id}, agent={agent_type}"
        )

        # STUB: Validate canvas exists
        if canvas_path.startswith("nonexistent"):
            raise FileNotFoundError(f"Canvas file '{canvas_path}' not found")

        # STUB: Validate node exists
        if node_id.startswith("nonexistent"):
            raise FileNotFoundError(f"Node '{node_id}' not found in canvas")

        # STUB: Return mock success
        return SingleAgentResponse(
            node_id=node_id,
            file_path=f"{canvas_path.replace('.canvas', '')}/{node_id}-{agent_type}.md",
            status=SingleAgentStatus.success,
            error_message=None,
        )

    # ═══════════════════════════════════════════════════════════════════════════════
    # WebSocket Integration Methods (Story 33.2)
    # [Source: docs/stories/33.2.story.md - Task 4]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Used by WebSocket endpoint for validation before accepting connections.

        [Source: docs/stories/33.2.story.md - AC1]

        Args:
            session_id: Session ID to check

        Returns:
            bool: True if session exists
        """
        return session_id in self._sessions

    async def notify_progress(
        self,
        session_id: str,
        progress_percent: int,
        completed_nodes: int,
        total_nodes: int,
    ) -> int:
        """
        Broadcast progress update to WebSocket clients.

        [Source: docs/stories/33.2.story.md - AC2, AC4]

        Args:
            session_id: Session ID to broadcast to
            progress_percent: Current progress percentage
            completed_nodes: Number of completed nodes
            total_nodes: Total number of nodes

        Returns:
            int: Number of clients that received the update
        """
        event = create_ws_progress_event(
            task_id=session_id,
            progress_percent=progress_percent,
            completed_nodes=completed_nodes,
            total_nodes=total_nodes,
        )
        return await self._connection_manager.broadcast_to_session(session_id, event)

    async def notify_node_complete(
        self,
        session_id: str,
        node_id: str,
        file_path: Optional[str] = None,
        file_size: Optional[str] = None,
        group_id: Optional[str] = None,
    ) -> int:
        """
        Broadcast node completion event to WebSocket clients.

        [Source: docs/stories/33.2.story.md - AC2]

        Args:
            session_id: Session ID to broadcast to
            node_id: Completed node ID
            file_path: Generated file path
            file_size: File size
            group_id: Parent group ID

        Returns:
            int: Number of clients that received the update
        """
        event = create_ws_node_complete_event(
            task_id=session_id,
            node_id=node_id,
            file_path=file_path,
            file_size=file_size,
            group_id=group_id,
        )
        return await self._connection_manager.broadcast_to_session(session_id, event)

    async def notify_group_complete(
        self,
        session_id: str,
        group_id: str,
        agent_type: str,
        results: Optional[List[NodeResult]] = None,
    ) -> int:
        """
        Broadcast group completion event to WebSocket clients.

        [Source: docs/stories/33.2.story.md - AC2]

        Args:
            session_id: Session ID to broadcast to
            group_id: Completed group ID
            agent_type: Agent type used
            results: Generated files

        Returns:
            int: Number of clients that received the update
        """
        event = create_ws_group_complete_event(
            task_id=session_id,
            group_id=group_id,
            agent_type=agent_type,
            results=results,
        )
        return await self._connection_manager.broadcast_to_session(session_id, event)

    async def notify_error(
        self,
        session_id: str,
        error_message: str,
        node_id: Optional[str] = None,
        group_id: Optional[str] = None,
        error_type: Optional[str] = None,
        recoverable: bool = True,
        retry_after: Optional[int] = None,
    ) -> int:
        """
        Broadcast error event to WebSocket clients.

        [Source: docs/stories/33.2.story.md - AC2, AC5]

        Args:
            session_id: Session ID to broadcast to
            error_message: Error message
            node_id: Failed node ID if applicable
            group_id: Parent group ID
            error_type: Error type classification
            recoverable: Whether error is recoverable
            retry_after: Seconds to wait before retry

        Returns:
            int: Number of clients that received the error
        """
        event = create_ws_error_event(
            task_id=session_id,
            error_message=error_message,
            node_id=node_id,
            group_id=group_id,
            error_type=error_type,
            recoverable=recoverable,
            retry_after=retry_after,
        )
        return await self._connection_manager.broadcast_to_session(session_id, event)

    async def notify_session_complete(
        self,
        session_id: str,
        status: ParallelTaskStatus,
        total_duration: float,
        success_count: int,
        failure_count: int,
    ) -> int:
        """
        Broadcast session completion event and close connections.

        [Source: docs/stories/33.2.story.md - AC2, AC3]

        Args:
            session_id: Session ID to broadcast to
            status: Final session status
            total_duration: Total duration in seconds
            success_count: Successful node count
            failure_count: Failed node count

        Returns:
            int: Number of clients that received the completion event
        """
        event = create_ws_complete_event(
            task_id=session_id,
            status=status,
            total_duration=total_duration,
            success_count=success_count,
            failure_count=failure_count,
        )
        sent_count = await self._connection_manager.broadcast_to_session(session_id, event)

        # AC3: Auto-close connection when session completes
        await self._connection_manager.close_session_connections(
            session_id,
            reason="Session completed"
        )

        return sent_count

    def get_connection_count(self, session_id: str) -> int:
        """
        Get number of WebSocket connections for a session.

        Args:
            session_id: Session ID to check

        Returns:
            int: Number of active connections
        """
        return self._connection_manager.get_connection_count(session_id)
