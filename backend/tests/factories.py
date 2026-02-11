# Canvas Learning System - Test Data Factories
# EPIC-33 P1-1: Centralized test data factories
"""
Test data factories for Canvas Learning System.

Eliminates hardcoded test data repetition across 22+ test files.
Each factory provides sensible defaults with full override capability.

Usage:
    from tests.factories import make_session_info, make_group_config
    session = make_session_info(node_count=5, status=SessionStatus.RUNNING)
    group = make_group_config(agent_type="oral-explanation")
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.session_models import NodeResult, SessionInfo, SessionStatus
from app.services.batch_orchestrator import GroupConfig, NodeExecutionResult


def make_session_info(
    session_id: Optional[str] = None,
    canvas_path: str = "test.canvas",
    node_count: int = 10,
    status: SessionStatus = SessionStatus.PENDING,
    **kwargs: Any,
) -> SessionInfo:
    """
    Create a SessionInfo with sensible defaults.

    Args:
        session_id: UUID string (auto-generated if None)
        canvas_path: Path to canvas file
        node_count: Total nodes to process
        status: Session status
        **kwargs: Override any SessionInfo field

    Returns:
        SessionInfo instance
    """
    now = datetime.now()
    defaults = {
        "session_id": session_id or str(uuid.uuid4()),
        "canvas_path": canvas_path,
        "node_count": node_count,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(kwargs)
    return SessionInfo(**defaults)


def make_group_config(
    group_id: Optional[str] = None,
    agent_type: str = "oral-explanation",
    node_count: int = 3,
    **kwargs: Any,
) -> GroupConfig:
    """
    Create a GroupConfig with sensible defaults.

    Args:
        group_id: Group identifier (auto-generated if None)
        agent_type: Agent type string
        node_count: Number of node IDs to generate
        **kwargs: Override any GroupConfig field

    Returns:
        GroupConfig instance
    """
    defaults = {
        "group_id": group_id or f"group-{uuid.uuid4().hex[:8]}",
        "agent_type": agent_type,
        "node_ids": [f"node-{i:03d}" for i in range(node_count)],
    }
    defaults.update(kwargs)
    return GroupConfig(**defaults)


def make_node_result(
    node_id: Optional[str] = None,
    success: bool = True,
    **kwargs: Any,
) -> NodeResult:
    """
    Create a NodeResult with sensible defaults.

    Args:
        node_id: Node identifier (auto-generated if None)
        success: Whether the node execution succeeded
        **kwargs: Override any NodeResult field

    Returns:
        NodeResult instance
    """
    status = "success" if success else "failed"
    defaults = {
        "node_id": node_id or f"node-{uuid.uuid4().hex[:8]}",
        "status": kwargs.pop("status", status),
    }
    if not success and "error" not in kwargs:
        defaults["error"] = "Mock execution error"
    defaults.update(kwargs)
    return NodeResult(**defaults)


def make_node_execution_result(
    node_id: Optional[str] = None,
    success: bool = True,
    **kwargs: Any,
) -> NodeExecutionResult:
    """
    Create a NodeExecutionResult with sensible defaults.

    Args:
        node_id: Node identifier (auto-generated if None)
        success: Whether the node execution succeeded
        **kwargs: Override any NodeExecutionResult field

    Returns:
        NodeExecutionResult instance
    """
    now = datetime.now()
    defaults = {
        "node_id": node_id or f"node-{uuid.uuid4().hex[:8]}",
        "success": success,
        "execution_time_ms": 150,
        "started_at": now,
        "completed_at": now,
    }
    if not success and "error_message" not in kwargs:
        defaults["error_message"] = "Mock execution error"
        defaults["error_type"] = "MockError"
    defaults.update(kwargs)
    return NodeExecutionResult(**defaults)
