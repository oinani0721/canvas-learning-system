# backend/app/api/v1/endpoints/rollback.py
"""
Rollback API Endpoints

Provides endpoints for operation history, snapshots, and rollback functionality.

[Source: docs/architecture/rollback-recovery-architecture.md:296-400]
[Source: docs/stories/18.1.story.md - AC 6]
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path for src imports
# [Source: docs/architecture/project-structure.md - Backend and src coexistence]
# Path: backend/app/api/v1/endpoints/rollback.py → need 6 levels up to Canvas/
_project_root = Path(__file__).parent.parent.parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# ✅ Verified from Context7:/fastapi/fastapi (topic: APIRouter, Query, Path)
from fastapi import APIRouter, HTTPException, Query, status  # noqa: E402

# Import rollback module
from src.rollback import (  # noqa: E402
    OperationTracker,
    RollbackEngine,
    RollbackType,
    SnapshotManager,
    SnapshotType,
)

from app.models.rollback import (  # noqa: E402
    CreateSnapshotRequest,
    DiffResponse,
    GraphSyncStatusEnum,
    OperationDataResponse,
    OperationHistoryResponse,
    OperationMetadataResponse,
    OperationResponse,
    OperationTypeEnum,
    RollbackRequest,
    RollbackResult,
    RollbackTypeEnum,
    SnapshotListResponse,
    SnapshotMetadataResponse,
    SnapshotResponse,
    SnapshotTypeEnum,
)

# ✅ Verified from Context7:/fastapi/fastapi (topic: APIRouter responses)
rollback_router = APIRouter(
    responses={
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    }
)

# 创建全局实例
# 注意: 在生产环境中应该通过依赖注入获取 (Story 18.5)
_tracker: Optional[OperationTracker] = None
_snapshot_manager: Optional[SnapshotManager] = None
_rollback_engine: Optional[RollbackEngine] = None


def get_operation_tracker() -> OperationTracker:
    """获取 OperationTracker 实例

    [Source: docs/architecture/rollback-recovery-architecture.md:602-640]

    Returns:
        OperationTracker 实例
    """
    global _tracker
    if _tracker is None:
        _tracker = OperationTracker(
            storage_root=Path(".canvas-learning"),
            max_history_per_canvas=100,
        )
    return _tracker


def get_snapshot_manager() -> SnapshotManager:
    """获取 SnapshotManager 实例

    [Source: docs/architecture/rollback-recovery-architecture.md:212-290]
    [Source: docs/stories/18.2.story.md - AC 6-7]

    Returns:
        SnapshotManager 实例
    """
    global _snapshot_manager
    if _snapshot_manager is None:
        _snapshot_manager = SnapshotManager(
            storage_root=Path(".canvas-learning"),
            auto_interval=300,
            max_snapshots=50,
        )
    return _snapshot_manager


def get_rollback_engine() -> RollbackEngine:
    """获取 RollbackEngine 实例

    [Source: docs/architecture/rollback-recovery-architecture.md:122-180]
    [Source: docs/stories/18.3.story.md - AC 1-7]

    Returns:
        RollbackEngine 实例
    """
    global _rollback_engine
    if _rollback_engine is None:
        _rollback_engine = RollbackEngine(
            operation_tracker=get_operation_tracker(),
            snapshot_manager=get_snapshot_manager(),
            create_backup=True,
        )
    return _rollback_engine


def _operation_to_response(op) -> OperationResponse:
    """将 Operation 对象转换为响应模型

    Args:
        op: Operation 对象

    Returns:
        OperationResponse 模型
    """
    return OperationResponse(
        id=op.id,
        type=OperationTypeEnum(op.type.value),
        canvas_path=op.canvas_path,
        timestamp=op.timestamp,
        user_id=op.user_id,
        data=OperationDataResponse(
            before=op.data.before,
            after=op.data.after,
            node_ids=op.data.node_ids,
            edge_ids=op.data.edge_ids,
        ),
        metadata=OperationMetadataResponse(
            description=op.metadata.description,
            agent_id=op.metadata.agent_id,
            request_id=op.metadata.request_id,
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.1: Operation History Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@rollback_router.get(
    "/history/{canvas_path:path}",
    response_model=OperationHistoryResponse,
    summary="Get operation history",
    operation_id="get_operation_history",
    responses={
        200: {
            "description": "Operation history retrieved successfully",
            "model": OperationHistoryResponse,
        },
    },
)
async def get_operation_history(
    canvas_path: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
) -> OperationHistoryResponse:
    """
    Get operation history for a Canvas file.

    Returns a paginated list of operations in reverse chronological order
    (newest first).

    - **canvas_path**: Canvas file path (e.g., "离散数学.canvas")
    - **limit**: Maximum number of records to return (1-100, default: 50)
    - **offset**: Number of records to skip (default: 0)

    [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
    [Source: docs/stories/18.1.story.md - AC 6]
    """
    tracker = get_operation_tracker()

    # 获取操作历史
    operations = tracker.get_history(canvas_path, limit=limit, offset=offset)
    total = tracker.get_total_count(canvas_path)

    # 转换为响应模型
    operation_responses = [_operation_to_response(op) for op in operations]

    return OperationHistoryResponse(
        canvas_path=canvas_path,
        total=total,
        limit=limit,
        offset=offset,
        operations=operation_responses,
    )


@rollback_router.get(
    "/operation/{operation_id}",
    response_model=OperationResponse,
    summary="Get single operation",
    operation_id="get_operation",
    responses={
        200: {
            "description": "Operation retrieved successfully",
            "model": OperationResponse,
        },
        404: {"description": "Operation not found"},
    },
)
async def get_operation(operation_id: str) -> OperationResponse:
    """
    Get a single operation by ID.

    - **operation_id**: Operation UUID

    [Source: docs/architecture/rollback-recovery-architecture.md:296-310]
    """
    tracker = get_operation_tracker()

    operation = tracker.get_operation(operation_id)

    if operation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation {operation_id} not found",
        )

    return _operation_to_response(operation)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.2: Snapshot Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


def _snapshot_entry_to_response(entry: dict) -> SnapshotResponse:
    """将快照索引条目转换为响应模型

    [Source: docs/stories/18.2.story.md - AC 6]

    Args:
        entry: 快照索引条目 (来自 SnapshotManager.list_snapshots)

    Returns:
        SnapshotResponse 模型
    """
    from datetime import datetime

    return SnapshotResponse(
        id=entry["id"],
        canvas_path=entry["canvas_path"],
        timestamp=datetime.fromisoformat(entry["timestamp"]),
        type=SnapshotTypeEnum(entry["type"]),
        last_operation_id=entry.get("last_operation_id"),
        metadata=SnapshotMetadataResponse(
            description=entry.get("metadata", {}).get("description"),
            created_by=entry.get("metadata", {}).get("created_by", "system"),
            tags=entry.get("metadata", {}).get("tags"),
            size_bytes=entry.get("metadata", {}).get("size_bytes", 0),
        ),
    )


# ✅ Verified from Context7:/fastapi/fastapi (topic: APIRouter, Path parameters)
@rollback_router.get(
    "/snapshots/{canvas_path:path}",
    response_model=SnapshotListResponse,
    summary="List snapshots",
    operation_id="list_snapshots",
    responses={
        200: {
            "description": "Snapshot list retrieved successfully",
            "model": SnapshotListResponse,
        },
    },
)
async def list_snapshots(
    canvas_path: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of snapshots to return"),
    offset: int = Query(0, ge=0, description="Number of snapshots to skip"),
) -> SnapshotListResponse:
    """
    List snapshots for a Canvas file.

    Returns a paginated list of snapshots in reverse chronological order
    (newest first). Does not include full canvas data, only metadata.

    - **canvas_path**: Canvas file path (e.g., "离散数学.canvas")
    - **limit**: Maximum number of snapshots to return (1-100, default: 20)
    - **offset**: Number of snapshots to skip (default: 0)

    [Source: docs/architecture/rollback-recovery-architecture.md:312-326]
    [Source: docs/stories/18.2.story.md - AC 6]
    """
    manager = get_snapshot_manager()

    # 获取快照列表
    entries = await manager.list_snapshots(canvas_path, limit=limit, offset=offset)
    total = await manager.get_total_count(canvas_path)

    # 转换为响应模型
    snapshot_responses = [_snapshot_entry_to_response(entry) for entry in entries]

    return SnapshotListResponse(
        canvas_path=canvas_path,
        total=total,
        snapshots=snapshot_responses,
    )


# ✅ Verified from Context7:/fastapi/fastapi (topic: POST request body)
@rollback_router.post(
    "/snapshot",
    response_model=SnapshotResponse,
    summary="Create manual snapshot",
    operation_id="create_snapshot",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Snapshot created successfully",
            "model": SnapshotResponse,
        },
        400: {"description": "Invalid request"},
    },
)
async def create_snapshot(request: CreateSnapshotRequest) -> SnapshotResponse:
    """
    Create a manual snapshot for a Canvas file.

    Creates a new snapshot with type "manual" that captures the current
    state of the Canvas file.

    - **canvas_path**: Canvas file path (e.g., "离散数学.canvas")
    - **description**: Optional description for the snapshot
    - **tags**: Optional list of tags

    [Source: docs/architecture/rollback-recovery-architecture.md:328-342]
    [Source: docs/stories/18.2.story.md - AC 7]
    """
    manager = get_snapshot_manager()

    # 创建手动快照
    snapshot = await manager.create_snapshot(
        canvas_path=request.canvas_path,
        snapshot_type=SnapshotType.MANUAL,
        description=request.description,
        created_by="user",
    )

    return SnapshotResponse(
        id=snapshot.id,
        canvas_path=snapshot.canvas_path,
        timestamp=snapshot.timestamp,
        type=SnapshotTypeEnum(snapshot.type.value),
        last_operation_id=snapshot.last_operation_id,
        metadata=SnapshotMetadataResponse(
            description=snapshot.metadata.description,
            created_by=snapshot.metadata.created_by,
            tags=request.tags,  # 使用请求中的tags
            size_bytes=snapshot.metadata.size_bytes,
        ),
    )


# ✅ Verified from Context7:/fastapi/fastapi (topic: Path parameters)
@rollback_router.get(
    "/snapshot/{snapshot_id}",
    response_model=SnapshotResponse,
    summary="Get single snapshot",
    operation_id="get_snapshot",
    responses={
        200: {
            "description": "Snapshot retrieved successfully",
            "model": SnapshotResponse,
        },
        404: {"description": "Snapshot not found"},
    },
)
async def get_snapshot(
    snapshot_id: str,
    canvas_path: str = Query(..., description="Canvas file path"),
) -> SnapshotResponse:
    """
    Get a single snapshot by ID.

    - **snapshot_id**: Snapshot UUID
    - **canvas_path**: Canvas file path (required for storage lookup)

    [Source: docs/architecture/rollback-recovery-architecture.md:312-326]
    """
    manager = get_snapshot_manager()

    snapshot = await manager.get_snapshot(canvas_path, snapshot_id)

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found for canvas {canvas_path}",
        )

    return SnapshotResponse(
        id=snapshot.id,
        canvas_path=snapshot.canvas_path,
        timestamp=snapshot.timestamp,
        type=SnapshotTypeEnum(snapshot.type.value),
        last_operation_id=snapshot.last_operation_id,
        metadata=SnapshotMetadataResponse(
            description=snapshot.metadata.description,
            created_by=snapshot.metadata.created_by,
            tags=snapshot.metadata.tags,
            size_bytes=snapshot.metadata.size_bytes,
        ),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.3: Rollback Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


# ✅ Verified from Context7:/fastapi/fastapi (topic: POST request body)
@rollback_router.post(
    "/rollback",
    response_model=RollbackResult,
    summary="Execute rollback",
    operation_id="execute_rollback",
    responses={
        200: {
            "description": "Rollback executed successfully",
            "model": RollbackResult,
        },
        400: {"description": "Invalid rollback request"},
        500: {"description": "Rollback failed"},
    },
)
async def execute_rollback(request: RollbackRequest) -> RollbackResult:
    """
    Execute a rollback operation on a Canvas file.

    Supports three rollback types:
    - **operation**: Undo a single operation by applying its reverse
    - **snapshot**: Restore to a specific snapshot state
    - **timepoint**: Restore to the nearest snapshot before a given time

    [Source: docs/architecture/rollback-recovery-architecture.md:122-180]
    [Source: docs/stories/18.3.story.md - AC 6]
    """
    from datetime import datetime

    engine = get_rollback_engine()

    # 转换回滚类型
    rollback_type = RollbackType(request.rollback_type.value)

    # 解析目标时间
    target_time = None
    if request.target_time:
        if isinstance(request.target_time, str):
            target_time = datetime.fromisoformat(request.target_time)
        else:
            target_time = request.target_time

    # 执行回滚
    result = await engine.rollback(
        canvas_path=request.canvas_path,
        rollback_type=rollback_type,
        target_id=request.target_id,
        target_time=target_time,
        create_backup=request.create_backup,
        preserve_graph=request.preserve_graph,
    )

    # 转换为响应模型
    return RollbackResult(
        success=result.success,
        rollback_type=RollbackTypeEnum(result.rollback_type.value),
        canvas_path=result.canvas_path,
        backup_snapshot_id=result.backup_snapshot_id,
        restored_operation_id=result.restored_operation_id,
        restored_snapshot_id=result.restored_snapshot_id,
        graph_sync_status=GraphSyncStatusEnum(result.graph_sync_status.value),
        message=result.message,
        error=result.error,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 18.5: Diff Endpoint
# ═══════════════════════════════════════════════════════════════════════════════


# ✅ Verified from Context7:/fastapi/fastapi (topic: Path parameters, Query)
@rollback_router.get(
    "/diff/{snapshot_id}",
    response_model=DiffResponse,
    summary="Get diff between snapshot and current Canvas",
    operation_id="get_diff",
    responses={
        200: {
            "description": "Diff retrieved successfully",
            "model": DiffResponse,
        },
        404: {"description": "Snapshot not found"},
    },
)
async def get_diff(
    snapshot_id: str,
    canvas_path: str = Query(..., description="Canvas file path"),
) -> DiffResponse:
    """
    Get the difference between a snapshot and the current Canvas state.

    Compares nodes and edges between the snapshot and current Canvas,
    returning lists of added, removed, and modified elements.

    - **snapshot_id**: Snapshot UUID to compare against
    - **canvas_path**: Canvas file path (required for loading current state)

    [Source: docs/architecture/rollback-recovery-architecture.md:382-400]
    [Source: docs/stories/18.5.story.md - AC 1]
    """
    import json
    from datetime import datetime, timezone

    manager = get_snapshot_manager()

    # 获取快照
    snapshot = await manager.get_snapshot(canvas_path, snapshot_id)

    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot {snapshot_id} not found for canvas {canvas_path}",
        )

    # 读取当前Canvas状态
    try:
        canvas_file = Path(canvas_path)
        if not canvas_file.exists():
            # 尝试从项目根目录查找
            canvas_file = _project_root / canvas_path

        if canvas_file.exists():
            with open(canvas_file, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        else:
            # Canvas不存在，视为空Canvas
            current_data = {"nodes": [], "edges": []}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read current canvas: {str(e)}",
        ) from e

    # 计算差异
    snapshot_data = snapshot.canvas_data
    diff_result = _compute_diff(snapshot_data, current_data)

    return DiffResponse(
        snapshot_id=snapshot_id,
        canvas_path=canvas_path,
        timestamp=datetime.now(timezone.utc),
        nodes_diff=diff_result["nodes"],
        edges_diff=diff_result["edges"],
    )


def _compute_diff(
    snapshot_data: dict,
    current_data: dict,
) -> dict:
    """
    计算快照与当前Canvas之间的差异

    [Source: docs/architecture/rollback-recovery-architecture.md:382-400]

    Args:
        snapshot_data: 快照中的Canvas数据
        current_data: 当前Canvas数据

    Returns:
        dict with nodes and edges diff
    """
    # 节点差异
    snapshot_nodes = {n.get("id"): n for n in snapshot_data.get("nodes", [])}
    current_nodes = {n.get("id"): n for n in current_data.get("nodes", [])}

    nodes_added = []
    nodes_removed = []
    nodes_modified = []

    # 查找新增的节点 (在当前但不在快照中)
    for node_id, node in current_nodes.items():
        if node_id not in snapshot_nodes:
            nodes_added.append({
                "id": node_id,
                "text": node.get("text", "")[:100] if node.get("text") else None,
                "color": node.get("color"),
            })

    # 查找删除的节点 (在快照但不在当前中)
    for node_id, node in snapshot_nodes.items():
        if node_id not in current_nodes:
            nodes_removed.append({
                "id": node_id,
                "text": node.get("text", "")[:100] if node.get("text") else None,
                "color": node.get("color"),
            })

    # 查找修改的节点 (在两者中但内容不同)
    for node_id in set(snapshot_nodes.keys()) & set(current_nodes.keys()):
        snap_node = snapshot_nodes[node_id]
        curr_node = current_nodes[node_id]

        # 比较关键字段
        changes = {}
        for key in ["text", "color", "x", "y", "width", "height"]:
            if snap_node.get(key) != curr_node.get(key):
                changes[key] = {
                    "before": snap_node.get(key),
                    "after": curr_node.get(key),
                }

        if changes:
            nodes_modified.append({
                "id": node_id,
                "before": {k: snap_node.get(k) for k in changes.keys()},
                "after": {k: curr_node.get(k) for k in changes.keys()},
            })

    # 边差异
    snapshot_edges = {e.get("id"): e for e in snapshot_data.get("edges", [])}
    current_edges = {e.get("id"): e for e in current_data.get("edges", [])}

    edges_added = []
    edges_removed = []

    # 查找新增的边
    for edge_id, edge in current_edges.items():
        if edge_id not in snapshot_edges:
            edges_added.append({
                "id": edge_id,
                "from_node": edge.get("fromNode", ""),
                "to_node": edge.get("toNode", ""),
            })

    # 查找删除的边
    for edge_id, edge in snapshot_edges.items():
        if edge_id not in current_edges:
            edges_removed.append({
                "id": edge_id,
                "from_node": edge.get("fromNode", ""),
                "to_node": edge.get("toNode", ""),
            })

    return {
        "nodes": {
            "added": nodes_added,
            "removed": nodes_removed,
            "modified": nodes_modified,
        },
        "edges": {
            "added": edges_added,
            "removed": edges_removed,
        },
    }
