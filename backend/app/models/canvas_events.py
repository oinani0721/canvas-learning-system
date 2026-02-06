# Canvas Learning System - Canvas CRUD Event Models
# Story 30.5: Canvas CRUD Operations Memory Trigger
# Source: specs/data/temporal-event.schema.json
# Source: docs/architecture/decisions/0003-graphiti-memory.md
"""
Canvas CRUD Event models for memory trigger system.

This module defines:
- CanvasEventType: Enum of CRUD event types
- CanvasEvent: Pydantic model for temporal event storage
- CanvasEventContext: Dataclass for hook context passing

Architecture Reference:
- ADR-0003: Graphiti Memory Architecture
- ADR-0004: Async Execution Engine (fire-and-forget pattern)
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class CanvasEventType(str, Enum):
    """
    Canvas CRUD事件类型枚举

    来源: specs/data/temporal-event.schema.json (event_type enum)

    Event Types:
    - NODE_CREATED: 节点创建 (AC-30.5.1)
    - NODE_UPDATED: 节点更新 (AC-30.5.3)
    - EDGE_CREATED: 边创建 (AC-30.5.2)
    - COLOR_CHANGED: 颜色变化 (Story 30.9 AC-30.9.5)
    - COLOR_REMOVED: 颜色移除 (Story 30.9 AC-30.9.5)
    - NODE_REMOVED: 节点删除 (Story 30.9 AC-30.9.5)
    """

    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"
    EDGE_CREATED = "edge_created"
    COLOR_CHANGED = "color_changed"
    COLOR_REMOVED = "color_removed"
    NODE_REMOVED = "node_removed"


class CanvasEvent(BaseModel):
    """
    Canvas CRUD事件模型 (Pydantic v2)

    来源: specs/data/temporal-event.schema.json
    用途: 记录Canvas结构变化事件到Neo4j Temporal Memory

    Required Fields:
    - event_id: UUID事件标识
    - session_id: 会话ID
    - event_type: 事件类型 (CanvasEventType)
    - timestamp: 事件时间戳

    Optional Fields:
    - canvas_path: Canvas文件路径
    - node_id: 节点ID (node事件)
    - edge_id: 边ID (edge事件)
    - metadata: 额外元数据
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="事件唯一标识 (UUID)"
    )
    session_id: str = Field(
        ...,
        description="会话ID"
    )
    event_type: CanvasEventType = Field(
        ...,
        description="事件类型"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="事件发生时间"
    )
    canvas_path: str = Field(
        ...,
        description="关联Canvas路径"
    )
    node_id: Optional[str] = Field(
        default=None,
        description="关联节点ID（可选）"
    )
    edge_id: Optional[str] = Field(
        default=None,
        description="关联边ID（可选）(Story 30.5 AC-30.5.2)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="事件元数据"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "session_abc123",
                "event_type": "node_created",
                "timestamp": "2026-01-16T10:30:00Z",
                "canvas_path": "Canvas/学习笔记.canvas",
                "node_id": "node_xyz789",
                "metadata": {
                    "concept": "机器学习",
                    "node_text": "监督学习定义"
                }
            }
        }
    }


@dataclass
class CanvasEventContext:
    """
    Canvas事件触发上下文 (Dataclass)

    用途: 在CanvasService CRUD方法中传递触发上下文

    Attributes:
        canvas_name: Canvas名称 (不含.canvas后缀)
        node_id: 节点ID (可选)
        edge_id: 边ID (可选)
        node_data: 节点数据字典 (可选)
        edge_data: 边数据字典 (可选)
    """

    canvas_name: str
    node_id: Optional[str] = None
    edge_id: Optional[str] = None
    node_data: Optional[Dict[str, Any]] = None
    edge_data: Optional[Dict[str, Any]] = None

    def to_metadata(self) -> Dict[str, Any]:
        """
        转换为事件元数据字典

        Returns:
            Dict with relevant context for memory storage
        """
        metadata: Dict[str, Any] = {}

        if self.node_data:
            if "text" in self.node_data:
                metadata["node_text"] = self.node_data["text"]
            if "type" in self.node_data:
                metadata["node_type"] = self.node_data["type"]
            if "color" in self.node_data:
                metadata["node_color"] = self.node_data["color"]

        if self.edge_data:
            if "fromNode" in self.edge_data:
                metadata["from_node"] = self.edge_data["fromNode"]
            if "toNode" in self.edge_data:
                metadata["to_node"] = self.edge_data["toNode"]
            if "label" in self.edge_data:
                metadata["edge_label"] = self.edge_data["label"]

        return metadata
