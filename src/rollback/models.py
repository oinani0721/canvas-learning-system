# src/rollback/models.py
"""
Canvas Rollback System - Data Models

Defines the core data models for operation tracking and rollback functionality.

[Source: docs/architecture/rollback-recovery-architecture.md:38-66]
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OperationType(str, Enum):
    """Canvas操作类型枚举

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
    """
    NODE_ADD = "node_add"
    NODE_DELETE = "node_delete"
    NODE_MODIFY = "node_modify"
    NODE_COLOR_CHANGE = "node_color_change"
    EDGE_ADD = "edge_add"
    EDGE_DELETE = "edge_delete"
    BATCH_OPERATION = "batch_operation"


@dataclass
class OperationData:
    """操作数据，记录操作前后的状态

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
    """
    before: Optional[Any] = None
    after: Optional[Any] = None
    node_ids: Optional[List[str]] = None
    edge_ids: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "before": self.before,
            "after": self.after,
            "node_ids": self.node_ids,
            "edge_ids": self.edge_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationData":
        """从字典创建实例"""
        return cls(
            before=data.get("before"),
            after=data.get("after"),
            node_ids=data.get("node_ids"),
            edge_ids=data.get("edge_ids"),
        )


@dataclass
class OperationMetadata:
    """操作元数据

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
    """
    description: str = ""
    agent_id: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "description": self.description,
            "agent_id": self.agent_id,
            "request_id": self.request_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OperationMetadata":
        """从字典创建实例"""
        return cls(
            description=data.get("description", ""),
            agent_id=data.get("agent_id"),
            request_id=data.get("request_id"),
        )


@dataclass
class Operation:
    """Canvas操作记录

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]

    Attributes:
        id: 操作唯一标识符 (UUID)
        type: 操作类型
        canvas_path: Canvas文件路径
        timestamp: 操作时间戳
        user_id: 执行操作的用户ID
        data: 操作数据 (before/after状态)
        metadata: 操作元数据
    """
    id: str
    type: OperationType
    canvas_path: str
    timestamp: datetime
    user_id: str
    data: OperationData = field(default_factory=OperationData)
    metadata: OperationMetadata = field(default_factory=OperationMetadata)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式 (用于JSON序列化)

        # ✅ Verified from Context7: orjson supports native datetime serialization
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "canvas_path": self.canvas_path,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "data": self.data.to_dict(),
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        """从字典创建Operation实例

        # ✅ Verified from Context7: orjson supports native datetime parsing
        """
        return cls(
            id=data["id"],
            type=OperationType(data["type"]),
            canvas_path=data["canvas_path"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data["user_id"],
            data=OperationData.from_dict(data.get("data", {})),
            metadata=OperationMetadata.from_dict(data.get("metadata", {})),
        )


# Snapshot相关模型 (Story 18.2使用)
class SnapshotType(str, Enum):
    """快照类型枚举

    [Source: docs/architecture/rollback-recovery-architecture.md:212-250]
    """
    AUTO = "auto"           # 自动快照 (定时创建)
    MANUAL = "manual"       # 手动快照 (用户创建)
    CHECKPOINT = "checkpoint"  # 检查点快照 (回滚前自动创建)


@dataclass
class SnapshotMetadata:
    """快照元数据

    [Source: docs/architecture/rollback-recovery-architecture.md:212-250]
    """
    description: Optional[str] = None
    created_by: str = "system"
    tags: Optional[List[str]] = None
    size_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "description": self.description,
            "created_by": self.created_by,
            "tags": self.tags,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMetadata":
        """从字典创建实例"""
        return cls(
            description=data.get("description"),
            created_by=data.get("created_by", "system"),
            tags=data.get("tags"),
            size_bytes=data.get("size_bytes", 0),
        )


@dataclass
class Snapshot:
    """Canvas快照

    [Source: docs/architecture/rollback-recovery-architecture.md:212-250]
    """
    id: str
    canvas_path: str
    timestamp: datetime
    type: SnapshotType
    canvas_data: Dict[str, Any]
    last_operation_id: Optional[str] = None
    metadata: SnapshotMetadata = field(default_factory=SnapshotMetadata)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "canvas_path": self.canvas_path,
            "timestamp": self.timestamp.isoformat(),
            "type": self.type.value,
            "canvas_data": self.canvas_data,
            "last_operation_id": self.last_operation_id,
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Snapshot":
        """从字典创建Snapshot实例"""
        return cls(
            id=data["id"],
            canvas_path=data["canvas_path"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            type=SnapshotType(data["type"]),
            canvas_data=data["canvas_data"],
            last_operation_id=data.get("last_operation_id"),
            metadata=SnapshotMetadata.from_dict(data.get("metadata", {})),
        )
