"""
TemporalClient - Temporal Memory 客户端封装

Story 12.4: Temporal Memory实现
- AC 4.1: FSRS库集成
- AC 4.2: 学习行为时序追踪
- AC 4.3: get_weak_concepts()返回低稳定性概念
- AC 4.4: update_behavior()更新FSRS卡片
- AC 4.5: 性能 (< 50ms)

封装现有的 TemporalMemory 类为异步接口，与 Agentic RAG StateGraph 集成。

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# ✅ Verified from Story 12.4 implementation
try:
    from fsrs import Rating

    from temporal_memory import TemporalMemory
    TEMPORAL_MEMORY_AVAILABLE = True
except ImportError:
    TEMPORAL_MEMORY_AVAILABLE = False
    Rating = None


class TemporalClient:
    """
    Temporal Memory 客户端封装

    将同步的 TemporalMemory 类封装为异步接口，用于 Agentic RAG 集成。

    ✅ Verified from Story 12.4 (docs/epics/EPIC-12-STORY-MAP.md):
    - AC 4.3: get_weak_concepts() 返回低稳定性概念
    - AC 4.5: 延迟 < 50ms

    Usage:
        >>> client = TemporalClient()
        >>> await client.initialize()
        >>> weak_concepts = await client.get_weak_concepts("离散数学.canvas")
        >>> print(weak_concepts[0])
        {'concept': '逆否命题', 'stability': 1.2, 'weakness_score': 0.82, ...}
    """

    def __init__(
        self,
        db_path: str = "learning_behavior.db",
        timeout_ms: int = 50,
        enable_fallback: bool = True
    ):
        """
        初始化 TemporalClient

        Args:
            db_path: SQLite数据库路径
            timeout_ms: 超时时间(毫秒), 默认50ms (Story 12.4 AC 4.5)
            enable_fallback: 启用降级(超时/错误时返回空结果)
        """
        self.db_path = db_path
        self.timeout_ms = timeout_ms
        self.enable_fallback = enable_fallback

        self._temporal_memory: Optional[TemporalMemory] = None
        self._initialized = False
        self._executor = ThreadPoolExecutor(max_workers=2)

    async def initialize(self) -> bool:
        """
        初始化客户端

        ✅ Story 12.4 AC 4.1: FSRS库集成

        Returns:
            True if initialization successful
        """
        if not TEMPORAL_MEMORY_AVAILABLE:
            if LOGURU_ENABLED:
                logger.warning(
                    "TemporalMemory not available. "
                    "Check: pip install fsrs>=4.1.0"
                )
            self._initialized = True
            return False

        try:
            # 在线程池中初始化 (SQLite 操作是同步的)
            loop = asyncio.get_event_loop()
            self._temporal_memory = await loop.run_in_executor(
                self._executor,
                lambda: TemporalMemory(db_path=self.db_path)
            )
            self._initialized = True

            if LOGURU_ENABLED:
                logger.info(
                    f"TemporalClient initialized: db_path={self.db_path}"
                )

            return True

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"TemporalClient initialization failed: {e}")

            self._initialized = True
            return False

    async def get_weak_concepts(
        self,
        canvas_file: str,
        limit: int = 10,
        stability_weight: float = 0.7,
        error_rate_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        获取薄弱概念

        ✅ Story 12.4 AC 4.3: get_weak_concepts()返回低稳定性概念
        - 权重: 70%低稳定性 + 30%高错误率
        - 延迟 < 50ms (AC 4.5)

        Args:
            canvas_file: Canvas文件路径
            limit: 返回结果数量
            stability_weight: 稳定性权重 (默认0.7)
            error_rate_weight: 错误率权重 (默认0.3)

        Returns:
            List[Dict]: 薄弱概念列表
            [
                {
                    "concept": str,
                    "stability": float,
                    "error_rate": float,
                    "weakness_score": float,
                    "last_review": str,
                    "reps": int
                }
            ]
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        if self._temporal_memory is None:
            return []

        try:
            # 设置超时
            timeout_seconds = self.timeout_ms / 1000.0

            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    lambda: self._temporal_memory.get_weak_concepts(
                        canvas_file=canvas_file,
                        limit=limit,
                        stability_weight=stability_weight,
                        error_rate_weight=error_rate_weight
                    )
                ),
                timeout=timeout_seconds
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.debug(
                    f"TemporalClient.get_weak_concepts: "
                    f"canvas={canvas_file}, "
                    f"results={len(results)}, "
                    f"latency={latency_ms:.2f}ms"
                )

            # ✅ AC 4.5: 检查性能
            if latency_ms > 50:
                if LOGURU_ENABLED:
                    logger.warning(
                        f"get_weak_concepts exceeded 50ms: {latency_ms:.2f}ms"
                    )

            return results

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(
                    f"TemporalClient.get_weak_concepts timeout ({self.timeout_ms}ms)"
                )

            if self.enable_fallback:
                return []
            else:
                raise

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"TemporalClient.get_weak_concepts error: {e}")

            if self.enable_fallback:
                return []
            else:
                raise

    async def update_behavior(
        self,
        concept: str,
        rating: int,
        canvas_file: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新FSRS卡片

        ✅ Story 12.4 AC 4.4: update_behavior()更新FSRS卡片
        - 输入: concept, rating (1-4分)
        - 更新: Card.difficulty, Card.stability, Card.due

        Args:
            concept: 概念名称
            rating: 评分 (1=Again, 2=Hard, 3=Good, 4=Easy)
            canvas_file: Canvas文件路径
            session_id: 会话ID (可选)

        Returns:
            Dict: 更新后的卡片状态
        """
        if not self._initialized:
            await self.initialize()

        if self._temporal_memory is None:
            return {}

        if not TEMPORAL_MEMORY_AVAILABLE or Rating is None:
            return {}

        try:
            # 转换rating数字为Rating枚举
            rating_map = {
                1: Rating.Again,
                2: Rating.Hard,
                3: Rating.Good,
                4: Rating.Easy
            }
            fsrs_rating = rating_map.get(rating, Rating.Good)

            # 在线程池中执行同步操作
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                lambda: self._temporal_memory.update_behavior(
                    concept=concept,
                    rating=fsrs_rating,
                    canvas_file=canvas_file,
                    session_id=session_id
                )
            )

            if LOGURU_ENABLED:
                logger.info(
                    f"Updated FSRS card: concept={concept}, "
                    f"rating={rating}, stability={result.get('stability', 0):.2f}"
                )

            return result

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"TemporalClient.update_behavior error: {e}")
            return {}

    async def record_behavior(
        self,
        canvas_file: str,
        concept: str,
        action_type: str,
        session_id: str,
        metadata: Optional[str] = None
    ) -> int:
        """
        记录学习行为

        ✅ Story 12.4 AC 4.2: 学习行为时序追踪

        Args:
            canvas_file: Canvas文件路径
            concept: 概念名称
            action_type: 行为类型 (explanation, decomposition, verification等)
            session_id: 会话ID
            metadata: JSON元数据 (可选)

        Returns:
            int: 插入的行ID
        """
        if not self._initialized:
            await self.initialize()

        if self._temporal_memory is None:
            return 0

        try:
            loop = asyncio.get_event_loop()
            row_id = await loop.run_in_executor(
                self._executor,
                lambda: self._temporal_memory.record_behavior(
                    canvas_file=canvas_file,
                    concept=concept,
                    action_type=action_type,
                    session_id=session_id,
                    metadata=metadata
                )
            )

            return row_id

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"TemporalClient.record_behavior error: {e}")
            return 0

    async def get_review_due_concepts(
        self,
        canvas_file: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取到期复习的概念

        Args:
            canvas_file: Canvas文件路径
            limit: 返回结果数量

        Returns:
            List[Dict]: 到期概念列表
        """
        if not self._initialized:
            await self.initialize()

        if self._temporal_memory is None:
            return []

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor,
                lambda: self._temporal_memory.get_review_due_concepts(
                    canvas_file=canvas_file,
                    limit=limit
                )
            )
            return results

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"TemporalClient.get_review_due_concepts error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "initialized": self._initialized,
            "db_path": self.db_path,
            "timeout_ms": self.timeout_ms,
            "enable_fallback": self.enable_fallback,
            "temporal_memory_available": TEMPORAL_MEMORY_AVAILABLE
        }

    async def close(self):
        """关闭客户端"""
        if self._temporal_memory is not None:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    self._executor,
                    self._temporal_memory.close
                )
            except Exception:
                pass

        self._executor.shutdown(wait=False)
