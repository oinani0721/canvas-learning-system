# Canvas Learning System - Session Management Models
# Story 33.3: Session Management Service
# Source: specs/api/parallel-api.openapi.yml:140-146
# Source: specs/data/parallel-task.schema.json
"""
Session Management Models for batch processing sessions.

This module defines data models for tracking batch processing session lifecycle:
- SessionStatus: State machine states (pending → running → completed/failed/cancelled)
- SessionInfo: Session metadata and progress tracking
- NodeResult: Per-node execution results within a session
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SessionStatus(str, Enum):
    """
    Session状态枚举
    [Source: specs/api/parallel-api.openapi.yml:140-146]
    [Source: specs/data/parallel-task.schema.json:24-27]

    State Machine:
    - pending → running (session started)
    - running → completed (all nodes succeeded)
    - running → partial_failure (some nodes failed)
    - running → failed (all nodes failed)
    - running → cancelled (user cancelled)
    - pending → cancelled (cancelled before start)
    """

    PENDING = "pending"                    # 等待执行
    RUNNING = "running"                    # 正在执行
    COMPLETED = "completed"                # 全部成功
    PARTIAL_FAILURE = "partial_failure"    # 部分失败
    FAILED = "failed"                      # 全部失败
    CANCELLED = "cancelled"                # 已取消

    @property
    def is_terminal(self) -> bool:
        """
        Check if this is a terminal state (no more transitions allowed).

        Returns:
            bool: True if session is in a final state
        """
        return self in {
            SessionStatus.COMPLETED,
            SessionStatus.PARTIAL_FAILURE,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        }

    @property
    def allows_progress_update(self) -> bool:
        """
        Check if progress can be updated in this state.

        Returns:
            bool: True if progress updates are allowed
        """
        return self == SessionStatus.RUNNING


@dataclass
class NodeResult:
    """
    Per-node execution result within a session.
    [Source: Story 33.3 AC:8 - Per-node result storage]

    Attributes:
        node_id: Unique identifier for the node
        status: Execution status (success/failed/skipped)
        result: Execution output (if success)
        error: Error message (if failed)
        started_at: When node execution started
        completed_at: When node execution completed
        execution_time_ms: Execution duration in milliseconds
    """

    node_id: str
    status: str  # "success", "failed", "skipped"
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        [Source: Story 33.3 Task 1.4]

        Returns:
            Dict representation of node result
        """
        return {
            "node_id": self.node_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class SessionInfo:
    """
    Session metadata and state tracking.
    [Source: Story 33.3 AC:6 - Session metadata storage]
    [Source: specs/data/parallel-task.schema.json]

    Attributes:
        session_id: Unique UUID4 identifier
        canvas_path: Path to the Canvas file being processed
        node_count: Total number of nodes to process
        status: Current session status
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        started_at: When processing started
        completed_at: When processing completed
        progress_percent: Processing progress (0-100)
        completed_nodes: Count of successfully completed nodes
        failed_nodes: Count of failed nodes
        node_results: Per-node execution results
        error_message: Overall error message (if any)
        metadata: Additional session metadata
    """

    session_id: str
    canvas_path: str
    node_count: int
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: float = 0.0
    completed_nodes: int = 0
    failed_nodes: int = 0
    node_results: Dict[str, NodeResult] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        [Source: Story 33.3 Task 1.4]

        Returns:
            Dict representation of session info
        """
        return {
            "session_id": self.session_id,
            "canvas_path": self.canvas_path,
            "node_count": self.node_count,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress_percent": self.progress_percent,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "node_results": {
                node_id: result.to_dict()
                for node_id, result in self.node_results.items()
            },
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


# Valid state transitions for the session state machine
VALID_TRANSITIONS: Dict[SessionStatus, List[SessionStatus]] = {
    SessionStatus.PENDING: [SessionStatus.RUNNING, SessionStatus.CANCELLED],
    SessionStatus.RUNNING: [
        SessionStatus.COMPLETED,
        SessionStatus.PARTIAL_FAILURE,
        SessionStatus.FAILED,
        SessionStatus.CANCELLED,
    ],
    SessionStatus.COMPLETED: [],      # Terminal state
    SessionStatus.PARTIAL_FAILURE: [],  # Terminal state
    SessionStatus.FAILED: [],          # Terminal state
    SessionStatus.CANCELLED: [],       # Terminal state
}


def is_valid_transition(from_status: SessionStatus, to_status: SessionStatus) -> bool:
    """
    Check if a state transition is valid.
    [Source: Story 33.3 AC:2 - State machine implementation]

    Args:
        from_status: Current session status
        to_status: Target session status

    Returns:
        bool: True if transition is valid
    """
    return to_status in VALID_TRANSITIONS.get(from_status, [])
