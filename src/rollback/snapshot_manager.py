# src/rollback/snapshot_manager.py
"""
Canvas Rollback System - Snapshot Manager

Manages Canvas state snapshots for rollback functionality.

[Source: docs/architecture/rollback-recovery-architecture.md:212-290]
[Source: docs/stories/18.2.story.md]
"""

import asyncio
import gzip
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ✅ Verified from Context7:/ijl/orjson (topic: serialization)
import orjson

from .models import Snapshot, SnapshotMetadata, SnapshotType


class SnapshotManager:
    """Canvas状态快照管理器

    管理Canvas快照的创建、存储、查询和清理。
    支持自动快照、手动快照和检查点快照三种类型。

    [Source: docs/architecture/rollback-recovery-architecture.md:212-290]
    """

    def __init__(
        self,
        storage_root: Path = Path(".canvas-learning"),
        auto_interval: int = 300,
        max_snapshots: int = 50,
        compress: bool = True,
    ):
        """初始化快照管理器

        Args:
            storage_root: 存储根目录
            auto_interval: 自动快照间隔(秒), 默认300秒
            max_snapshots: 每Canvas最大快照数, 默认50
            compress: 是否压缩快照数据, 默认True
        """
        self.storage_root = Path(storage_root)
        self.auto_interval = auto_interval
        self.max_snapshots = max_snapshots
        self.compress = compress
        self._auto_tasks: Dict[str, asyncio.Task] = {}
        self._index_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, canvas_path: str) -> asyncio.Lock:
        """获取Canvas的锁

        [Source: docs/stories/18.2.story.md - Risk: 并发快照创建冲突]
        """
        if canvas_path not in self._locks:
            self._locks[canvas_path] = asyncio.Lock()
        return self._locks[canvas_path]

    def _get_canvas_name(self, canvas_path: str) -> str:
        """从Canvas路径获取名称 (不含扩展名)"""
        return Path(canvas_path).stem

    def _get_snapshots_dir(self, canvas_path: str) -> Path:
        """获取Canvas快照存储目录

        [Source: docs/architecture/rollback-recovery-architecture.md:182-210]
        存储结构: .canvas-learning/snapshots/{canvas_name}/snapshots/
        """
        canvas_name = self._get_canvas_name(canvas_path)
        return self.storage_root / "snapshots" / canvas_name / "snapshots"

    def _get_index_path(self, canvas_path: str) -> Path:
        """获取快照索引文件路径

        [Source: docs/architecture/rollback-recovery-architecture.md:182-210]
        """
        canvas_name = self._get_canvas_name(canvas_path)
        return self.storage_root / "snapshots" / canvas_name / "snapshots_index.json"

    def _get_snapshot_path(self, canvas_path: str, snapshot_id: str) -> Path:
        """获取快照文件路径"""
        extension = ".json.gz" if self.compress else ".json"
        return self._get_snapshots_dir(canvas_path) / f"{snapshot_id}{extension}"

    async def _read_canvas(self, canvas_path: str) -> Dict[str, Any]:
        """读取Canvas文件数据

        [Source: docs/architecture/rollback-recovery-architecture.md:212-290]

        Args:
            canvas_path: Canvas文件路径

        Returns:
            Canvas JSON数据
        """
        # 尝试多个可能的Canvas位置
        possible_paths = [
            Path(canvas_path),
            Path.cwd() / canvas_path,
        ]

        for path in possible_paths:
            if path.exists():
                # ✅ Verified from Context7:/ijl/orjson (topic: loads)
                data = path.read_bytes()
                return orjson.loads(data)

        # Canvas不存在时返回空结构
        return {"nodes": [], "edges": []}

    async def create_snapshot(
        self,
        canvas_path: str,
        snapshot_type: SnapshotType,
        description: Optional[str] = None,
        created_by: str = "system",
        last_operation_id: Optional[str] = None,
    ) -> Snapshot:
        """创建Canvas快照

        [Source: docs/architecture/rollback-recovery-architecture.md:212-290]

        Args:
            canvas_path: Canvas文件路径
            snapshot_type: 快照类型 (auto/manual/checkpoint)
            description: 快照描述
            created_by: 创建者
            last_operation_id: 关联的最后操作ID

        Returns:
            创建的Snapshot对象
        """
        async with self._get_lock(canvas_path):
            # 读取当前Canvas数据
            canvas_data = await self._read_canvas(canvas_path)

            # ✅ Verified from Context7:/ijl/orjson (topic: dumps)
            canvas_bytes = orjson.dumps(canvas_data)

            snapshot = Snapshot(
                id=str(uuid.uuid4()),
                canvas_path=canvas_path,
                timestamp=datetime.now(timezone.utc),
                type=snapshot_type,
                canvas_data=canvas_data,
                last_operation_id=last_operation_id,
                metadata=SnapshotMetadata(
                    description=description,
                    created_by=created_by,
                    size_bytes=len(canvas_bytes),
                ),
            )

            # 保存快照
            await self._save_snapshot(snapshot)

            # 清理旧快照
            await self._cleanup_old_snapshots(canvas_path)

            return snapshot

    async def _save_snapshot(self, snapshot: Snapshot) -> None:
        """保存快照到磁盘

        [Source: docs/architecture/rollback-recovery-architecture.md:212-290]
        使用原子写入确保数据完整性
        """
        # 确保目录存在
        snapshots_dir = self._get_snapshots_dir(snapshot.canvas_path)
        snapshots_dir.mkdir(parents=True, exist_ok=True)

        # 序列化快照数据
        # ✅ Verified from Context7:/ijl/orjson (topic: OPT_INDENT_2, OPT_SORT_KEYS)
        snapshot_bytes = orjson.dumps(
            snapshot.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )

        # 压缩 (如果启用)
        if self.compress:
            snapshot_bytes = gzip.compress(snapshot_bytes)

        # 原子写入
        snapshot_path = self._get_snapshot_path(snapshot.canvas_path, snapshot.id)
        fd, temp_path = tempfile.mkstemp(dir=snapshots_dir, suffix=".tmp")
        try:
            os.write(fd, snapshot_bytes)
            os.close(fd)
            os.replace(temp_path, snapshot_path)
        except Exception:
            os.close(fd)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

        # 更新索引
        await self._update_index(snapshot)

    async def _update_index(self, snapshot: Snapshot) -> None:
        """更新快照索引

        [Source: docs/architecture/rollback-recovery-architecture.md:182-210]
        """
        index_path = self._get_index_path(snapshot.canvas_path)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取现有索引
        index_entries = []
        if index_path.exists():
            data = index_path.read_bytes()
            index_entries = orjson.loads(data)

        # 添加新条目 (不包含完整canvas_data，只保存元数据)
        entry = {
            "id": snapshot.id,
            "timestamp": snapshot.timestamp.isoformat(),
            "type": snapshot.type.value,
            "canvas_path": snapshot.canvas_path,
            "last_operation_id": snapshot.last_operation_id,
            "metadata": snapshot.metadata.to_dict(),
        }
        index_entries.insert(0, entry)  # 最新的在前

        # 保存索引
        index_bytes = orjson.dumps(
            index_entries,
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )

        fd, temp_path = tempfile.mkstemp(dir=index_path.parent, suffix=".tmp")
        try:
            os.write(fd, index_bytes)
            os.close(fd)
            os.replace(temp_path, index_path)
        except Exception:
            os.close(fd)
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

        # 更新缓存
        self._index_cache[snapshot.canvas_path] = index_entries

    async def _cleanup_old_snapshots(self, canvas_path: str) -> int:
        """清理旧快照

        [Source: docs/architecture/rollback-recovery-architecture.md:212-290]
        当快照数量超过max_snapshots时,删除最旧的快照

        Returns:
            删除的快照数量
        """
        index_path = self._get_index_path(canvas_path)
        if not index_path.exists():
            return 0

        data = index_path.read_bytes()
        index_entries = orjson.loads(data)

        if len(index_entries) <= self.max_snapshots:
            return 0

        # 删除超出限制的旧快照
        deleted = 0
        entries_to_keep = index_entries[: self.max_snapshots]
        entries_to_delete = index_entries[self.max_snapshots :]

        for entry in entries_to_delete:
            snapshot_path = self._get_snapshot_path(canvas_path, entry["id"])
            if snapshot_path.exists():
                snapshot_path.unlink()
                deleted += 1

        # 更新索引
        index_bytes = orjson.dumps(
            entries_to_keep,
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )
        index_path.write_bytes(index_bytes)

        # 更新缓存
        self._index_cache[canvas_path] = entries_to_keep

        return deleted

    async def get_snapshot(self, canvas_path: str, snapshot_id: str) -> Optional[Snapshot]:
        """获取快照

        Args:
            canvas_path: Canvas文件路径
            snapshot_id: 快照ID

        Returns:
            Snapshot对象,如果不存在则返回None
        """
        snapshot_path = self._get_snapshot_path(canvas_path, snapshot_id)
        if not snapshot_path.exists():
            return None

        data = snapshot_path.read_bytes()

        # 解压 (如果压缩)
        if self.compress:
            data = gzip.decompress(data)

        snapshot_dict = orjson.loads(data)
        return Snapshot.from_dict(snapshot_dict)

    async def list_snapshots(
        self,
        canvas_path: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出Canvas的快照

        [Source: docs/architecture/rollback-recovery-architecture.md:312-326]

        Args:
            canvas_path: Canvas文件路径
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            快照索引条目列表 (不含完整canvas_data)
        """
        # 检查缓存
        if canvas_path in self._index_cache:
            entries = self._index_cache[canvas_path]
            return entries[offset : offset + limit]

        # 从磁盘读取
        index_path = self._get_index_path(canvas_path)
        if not index_path.exists():
            return []

        data = index_path.read_bytes()
        index_entries = orjson.loads(data)

        # 更新缓存
        self._index_cache[canvas_path] = index_entries

        return index_entries[offset : offset + limit]

    async def get_total_count(self, canvas_path: str) -> int:
        """获取快照总数

        Args:
            canvas_path: Canvas文件路径

        Returns:
            快照总数
        """
        # 检查缓存
        if canvas_path in self._index_cache:
            return len(self._index_cache[canvas_path])

        index_path = self._get_index_path(canvas_path)
        if not index_path.exists():
            return 0

        data = index_path.read_bytes()
        index_entries = orjson.loads(data)

        # 更新缓存
        self._index_cache[canvas_path] = index_entries

        return len(index_entries)

    async def delete_snapshot(self, canvas_path: str, snapshot_id: str) -> bool:
        """删除快照

        Args:
            canvas_path: Canvas文件路径
            snapshot_id: 快照ID

        Returns:
            是否成功删除
        """
        async with self._get_lock(canvas_path):
            # 删除快照文件
            snapshot_path = self._get_snapshot_path(canvas_path, snapshot_id)
            if not snapshot_path.exists():
                return False

            snapshot_path.unlink()

            # 更新索引
            index_path = self._get_index_path(canvas_path)
            if index_path.exists():
                data = index_path.read_bytes()
                index_entries = orjson.loads(data)

                # 移除条目
                index_entries = [e for e in index_entries if e["id"] != snapshot_id]

                index_bytes = orjson.dumps(
                    index_entries,
                    option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
                )
                index_path.write_bytes(index_bytes)

                # 更新缓存
                self._index_cache[canvas_path] = index_entries

            return True

    # ═══════════════════════════════════════════════════════════════════════════════
    # 自动快照功能
    # ═══════════════════════════════════════════════════════════════════════════════

    async def start_auto_snapshot(self, canvas_path: str) -> None:
        """启动自动快照任务

        [Source: docs/architecture/rollback-recovery-architecture.md:252-280]

        Args:
            canvas_path: Canvas文件路径
        """
        if canvas_path in self._auto_tasks:
            return

        # ✅ Verified from Context7:/python/cpython (topic: asyncio.create_task)
        task = asyncio.create_task(self._auto_snapshot_loop(canvas_path))
        self._auto_tasks[canvas_path] = task

    async def stop_auto_snapshot(self, canvas_path: str) -> None:
        """停止自动快照任务

        [Source: docs/architecture/rollback-recovery-architecture.md:252-280]

        Args:
            canvas_path: Canvas文件路径
        """
        if canvas_path not in self._auto_tasks:
            return

        task = self._auto_tasks.pop(canvas_path)
        task.cancel()

        # ✅ Verified from Context7:/python/cpython (topic: asyncio.CancelledError)
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def stop_all_auto_snapshots(self) -> None:
        """停止所有自动快照任务"""
        canvas_paths = list(self._auto_tasks.keys())
        for canvas_path in canvas_paths:
            await self.stop_auto_snapshot(canvas_path)

    def is_auto_snapshot_running(self, canvas_path: str) -> bool:
        """检查自动快照是否运行中

        Args:
            canvas_path: Canvas文件路径

        Returns:
            是否运行中
        """
        return canvas_path in self._auto_tasks and not self._auto_tasks[canvas_path].done()

    async def _auto_snapshot_loop(self, canvas_path: str) -> None:
        """自动快照循环

        [Source: docs/architecture/rollback-recovery-architecture.md:252-280]
        """
        while True:
            # ✅ Verified from Context7:/python/cpython (topic: asyncio.sleep)
            await asyncio.sleep(self.auto_interval)

            try:
                await self.create_snapshot(
                    canvas_path,
                    SnapshotType.AUTO,
                    description="Auto snapshot",
                )
            except Exception:
                # 记录错误但继续循环
                # [Source: docs/stories/18.2.story.md - ADR-0009 Error Handling]
                pass

    # ═══════════════════════════════════════════════════════════════════════════════
    # 便捷方法
    # ═══════════════════════════════════════════════════════════════════════════════

    async def create_checkpoint(
        self,
        canvas_path: str,
        description: str = "Pre-rollback checkpoint",
    ) -> Snapshot:
        """创建检查点快照 (回滚前自动调用)

        [Source: docs/architecture/rollback-recovery-architecture.md:212-290]

        Args:
            canvas_path: Canvas文件路径
            description: 描述

        Returns:
            创建的Snapshot对象
        """
        return await self.create_snapshot(
            canvas_path,
            SnapshotType.CHECKPOINT,
            description=description,
            created_by="rollback_engine",
        )

    async def get_latest_snapshot(self, canvas_path: str) -> Optional[Snapshot]:
        """获取最新的快照

        Args:
            canvas_path: Canvas文件路径

        Returns:
            最新的Snapshot对象,如果不存在则返回None
        """
        entries = await self.list_snapshots(canvas_path, limit=1)
        if not entries:
            return None

        return await self.get_snapshot(canvas_path, entries[0]["id"])

    def clear_cache(self, canvas_path: Optional[str] = None) -> None:
        """清除索引缓存

        Args:
            canvas_path: Canvas路径,为None时清除所有缓存
        """
        if canvas_path:
            self._index_cache.pop(canvas_path, None)
        else:
            self._index_cache.clear()
