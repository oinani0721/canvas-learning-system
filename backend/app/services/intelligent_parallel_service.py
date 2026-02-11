# Canvas Learning System - Intelligent Parallel Service
# EPIC-33 P0 Fix: Replace all STUB methods with real service calls
"""
IntelligentParallelService - Service layer for parallel batch processing.

Connects REST endpoints to real backend services:
- IntelligentGroupingService for canvas analysis (Story 33.4)
- SessionManager for session lifecycle (Story 33.3)
- BatchOrchestrator for parallel execution (Story 33.6)
- AgentService for single-node agent calls
- AgentRoutingEngine for content-based routing (Story 33.5)
- WebSocket broadcasting via ConnectionManager (Story 33.2)
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from app.services.intelligent_grouping_service import IntelligentGroupingService
    from app.services.session_manager import SessionManager
    from app.services.batch_orchestrator import BatchOrchestrator
    from app.services.agent_service import AgentService
    from app.services.agent_routing_engine import AgentRoutingEngine
    from app.services.canvas_service import CanvasService

from app.models.intelligent_parallel_models import (
    CancelResponse,
    GroupExecuteConfig,
    GroupPriority,
    GroupProgress,
    GroupStatus,
    IntelligentParallelResponse,
    NodeError,
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

    EPIC-33 P0 Fix: All methods now delegate to real services instead of
    returning STUB/hardcoded data.
    """

    def __init__(
        self,
        grouping_service: Optional["IntelligentGroupingService"] = None,
        session_manager: Optional["SessionManager"] = None,
        batch_orchestrator: Optional["BatchOrchestrator"] = None,
        agent_service: Optional["AgentService"] = None,
        routing_engine: Optional["AgentRoutingEngine"] = None,
        connection_manager: Optional[ConnectionManager] = None,
        canvas_service: Optional["CanvasService"] = None,
    ) -> None:
        """
        Initialize service with all required dependencies.

        Args:
            grouping_service: IntelligentGroupingService for canvas analysis
            session_manager: SessionManager for session lifecycle
            batch_orchestrator: BatchOrchestrator for parallel execution
            agent_service: AgentService for single-node agent calls
            routing_engine: AgentRoutingEngine for content-based routing
            connection_manager: ConnectionManager for WebSocket broadcasting
            canvas_service: CanvasService for reading node content (Story 33.10)
        """
        self._grouping_service = grouping_service
        self._session_manager = session_manager
        self._batch_orchestrator = batch_orchestrator
        self._agent_service = agent_service
        self._routing_engine = routing_engine
        self._connection_manager = connection_manager or get_connection_manager()
        self._canvas_service = canvas_service

        # Log dependency injection status
        if self._grouping_service is None:
            logger.warning(
                "IntelligentParallelService: grouping_service not injected — "
                "analyze_canvas() will fail"
            )
        if self._session_manager is None:
            logger.warning(
                "IntelligentParallelService: session_manager not injected — "
                "start_batch_session()/get_session_status() will fail"
            )
        if self._batch_orchestrator is None:
            logger.warning(
                "IntelligentParallelService: batch_orchestrator not injected — "
                "batch execution will fail"
            )
        if self._agent_service is None:
            logger.warning(
                "IntelligentParallelService: agent_service not injected — "
                "retry_single_node() will fail"
            )
        if self._routing_engine is None:
            logger.warning(
                "IntelligentParallelService: routing_engine not injected — "
                "auto-routing disabled for retry_single_node()"
            )

        logger.info("IntelligentParallelService initialized with real service dependencies")

    async def analyze_canvas(
        self,
        canvas_path: str,
        target_color: str = "3",
        max_groups: Optional[int] = None,
        min_nodes_per_group: int = 2,
    ) -> IntelligentParallelResponse:
        """
        Analyze canvas and return node groupings with agent recommendations.

        Delegates to IntelligentGroupingService.analyze_canvas() which uses
        TF-IDF + K-Means clustering.

        Args:
            canvas_path: Path to canvas file
            target_color: Target node color (1-6, default "3" for purple)
            max_groups: Maximum number of groups (optional)
            min_nodes_per_group: Minimum nodes per group

        Returns:
            IntelligentParallelResponse with grouped nodes

        Raises:
            FileNotFoundError: If canvas file not found
            RuntimeError: If grouping_service not injected
        """
        logger.info(
            f"analyze_canvas called: path={canvas_path}, color={target_color}"
        )

        if self._grouping_service is None:
            raise RuntimeError(
                "grouping_service not injected — cannot analyze canvas. "
                "Check dependencies.py EPIC-33 service registration."
            )

        return await self._grouping_service.analyze_canvas(
            canvas_path=canvas_path,
            target_color=target_color,
            max_groups=max_groups,
            min_nodes_per_group=min_nodes_per_group,
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

        Creates a real session via SessionManager, then launches
        BatchOrchestrator execution in a background task.

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
            RuntimeError: If required services not injected
        """
        logger.info(
            f"start_batch_session called: path={canvas_path}, groups={len(groups)}"
        )

        if self._session_manager is None:
            raise RuntimeError(
                "session_manager not injected — cannot create session. "
                "Check dependencies.py EPIC-33 service registration."
            )

        if not groups:
            raise ValueError("At least one group must be specified")

        # Calculate total nodes
        total_nodes = sum(len(g.node_ids) for g in groups)

        # Create real session via SessionManager
        session_id = await self._session_manager.create_session(
            canvas_path=canvas_path,
            node_count=total_nodes,
            metadata={
                "groups": [g.model_dump() if hasattr(g, 'model_dump') else {"group_id": g.group_id, "agent_type": g.agent_type, "node_ids": g.node_ids} for g in groups],
                "max_concurrent": max_concurrent or 12,
                "timeout": timeout,
            }
        )

        now = datetime.now()
        logger.info(f"Session created via SessionManager: {session_id}")

        # Launch batch execution in background if orchestrator available
        if self._batch_orchestrator is not None:
            # Convert GroupExecuteConfig to BatchOrchestrator's GroupConfig
            from app.services.batch_orchestrator import GroupConfig

            orchestrator_groups = [
                GroupConfig(
                    group_id=g.group_id,
                    agent_type=g.agent_type,
                    node_ids=list(g.node_ids),
                )
                for g in groups
            ]

            asyncio.create_task(
                self._run_batch_in_background(
                    session_id=session_id,
                    canvas_path=canvas_path,
                    groups=orchestrator_groups,
                    timeout=timeout,
                )
            )
            logger.info(f"Batch execution launched as background task for session {session_id}")
        else:
            logger.warning(
                f"batch_orchestrator not injected — session {session_id} created "
                "but execution will NOT start. Check dependencies.py."
            )

        return SessionResponse(
            session_id=session_id,
            status=ParallelTaskStatus.pending,
            total_groups=len(groups),
            total_nodes=total_nodes,
            created_at=now,
            estimated_completion=now + timedelta(seconds=timeout // 2),
            websocket_url=None,  # Story 33.10 Fix #4: let frontend build from window.location
        )

    async def _run_batch_in_background(
        self,
        session_id: str,
        canvas_path: str,
        groups: list,
        timeout: int,
    ) -> None:
        """
        Run batch orchestrator in background, catching all exceptions.

        Args:
            session_id: Session ID
            canvas_path: Canvas file path
            groups: List of GroupConfig for orchestrator
            timeout: Timeout in seconds
        """
        try:
            await self._batch_orchestrator.start_batch_session(
                session_id=session_id,
                canvas_path=canvas_path,
                groups=groups,
                timeout=timeout,
            )
        except Exception as e:
            logger.error(
                f"Background batch execution failed for session {session_id}: {e}"
            )
            # Notify WebSocket clients of failure
            await self.notify_error(
                session_id=session_id,
                error_message=str(e),
                error_type=type(e).__name__,
                recoverable=False,
            )

    async def get_session_status(
        self,
        session_id: str,
    ) -> Optional[ProgressResponse]:
        """
        Get current progress status for a batch session.

        Reads real session state from SessionManager.

        Args:
            session_id: Session ID

        Returns:
            ProgressResponse or None if session not found
        """
        logger.info(f"get_session_status called: session_id={session_id}")

        if self._session_manager is None:
            logger.warning(
                "session_manager not injected — cannot get session status"
            )
            return None

        try:
            session = await self._session_manager.get_session(session_id)
        except Exception:
            # SessionNotFoundError or similar
            return None

        # Map SessionStatus to ParallelTaskStatus
        status_map = {
            "pending": ParallelTaskStatus.pending,
            "running": ParallelTaskStatus.running,
            "completed": ParallelTaskStatus.completed,
            "failed": ParallelTaskStatus.failed,
            "cancelled": ParallelTaskStatus.cancelled,
            "partial_failure": ParallelTaskStatus.partial_failure,
        }
        session_status_value = session.status.value
        parallel_status = status_map.get(
            session_status_value, ParallelTaskStatus.pending
        )

        # Build progress percent
        total_nodes = session.node_count
        completed_nodes = session.completed_nodes
        failed_nodes = session.failed_nodes
        progress_percent = (
            int(completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
        )

        # Story 33.10 Fix #3: Build group progress from session.node_results
        groups_progress = []
        metadata = session.metadata
        node_results = session.node_results
        if metadata and "groups" in metadata:
            for g_meta in metadata["groups"]:
                group_id = g_meta.get("group_id", "unknown")
                agent_type = g_meta.get("agent_type", "unknown")
                node_ids = g_meta.get("node_ids", [])
                node_ids_set = set(node_ids)

                # Count completed/failed from actual results
                group_completed = 0
                group_errors: List[Any] = []
                group_results_list: List[Any] = []
                for nid in node_ids:
                    if nid in node_results:
                        nr = node_results[nid]
                        nr_status = nr.status
                        if nr_status == "success":
                            group_completed += 1
                            # Build NodeResult for the response model
                            file_path = nr.result
                            group_results_list.append(
                                NodeResult(
                                    node_id=nid,
                                    file_path=str(file_path) if file_path else None,
                                )
                            )
                        elif nr_status == "failed":
                            error_msg = nr.error
                            group_errors.append(
                                NodeError(
                                    node_id=nid,
                                    error_message=error_msg or "Unknown error",
                                )
                            )

                # Determine group status
                total_in_group = len(node_ids)
                processed = group_completed + len(group_errors)
                if processed == 0:
                    group_status = GroupStatus.pending
                elif processed < total_in_group:
                    group_status = GroupStatus.running
                elif len(group_errors) > 0 and group_completed == 0:
                    group_status = GroupStatus.failed
                elif len(group_errors) > 0:
                    group_status = GroupStatus.failed  # partial failure
                else:
                    group_status = GroupStatus.completed

                groups_progress.append(
                    GroupProgress(
                        group_id=group_id,
                        status=group_status,
                        agent_type=agent_type,
                        completed_nodes=group_completed,
                        total_nodes=total_in_group,
                        results=group_results_list,
                        errors=group_errors,
                    )
                )

        # Build performance metrics if completed
        perf_metrics = None
        if parallel_status in (
            ParallelTaskStatus.completed,
            ParallelTaskStatus.partial_failure,
        ):
            started = session.started_at
            ended = session.completed_at
            if started and ended:
                duration = (ended - started).total_seconds()
                perf_metrics = PerformanceMetrics(
                    total_duration_seconds=duration,
                    average_duration_per_node=(
                        duration / completed_nodes if completed_nodes > 0 else 0
                    ),
                    parallel_efficiency=0.0,
                    peak_concurrent=0,
                )

        return ProgressResponse(
            session_id=session_id,
            status=parallel_status,
            total_groups=len(groups_progress) if groups_progress else 0,
            total_nodes=total_nodes,
            completed_groups=sum(
                1 for g in groups_progress
                if g.status in (GroupStatus.completed, GroupStatus.failed)
            ),
            completed_nodes=completed_nodes,
            failed_nodes=failed_nodes,
            progress_percent=progress_percent,
            created_at=session.created_at,
            started_at=session.started_at,
            completed_at=session.completed_at,
            groups=groups_progress,
            performance_metrics=perf_metrics,
        )

    async def cancel_session(
        self,
        session_id: str,
    ) -> Optional[CancelResponse]:
        """
        Cancel an in-progress batch processing session.

        Delegates to BatchOrchestrator.cancel_session() for graceful cancellation.

        Args:
            session_id: Session ID to cancel

        Returns:
            CancelResponse or None if session not found

        Raises:
            ValueError: If session already completed or cancelled
        """
        logger.info(f"cancel_session called: session_id={session_id}")

        if self._session_manager is None:
            logger.warning("session_manager not injected — cannot cancel session")
            return None

        # Check session exists
        try:
            session = await self._session_manager.get_session(session_id)
        except Exception:
            return None

        # Check if already terminal
        session_status_value = session.status.value
        if session_status_value in ("completed", "cancelled", "failed"):
            raise ValueError(
                f"Session already {session_status_value}, cannot cancel"
            )

        completed_count = session.completed_nodes

        # Use batch orchestrator for graceful cancellation if available
        if self._batch_orchestrator is not None:
            result = await self._batch_orchestrator.cancel_session(session_id)
            if result and result.get("success"):
                completed_count = result.get("completed_count", completed_count)

        # Always transition session state to CANCELLED immediately
        # (batch_orchestrator.cancel_session only sets a flag; we must also
        # persist the terminal state so GET /progress reflects it right away)
        try:
            from app.models.session_models import SessionStatus
            await self._session_manager.transition_state(
                session_id, SessionStatus.CANCELLED
            )
        except Exception as e:
            logger.warning(f"Session cancel: state transition failed: {e}")

        logger.info(
            f"Session cancelled: {session_id}, completed_count={completed_count}"
        )

        return CancelResponse(
            success=True,
            message="Task cancelled successfully",
            completed_count=completed_count,
        )

    async def _get_node_content(
        self,
        canvas_path: str,
        node_id: str,
    ) -> Optional[str]:
        """
        Get actual node content from canvas_service.

        Story 33.10 Fix #2: Fetches real node content instead of using
        a placeholder prompt string.

        Args:
            canvas_path: Path to the canvas file
            node_id: ID of the node to retrieve

        Returns:
            Node content string if available, None otherwise
        """
        if self._canvas_service is None:
            logger.warning(
                "[Story 33.10] canvas_service not injected — "
                "cannot fetch real node content"
            )
            return None

        try:
            canvas_name = Path(canvas_path).stem
            canvas_data = await self._canvas_service.read_canvas(canvas_name)
            if not canvas_data:
                logger.warning(f"[Story 33.10] Canvas not found: {canvas_name}")
                return None

            nodes = canvas_data.get("nodes", [])
            target_node = None
            for node in nodes:
                if node.get("id") == node_id:
                    target_node = node
                    break

            if target_node is None:
                logger.warning(
                    f"[Story 33.10] Node not found: {node_id} in {canvas_name}"
                )
                return None

            from .context_enrichment_service import get_node_content

            vault_path = ""
            if self._canvas_service and hasattr(self._canvas_service, 'canvas_base_path'):
                vault_path = self._canvas_service.canvas_base_path or ""

            # Wrap sync file I/O in thread to avoid blocking event loop
            # (get_node_content reads files synchronously for "file" type nodes)
            content = await asyncio.to_thread(get_node_content, target_node, vault_path)
            if content:
                logger.debug(
                    f"[Story 33.10] Retrieved content for node {node_id}: "
                    f"{len(content)} chars"
                )
            return content

        except Exception as e:
            logger.warning(
                f"[Story 33.10] Failed to get node content (non-blocking): {e}"
            )
            return None

    async def retry_single_node(
        self,
        node_id: str,
        agent_type: str,
        canvas_path: str,
    ) -> SingleAgentResponse:
        """
        Execute single agent on a specific node.

        Uses AgentService.call_agent() for real agent invocation.
        Story 33.10 Fix #2: Fetches real node content from canvas file
        instead of using a meaningless placeholder string.

        Args:
            node_id: Node ID to process
            agent_type: Agent type to use
            canvas_path: Canvas file path

        Returns:
            SingleAgentResponse with result

        Raises:
            FileNotFoundError: If node or canvas not found
            RuntimeError: If agent_service not injected
        """
        logger.info(
            f"retry_single_node called: node={node_id}, agent={agent_type}"
        )

        if self._agent_service is None:
            raise RuntimeError(
                "agent_service not injected — cannot execute single node. "
                "Check dependencies.py EPIC-33 service registration."
            )

        try:
            # Story 33.10 Fix #2: Fetch real node content from canvas
            node_content = await self._get_node_content(canvas_path, node_id)
            if node_content:
                prompt = node_content
            else:
                logger.warning(
                    f"[Story 33.10] Could not fetch content for node {node_id}, "
                    "using fallback prompt"
                )
                prompt = f"Process node {node_id} from canvas {canvas_path}"

            # Call real agent
            result = await self._agent_service.call_agent(
                agent_type=agent_type,
                prompt=prompt,
            )

            if result.success:
                file_path = result.file_path if hasattr(result, 'file_path') else None
                if not file_path:
                    file_path = f"{canvas_path.replace('.canvas', '')}/{node_id}-{agent_type}.md"

                return SingleAgentResponse(
                    node_id=node_id,
                    file_path=file_path,
                    status=SingleAgentStatus.success,
                    error_message=None,
                )
            else:
                error_msg = result.error if hasattr(result, 'error') else "Agent execution failed"
                return SingleAgentResponse(
                    node_id=node_id,
                    file_path=None,
                    status=SingleAgentStatus.failed,
                    error_message=error_msg,
                )
        except Exception as e:
            logger.error(f"retry_single_node failed: {e}")
            return SingleAgentResponse(
                node_id=node_id,
                file_path=None,
                status=SingleAgentStatus.failed,
                error_message=str(e),
            )

    # ═══════════════════════════════════════════════════════════════════════════════
    # WebSocket Integration Methods (Story 33.2 - kept as-is, real implementations)
    # ═══════════════════════════════════════════════════════════════════════════════

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Uses SessionManager for real session lookup.

        Args:
            session_id: Session ID to check

        Returns:
            bool: True if session exists
        """
        if self._session_manager is None:
            logger.warning("session_manager not injected — session_exists returns False")
            return False

        try:
            await self._session_manager.get_session(session_id)
            return True
        except Exception:
            return False

    async def notify_progress(
        self,
        session_id: str,
        progress_percent: int,
        completed_nodes: int,
        total_nodes: int,
    ) -> int:
        """
        Broadcast progress update to WebSocket clients.

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

        # Auto-close connection when session completes
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
