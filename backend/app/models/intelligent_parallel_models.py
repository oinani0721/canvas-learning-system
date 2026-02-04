# Canvas Learning System - Intelligent Parallel Processing Models
# Story 33.1: Backend REST Endpoints
# ✅ Verified from specs/api/parallel-api.openapi.yml
# ✅ Verified from specs/data/parallel-task.schema.json
"""
Pydantic Models for Intelligent Parallel Batch Processing API.

All models are derived from the OpenAPI specification:
[Source: specs/api/parallel-api.openapi.yml]
[Source: specs/data/parallel-task.schema.json]
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# [Source: specs/api/parallel-api.openapi.yml#/components/schemas]
# [Source: specs/data/parallel-task.schema.json#/properties/status]
# ═══════════════════════════════════════════════════════════════════════════════

class ParallelTaskStatus(str, Enum):
    """
    Parallel task status enum.

    [Source: specs/data/parallel-task.schema.json#/properties/status]
    """
    pending = "pending"
    running = "running"
    completed = "completed"
    partial_failure = "partial_failure"
    failed = "failed"
    cancelled = "cancelled"


class GroupStatus(str, Enum):
    """
    Individual group status enum.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskStatus/groups/status]
    """
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class GroupPriority(str, Enum):
    """
    Group priority enum.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/NodeGroup/priority]
    """
    urgent = "urgent"
    high = "high"
    medium = "medium"
    low = "low"


class SingleAgentStatus(str, Enum):
    """
    Single agent execution status.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/SingleAgentResponse/status]
    """
    success = "success"
    failed = "failed"


# ═══════════════════════════════════════════════════════════════════════════════
# Request Models
# [Source: specs/api/parallel-api.openapi.yml#/components/schemas]
# ═══════════════════════════════════════════════════════════════════════════════

class IntelligentParallelRequest(BaseModel):
    """
    Request model for intelligent parallel grouping analysis (POST /canvas/intelligent-parallel).

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelAnalyzeRequest]
    """
    canvas_path: str = Field(
        ...,
        description="Canvas file path",
        examples=["离散数学.canvas"]
    )
    target_color: str = Field(
        default="3",
        description="Target node color (default purple). 1=gray, 2=green, 3=purple, 4=red, 5=blue, 6=yellow",
        pattern="^[1-6]$"
    )
    max_groups: Optional[int] = Field(
        None,
        ge=1,
        le=20,
        description="Maximum number of groups (optional, auto-determined if not specified)"
    )
    min_nodes_per_group: int = Field(
        default=2,
        ge=1,
        description="Minimum nodes per group"
    )


class NodeInGroup(BaseModel):
    """
    Node information within a group.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/NodeGroup/nodes]
    """
    node_id: str = Field(..., description="Node ID", examples=["node-001"])
    text: str = Field(..., description="Node text content", examples=["逆否命题 vs 否命题"])


class NodeGroup(BaseModel):
    """
    Node group with recommended agent.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/NodeGroup]
    [Source: specs/data/parallel-task.schema.json#/definitions/NodeGroup]
    """
    group_id: str = Field(..., description="Group ID", examples=["group-1"])
    group_name: str = Field(..., description="Auto-generated group name", examples=["对比类概念"])
    group_emoji: Optional[str] = Field(None, description="Group icon", examples=["📊"])
    nodes: List[NodeInGroup] = Field(..., description="Nodes in this group")
    recommended_agent: str = Field(
        ...,
        description="Recommended agent type",
        examples=["comparison-table"]
    )
    confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Recommendation confidence score",
        examples=[0.85]
    )
    priority: Optional[GroupPriority] = Field(
        None,
        description="Group priority"
    )


class GroupExecuteConfig(BaseModel):
    """
    Group configuration for batch execution (used in confirm request).

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelExecuteRequest/groups]
    """
    group_id: str = Field(..., description="Group ID", examples=["group-1"])
    agent_type: str = Field(..., description="Agent type to use", examples=["comparison-table"])
    node_ids: List[str] = Field(..., description="Node IDs to process", examples=[["node-001", "node-002"]])


class ConfirmRequest(BaseModel):
    """
    Request model for confirming and executing parallel processing (POST /canvas/intelligent-parallel/confirm).

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelExecuteRequest]
    """
    canvas_path: str = Field(..., description="Canvas file path", examples=["离散数学.canvas"])
    groups: List[GroupExecuteConfig] = Field(
        ...,
        description="Group configurations with agent assignments (can override recommendations)"
    )
    max_concurrent: Optional[int] = Field(
        None,
        ge=1,
        le=50,
        description="Maximum concurrent executions (optional, scheduler decides if not specified)"
    )
    timeout: int = Field(
        default=600,
        ge=60,
        le=3600,
        description="Total timeout in seconds"
    )


class SingleAgentRequest(BaseModel):
    """
    Request model for single node agent retry (POST /canvas/single-agent).

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/SingleAgentRequest]
    """
    node_id: str = Field(..., description="Node ID to process", examples=["node-005"])
    agent_type: str = Field(..., description="Agent type", examples=["oral-explanation"])
    canvas_path: str = Field(..., description="Canvas file path", examples=["离散数学.canvas"])


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# [Source: specs/api/parallel-api.openapi.yml#/components/schemas]
# ═══════════════════════════════════════════════════════════════════════════════

class IntelligentParallelResponse(BaseModel):
    """
    Response model for intelligent parallel grouping analysis.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelAnalyzeResponse]
    Story 33.4: Added subject and subject_group_id for multi-subject isolation (AC-33.4.5)
    """
    canvas_path: str = Field(..., description="Canvas file path", examples=["离散数学.canvas"])
    total_nodes: int = Field(..., description="Total target nodes detected", examples=[12])
    groups: List[NodeGroup] = Field(..., description="Grouped nodes with recommendations")
    estimated_duration: Optional[str] = Field(
        None,
        description="Estimated execution time",
        examples=["2分钟"]
    )
    resource_warning: Optional[str] = Field(
        None,
        description="Resource warning if applicable",
        examples=["CPU使用率较高，建议减少并发数"]
    )
    # Story 33.4 AC-33.4.5: Subject isolation fields (依赖30.8)
    subject: Optional[str] = Field(
        None,
        description="Subject extracted from canvas_path using extract_subject_from_canvas_path()",
        examples=["数学"]
    )
    subject_group_id: Optional[str] = Field(
        None,
        description="Subject isolation group_id, format: {subject}:{canvas_name}",
        examples=["数学:离散数学"]
    )
    # Story 33.4 AC-33.4.3: Clustering quality metrics
    silhouette_score: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Clustering quality (Silhouette Score). Recommend re-clustering if < 0.3",
        examples=[0.72]
    )
    recommended_k: Optional[int] = Field(
        None,
        description="Auto-determined optimal number of clusters",
        examples=[4]
    )


class SessionResponse(BaseModel):
    """
    Response model for batch session creation (202 Accepted).

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskCreated]
    """
    task_id: str = Field(
        ...,
        alias="session_id",
        description="Session/Task ID",
        examples=["parallel-20250118-001"]
    )
    status: ParallelTaskStatus = Field(
        default=ParallelTaskStatus.pending,
        description="Initial status"
    )
    total_groups: int = Field(..., description="Total number of groups", examples=[4])
    total_nodes: Optional[int] = Field(None, description="Total number of nodes", examples=[12])
    created_at: datetime = Field(..., description="Creation timestamp")
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated completion time"
    )
    websocket_url: Optional[str] = Field(
        None,
        description="WebSocket URL for progress subscription",
        examples=["ws://localhost:8000/ws/intelligent-parallel/parallel-20250118-001"]
    )

    model_config = ConfigDict(populate_by_name=True)


class NodeResult(BaseModel):
    """
    Result for a processed node.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskStatus/groups/results]
    """
    node_id: str = Field(..., description="Node ID", examples=["node-001"])
    file_path: Optional[str] = Field(
        None,
        description="Generated file path",
        examples=["逆否命题 vs 否命题.md"]
    )
    file_size: Optional[str] = Field(None, description="File size", examples=["3.2KB"])


class NodeError(BaseModel):
    """
    Error information for a failed node.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskStatus/groups/errors]
    """
    node_id: str = Field(..., description="Node ID")
    error_message: str = Field(..., description="Error message")


class GroupProgress(BaseModel):
    """
    Progress information for a group.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskStatus/groups]
    """
    group_id: str = Field(..., description="Group ID", examples=["group-1"])
    status: GroupStatus = Field(..., description="Group status")
    agent_type: str = Field(..., description="Agent type used", examples=["comparison-table"])
    completed_nodes: int = Field(default=0, description="Completed nodes count")
    total_nodes: int = Field(..., description="Total nodes in group")
    results: List[NodeResult] = Field(default_factory=list, description="Generated files")
    errors: List[NodeError] = Field(default_factory=list, description="Error list")


class PerformanceMetrics(BaseModel):
    """
    Performance metrics for completed session.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskStatus/performance_metrics]
    """
    total_duration_seconds: Optional[float] = Field(
        None,
        description="Total duration in seconds",
        examples=[135]
    )
    average_duration_per_node: Optional[float] = Field(
        None,
        description="Average time per node in seconds",
        examples=[11.25]
    )
    parallel_efficiency: Optional[float] = Field(
        None,
        description="Parallel efficiency (speedup ratio)",
        examples=[7.2]
    )
    peak_concurrent: Optional[int] = Field(
        None,
        description="Peak concurrent executions",
        examples=[8]
    )


class ProgressResponse(BaseModel):
    """
    Response model for session progress status (GET /canvas/intelligent-parallel/{session_id}).

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/ParallelTaskStatus]
    """
    task_id: str = Field(
        ...,
        alias="session_id",
        description="Session/Task ID",
        examples=["parallel-20250118-001"]
    )
    status: ParallelTaskStatus = Field(..., description="Current status")
    total_groups: int = Field(..., description="Total groups", examples=[4])
    total_nodes: int = Field(..., description="Total nodes", examples=[12])
    completed_groups: int = Field(default=0, description="Completed groups")
    completed_nodes: int = Field(default=0, description="Completed nodes")
    failed_nodes: int = Field(default=0, description="Failed nodes")
    progress_percent: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Progress percentage"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    groups: List[GroupProgress] = Field(default_factory=list, description="Group progress details")
    performance_metrics: Optional[PerformanceMetrics] = Field(
        None,
        description="Performance metrics (available after completion)"
    )

    model_config = ConfigDict(populate_by_name=True)


class CancelResponse(BaseModel):
    """
    Response model for session cancellation.

    [Source: specs/api/parallel-api.openapi.yml#/paths/cancel/responses/200]
    """
    success: bool = Field(..., description="Whether cancellation succeeded")
    message: str = Field(..., description="Status message", examples=["Task cancelled successfully"])
    completed_count: int = Field(
        default=0,
        description="Number of tasks completed before cancellation"
    )


class SingleAgentResponse(BaseModel):
    """
    Response model for single agent execution.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/SingleAgentResponse]
    """
    node_id: str = Field(..., description="Processed node ID", examples=["node-005"])
    file_path: Optional[str] = Field(
        None,
        description="Generated file path",
        examples=["离散数学/逻辑表达式-explanation.md"]
    )
    status: SingleAgentStatus = Field(..., description="Execution status")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# ═══════════════════════════════════════════════════════════════════════════════
# Error Response Model
# [Source: specs/api/parallel-api.openapi.yml#/components/schemas/Error]
# ═══════════════════════════════════════════════════════════════════════════════

class ParallelErrorResponse(BaseModel):
    """
    Error response model for parallel processing endpoints.

    [Source: specs/api/parallel-api.openapi.yml#/components/schemas/Error]
    """
    error: str = Field(
        ...,
        description="Error type",
        examples=["CanvasNotFoundError"]
    )
    message: str = Field(
        ...,
        description="Error message",
        examples=["Canvas file '离散数学.canvas' not found"]
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket Event Models (Story 33.2)
# [Source: specs/api/parallel-api.openapi.yml#L529-L558]
# [Source: docs/stories/33.2.story.md - AC2]
# ═══════════════════════════════════════════════════════════════════════════════

class WSEventType(str, Enum):
    """
    WebSocket event type enum.

    [Source: specs/api/parallel-api.openapi.yml#L529-L558]
    [Source: docs/architecture/decisions/ADR-007-WEBSOCKET-BATCH-PROCESSING.md]
    """
    progress = "progress"
    group_complete = "group_complete"
    node_complete = "node_complete"
    error = "error"
    complete = "complete"
    ping = "ping"
    connected = "connected"


class WSProgressData(BaseModel):
    """
    Data payload for progress_update event.

    [Source: specs/api/parallel-api.openapi.yml#L536-L538]
    """
    progress_percent: int = Field(..., ge=0, le=100, description="Progress percentage")
    completed_nodes: int = Field(..., ge=0, description="Completed nodes count")
    total_nodes: int = Field(..., ge=1, description="Total nodes count")


class WSGroupCompleteData(BaseModel):
    """
    Data payload for group_complete event.

    [Source: specs/api/parallel-api.openapi.yml#L541-L544]
    """
    group_id: str = Field(..., description="Completed group ID", examples=["group-1"])
    agent_type: str = Field(..., description="Agent type used", examples=["comparison-table"])
    results: List[NodeResult] = Field(default_factory=list, description="Generated files")


class WSNodeCompleteData(BaseModel):
    """
    Data payload for node_complete (task_completed) event.

    [Source: specs/api/parallel-api.openapi.yml#L547-L548]
    """
    node_id: str = Field(..., description="Completed node ID", examples=["node-001"])
    file_path: Optional[str] = Field(None, description="Generated file path")
    file_size: Optional[str] = Field(None, description="File size", examples=["3.2KB"])
    group_id: Optional[str] = Field(None, description="Parent group ID")


class WSErrorData(BaseModel):
    """
    Data payload for error event (task_failed or recoverable error).

    [Source: specs/api/parallel-api.openapi.yml#L551-L553]
    [Source: docs/stories/33.2.story.md - AC2, AC5]
    """
    node_id: Optional[str] = Field(None, description="Failed node ID if applicable")
    error_message: str = Field(..., description="Error message")
    group_id: Optional[str] = Field(None, description="Parent group ID")
    error_type: Optional[str] = Field(None, description="Error type classification")
    recoverable: bool = Field(default=True, description="Whether error is recoverable")
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retry (for reconnection guidance)",
        examples=[5]
    )


class WSCompleteData(BaseModel):
    """
    Data payload for session_completed event.

    [Source: specs/api/parallel-api.openapi.yml#L556-L560]
    """
    status: ParallelTaskStatus = Field(..., description="Final session status")
    total_duration: float = Field(..., description="Total duration in seconds", examples=[135])
    success_count: int = Field(..., ge=0, description="Successful node count")
    failure_count: int = Field(..., ge=0, description="Failed node count")


class WebSocketMessage(BaseModel):
    """
    WebSocket message wrapper with type discriminator.

    All WebSocket messages follow this structure for consistent parsing.

    [Source: specs/api/parallel-api.openapi.yml#L529-L558]
    [Source: docs/stories/33.2.story.md - Task 3]
    """
    type: WSEventType = Field(..., description="Event type")
    task_id: str = Field(..., description="Session/Task ID", examples=["parallel-20250118-001"])
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Event-specific data payload")

    # Note: In Pydantic V2, datetime is automatically serialized to ISO format
    model_config = ConfigDict()


# Type-safe event constructors (Story 33.2 - Task 3)
def create_ws_progress_event(
    task_id: str,
    progress_percent: int,
    completed_nodes: int,
    total_nodes: int,
) -> WebSocketMessage:
    """Create progress update event."""
    return WebSocketMessage(
        type=WSEventType.progress,
        task_id=task_id,
        timestamp=datetime.now(),
        data=WSProgressData(
            progress_percent=progress_percent,
            completed_nodes=completed_nodes,
            total_nodes=total_nodes,
        ).model_dump(),
    )


def create_ws_node_complete_event(
    task_id: str,
    node_id: str,
    file_path: Optional[str] = None,
    file_size: Optional[str] = None,
    group_id: Optional[str] = None,
) -> WebSocketMessage:
    """Create node complete event."""
    return WebSocketMessage(
        type=WSEventType.node_complete,
        task_id=task_id,
        timestamp=datetime.now(),
        data=WSNodeCompleteData(
            node_id=node_id,
            file_path=file_path,
            file_size=file_size,
            group_id=group_id,
        ).model_dump(),
    )


def create_ws_group_complete_event(
    task_id: str,
    group_id: str,
    agent_type: str,
    results: Optional[List[NodeResult]] = None,
) -> WebSocketMessage:
    """Create group complete event."""
    return WebSocketMessage(
        type=WSEventType.group_complete,
        task_id=task_id,
        timestamp=datetime.now(),
        data=WSGroupCompleteData(
            group_id=group_id,
            agent_type=agent_type,
            results=results or [],
        ).model_dump(),
    )


def create_ws_error_event(
    task_id: str,
    error_message: str,
    node_id: Optional[str] = None,
    group_id: Optional[str] = None,
    error_type: Optional[str] = None,
    recoverable: bool = True,
    retry_after: Optional[int] = None,
) -> WebSocketMessage:
    """Create error event."""
    return WebSocketMessage(
        type=WSEventType.error,
        task_id=task_id,
        timestamp=datetime.now(),
        data=WSErrorData(
            node_id=node_id,
            error_message=error_message,
            group_id=group_id,
            error_type=error_type,
            recoverable=recoverable,
            retry_after=retry_after,
        ).model_dump(),
    )


def create_ws_complete_event(
    task_id: str,
    status: ParallelTaskStatus,
    total_duration: float,
    success_count: int,
    failure_count: int,
) -> WebSocketMessage:
    """Create session complete event."""
    return WebSocketMessage(
        type=WSEventType.complete,
        task_id=task_id,
        timestamp=datetime.now(),
        data=WSCompleteData(
            status=status,
            total_duration=total_duration,
            success_count=success_count,
            failure_count=failure_count,
        ).model_dump(),
    )


def create_ws_ping_event(task_id: str) -> WebSocketMessage:
    """Create heartbeat ping event."""
    return WebSocketMessage(
        type=WSEventType.ping,
        task_id=task_id,
        timestamp=datetime.now(),
        data=None,
    )


def create_ws_connected_event(task_id: str) -> WebSocketMessage:
    """Create connection established event."""
    return WebSocketMessage(
        type=WSEventType.connected,
        task_id=task_id,
        timestamp=datetime.now(),
        data=None,
    )
