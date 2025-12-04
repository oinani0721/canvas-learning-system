# src/rollback/operation_tracker.py
"""
Canvas Operation Tracker

Tracks all Canvas operations for rollback functionality.

[Source: docs/architecture/rollback-recovery-architecture.md:68-120]
"""

import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# ✅ Verified from Context7: orjson provides fast JSON serialization
# orjson.dumps() returns bytes, orjson.loads() accepts bytes or str
import orjson

from .models import Operation, OperationData, OperationMetadata, OperationType


class OperationTracker:
    """Canvas操作历史追踪器

    追踪所有Canvas操作，支持查询历史记录，并提供持久化存储。

    [Source: docs/architecture/rollback-recovery-architecture.md:68-120]

    Attributes:
        storage_root: 存储根目录
        max_history: 每个Canvas的最大历史记录数
    """

    def __init__(
        self,
        storage_root: Path = Path(".canvas-learning"),
        max_history_per_canvas: int = 100,
    ):
        """初始化OperationTracker

        Args:
            storage_root: 存储根目录，默认为.canvas-learning
            max_history_per_canvas: 每个Canvas的最大历史记录数，默认100
        """
        self.storage_root = storage_root
        self.max_history = max_history_per_canvas
        self._history_cache: Dict[str, List[Operation]] = {}

    def _get_history_dir(self, canvas_path: str) -> Path:
        """获取Canvas的历史记录目录

        [Source: docs/architecture/rollback-recovery-architecture.md:182-210]

        Args:
            canvas_path: Canvas文件路径

        Returns:
            历史记录目录路径
        """
        # 从canvas路径提取名称 (去掉.canvas扩展名)
        canvas_name = Path(canvas_path).stem
        return self.storage_root / "history" / canvas_name

    def _get_history_file(self, canvas_path: str) -> Path:
        """获取操作历史JSON文件路径

        Args:
            canvas_path: Canvas文件路径

        Returns:
            操作历史文件路径
        """
        return self._get_history_dir(canvas_path) / "operations.json"

    def _ensure_history_dir(self, canvas_path: str) -> Path:
        """确保历史记录目录存在

        Args:
            canvas_path: Canvas文件路径

        Returns:
            创建/确认存在的目录路径
        """
        history_dir = self._get_history_dir(canvas_path)
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir

    def _load_history(self, canvas_path: str) -> List[Operation]:
        """从磁盘加载Canvas的操作历史

        # ✅ Verified from Context7: orjson.loads() accepts bytes or str

        Args:
            canvas_path: Canvas文件路径

        Returns:
            操作历史列表 (按时间顺序，最旧的在前)
        """
        history_file = self._get_history_file(canvas_path)

        if not history_file.exists():
            return []

        try:
            with open(history_file, "rb") as f:
                data = orjson.loads(f.read())
            return [Operation.from_dict(op) for op in data]
        except (orjson.JSONDecodeError, KeyError, ValueError):
            # 日志记录错误但返回空列表，避免阻塞
            # TODO: 添加structlog日志 (ADR-0010)
            return []

    def _save_history(self, canvas_path: str, history: List[Operation]) -> None:
        """将操作历史持久化到磁盘

        使用原子写入模式：先写入临时文件，再重命名，确保数据一致性。

        # ✅ Verified from Context7: orjson.dumps() returns bytes with OPT_INDENT_2 for readability

        Args:
            canvas_path: Canvas文件路径
            history: 操作历史列表
        """
        self._ensure_history_dir(canvas_path)
        history_file = self._get_history_file(canvas_path)

        # 序列化数据
        data = [op.to_dict() for op in history]
        json_bytes = orjson.dumps(
            data,
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
        )

        # 原子写入：临时文件 + 重命名
        # ✅ Verified from Python stdlib: tempfile + os.replace for atomic write
        fd, temp_path = tempfile.mkstemp(
            dir=history_file.parent,
            suffix=".tmp"
        )
        try:
            os.write(fd, json_bytes)
            os.close(fd)
            os.replace(temp_path, history_file)
        except Exception:
            os.close(fd)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def track_operation(self, operation: Operation) -> str:
        """追踪一个Canvas操作

        将操作添加到历史记录中，如果超过限制则删除最旧的记录。

        Args:
            operation: 操作记录

        Returns:
            操作ID
        """
        canvas_path = operation.canvas_path

        # 加载现有历史 (优先从缓存)
        if canvas_path in self._history_cache:
            history = self._history_cache[canvas_path]
        else:
            history = self._load_history(canvas_path)

        # 添加新操作
        history.append(operation)

        # 限制历史记录数量 (保留最新的)
        if len(history) > self.max_history:
            history = history[-self.max_history:]

        # 持久化
        self._save_history(canvas_path, history)

        # 更新缓存
        self._history_cache[canvas_path] = history

        return operation.id

    def get_history(
        self,
        canvas_path: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Operation]:
        """获取Canvas的操作历史

        Args:
            canvas_path: Canvas文件路径
            limit: 返回的最大记录数，默认50
            offset: 跳过的记录数，默认0

        Returns:
            操作历史列表 (按时间倒序，最新的在前)
        """
        # 优先从缓存获取
        if canvas_path in self._history_cache:
            history = self._history_cache[canvas_path]
        else:
            history = self._load_history(canvas_path)
            self._history_cache[canvas_path] = history

        # 返回最新的记录 (倒序)
        reversed_history = list(reversed(history))
        return reversed_history[offset:offset + limit]

    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """根据ID获取单个操作

        Args:
            operation_id: 操作ID

        Returns:
            操作记录，如果不存在则返回None
        """
        # 遍历所有缓存的历史
        for history in self._history_cache.values():
            for op in history:
                if op.id == operation_id:
                    return op

        # 如果缓存中没有，需要遍历所有Canvas的历史文件
        history_root = self.storage_root / "history"
        if not history_root.exists():
            return None

        for canvas_dir in history_root.iterdir():
            if canvas_dir.is_dir():
                canvas_path = str(canvas_dir.name) + ".canvas"
                history = self._load_history(canvas_path)
                for op in history:
                    if op.id == operation_id:
                        return op

        return None

    def get_total_count(self, canvas_path: str) -> int:
        """获取Canvas的操作历史总数

        Args:
            canvas_path: Canvas文件路径

        Returns:
            操作历史总数
        """
        if canvas_path in self._history_cache:
            return len(self._history_cache[canvas_path])

        history = self._load_history(canvas_path)
        self._history_cache[canvas_path] = history
        return len(history)

    def clear_history(self, canvas_path: str) -> None:
        """清除Canvas的所有操作历史

        Args:
            canvas_path: Canvas文件路径
        """
        history_file = self._get_history_file(canvas_path)

        if history_file.exists():
            history_file.unlink()

        # 清除缓存
        if canvas_path in self._history_cache:
            del self._history_cache[canvas_path]

    def create_operation(
        self,
        operation_type: OperationType,
        canvas_path: str,
        user_id: str = "system",
        before: Optional[any] = None,
        after: Optional[any] = None,
        node_ids: Optional[List[str]] = None,
        edge_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None,
        description: str = "",
    ) -> Operation:
        """创建一个新的操作记录

        便捷方法，用于快速创建Operation对象。

        Args:
            operation_type: 操作类型
            canvas_path: Canvas文件路径
            user_id: 用户ID
            before: 操作前状态
            after: 操作后状态
            node_ids: 影响的节点ID列表
            edge_ids: 影响的边ID列表
            agent_id: 执行Agent ID
            request_id: 请求追踪ID
            description: 操作描述

        Returns:
            新创建的Operation对象
        """
        return Operation(
            id=str(uuid.uuid4()),
            type=operation_type,
            canvas_path=canvas_path,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            data=OperationData(
                before=before,
                after=after,
                node_ids=node_ids,
                edge_ids=edge_ids,
            ),
            metadata=OperationMetadata(
                agent_id=agent_id,
                request_id=request_id,
                description=description,
            ),
        )
