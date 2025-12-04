# src/rollback/graph_sync_service.py
"""
Graph Sync Service - Graphiti知识图谱同步服务

Story 18.4: Graph Sync Service - Graphiti知识图谱同步
- AC 1: 集成现有GraphitiClient
- AC 2: 回滚后使用add_episode()同步节点状态
- AC 3: 已删除节点在图谱中标记deleted_at(软删除)
- AC 4: 回滚结果包含graphSyncStatus: synced/pending/skipped
- AC 5: preserveGraph选项跳过图谱同步
- AC 6: 图谱同步失败不阻塞回滚成功(优雅降级)
- AC 7: Graphiti操作超时200ms

[Source: docs/architecture/rollback-recovery-architecture.md:180-210]
[Source: docs/stories/18.4.story.md]

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-04
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


class GraphSyncStatus(str, Enum):
    """
    图谱同步状态枚举

    [Source: docs/architecture/rollback-recovery-architecture.md:180-190]

    Attributes:
        SYNCED: 同步成功
        PENDING: 同步待处理
        SKIPPED: 同步被跳过
        FAILED: 同步失败（但回滚成功）
    """
    SYNCED = "synced"
    PENDING = "pending"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class SyncResult:
    """
    同步结果数据类

    [Source: docs/architecture/rollback-recovery-architecture.md:190-200]

    Attributes:
        status: 同步状态
        synced_nodes: 已同步的节点ID列表
        deleted_nodes: 软删除的节点ID列表
        episode_id: Graphiti episode ID
        error: 错误信息（如果有）
        latency_ms: 同步耗时（毫秒）
    """
    status: GraphSyncStatus
    synced_nodes: List[str] = field(default_factory=list)
    deleted_nodes: List[str] = field(default_factory=list)
    episode_id: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0.0


class GraphSyncService:
    """
    Graphiti知识图谱同步服务

    负责在回滚操作后同步Canvas状态到Graphiti知识图谱。

    [Source: docs/architecture/rollback-recovery-architecture.md:180-210]
    [Source: docs/stories/18.4.story.md - AC 1-7]

    Features:
        - 集成GraphitiClient进行图谱操作
        - 使用add_episode()记录回滚事件
        - 软删除标记已删除节点
        - 200ms超时保护
        - 优雅降级（同步失败不阻塞回滚）

    Usage:
        >>> service = GraphSyncService()
        >>> result = await service.sync_rollback(
        ...     canvas_path="离散数学.canvas",
        ...     rollback_type="snapshot",
        ...     affected_nodes=["node-1", "node-2"],
        ...     deleted_nodes=["node-3"]
        ... )
        >>> print(result.status)
        GraphSyncStatus.SYNCED
    """

    # ✅ AC 7: Graphiti操作超时200ms
    DEFAULT_TIMEOUT_MS = 200

    def __init__(
        self,
        graphiti_client: Optional[Any] = None,
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        enable_fallback: bool = True,
    ):
        """
        初始化GraphSyncService

        [Source: docs/architecture/rollback-recovery-architecture.md:180-190]

        Args:
            graphiti_client: GraphitiClient实例（可选，用于依赖注入）
            timeout_ms: 超时时间（毫秒），默认200ms
            enable_fallback: 启用优雅降级
        """
        self._client = graphiti_client
        self._timeout_ms = timeout_ms
        self._enable_fallback = enable_fallback
        self._initialized = False

    async def initialize(self) -> bool:
        """
        初始化服务，创建GraphitiClient

        [Source: docs/stories/18.4.story.md - AC 1]

        Returns:
            True if initialized successfully
        """
        if self._initialized:
            return True

        try:
            if self._client is None:
                # ✅ AC 1: 集成现有GraphitiClient
                from src.agentic_rag.clients.graphiti_client import GraphitiClient
                self._client = GraphitiClient(
                    timeout_ms=self._timeout_ms,
                    enable_fallback=self._enable_fallback,
                )

            # 初始化客户端
            if hasattr(self._client, 'initialize'):
                await self._client.initialize()

            self._initialized = True

            if LOGURU_ENABLED:
                logger.info("GraphSyncService initialized successfully")

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"GraphSyncService initialization failed: {e}")

            # ✅ AC 6: 初始化失败不阻塞
            if self._enable_fallback:
                self._initialized = True  # 标记为已初始化，使用降级模式
                return False
            else:
                raise

    async def sync_rollback(
        self,
        canvas_path: str,
        rollback_type: str,
        affected_nodes: Optional[List[str]] = None,
        deleted_nodes: Optional[List[str]] = None,
        restored_data: Optional[Dict[str, Any]] = None,
        preserve_graph: bool = False,
    ) -> SyncResult:
        """
        同步回滚操作到Graphiti知识图谱

        [Source: docs/architecture/rollback-recovery-architecture.md:190-210]
        [Source: docs/stories/18.4.story.md - AC 2-6]

        Args:
            canvas_path: Canvas文件路径
            rollback_type: 回滚类型 (operation/snapshot/timepoint)
            affected_nodes: 受影响的节点ID列表
            deleted_nodes: 被删除的节点ID列表
            restored_data: 恢复的Canvas数据
            preserve_graph: 是否跳过图谱同步

        Returns:
            SyncResult: 同步结果
        """
        import time
        start_time = time.perf_counter()

        # ✅ AC 5: preserveGraph选项跳过图谱同步
        if preserve_graph:
            if LOGURU_ENABLED:
                logger.info(
                    f"GraphSyncService: Skipping sync for {canvas_path} "
                    "(preserve_graph=True)"
                )
            return SyncResult(
                status=GraphSyncStatus.SKIPPED,
                latency_ms=0.0,
            )

        # 确保已初始化
        if not self._initialized:
            await self.initialize()

        try:
            # ✅ AC 7: 200ms超时保护
            timeout_seconds = self._timeout_ms / 1000.0

            result = await asyncio.wait_for(
                self._do_sync(
                    canvas_path=canvas_path,
                    rollback_type=rollback_type,
                    affected_nodes=affected_nodes or [],
                    deleted_nodes=deleted_nodes or [],
                    restored_data=restored_data,
                ),
                timeout=timeout_seconds,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000
            result.latency_ms = latency_ms

            if LOGURU_ENABLED:
                logger.info(
                    f"GraphSyncService: Sync completed for {canvas_path}, "
                    f"status={result.status.value}, latency={latency_ms:.2f}ms"
                )

            return result

        except asyncio.TimeoutError:
            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.warning(
                    f"GraphSyncService: Sync timeout for {canvas_path} "
                    f"({self._timeout_ms}ms)"
                )

            # ✅ AC 6: 超时不阻塞回滚
            if self._enable_fallback:
                return SyncResult(
                    status=GraphSyncStatus.PENDING,
                    error=f"Sync timeout after {self._timeout_ms}ms",
                    latency_ms=latency_ms,
                )
            else:
                raise

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.error(f"GraphSyncService: Sync failed for {canvas_path}: {e}")

            # ✅ AC 6: 同步失败不阻塞回滚
            if self._enable_fallback:
                return SyncResult(
                    status=GraphSyncStatus.FAILED,
                    error=str(e),
                    latency_ms=latency_ms,
                )
            else:
                raise

    async def _do_sync(
        self,
        canvas_path: str,
        rollback_type: str,
        affected_nodes: List[str],
        deleted_nodes: List[str],
        restored_data: Optional[Dict[str, Any]],
    ) -> SyncResult:
        """
        执行实际的同步操作

        [Source: docs/stories/18.4.story.md - AC 2-3]
        """
        synced_nodes: List[str] = []
        soft_deleted_nodes: List[str] = []
        episode_id: Optional[str] = None

        # 检查客户端是否可用
        if self._client is None:
            return SyncResult(
                status=GraphSyncStatus.FAILED,
                error="GraphitiClient not available",
            )

        # ✅ AC 2: 使用add_episode()同步节点状态
        try:
            # 构建回滚事件内容
            episode_content = self._build_episode_content(
                canvas_path=canvas_path,
                rollback_type=rollback_type,
                affected_nodes=affected_nodes,
                deleted_nodes=deleted_nodes,
            )

            # 添加episode到Graphiti
            if hasattr(self._client, 'add_episode'):
                episode_id = await self._client.add_episode(
                    content=episode_content,
                    canvas_file=canvas_path,
                    metadata={
                        "event_type": "rollback",
                        "rollback_type": rollback_type,
                        "affected_nodes": affected_nodes,
                        "deleted_nodes": deleted_nodes,
                    }
                )

                if episode_id:
                    synced_nodes = affected_nodes.copy()

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"add_episode failed: {e}")

        # ✅ AC 3: 已删除节点软删除标记
        for node_id in deleted_nodes:
            try:
                success = await self._mark_node_deleted(
                    canvas_path=canvas_path,
                    node_id=node_id,
                )
                if success:
                    soft_deleted_nodes.append(node_id)
            except Exception as e:
                if LOGURU_ENABLED:
                    logger.warning(f"Failed to soft-delete node {node_id}: {e}")

        # ✅ AC 4: 确定同步状态
        if episode_id and len(synced_nodes) == len(affected_nodes):
            status = GraphSyncStatus.SYNCED
        elif episode_id or synced_nodes:
            status = GraphSyncStatus.PENDING  # 部分成功
        else:
            status = GraphSyncStatus.FAILED

        return SyncResult(
            status=status,
            synced_nodes=synced_nodes,
            deleted_nodes=soft_deleted_nodes,
            episode_id=episode_id,
        )

    def _build_episode_content(
        self,
        canvas_path: str,
        rollback_type: str,
        affected_nodes: List[str],
        deleted_nodes: List[str],
    ) -> str:
        """
        构建回滚事件的episode内容

        [Source: docs/stories/18.4.story.md - AC 2]
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        content_parts = [
            "[Canvas Rollback Event]",
            f"Canvas: {canvas_path}",
            f"Type: {rollback_type}",
            f"Timestamp: {timestamp}",
        ]

        if affected_nodes:
            content_parts.append(f"Affected nodes: {', '.join(affected_nodes)}")

        if deleted_nodes:
            content_parts.append(f"Deleted nodes: {', '.join(deleted_nodes)}")

        return "\n".join(content_parts)

    async def _mark_node_deleted(
        self,
        canvas_path: str,
        node_id: str,
    ) -> bool:
        """
        在Graphiti中标记节点为软删除

        [Source: docs/stories/18.4.story.md - AC 3]

        Args:
            canvas_path: Canvas文件路径
            node_id: 节点ID

        Returns:
            success: 是否成功标记
        """
        if self._client is None:
            return False

        try:
            # 使用add_memory记录删除事件
            if hasattr(self._client, 'add_memory'):
                deleted_at = datetime.now(timezone.utc).isoformat()

                success = await self._client.add_memory(
                    key=f"deleted_node_{node_id}",
                    content=f"Node {node_id} deleted from {canvas_path} at {deleted_at}",
                    importance=3,  # 中等重要性
                    tags=["deleted", "rollback", canvas_path],
                )

                if LOGURU_ENABLED and success:
                    logger.debug(f"Soft-deleted node {node_id} in Graphiti")

                return success

            return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"_mark_node_deleted failed: {e}")
            return False

    async def sync_node_state(
        self,
        canvas_path: str,
        node_id: str,
        node_data: Dict[str, Any],
        operation: str = "update",
    ) -> bool:
        """
        同步单个节点状态到Graphiti

        [Source: docs/stories/18.4.story.md - AC 2]

        Args:
            canvas_path: Canvas文件路径
            node_id: 节点ID
            node_data: 节点数据
            operation: 操作类型 (add/update/delete)

        Returns:
            success: 是否成功
        """
        if not self._initialized:
            await self.initialize()

        if self._client is None:
            return False

        try:
            # 构建内容
            content = (
                f"[Node {operation.upper()}] "
                f"Canvas: {canvas_path}, "
                f"Node: {node_id}, "
                f"Type: {node_data.get('type', 'unknown')}"
            )

            if 'text' in node_data:
                text_preview = node_data['text'][:100]
                content += f", Text: {text_preview}"

            # 添加episode
            if hasattr(self._client, 'add_episode'):
                episode_id = await self._client.add_episode(
                    content=content,
                    canvas_file=canvas_path,
                    metadata={
                        "node_id": node_id,
                        "operation": operation,
                        "node_type": node_data.get("type"),
                    }
                )
                return episode_id is not None

            return False

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"sync_node_state failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取服务统计信息"""
        return {
            "initialized": self._initialized,
            "timeout_ms": self._timeout_ms,
            "enable_fallback": self._enable_fallback,
            "client_available": self._client is not None,
        }
