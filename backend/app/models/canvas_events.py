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

from dataclasses import dataclass, field
from datetime import datetime, timezone
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

    # Story 7.1: QA Pipeline Events
    FAITHFULNESS_CHECKED = "faithfulness_checked"
    INJECTION_DETECTED = "injection_detected"

    # Story 7.2 Task 5.1: LLM call logged event (Tier3 fire-and-forget)
    # [Source: _bmad-output/implementation-artifacts/7-2-llm-logging-token-tracking.md]
    LLM_CALL_LOGGED = "llm_call_logged"

    # Story 7.4: Difficulty evaluation completed (Tier3 fire-and-forget)
    # [Source: _bmad-output/implementation-artifacts/7-4-difficulty-matching-extraction-validation.md]
    DIFFICULTY_EVALUATED = "difficulty_evaluated"


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

    event_id: str = Field(default_factory=lambda: str(uuid4()), description="事件唯一标识 (UUID)")
    session_id: str = Field(..., description="会话ID")
    event_type: CanvasEventType = Field(..., description="事件类型")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="事件发生时间")
    canvas_path: str = Field(..., description="关联Canvas路径")
    node_id: Optional[str] = Field(default=None, description="关联节点ID（可选）")
    edge_id: Optional[str] = Field(default=None, description="关联边ID（可选）(Story 30.5 AC-30.5.2)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="事件元数据")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "session_abc123",
                "event_type": "node_created",
                "timestamp": "2026-01-16T10:30:00Z",
                "canvas_path": "Canvas/学习笔记.canvas",
                "node_id": "node_xyz789",
                "metadata": {"concept": "机器学习", "node_text": "监督学习定义"},
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


# ═══════════════════════════════════════════════════════════════════════════════
# Story 5.7: Learning Event Types for EventBus
# [Source: _bmad-output/implementation-artifacts/5-7-eventbus-triconnect.md]
# [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns #10]
# ═══════════════════════════════════════════════════════════════════════════════


class LearningEventType(str, Enum):
    """Learning event types for the mastery EventBus.

    8 event types spanning FSRS, Graphiti, and RAG subsystems.
    Each event has an assigned tier (priority level).
    """

    # Tier 1 (P0) CRITICAL — await synchronous execution
    SCORE_SUBMITTED = "score_submitted"

    # Tier 2 (P1) IMPORTANT — fire + retry + JSONL outbox
    BKT_UPDATED = "bkt_updated"
    FSRS_UPDATED = "fsrs_updated"
    MASTERY_CHANGED = "mastery_changed"
    CALIBRATION_RECORDED = "calibration_recorded"
    MEMORY_WRITE_REQUESTED = "memory_write_requested"

    # Tier 3 (P2) BEST_EFFORT — fire-and-forget
    RAG_WEIGHT_ADJUST = "rag_weight_adjust"
    UI_MASTERY_PUSH = "ui_mastery_push"


class EventTier(str, Enum):
    """Event priority tiers for the EventBus.

    Tier 1: CRITICAL — await synchronous, failure raises exception
    Tier 2: IMPORTANT — async with retry (exponential backoff 2s->4s->8s, max 3) + JSONL outbox
    Tier 3: BEST_EFFORT — fire-and-forget, failure only logged
    """

    TIER_1_CRITICAL = "tier_1_critical"
    TIER_2_IMPORTANT = "tier_2_important"
    TIER_3_BEST_EFFORT = "tier_3_best_effort"


# Mapping from event type to its tier (immutable, not overridable by handlers)
LEARNING_EVENT_TIER_MAP: Dict[LearningEventType, EventTier] = {
    LearningEventType.SCORE_SUBMITTED: EventTier.TIER_1_CRITICAL,
    LearningEventType.BKT_UPDATED: EventTier.TIER_2_IMPORTANT,
    LearningEventType.FSRS_UPDATED: EventTier.TIER_2_IMPORTANT,
    LearningEventType.MASTERY_CHANGED: EventTier.TIER_2_IMPORTANT,
    LearningEventType.CALIBRATION_RECORDED: EventTier.TIER_2_IMPORTANT,
    LearningEventType.MEMORY_WRITE_REQUESTED: EventTier.TIER_2_IMPORTANT,
    LearningEventType.RAG_WEIGHT_ADJUST: EventTier.TIER_3_BEST_EFFORT,
    LearningEventType.UI_MASTERY_PUSH: EventTier.TIER_3_BEST_EFFORT,
}


@dataclass
class LearningEvent:
    """Structured learning event for EventBus.

    Every event must carry:
      - event_id: UUID for idempotent deduplication
      - event_type: LearningEventType enum
      - payload: dict with at least node_id + session_id
      - timestamp: auto-generated
      - source: originator identifier
      - tier: EventTier (determined from LEARNING_EVENT_TIER_MAP, not overridable)
    """

    event_type: LearningEventType
    payload: Dict[str, Any]
    source: str
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def tier(self) -> EventTier:
        """Tier is determined by event_type, not overridable."""
        return LEARNING_EVENT_TIER_MAP.get(self.event_type, EventTier.TIER_3_BEST_EFFORT)

    @property
    def node_id(self) -> Optional[str]:
        return self.payload.get("node_id")

    @property
    def session_id(self) -> Optional[str]:
        return self.payload.get("session_id")
