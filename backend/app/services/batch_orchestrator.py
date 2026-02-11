# Canvas Learning System - Batch Processing Orchestrator
# Story 33.6: Batch Processing Orchestrator
# [Source: docs/stories/33.6.story.md]
"""
BatchOrchestrator - Connects AsyncExecutionEngine to API endpoints.

This orchestrator enables parallel execution of multiple agents across
Canvas nodes with:
- AC1: Session lifecycle management (pending → running → completed/failed)
- AC2: Semaphore(12) concurrency control
- AC3: Real-time progress broadcasting via callbacks
- AC4: Partial failure handling with graceful error recovery
- AC5: Result aggregation with performance metrics
- AC6: Fire-and-forget memory write integration (Story 30.4)

Architecture References:
- [Source: docs/architecture/decisions/0004-async-execution-engine.md]
- [Source: docs/architecture/decisions/ADR-006-REALTIME-COMMUNICATION-SSE-HTTP.md]
"""

import asyncio
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..models.session_models import (
    NodeResult,
    SessionInfo,
    SessionStatus,
)
from .session_manager import (
    SessionManager,
    SessionNotFoundError,
    InvalidStateTransitionError,
)

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# [Source: docs/architecture/decisions/0004-async-execution-engine.md#L56-L68]
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_MAX_CONCURRENT = 12  # ADR-0004: Max 12 concurrent agents
DEFAULT_TIMEOUT_SECONDS = 600  # 10 minutes default timeout
PROGRESS_UPDATE_INTERVAL = 0.5  # 500ms per ADR-006


# ═══════════════════════════════════════════════════════════════════════════════
# Event Types for Progress Broadcasting
# [Source: specs/api/parallel-api.openapi.yml#L643-L676]
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressEventType(str, Enum):
    """Progress event types for WebSocket/SSE broadcasting."""
    PROGRESS_UPDATE = "progress_update"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    GROUP_COMPLETED = "group_completed"
    SESSION_COMPLETED = "session_completed"
    ERROR = "error"
    CANCELLED = "cancelled"


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes for Orchestration
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GroupConfig:
    """
    Configuration for a node group to be processed.
    [Source: specs/api/parallel-api.openapi.yml#L399-L412]
    """
    group_id: str
    agent_type: str
    node_ids: List[str]
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class NodeExecutionResult:
    """Result of executing an agent on a single node."""
    node_id: str
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[str] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    execution_time_ms: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class GroupExecutionResult:
    """Result of executing a group of nodes."""
    group_id: str
    agent_type: str
    status: str  # completed, failed, partial_failure
    node_results: List[NodeExecutionResult] = field(default_factory=list)
    completed_count: int = 0
    failed_count: int = 0


@dataclass
class PerformanceMetrics:
    """
    Performance metrics for batch execution.
    [Source: specs/api/parallel-api.openapi.yml#L555-L574]
    """
    total_duration_seconds: float = 0.0
    average_duration_per_node: float = 0.0
    parallel_efficiency: float = 0.0
    peak_concurrent: int = 0
    sequential_time_estimate: float = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# Progress Event Data Class
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ProgressEvent:
    """Progress event for broadcasting."""
    event_type: ProgressEventType
    session_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "type": self.event_type.value,
            "task_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BatchOrchestrator Class
# [Source: Story 33.6 Task 1]
# ═══════════════════════════════════════════════════════════════════════════════

class BatchOrchestrator:
    """
    Batch Processing Orchestrator for parallel agent execution.

    Connects the AsyncExecutionEngine pattern to API endpoints,
    managing concurrent agent calls with proper error handling,
    progress broadcasting, and memory persistence.

    [Source: docs/stories/33.6.story.md]
    [Source: docs/architecture/decisions/0004-async-execution-engine.md]
    """

    def __init__(
        self,
        session_manager: SessionManager,
        agent_service: Any,  # AgentService - avoid circular import
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        progress_callback: Optional[Callable[[ProgressEvent], None]] = None,
        canvas_service: Optional[Any] = None,  # CanvasService - optional for node content
        vault_path: Optional[str] = None,  # Vault path for file node content extraction
        routing_engine: Optional[Any] = None,  # AgentRoutingEngine for auto-routing
    ):
        """
        Initialize BatchOrchestrator.

        Args:
            session_manager: SessionManager instance for session lifecycle
            agent_service: AgentService instance for agent calls
            max_concurrent: Maximum concurrent executions (default: 12)
            progress_callback: Optional callback for progress events
            canvas_service: Optional CanvasService for fetching real node content (QA-002)
            vault_path: Optional vault path for file node content extraction
            routing_engine: Optional AgentRoutingEngine for auto-routing when agent_type unspecified

        [Source: Story 33.6 Task 1.2]
        [QA-002: Added canvas_service for production node content retrieval]
        [EPIC-33 P0: Added routing_engine for content-based agent routing]
        """
        self.session_manager = session_manager
        self.agent_service = agent_service
        self.max_concurrent = max_concurrent
        self.progress_callback = progress_callback
        self.canvas_service = canvas_service
        self.vault_path = vault_path
        self.routing_engine = routing_engine

        if self.routing_engine is None:
            logger.warning(
                "routing_engine_not_injected",
                detail="auto-routing disabled, will use agent_type as-is",
            )

        # AC2: Semaphore for concurrency control
        # [Source: docs/architecture/decisions/0004-async-execution-engine.md#L56-L68]
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Cancellation flag per session
        self._cancel_requested: Dict[str, bool] = {}

        # Peak concurrent tracking
        self._current_concurrent = 0
        self._peak_concurrent = 0
        self._concurrent_lock = asyncio.Lock()

        logger.info("batch_orchestrator_initialized", max_concurrent=max_concurrent)

    # ═══════════════════════════════════════════════════════════════════════════
    # Task 1: Session Validation and Startup
    # [Source: Story 33.6 AC:1]
    # ═══════════════════════════════════════════════════════════════════════════

    async def _validate_session(self, session_id: str) -> SessionInfo:
        """
        Validate session exists and is in pending state.

        Args:
            session_id: Session ID to validate

        Returns:
            SessionInfo: The validated session

        Raises:
            SessionNotFoundError: If session not found
            InvalidStateTransitionError: If session not in pending state

        [Source: Story 33.6 Task 1.5]
        """
        try:
            session = await self.session_manager.get_session(session_id)
        except SessionNotFoundError:
            logger.error(f"[Story 33.6] Session not found: {session_id}")
            raise

        if session.status != SessionStatus.PENDING:
            logger.error(
                f"[Story 33.6] Session {session_id} is in {session.status.value}, "
                "expected pending"
            )
            raise InvalidStateTransitionError(
                session.status,
                SessionStatus.RUNNING
            )

        return session

    async def start_batch_session(
        self,
        session_id: str,
        canvas_path: str,
        groups: List[GroupConfig],
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> Dict[str, Any]:
        """
        Start executing a batch session.

        Args:
            session_id: Session ID (must exist and be pending)
            canvas_path: Canvas file path
            groups: List of GroupConfig with node assignments
            timeout: Total timeout in seconds

        Returns:
            Dict with execution results and metrics

        [Source: Story 33.6 Task 1.3]
        """
        start_time = datetime.now()
        self._cancel_requested[session_id] = False

        # AC1: Validate session exists and is pending
        session = await self._validate_session(session_id)

        # Transition to running state
        try:
            await self.session_manager.transition_state(
                session_id,
                SessionStatus.RUNNING
            )
        except InvalidStateTransitionError as e:
            logger.error(f"[Story 33.6] Failed to transition session: {e}")
            raise

        logger.info("batch_session_starting", session_id=session_id, group_count=len(groups))

        # Story 30.12 AC-30.12.2: canvas-orchestrator memory write on session start
        try:
            await self._trigger_memory_write(
                session_id=session_id,
                agent_type="canvas-orchestrator",
                canvas_path=canvas_path,
                node_id="session-start",
                result=None,
            )
        except Exception as mem_err:
            logger.warning(f"canvas-orchestrator memory write failed (non-blocking): {mem_err}")

        # Broadcast session started
        await self._broadcast_progress(
            ProgressEventType.PROGRESS_UPDATE,
            session_id,
            {
                "progress_percent": 0,
                "completed_nodes": 0,
                "total_nodes": session.node_count,
                "status": "running",
            }
        )

        try:
            # Execute all groups with timeout
            results = await asyncio.wait_for(
                self._execute_all_groups(session_id, canvas_path, groups),
                timeout=timeout
            )

            # Calculate final results
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Determine final status BEFORE aggregation
            # [FIX: Story 33.6] Calculate status first so it can be included in results
            total_failed = sum(r.failed_count for r in results)
            total_completed = sum(r.completed_count for r in results)

            if self._cancel_requested.get(session_id, False):
                final_status = SessionStatus.CANCELLED
            elif total_failed == 0:
                final_status = SessionStatus.COMPLETED
            elif total_completed == 0:
                final_status = SessionStatus.FAILED
            else:
                final_status = SessionStatus.PARTIAL_FAILURE

            # Aggregate results with determined final_status
            final_result = await self._aggregate_results(
                session_id=session_id,
                groups=groups,
                group_results=results,
                start_time=start_time,
                end_time=end_time,
                final_status=final_status,
            )

            # Update session with final status
            # Guard against race with external cancel_session() which may
            # have already transitioned the session to a terminal state.
            try:
                await self.session_manager.transition_state(
                    session_id,
                    final_status
                )
            except InvalidStateTransitionError:
                logger.warning(
                    "batch_session_transition_skipped",
                    session_id=session_id,
                    target_status=final_status.value,
                    reason="session already in terminal state (likely cancelled externally)",
                )

            # Broadcast completion
            await self._broadcast_progress(
                ProgressEventType.SESSION_COMPLETED,
                session_id,
                {
                    "status": final_status.value,
                    "total_duration": duration,
                    "success_count": total_completed,
                    "failure_count": total_failed,
                }
            )

            logger.info(
                "batch_session_completed",
                session_id=session_id,
                status=final_status.value,
                success_count=total_completed,
                failure_count=total_failed,
            )

            return final_result

        except asyncio.TimeoutError:
            logger.error(f"[Story 33.6] Session {session_id} timed out after {timeout}s")
            try:
                await self.session_manager.transition_state(
                    session_id,
                    SessionStatus.FAILED,
                    error_message=f"Timeout after {timeout} seconds"
                )
            except InvalidStateTransitionError:
                logger.warning(
                    "batch_session_timeout_transition_skipped",
                    session_id=session_id,
                    reason="session already in terminal state (likely cancelled externally)",
                )
            await self._broadcast_progress(
                ProgressEventType.ERROR,
                session_id,
                {
                    "error_type": "TIMEOUT",
                    "message": f"Session timed out after {timeout} seconds",
                    "recoverable": False,
                }
            )
            raise
        except Exception as e:
            logger.exception(f"[Story 33.6] Session {session_id} failed: {e}")
            try:
                await self.session_manager.transition_state(
                    session_id,
                    SessionStatus.FAILED,
                    error_message=str(e)
                )
            except InvalidStateTransitionError:
                logger.warning(
                    "batch_session_error_transition_skipped",
                    session_id=session_id,
                    reason="session already in terminal state (likely cancelled externally)",
                )
            await self._broadcast_progress(
                ProgressEventType.ERROR,
                session_id,
                {
                    "error_type": "EXECUTION_ERROR",
                    "message": str(e),
                    "recoverable": False,
                }
            )
            raise
        finally:
            # Cleanup cancellation flag
            self._cancel_requested.pop(session_id, None)

    # ═══════════════════════════════════════════════════════════════════════════
    # Task 2: Parallel Execution Logic
    # [Source: Story 33.6 AC:2, AC:4]
    # ═══════════════════════════════════════════════════════════════════════════

    async def _execute_all_groups(
        self,
        session_id: str,
        canvas_path: str,
        groups: List[GroupConfig],
    ) -> List[GroupExecutionResult]:
        """
        Execute all groups in parallel using asyncio.gather.

        Args:
            session_id: Session ID for tracking
            canvas_path: Canvas file path
            groups: List of group configurations

        Returns:
            List of GroupExecutionResult

        [Source: Story 33.6 Task 2]
        """
        # AC2: Use asyncio.gather with return_exceptions=True
        # [Source: docs/architecture/decisions/0004-async-execution-engine.md#L114-L149]
        tasks = [
            self._execute_group(session_id, canvas_path, group)
            for group in groups
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results, converting exceptions to failed GroupExecutionResult
        processed_results: List[GroupExecutionResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"[Story 33.6] Group {groups[i].group_id} failed with exception: {result}"
                )
                processed_results.append(GroupExecutionResult(
                    group_id=groups[i].group_id,
                    agent_type=groups[i].agent_type,
                    status="failed",
                    failed_count=len(groups[i].node_ids),
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_group(
        self,
        session_id: str,
        canvas_path: str,
        group: GroupConfig,
    ) -> GroupExecutionResult:
        """
        Execute all nodes in a single group.

        Args:
            session_id: Session ID for tracking
            canvas_path: Canvas file path
            group: Group configuration with node_ids and agent_type

        Returns:
            GroupExecutionResult with all node results

        [Source: Story 33.6 Task 2.1]
        """
        logger.debug(
            f"[Story 33.6] Starting group {group.group_id} "
            f"with {len(group.node_ids)} nodes using {group.agent_type}"
        )

        # Execute all nodes in parallel within this group
        tasks = [
            self._execute_node_with_semaphore(
                session_id=session_id,
                canvas_path=canvas_path,
                node_id=node_id,
                agent_type=group.agent_type,
            )
            for node_id in group.node_ids
        ]

        # AC2, AC4: gather with return_exceptions for partial failure support
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process node results
        node_results: List[NodeExecutionResult] = []
        completed_count = 0
        failed_count = 0

        for i, result in enumerate(results):
            node_id = group.node_ids[i]

            if isinstance(result, Exception):
                node_results.append(NodeExecutionResult(
                    node_id=node_id,
                    success=False,
                    error_message=str(result),
                    error_type=type(result).__name__,
                ))
                failed_count += 1
            else:
                node_results.append(result)
                if result.success:
                    completed_count += 1
                else:
                    failed_count += 1

        # Determine group status
        if failed_count == 0:
            status = "completed"
        elif completed_count == 0:
            status = "failed"
        else:
            status = "partial_failure"

        # Broadcast group completed
        await self._broadcast_progress(
            ProgressEventType.GROUP_COMPLETED,
            session_id,
            {
                "group_id": group.group_id,
                "agent_type": group.agent_type,
                "status": status,
                "completed_nodes": completed_count,
                "failed_nodes": failed_count,
            }
        )

        logger.info(
            "group_completed",
            session_id=session_id,
            group_id=group.group_id,
            status=status,
            completed=completed_count,
            failed=failed_count,
        )

        return GroupExecutionResult(
            group_id=group.group_id,
            agent_type=group.agent_type,
            status=status,
            node_results=node_results,
            completed_count=completed_count,
            failed_count=failed_count,
        )

    async def _execute_node_with_semaphore(
        self,
        session_id: str,
        canvas_path: str,
        node_id: str,
        agent_type: str,
    ) -> NodeExecutionResult:
        """
        Execute agent on a single node with semaphore control.

        Args:
            session_id: Session ID for tracking
            canvas_path: Canvas file path
            node_id: Node ID to process
            agent_type: Agent type to invoke

        Returns:
            NodeExecutionResult

        [Source: Story 33.6 Task 2.2]
        """
        # Check for cancellation before acquiring semaphore
        if self._cancel_requested.get(session_id, False):
            return NodeExecutionResult(
                node_id=node_id,
                success=False,
                error_message="Cancelled",
                error_type="CancellationError",
            )

        # AC2: Acquire semaphore for concurrency control
        async with self.semaphore:
            # Track concurrent executions
            async with self._concurrent_lock:
                self._current_concurrent += 1
                if self._current_concurrent > self._peak_concurrent:
                    self._peak_concurrent = self._current_concurrent

            try:
                return await self._execute_node(
                    session_id=session_id,
                    canvas_path=canvas_path,
                    node_id=node_id,
                    agent_type=agent_type,
                )
            finally:
                async with self._concurrent_lock:
                    self._current_concurrent -= 1

    async def _execute_node(
        self,
        session_id: str,
        canvas_path: str,
        node_id: str,
        agent_type: str,
    ) -> NodeExecutionResult:
        """
        Execute agent on a single node.

        Args:
            session_id: Session ID for tracking
            canvas_path: Canvas file path
            node_id: Node ID to process
            agent_type: Agent type to invoke

        Returns:
            NodeExecutionResult

        [Source: Story 33.6 Task 2.2, Task 7]
        [QA-002: Enhanced to fetch real node content when canvas_service available]
        """
        started_at = datetime.now()

        try:
            # QA-002: Get real node content from canvas_service if available
            node_content = await self._get_node_content(canvas_path, node_id)

            # Construct prompt with actual node content
            if node_content:
                prompt = node_content
            else:
                # Fallback to simple prompt if content unavailable
                prompt = f"Process node {node_id} from canvas {canvas_path}"

            # EPIC-33 P0: Use routing engine if agent_type is unspecified/generic
            effective_agent_type = agent_type
            if self.routing_engine is not None and node_content:
                try:
                    from app.models.agent_routing_models import RoutingRequest
                    routing_req = RoutingRequest(
                        node_id=node_id,
                        node_text=node_content,
                        agent_override=agent_type if agent_type != "auto" else None,
                    )
                    routing_result = self.routing_engine.route_single_node(routing_req)
                    if routing_result and routing_result.confidence >= 0.7:
                        effective_agent_type = routing_result.recommended_agent
                        logger.debug(
                            f"[EPIC-33] Routing engine: {node_id} → "
                            f"{effective_agent_type} (confidence={routing_result.confidence:.2f})"
                        )
                except Exception as e:
                    logger.warning(f"[EPIC-33] Routing engine failed, using original agent_type: {e}")

            # Call agent through agent_service
            result = await self.agent_service.call_agent(
                agent_type=effective_agent_type,
                prompt=prompt,
            )

            completed_at = datetime.now()
            execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

            if result.success:
                # AC6: Fire-and-forget memory write
                await self._trigger_memory_write(
                    session_id=session_id,
                    agent_type=agent_type,
                    canvas_path=canvas_path,
                    node_id=node_id,
                    result=result,
                )

                # Update session with node result
                await self.session_manager.add_node_result(
                    session_id=session_id,
                    node_id=node_id,
                    status="success",
                    result=result.content if hasattr(result, 'content') else None,
                    started_at=started_at,
                    completed_at=completed_at,
                )

                # Broadcast task completed
                await self._broadcast_progress(
                    ProgressEventType.TASK_COMPLETED,
                    session_id,
                    {
                        "node_id": node_id,
                        "agent_type": agent_type,
                        "file_path": result.file_path if hasattr(result, 'file_path') else None,
                        "execution_time_ms": execution_time_ms,
                    }
                )

                return NodeExecutionResult(
                    node_id=node_id,
                    success=True,
                    file_path=result.file_path if hasattr(result, 'file_path') else None,
                    execution_time_ms=execution_time_ms,
                    started_at=started_at,
                    completed_at=completed_at,
                )
            else:
                # Agent returned failure
                error_msg = result.error if hasattr(result, 'error') else "Agent execution failed"

                await self.session_manager.add_node_result(
                    session_id=session_id,
                    node_id=node_id,
                    status="failed",
                    error=error_msg,
                    started_at=started_at,
                    completed_at=completed_at,
                )

                await self._broadcast_progress(
                    ProgressEventType.TASK_FAILED,
                    session_id,
                    {
                        "node_id": node_id,
                        "agent_type": agent_type,
                        "error_message": error_msg,
                    }
                )

                return NodeExecutionResult(
                    node_id=node_id,
                    success=False,
                    error_message=error_msg,
                    execution_time_ms=execution_time_ms,
                    started_at=started_at,
                    completed_at=completed_at,
                )

        except Exception as e:
            completed_at = datetime.now()
            execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)
            error_msg = str(e)

            logger.error(
                f"[Story 33.6] Node {node_id} execution failed: {error_msg}"
            )

            await self.session_manager.add_node_result(
                session_id=session_id,
                node_id=node_id,
                status="failed",
                error=error_msg,
                started_at=started_at,
                completed_at=completed_at,
            )

            await self._broadcast_progress(
                ProgressEventType.TASK_FAILED,
                session_id,
                {
                    "node_id": node_id,
                    "agent_type": agent_type,
                    "error_message": error_msg,
                }
            )

            return NodeExecutionResult(
                node_id=node_id,
                success=False,
                error_message=error_msg,
                error_type=type(e).__name__,
                execution_time_ms=execution_time_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # QA-002: Node Content Retrieval
    # [Source: QA Review 2026-01-31 - Production node content support]
    # ═══════════════════════════════════════════════════════════════════════════

    async def _get_node_content(
        self,
        canvas_path: str,
        node_id: str,
    ) -> Optional[str]:
        """
        Get actual node content from canvas_service.

        This method fetches real node content for production use.
        Falls back gracefully if canvas_service is not configured.

        Args:
            canvas_path: Path to the canvas file
            node_id: ID of the node to retrieve

        Returns:
            Node content string if available, None otherwise

        [QA-002: Added for production node content retrieval]
        """
        if self.canvas_service is None:
            logger.debug(
                f"[Story 33.6] canvas_service not configured, skipping node content fetch"
            )
            return None

        try:
            # Extract canvas name using pathlib (QA-001 pattern)
            canvas_name = Path(canvas_path).stem

            # Read canvas data
            canvas_data = await self.canvas_service.read_canvas(canvas_name)
            if not canvas_data:
                logger.warning(f"[Story 33.6] Canvas not found: {canvas_name}")
                return None

            # Find the node by ID
            nodes = canvas_data.get("nodes", [])
            target_node = None
            for node in nodes:
                if node.get("id") == node_id:
                    target_node = node
                    break

            if target_node is None:
                logger.warning(f"[Story 33.6] Node not found: {node_id} in {canvas_name}")
                return None

            # Extract content based on node type
            # Import get_node_content locally to avoid circular imports
            from .context_enrichment_service import get_node_content

            vault_path = self.vault_path or ""
            content = get_node_content(target_node, vault_path)

            if content:
                logger.debug(
                    f"[Story 33.6] Retrieved content for node {node_id}: {len(content)} chars"
                )
            return content

        except Exception as e:
            logger.warning(
                f"[Story 33.6] Failed to get node content (non-blocking): {e}"
            )
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # Task 3: Progress Broadcasting
    # [Source: Story 33.6 AC:3]
    # ═══════════════════════════════════════════════════════════════════════════

    async def _broadcast_progress(
        self,
        event_type: ProgressEventType,
        session_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Broadcast progress event via callback.

        Args:
            event_type: Type of progress event
            session_id: Session ID
            data: Event data

        [Source: Story 33.6 Task 3]
        """
        if self.progress_callback is None:
            return

        event = ProgressEvent(
            event_type=event_type,
            session_id=session_id,
            data=data,
        )

        try:
            # Callback can be sync or async
            if asyncio.iscoroutinefunction(self.progress_callback):
                await self.progress_callback(event)
            else:
                self.progress_callback(event)
        except Exception as e:
            # Don't let callback errors break execution
            logger.warning(f"[Story 33.6] Progress callback error: {e}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Task 4: Fire-and-Forget Memory Integration
    # [Source: Story 33.6 AC:6]
    # ═══════════════════════════════════════════════════════════════════════════

    async def _trigger_memory_write(
        self,
        session_id: str,
        agent_type: str,
        canvas_path: str,
        node_id: str,
        result: Any,
    ) -> None:
        """
        Trigger fire-and-forget memory write after agent completion.

        This integrates with Story 30.4's memory write pattern,
        ensuring memory writes don't block agent execution.

        Args:
            session_id: Session ID
            agent_type: Agent type that completed
            canvas_path: Canvas file path
            node_id: Node ID that was processed
            result: Agent result

        [Source: Story 33.6 Task 4]
        [Source: backend/app/services/agent_service.py#L2988-L3072]
        [QA-001: Using pathlib.Path for cross-platform path parsing]
        """
        try:
            # QA-001: Extract canvas name using pathlib for cross-platform compatibility
            canvas_name = Path(canvas_path).stem  # Handles both / and \ separators

            # Extract concept from result or use node_id
            concept = node_id  # Fallback
            if hasattr(result, 'content') and result.content:
                concept = result.content[:50] if len(result.content) > 50 else result.content

            # Call agent_service._trigger_memory_write (fire-and-forget)
            # This is already wrapped in try-except and asyncio.create_task
            if hasattr(self.agent_service, '_trigger_memory_write'):
                await self.agent_service._trigger_memory_write(
                    agent_type=agent_type,
                    canvas_name=canvas_name,
                    node_id=node_id,
                    concept=concept,
                )
                logger.debug(
                    f"[Story 33.6] Memory write triggered for {agent_type} on {node_id}"
                )
            else:
                logger.debug(
                    f"[Story 33.6] agent_service doesn't have _trigger_memory_write, skipping"
                )

        except Exception as e:
            # AC6: Memory write failures must NOT block agent execution
            logger.error(
                f"[Story 33.6] Memory write trigger failed (non-blocking): {e}"
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # Task 5: Result Aggregation
    # [Source: Story 33.6 AC:5]
    # ═══════════════════════════════════════════════════════════════════════════

    async def _aggregate_results(
        self,
        session_id: str,
        groups: List[GroupConfig],
        group_results: List[GroupExecutionResult],
        start_time: datetime,
        end_time: datetime,
        final_status: SessionStatus,
    ) -> Dict[str, Any]:
        """
        Aggregate all results and calculate performance metrics.

        Args:
            session_id: Session ID
            groups: Original group configurations
            group_results: Execution results for each group
            start_time: Session start time
            end_time: Session end time
            final_status: The determined final status for the session

        Returns:
            Aggregated results with performance metrics

        [Source: Story 33.6 Task 5]
        """
        total_duration = (end_time - start_time).total_seconds()

        # Count totals
        total_completed = sum(r.completed_count for r in group_results)
        total_failed = sum(r.failed_count for r in group_results)
        total_nodes = total_completed + total_failed

        # Calculate sequential time estimate (sum of all node execution times)
        sequential_time_estimate = 0.0
        for gr in group_results:
            for nr in gr.node_results:
                sequential_time_estimate += nr.execution_time_ms / 1000.0

        # Calculate parallel efficiency
        parallel_efficiency = 0.0
        if total_duration > 0:
            parallel_efficiency = sequential_time_estimate / total_duration

        # Calculate average duration per node
        average_duration = 0.0
        if total_completed > 0:
            average_duration = total_duration / total_completed

        # Build performance metrics
        metrics = PerformanceMetrics(
            total_duration_seconds=total_duration,
            average_duration_per_node=average_duration,
            parallel_efficiency=parallel_efficiency,
            peak_concurrent=self._peak_concurrent,
            sequential_time_estimate=sequential_time_estimate,
        )

        # Reset peak tracking
        self._peak_concurrent = 0

        # Build group status list
        group_statuses = []
        for gr in group_results:
            results_list = []
            errors_list = []
            for nr in gr.node_results:
                if nr.success:
                    results_list.append({
                        "node_id": nr.node_id,
                        "file_path": nr.file_path,
                        "file_size": nr.file_size,
                    })
                else:
                    errors_list.append({
                        "node_id": nr.node_id,
                        "error_message": nr.error_message,
                    })

            group_statuses.append({
                "group_id": gr.group_id,
                "agent_type": gr.agent_type,
                "status": gr.status,
                "completed_nodes": gr.completed_count,
                "total_nodes": gr.completed_count + gr.failed_count,
                "results": results_list,
                "errors": errors_list,
            })

        # Use the passed final_status instead of fetching from session
        # [FIX: Story 33.6] Status is passed in since transition hasn't happened yet

        return {
            "task_id": session_id,
            "status": final_status.value,
            "total_groups": len(groups),
            "total_nodes": total_nodes,
            "completed_nodes": total_completed,
            "failed_nodes": total_failed,
            "progress_percent": 100 if total_nodes > 0 else 0,
            "groups": group_statuses,
            "performance_metrics": {
                "total_duration_seconds": metrics.total_duration_seconds,
                "average_duration_per_node": metrics.average_duration_per_node,
                "parallel_efficiency": metrics.parallel_efficiency,
                "peak_concurrent": metrics.peak_concurrent,
            },
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Task 6: Cancellation Support
    # [Source: Story 33.6 AC:4]
    # ═══════════════════════════════════════════════════════════════════════════

    async def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """
        Request cancellation of a running session.

        Implements graceful cancellation:
        - Sets cancel flag for session
        - Currently running tasks complete
        - Remaining tasks are skipped
        - Returns count of completed tasks before cancellation

        Args:
            session_id: Session ID to cancel

        Returns:
            Dict with cancellation result

        [Source: Story 33.6 Task 6]
        """
        # Check session exists and is cancellable
        try:
            session = await self.session_manager.get_session(session_id)
        except SessionNotFoundError:
            return {
                "success": False,
                "message": f"Session not found: {session_id}",
                "completed_count": 0,
            }

        if session.status.is_terminal:
            return {
                "success": False,
                "message": f"Session already in terminal state: {session.status.value}",
                "completed_count": session.completed_nodes,
            }

        # Set cancellation flag
        self._cancel_requested[session_id] = True

        # Broadcast cancellation
        await self._broadcast_progress(
            ProgressEventType.CANCELLED,
            session_id,
            {
                "status": "cancelled",
                "completed_before_cancel": session.completed_nodes,
            }
        )

        logger.info("cancellation_requested", session_id=session_id)

        return {
            "success": True,
            "message": "Cancellation requested",
            "completed_count": session.completed_nodes,
        }

    def is_cancelled(self, session_id: str) -> bool:
        """
        Check if cancellation has been requested for a session.

        Args:
            session_id: Session ID to check

        Returns:
            bool: True if cancellation requested
        """
        return self._cancel_requested.get(session_id, False)
