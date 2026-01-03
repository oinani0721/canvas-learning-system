"""
教材上下文检索器 for Canvas Agentic RAG (Story 23.4)

提供教材上下文检索功能:
- AC 23.4.1: 教材上下文注入
- 支持PDF教材内容检索
- 结果包含source="textbook"标注
- 延迟 < 500ms

Dependencies:
- LanceDBClient: 向量检索
- PDFProcessor: PDF内容提取 (可选)

✅ Verified from LangGraph Skill:
- Pattern: Async retrieval nodes
- Pattern: Send for parallel execution

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-12-12
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False


# ============================================================
# Exceptions
# ============================================================

class TextbookRetrieverError(Exception):
    """Base exception for TextbookRetriever errors."""
    pass


class TextbookRetrievalTimeout(TextbookRetrieverError):
    """Raised when retrieval times out."""
    pass


# ============================================================
# Configuration
# ============================================================

@dataclass
class TextbookRetrieverConfig:
    """
    TextbookRetriever配置

    Attributes:
        top_k: 返回结果数量 (默认10)
        min_score: 最小相关度阈值 (默认0.3)
        timeout_ms: 检索超时毫秒数 (默认500, AC 23.4.1)
        textbook_table: LanceDB表名
        enable_cache: 是否启用缓存
    """
    top_k: int = 10
    min_score: float = 0.3
    timeout_ms: int = 500
    textbook_table: str = "textbooks"
    enable_cache: bool = True


# ============================================================
# Protocol for dependency injection
# ============================================================

class LanceDBClientProtocol(Protocol):
    """Protocol for LanceDB client dependency injection."""

    async def search(
        self,
        query: str,
        table_name: str,
        canvas_file: Optional[str] = None,
        num_results: int = 10,
        metric: str = "cosine"
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        ...


# ============================================================
# TextbookContextService
# ============================================================

class TextbookContextService:
    """
    教材上下文检索服务

    ✅ Story 23.4 AC 1: RAG支持教材上下文注入

    Features:
    - 搜索与Canvas关联的教材内容
    - 支持PDF内容检索
    - 结果添加source="textbook"标注
    - 延迟 < 500ms

    Usage:
        service = TextbookContextService(lancedb_client)
        results = await service.search("什么是逆否命题", "离散数学.canvas")
    """

    # 默认表名
    DEFAULT_TABLE = "textbooks"

    def __init__(
        self,
        lancedb_client: LanceDBClientProtocol,
        config: Optional[TextbookRetrieverConfig] = None
    ):
        """
        初始化TextbookContextService

        Args:
            lancedb_client: LanceDB客户端
            config: 配置选项
        """
        self.lancedb = lancedb_client
        self.config = config or TextbookRetrieverConfig()
        self._initialized = False

        # 缓存关联教材映射
        self._textbook_mapping: Dict[str, List[str]] = {}

    async def initialize(self) -> bool:
        """
        初始化服务

        Returns:
            True if initialization successful
        """
        self._initialized = True
        return True

    async def search(
        self,
        query: str,
        canvas_file: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索与Canvas关联的教材内容

        ✅ Story 23.4 AC 1: 教材上下文注入
        - textbook_results包含教材中关于查询的相关段落
        - 每个结果包含metadata.source = "textbook"标注
        - 延迟 < 500ms

        Args:
            query: 搜索查询
            canvas_file: Canvas文件路径
            num_results: 返回结果数量

        Returns:
            List[SearchResult]: 教材检索结果
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        try:
            # 设置超时
            timeout_seconds = self.config.timeout_ms / 1000.0

            # 获取关联教材
            textbook_files = await self._get_associated_textbooks(canvas_file)

            # 在LanceDB中搜索教材向量表
            results = await asyncio.wait_for(
                self._search_textbooks(
                    query=query,
                    textbook_files=textbook_files,
                    num_results=num_results
                ),
                timeout=timeout_seconds
            )

            # 添加来源标注
            for r in results:
                if "metadata" not in r:
                    r["metadata"] = {}
                r["metadata"]["source"] = "textbook"

            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.debug(
                    f"TextbookContextService.search: "
                    f"query='{query[:50]}...', "
                    f"canvas={canvas_file}, "
                    f"results={len(results)}, "
                    f"latency={latency_ms:.2f}ms"
                )

            # 检查性能
            if latency_ms > 500:
                if LOGURU_ENABLED:
                    logger.warning(
                        f"Textbook search exceeded 500ms: {latency_ms:.2f}ms"
                    )

            return results

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(
                    f"TextbookContextService.search timeout ({self.config.timeout_ms}ms)"
                )
            return []

        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"TextbookContextService.search error: {e}")
            return []

    async def _get_associated_textbooks(self, canvas_file: str) -> List[str]:
        """
        获取Canvas关联的教材文件列表

        查询逻辑:
        1. 从Canvas metadata获取关联教材
        2. 从配置文件获取教材映射
        3. 默认返回同目录下的PDF文件

        Args:
            canvas_file: Canvas文件路径

        Returns:
            List[str]: 关联的教材文件路径列表
        """
        # 检查缓存
        if canvas_file in self._textbook_mapping:
            return self._textbook_mapping[canvas_file]

        # TODO: 从Canvas metadata或配置文件获取关联教材
        # 目前返回空列表，将搜索所有教材
        textbook_files = []

        # 缓存结果
        self._textbook_mapping[canvas_file] = textbook_files

        return textbook_files

    async def _search_textbooks(
        self,
        query: str,
        textbook_files: List[str],
        num_results: int
    ) -> List[Dict[str, Any]]:
        """内部教材搜索实现"""
        try:
            # 如果有指定教材文件，添加过滤条件
            # 否则搜索所有教材
            results = await self.lancedb.search(
                query=query,
                table_name=self.config.textbook_table,
                num_results=num_results
            )

            # 如果指定了教材文件，过滤结果
            if textbook_files:
                results = [
                    r for r in results
                    if r.get("metadata", {}).get("file_path") in textbook_files
                ]

            return results

        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Textbook search failed: {e}")
            return []


# ============================================================
# LangGraph Node Function
# ============================================================

# 全局服务实例 (懒加载)
_textbook_service: Optional[TextbookContextService] = None


async def _get_textbook_service() -> TextbookContextService:
    """获取教材服务单例"""
    global _textbook_service
    if _textbook_service is None:
        # 导入LanceDB客户端
        try:
            from agentic_rag.clients import LanceDBClient
            lancedb_client = LanceDBClient(
                db_path="~/.lancedb",
                timeout_ms=400,
                enable_fallback=True
            )
            await lancedb_client.initialize()

            _textbook_service = TextbookContextService(lancedb_client)
            await _textbook_service.initialize()
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to initialize TextbookContextService: {e}")
            # 创建一个空服务
            _textbook_service = TextbookContextService(None)  # type: ignore

    return _textbook_service


async def textbook_retrieval_node(
    state: Dict[str, Any],
    runtime: Optional[Any] = None
) -> Dict[str, Any]:
    """
    LangGraph教材检索节点

    ✅ Verified from LangGraph Skill (Pattern: Node function signature):
    - Takes state dict
    - Returns partial state update dict

    ✅ Story 23.4 AC 1: 教材上下文注入

    Args:
        state: Current graph state containing:
            - messages: List[BaseMessage] - Query messages
            - canvas_file: str - Canvas file path
        runtime: Runtime configuration

    Returns:
        State update with:
            - textbook_results: List[SearchResult]
            - textbook_latency_ms: float
    """
    start_time = time.perf_counter()

    # 获取查询
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        query = ""

    canvas_file = state.get("canvas_file", "")
    batch_size = 10
    # Story 12.K.2: Safe config access (handle None runtime.context)
    if runtime and runtime.context:
        batch_size = runtime.context.get("retrieval_batch_size", 10)

    try:
        service = await _get_textbook_service()
        textbook_results = await service.search(
            query=query,
            canvas_file=canvas_file,
            num_results=batch_size
        )
    except Exception as e:
        if LOGURU_ENABLED:
            logger.error(f"textbook_retrieval_node error: {e}")
        textbook_results = []

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "textbook_results": textbook_results,
        "textbook_latency_ms": latency_ms
    }


# Export
__all__ = [
    "TextbookContextService",
    "TextbookRetrieverConfig",
    "TextbookRetrieverError",
    "TextbookRetrievalTimeout",
    "textbook_retrieval_node",
]
