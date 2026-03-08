"""
Vault Notes 检索器 for Canvas Agentic RAG

提供 vault-wide .md 笔记检索功能:
- 从 LanceDB vault_notes 表中检索与查询相关的笔记段落
- 结果包含 source="vault_note" 标注
- 延迟 < 500ms

Dependencies:
- LanceDBClient: 向量检索

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2026-03-08
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

class VaultNotesRetrieverError(Exception):
    """Base exception for VaultNotesRetriever errors."""
    pass


class VaultNotesRetrievalTimeout(VaultNotesRetrieverError):
    """Raised when retrieval times out."""
    pass


# ============================================================
# Configuration
# ============================================================

@dataclass
class VaultNotesRetrieverConfig:
    """
    VaultNotesRetriever配置

    Attributes:
        top_k: 返回结果数量 (默认10)
        min_score: 最小相关度阈值 (默认0.3)
        timeout_ms: 检索超时毫秒数 (默认500)
        vault_notes_table: LanceDB表名
        enable_cache: 是否启用缓存
    """
    top_k: int = 10
    min_score: float = 0.3
    timeout_ms: int = 500
    vault_notes_table: str = "vault_notes"
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
# VaultNotesService
# ============================================================

class VaultNotesService:
    """
    Vault 笔记检索服务

    从 LanceDB vault_notes 表中检索与查询相关的 .md 笔记段落。

    Usage:
        service = VaultNotesService(lancedb_client)
        results = await service.search("A* admissible heuristic")
    """

    DEFAULT_TABLE = "vault_notes"

    def __init__(
        self,
        lancedb_client: LanceDBClientProtocol,
        config: Optional[VaultNotesRetrieverConfig] = None
    ):
        self.lancedb = lancedb_client
        self.config = config or VaultNotesRetrieverConfig()
        self._initialized = False

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def search(
        self,
        query: str,
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索 vault 笔记内容

        Args:
            query: 搜索查询
            num_results: 返回结果数量

        Returns:
            List[SearchResult]: 笔记检索结果，每个包含 source="vault_note"
        """
        start_time = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        try:
            timeout_seconds = self.config.timeout_ms / 1000.0

            results = await asyncio.wait_for(
                self.lancedb.search(
                    query=query,
                    table_name=self.config.vault_notes_table,
                    num_results=num_results
                ),
                timeout=timeout_seconds
            )

            # 添加来源标注
            for r in results:
                if "metadata" not in r:
                    r["metadata"] = {}
                r["metadata"]["source"] = "vault_note"

            latency_ms = (time.perf_counter() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.debug(
                    f"VaultNotesService.search: "
                    f"query='{query[:50]}...', "
                    f"results={len(results)}, "
                    f"latency={latency_ms:.2f}ms"
                )

            return results

        except asyncio.TimeoutError:
            if LOGURU_ENABLED:
                logger.warning(
                    f"VaultNotesService.search timeout ({self.config.timeout_ms}ms)"
                )
            return []

        except Exception as e:
            if LOGURU_ENABLED:
                logger.debug(f"Vault notes search failed (table may not exist yet): {e}")
            return []


# ============================================================
# LangGraph Node Function
# ============================================================

_vault_notes_service: Optional[VaultNotesService] = None


async def _get_vault_notes_service() -> VaultNotesService:
    """获取 vault notes 服务单例"""
    global _vault_notes_service
    if _vault_notes_service is None:
        try:
            from agentic_rag.clients import LanceDBClient
            from agentic_rag.config import LANCEDB_CONFIG
            lancedb_client = LanceDBClient(
                db_path=LANCEDB_CONFIG["db_path"],
                timeout_ms=400,
                enable_fallback=True
            )
            await lancedb_client.initialize()

            _vault_notes_service = VaultNotesService(lancedb_client)
            await _vault_notes_service.initialize()
        except Exception as e:
            if LOGURU_ENABLED:
                logger.error(f"Failed to initialize VaultNotesService: {e}")
            _vault_notes_service = VaultNotesService(None)  # type: ignore

    return _vault_notes_service


async def vault_notes_retrieval_node(
    state: Dict[str, Any],
    runtime: Optional[Any] = None
) -> Dict[str, Any]:
    """
    LangGraph vault notes 检索节点

    Args:
        state: Current graph state containing:
            - messages: List[BaseMessage] - Query messages
        runtime: Runtime configuration

    Returns:
        State update with:
            - vault_notes_results: List[SearchResult]
            - vault_notes_latency_ms: float
    """
    start_time = time.perf_counter()

    # 获取查询
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        query = last_msg.get("content", "") if isinstance(last_msg, dict) else getattr(last_msg, "content", "")
    else:
        query = ""

    batch_size = 10
    if runtime and runtime.context:
        batch_size = runtime.context.get("retrieval_batch_size", 10)

    try:
        service = await _get_vault_notes_service()
        vault_notes_results = await service.search(
            query=query,
            num_results=batch_size
        )
    except Exception as e:
        if LOGURU_ENABLED:
            logger.error(f"vault_notes_retrieval_node error: {e}")
        vault_notes_results = []

    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "vault_notes_results": vault_notes_results,
        "vault_notes_latency_ms": latency_ms
    }


# Export
__all__ = [
    "VaultNotesService",
    "VaultNotesRetrieverConfig",
    "VaultNotesRetrieverError",
    "VaultNotesRetrievalTimeout",
    "vault_notes_retrieval_node",
]
