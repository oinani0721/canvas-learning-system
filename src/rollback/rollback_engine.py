# src/rollback/rollback_engine.py
"""
Canvas Rollback Engine

Executes rollback operations for Canvas state recovery.

[Source: docs/architecture/rollback-recovery-architecture.md:122-180]
[Source: docs/stories/18.3.story.md]
"""

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

# ✅ Verified from Context7:/ijl/orjson (topic: serialization)
import orjson

from .models import (
    Operation,
    OperationType,
)
from .operation_tracker import OperationTracker
from .snapshot_manager import SnapshotManager


class RollbackType(str, Enum):
    """回滚类型枚举

    [Source: docs/architecture/rollback-recovery-architecture.md:122-140]
    """

    OPERATION = "operation"  # 单次操作撤销
    SNAPSHOT = "snapshot"  # 恢复到快照
    TIMEPOINT = "timepoint"  # 恢复到时间点 (最近快照)


class GraphSyncStatus(str, Enum):
    """图谱同步状态

    [Source: docs/architecture/rollback-recovery-architecture.md:380-400]
    """

    SYNCED = "synced"  # 已同步
    PENDING = "pending"  # 待同步
    SKIPPED = "skipped"  # 跳过


@dataclass
class RollbackResult:
    """回滚结果

    [Source: docs/architecture/rollback-recovery-architecture.md:344-380]
    """

    success: bool
    rollback_type: RollbackType
    canvas_path: str
    backup_snapshot_id: Optional[str] = None
    restored_operation_id: Optional[str] = None
    restored_snapshot_id: Optional[str] = None
    graph_sync_status: GraphSyncStatus = GraphSyncStatus.SKIPPED
    message: str = ""
    error: Optional[str] = None


class RollbackError(Exception):
    """回滚操作错误

    [Source: docs/architecture/rollback-recovery-architecture.md:160-180]
    """

    pass


class RollbackEngine:
    """Canvas回滚引擎

    支持三种回滚方式:
    1. operation - 单次操作撤销 (应用反向操作)
    2. snapshot - 恢复到指定快照
    3. timepoint - 恢复到指定时间点的最近快照

    [Source: docs/architecture/rollback-recovery-architecture.md:122-180]
    """

    def __init__(
        self,
        operation_tracker: OperationTracker,
        snapshot_manager: SnapshotManager,
        create_backup: bool = True,
    ):
        """初始化回滚引擎

        Args:
            operation_tracker: 操作追踪器
            snapshot_manager: 快照管理器
            create_backup: 是否在回滚前创建备份快照, 默认True
        """
        self.operation_tracker = operation_tracker
        self.snapshot_manager = snapshot_manager
        self.create_backup = create_backup

    async def rollback(
        self,
        canvas_path: str,
        rollback_type: RollbackType,
        target_id: Optional[str] = None,
        target_time: Optional[datetime] = None,
        create_backup: Optional[bool] = None,
        preserve_graph: bool = False,
    ) -> RollbackResult:
        """执行回滚操作

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]

        Args:
            canvas_path: Canvas文件路径
            rollback_type: 回滚类型
            target_id: 目标ID (operation_id 或 snapshot_id)
            target_time: 目标时间点 (仅 timepoint 类型)
            create_backup: 是否创建备份 (覆盖默认设置)
            preserve_graph: 是否跳过图谱同步

        Returns:
            RollbackResult
        """
        # 决定是否创建备份
        should_backup = create_backup if create_backup is not None else self.create_backup
        backup_snapshot_id = None

        try:
            # Step 1: 创建备份快照 (如果配置)
            if should_backup:
                backup = await self.snapshot_manager.create_checkpoint(
                    canvas_path,
                    description=f"Pre-rollback backup ({rollback_type.value})",
                )
                backup_snapshot_id = backup.id

            # Step 2: 执行回滚
            if rollback_type == RollbackType.OPERATION:
                result = await self._rollback_operation(canvas_path, target_id)
            elif rollback_type == RollbackType.SNAPSHOT:
                result = await self._rollback_to_snapshot(canvas_path, target_id)
            elif rollback_type == RollbackType.TIMEPOINT:
                result = await self._rollback_to_timepoint(canvas_path, target_time)
            else:
                raise RollbackError(f"Unknown rollback type: {rollback_type}")

            # Step 3: 图谱同步 (Story 18.4实现)
            graph_status = GraphSyncStatus.SKIPPED
            if not preserve_graph:
                # 图谱同步逻辑将在 Story 18.4 实现
                graph_status = GraphSyncStatus.PENDING

            return RollbackResult(
                success=True,
                rollback_type=rollback_type,
                canvas_path=canvas_path,
                backup_snapshot_id=backup_snapshot_id,
                restored_operation_id=result.get("operation_id"),
                restored_snapshot_id=result.get("snapshot_id"),
                graph_sync_status=graph_status,
                message=result.get("message", "Rollback successful"),
            )

        except Exception as e:
            # 回滚失败，尝试从备份恢复
            error_message = str(e)

            if backup_snapshot_id and should_backup:
                try:
                    await self._restore_from_backup(canvas_path, backup_snapshot_id)
                    error_message += " (restored from backup)"
                except Exception as restore_err:
                    error_message += f" (backup restore failed: {restore_err})"

            return RollbackResult(
                success=False,
                rollback_type=rollback_type,
                canvas_path=canvas_path,
                backup_snapshot_id=backup_snapshot_id,
                graph_sync_status=GraphSyncStatus.SKIPPED,
                message="Rollback failed",
                error=error_message,
            )

    async def _rollback_operation(
        self,
        canvas_path: str,
        operation_id: Optional[str],
    ) -> Dict[str, Any]:
        """撤销单个操作

        [Source: docs/architecture/rollback-recovery-architecture.md:142-158]

        通过应用反向操作来撤销指定操作。
        如果 operation_id 为 None，撤销最新操作。

        Args:
            canvas_path: Canvas文件路径
            operation_id: 操作ID (None表示最新操作)

        Returns:
            包含恢复结果的字典
        """
        # 获取要撤销的操作
        if operation_id:
            operation = self.operation_tracker.get_operation(operation_id)
            if not operation:
                raise RollbackError(f"Operation not found: {operation_id}")
        else:
            # 获取最新操作
            history = self.operation_tracker.get_history(canvas_path, limit=1)
            if not history:
                raise RollbackError(f"No operations to rollback for: {canvas_path}")
            operation = history[0]

        # 读取当前Canvas数据
        canvas_data = await self._read_canvas(canvas_path)

        # 应用反向操作
        reversed_data = self._apply_reverse_operation(canvas_data, operation)

        # 保存修改后的Canvas
        await self._write_canvas(canvas_path, reversed_data)

        return {
            "operation_id": operation.id,
            "message": f"Reversed operation: {operation.type.value}",
        }

    def _apply_reverse_operation(
        self,
        canvas_data: Dict[str, Any],
        operation: Operation,
    ) -> Dict[str, Any]:
        """应用反向操作

        [Source: docs/architecture/rollback-recovery-architecture.md:142-158]

        根据操作类型，应用相应的反向操作。

        Args:
            canvas_data: 当前Canvas数据
            operation: 要撤销的操作

        Returns:
            修改后的Canvas数据
        """
        nodes = canvas_data.get("nodes", [])
        edges = canvas_data.get("edges", [])

        op_type = operation.type
        op_data = operation.data

        if op_type == OperationType.NODE_ADD:
            # 反向: 删除节点
            if op_data.node_ids:
                nodes = [n for n in nodes if n.get("id") not in op_data.node_ids]

        elif op_type == OperationType.NODE_DELETE:
            # 反向: 恢复节点
            if op_data.before:
                if isinstance(op_data.before, list):
                    nodes.extend(op_data.before)
                else:
                    nodes.append(op_data.before)

        elif op_type == OperationType.NODE_MODIFY:
            # 反向: 恢复原始数据
            if op_data.before and op_data.node_ids:
                before_data = op_data.before if isinstance(op_data.before, list) else [op_data.before]
                for i, node in enumerate(nodes):
                    if node.get("id") in op_data.node_ids:
                        # 找到对应的before数据
                        for bd in before_data:
                            if bd.get("id") == node.get("id"):
                                nodes[i] = bd
                                break

        elif op_type == OperationType.NODE_COLOR_CHANGE:
            # 反向: 恢复原始颜色
            if op_data.before and op_data.node_ids:
                before_colors = op_data.before if isinstance(op_data.before, dict) else {}
                for node in nodes:
                    node_id = node.get("id")
                    if node_id in op_data.node_ids and node_id in before_colors:
                        node["color"] = before_colors[node_id]

        elif op_type == OperationType.EDGE_ADD:
            # 反向: 删除边
            if op_data.edge_ids:
                edges = [e for e in edges if e.get("id") not in op_data.edge_ids]

        elif op_type == OperationType.EDGE_DELETE:
            # 反向: 恢复边
            if op_data.before:
                if isinstance(op_data.before, list):
                    edges.extend(op_data.before)
                else:
                    edges.append(op_data.before)

        elif op_type == OperationType.BATCH_OPERATION:
            # 批量操作: 完整恢复before状态
            if op_data.before:
                return op_data.before

        return {"nodes": nodes, "edges": edges}

    async def _rollback_to_snapshot(
        self,
        canvas_path: str,
        snapshot_id: Optional[str],
    ) -> Dict[str, Any]:
        """恢复到指定快照

        [Source: docs/architecture/rollback-recovery-architecture.md:160-175]

        Args:
            canvas_path: Canvas文件路径
            snapshot_id: 快照ID (None表示最新快照)

        Returns:
            包含恢复结果的字典
        """
        # 获取快照
        if snapshot_id:
            snapshot = await self.snapshot_manager.get_snapshot(canvas_path, snapshot_id)
            if not snapshot:
                raise RollbackError(f"Snapshot not found: {snapshot_id}")
        else:
            # 获取最新快照
            snapshot = await self.snapshot_manager.get_latest_snapshot(canvas_path)
            if not snapshot:
                raise RollbackError(f"No snapshots available for: {canvas_path}")

        # 恢复Canvas到快照状态
        await self._write_canvas(canvas_path, snapshot.canvas_data)

        return {
            "snapshot_id": snapshot.id,
            "message": f"Restored to snapshot: {snapshot.id}",
        }

    async def _rollback_to_timepoint(
        self,
        canvas_path: str,
        target_time: Optional[datetime],
    ) -> Dict[str, Any]:
        """恢复到指定时间点的最近快照

        [Source: docs/architecture/rollback-recovery-architecture.md:160-175]

        Args:
            canvas_path: Canvas文件路径
            target_time: 目标时间点

        Returns:
            包含恢复结果的字典
        """
        if not target_time:
            raise RollbackError("Target time is required for timepoint rollback")

        # 获取所有快照
        entries = await self.snapshot_manager.list_snapshots(canvas_path, limit=100)
        if not entries:
            raise RollbackError(f"No snapshots available for: {canvas_path}")

        # 找到目标时间点之前的最近快照
        target_entry = None
        for entry in entries:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            # 确保时区一致
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
            if target_time.tzinfo is None:
                target_time = target_time.replace(tzinfo=timezone.utc)

            if entry_time <= target_time:
                target_entry = entry
                break

        if not target_entry:
            raise RollbackError(f"No snapshot found before: {target_time.isoformat()}")

        # 恢复到该快照
        return await self._rollback_to_snapshot(canvas_path, target_entry["id"])

    async def _restore_from_backup(
        self,
        canvas_path: str,
        backup_snapshot_id: str,
    ) -> None:
        """从备份快照恢复

        [Source: docs/architecture/rollback-recovery-architecture.md:160-180]
        回滚失败时的恢复机制

        Args:
            canvas_path: Canvas文件路径
            backup_snapshot_id: 备份快照ID
        """
        snapshot = await self.snapshot_manager.get_snapshot(canvas_path, backup_snapshot_id)
        if snapshot:
            await self._write_canvas(canvas_path, snapshot.canvas_data)

    async def _read_canvas(self, canvas_path: str) -> Dict[str, Any]:
        """读取Canvas文件

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]

        Args:
            canvas_path: Canvas文件路径

        Returns:
            Canvas JSON数据
        """
        possible_paths = [
            Path(canvas_path),
            Path.cwd() / canvas_path,
        ]

        for path in possible_paths:
            if path.exists():
                # ✅ Verified from Context7:/ijl/orjson (topic: loads)
                data = path.read_bytes()
                return orjson.loads(data)

        return {"nodes": [], "edges": []}

    async def _write_canvas(
        self,
        canvas_path: str,
        canvas_data: Dict[str, Any],
    ) -> None:
        """写入Canvas文件

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]
        使用原子写入确保数据完整性

        Args:
            canvas_path: Canvas文件路径
            canvas_data: Canvas数据
        """
        # 确定写入路径
        path = Path(canvas_path)
        if not path.exists():
            path = Path.cwd() / canvas_path
            if not path.exists():
                # 如果文件不存在，在当前目录创建
                path = Path.cwd() / canvas_path

        # 确保父目录存在
        path.parent.mkdir(parents=True, exist_ok=True)

        # ✅ Verified from Context7:/ijl/orjson (topic: OPT_INDENT_2)
        json_bytes = orjson.dumps(
            canvas_data,
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )

        # 原子写入
        fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            os.write(fd, json_bytes)
            os.close(fd)
            os.replace(temp_path, path)
        except Exception:
            os.close(fd)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    async def undo_last_operation(self, canvas_path: str) -> RollbackResult:
        """撤销最近一次操作

        便捷方法，等同于 rollback(type=OPERATION, target_id=None)

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]

        Args:
            canvas_path: Canvas文件路径

        Returns:
            RollbackResult
        """
        return await self.rollback(
            canvas_path,
            RollbackType.OPERATION,
            target_id=None,
        )

    async def restore_latest_snapshot(self, canvas_path: str) -> RollbackResult:
        """恢复到最新快照

        便捷方法，等同于 rollback(type=SNAPSHOT, target_id=None)

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]

        Args:
            canvas_path: Canvas文件路径

        Returns:
            RollbackResult
        """
        return await self.rollback(
            canvas_path,
            RollbackType.SNAPSHOT,
            target_id=None,
        )

    def get_available_rollback_targets(
        self,
        canvas_path: str,
    ) -> Dict[str, Any]:
        """获取可用的回滚目标

        [Source: docs/architecture/rollback-recovery-architecture.md:122-180]

        Args:
            canvas_path: Canvas文件路径

        Returns:
            包含可回滚操作和快照的字典
        """
        # 获取最近的操作
        operations = self.operation_tracker.get_history(canvas_path, limit=10)

        return {
            "canvas_path": canvas_path,
            "operations": [
                {
                    "id": op.id,
                    "type": op.type.value,
                    "timestamp": op.timestamp.isoformat(),
                    "description": op.metadata.description,
                }
                for op in operations
            ],
            "latest_operation_id": operations[0].id if operations else None,
        }
