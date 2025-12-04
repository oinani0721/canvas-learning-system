# backend/app/models/rollback.py
"""
Pydantic models for Rollback API

[Source: docs/architecture/rollback-recovery-architecture.md:296-400]
[Source: docs/stories/18.1.story.md - AC 6]
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# ✅ Verified from Context7:/pydantic/pydantic (topic: BaseModel, Field)
from pydantic import BaseModel, Field


class OperationTypeEnum(str, Enum):
    """操作类型枚举

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
    """

    NODE_ADD = "node_add"
    NODE_DELETE = "node_delete"
    NODE_MODIFY = "node_modify"
    NODE_COLOR_CHANGE = "node_color_change"
    EDGE_ADD = "edge_add"
    EDGE_DELETE = "edge_delete"
    BATCH_OPERATION = "batch_operation"


class OperationDataResponse(BaseModel):
    """操作数据响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
    """

    before: Optional[Any] = Field(None, description="操作前状态")
    after: Optional[Any] = Field(None, description="操作后状态")
    node_ids: Optional[List[str]] = Field(None, description="影响的节点ID列表")
    edge_ids: Optional[List[str]] = Field(None, description="影响的边ID列表")


class OperationMetadataResponse(BaseModel):
    """操作元数据响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:38-66]
    """

    description: str = Field("", description="操作描述")
    agent_id: Optional[str] = Field(None, description="执行Agent ID")
    request_id: Optional[str] = Field(None, description="请求追踪ID")


class OperationResponse(BaseModel):
    """操作历史记录响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
    """

    id: str = Field(..., description="操作唯一标识符 (UUID)")
    type: OperationTypeEnum = Field(..., description="操作类型")
    canvas_path: str = Field(..., description="Canvas文件路径")
    timestamp: datetime = Field(..., description="操作时间戳 (UTC)")
    user_id: str = Field(..., description="执行操作的用户ID")
    data: OperationDataResponse = Field(
        default_factory=OperationDataResponse, description="操作数据"
    )
    metadata: OperationMetadataResponse = Field(
        default_factory=OperationMetadataResponse, description="操作元数据"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "node_add",
                "canvas_path": "离散数学.canvas",
                "timestamp": "2025-12-04T01:30:00Z",
                "user_id": "system",
                "data": {
                    "before": None,
                    "after": {"id": "node1", "text": "逆否命题", "color": "1"},
                    "node_ids": ["node1"],
                    "edge_ids": None,
                },
                "metadata": {
                    "description": "Add node: 逆否命题",
                    "agent_id": "basic-decomposition",
                    "request_id": "req-123",
                },
            }
        }


class OperationHistoryResponse(BaseModel):
    """操作历史列表响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
    """

    canvas_path: str = Field(..., description="Canvas文件路径")
    total: int = Field(..., description="总操作数")
    limit: int = Field(..., description="返回的最大记录数")
    offset: int = Field(..., description="跳过的记录数")
    operations: List[OperationResponse] = Field(
        default_factory=list, description="操作历史列表 (按时间倒序)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "canvas_path": "离散数学.canvas",
                "total": 25,
                "limit": 10,
                "offset": 0,
                "operations": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "type": "node_add",
                        "canvas_path": "离散数学.canvas",
                        "timestamp": "2025-12-04T01:30:00Z",
                        "user_id": "system",
                        "data": {
                            "before": None,
                            "after": {"id": "node1", "text": "逆否命题"},
                            "node_ids": ["node1"],
                            "edge_ids": None,
                        },
                        "metadata": {
                            "description": "Add node: 逆否命题",
                            "agent_id": "basic-decomposition",
                            "request_id": None,
                        },
                    }
                ],
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.2 相关模型 (预留)
# ═══════════════════════════════════════════════════════════════════════════════


class SnapshotTypeEnum(str, Enum):
    """快照类型枚举

    [Source: docs/architecture/rollback-recovery-architecture.md:212-250]
    """

    AUTO = "auto"
    MANUAL = "manual"
    CHECKPOINT = "checkpoint"


class SnapshotMetadataResponse(BaseModel):
    """快照元数据响应模型"""

    description: Optional[str] = None
    created_by: str = "system"
    tags: Optional[List[str]] = None
    size_bytes: int = 0


class SnapshotResponse(BaseModel):
    """快照响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:312-326]
    """

    id: str = Field(..., description="快照唯一标识符")
    canvas_path: str = Field(..., description="Canvas文件路径")
    timestamp: datetime = Field(..., description="创建时间戳")
    type: SnapshotTypeEnum = Field(..., description="快照类型")
    last_operation_id: Optional[str] = Field(None, description="关联的最后操作ID")
    metadata: SnapshotMetadataResponse = Field(
        default_factory=SnapshotMetadataResponse
    )


class SnapshotListResponse(BaseModel):
    """快照列表响应模型"""

    canvas_path: str
    total: int
    snapshots: List[SnapshotResponse] = []


class CreateSnapshotRequest(BaseModel):
    """创建快照请求模型

    [Source: docs/architecture/rollback-recovery-architecture.md:328-342]
    """

    canvas_path: str = Field(..., description="Canvas文件路径")
    description: Optional[str] = Field(None, description="快照描述")
    tags: Optional[List[str]] = Field(None, description="标签列表")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.3 相关模型 (预留)
# ═══════════════════════════════════════════════════════════════════════════════


class RollbackTypeEnum(str, Enum):
    """回滚类型枚举"""

    OPERATION = "operation"
    SNAPSHOT = "snapshot"
    TIMEPOINT = "timepoint"


class RollbackRequest(BaseModel):
    """回滚请求模型

    [Source: docs/architecture/rollback-recovery-architecture.md:344-380]
    """

    canvas_path: str = Field(..., description="Canvas文件路径")
    rollback_type: RollbackTypeEnum = Field(..., description="回滚类型")
    target_id: Optional[str] = Field(
        None, description="目标ID (operation_id 或 snapshot_id)"
    )
    target_time: Optional[datetime] = Field(
        None, description="目标时间点 (仅 timepoint 类型)"
    )
    create_backup: bool = Field(True, description="是否在回滚前创建备份快照")
    preserve_graph: bool = Field(False, description="是否跳过知识图谱同步")


class GraphSyncStatusEnum(str, Enum):
    """图谱同步状态"""

    SYNCED = "synced"
    PENDING = "pending"
    SKIPPED = "skipped"


class RollbackResult(BaseModel):
    """回滚结果响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:344-380]
    """

    success: bool = Field(..., description="是否成功")
    rollback_type: RollbackTypeEnum = Field(..., description="回滚类型")
    canvas_path: str = Field(..., description="Canvas文件路径")
    backup_snapshot_id: Optional[str] = Field(None, description="备份快照ID")
    restored_operation_id: Optional[str] = Field(None, description="恢复到的操作ID")
    restored_snapshot_id: Optional[str] = Field(None, description="恢复到的快照ID")
    graph_sync_status: GraphSyncStatusEnum = Field(
        GraphSyncStatusEnum.SKIPPED, description="图谱同步状态"
    )
    message: str = Field("", description="结果消息")
    error: Optional[str] = Field(None, description="错误信息")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.5 相关模型 (预留)
# ═══════════════════════════════════════════════════════════════════════════════


class NodeDiffInfo(BaseModel):
    """节点差异信息"""

    id: str
    text: Optional[str] = None
    color: Optional[str] = None


class NodeModification(BaseModel):
    """节点修改详情"""

    id: str
    before: Dict[str, Any]
    after: Dict[str, Any]


class EdgeDiffInfo(BaseModel):
    """边差异信息"""

    id: str
    from_node: str
    to_node: str


class DiffResponse(BaseModel):
    """差异响应模型

    [Source: docs/architecture/rollback-recovery-architecture.md:382-400]
    """

    snapshot_id: str = Field(..., description="快照ID")
    canvas_path: str = Field(..., description="Canvas文件路径")
    timestamp: datetime = Field(..., description="比较时间戳")
    nodes_diff: Dict[str, Any] = Field(
        default_factory=lambda: {"added": [], "removed": [], "modified": []},
        description="节点差异",
    )
    edges_diff: Dict[str, Any] = Field(
        default_factory=lambda: {"added": [], "removed": []}, description="边差异"
    )
