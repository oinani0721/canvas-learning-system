# Canvas Learning System - RAG Service
# Story 23.1: LangGraph导入问题修复
# ✅ Verified from docs/stories/23.1.story.md#Dev-Notes
"""
RAG Service - Agentic RAG orchestration service.

Story 23.1 Implementation:
- AC-23.1.2: LANGGRAPH_AVAILABLE = True when import succeeds
- Provides async query interface for Agentic RAG
- Graceful degradation when LangGraph not available

[Source: docs/stories/23.1.story.md#Step-4-创建rag_service.py]
[Source: docs/architecture/ADR-003-AGENTIC-RAG-ARCHITECTURE.md]
"""

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

import structlog

from app.core.decision_tracker import log_decision

if TYPE_CHECKING:  # CARD-G4-2: 仅类型注解需要, 运行时走函数体内延迟 import
    from app.models.service_status import StatusedResult

logger = structlog.get_logger(__name__)

# ============================================================
# Path Configuration for agentic_rag import
# ✅ Verified: backend needs src/ in sys.path for agentic_rag
# ============================================================

# Add backend/lib to sys.path for agentic_rag imports
_project_root = Path(__file__).parent.parent.parent  # backend/app/services/ -> backend/
_src_path = str(_project_root / "lib")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
    logger.debug(f"RAGService: Added {_src_path} to sys.path")

# ============================================================
# Import Agentic RAG with availability check
# ============================================================

# AC-23.1.2: LANGGRAPH_AVAILABLE 标志
LANGGRAPH_AVAILABLE: bool = False
_IMPORT_ERROR: Optional[str] = None

try:
    # ✅ Verified from agentic_rag/__init__.py
    from agentic_rag import (
        AGENTIC_RAG_AVAILABLE,
        CanvasRAGConfig,
        canvas_agentic_rag,
        get_import_error,
    )

    if AGENTIC_RAG_AVAILABLE and canvas_agentic_rag is not None:
        LANGGRAPH_AVAILABLE = True
        logger.info(
            "RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True"
        )
    else:
        LANGGRAPH_AVAILABLE = False
        _IMPORT_ERROR = (
            get_import_error() or "agentic_rag module loaded but components are None"
        )
        logger.warning(f"RAGService: Agentic RAG not fully loaded: {_IMPORT_ERROR}")

except ImportError as e:
    LANGGRAPH_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    logger.warning(f"RAGService: LangGraph not available: {e}")

    # Define placeholders
    CanvasRAGConfig = None
    canvas_agentic_rag = None

except Exception as e:
    LANGGRAPH_AVAILABLE = False
    _IMPORT_ERROR = str(e)
    logger.error(f"RAGService: Unexpected error importing agentic_rag: {e}")

    CanvasRAGConfig = None
    canvas_agentic_rag = None


# ============================================================
# Custom Exceptions (Story 12.4 - RAG Endpoint Integration)
# ============================================================


class RAGServiceError(Exception):
    """
    Base exception for RAG service errors.

    Raised when RAG query execution fails.

    [Source: backend/app/api/v1/endpoints/rag.py - Error handling]
    """

    pass


class RAGUnavailableError(RAGServiceError):
    """
    Exception raised when RAG service is not available.

    This occurs when LangGraph is not installed or import fails.

    CARD-G4-2 (2026-08-28): 该异常语义收编进统一四态 —
    ``service_status`` 属性恒为 ``ServiceStatus.UNAVAILABLE.value``,
    API/调用方可直接映射, 不再各自解释裸字符串。

    [Source: backend/app/api/v1/endpoints/rag.py - 503 response]
    """

    service_status = "unavailable"  # ServiceStatus.UNAVAILABLE.value 镜像


# ============================================================
# RAG Service Class
# ============================================================


class RAGService:
    """
    RAG检索服务

    Story 23.1 Implementation:
    - Wraps canvas_agentic_rag StateGraph
    - Provides async query interface
    - Graceful degradation when LangGraph not available

    ✅ Verified from LangGraph Skill:
    - CompiledStateGraph.ainvoke() for async execution
    - State dict with messages key

    [Source: docs/stories/23.1.story.md#Step-4-创建rag_service.py]
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize RAGService.

        Args:
            config: Optional configuration dict for CanvasRAGConfig

        Raises:
            RuntimeError: If LangGraph not available and strict mode enabled

        [Source: docs/stories/23.1.story.md#Dev-Notes]
        """
        self._config = config or {}
        self._initialized = False

        if not LANGGRAPH_AVAILABLE:
            logger.warning(
                "RAGService initialized without LangGraph support. "
                f"Reason: {_IMPORT_ERROR}"
            )

    @property
    def is_available(self) -> bool:
        """Check if RAG functionality is available."""
        return LANGGRAPH_AVAILABLE

    @property
    def import_error(self) -> Optional[str]:
        """Get the import error message if LangGraph not available."""
        return _IMPORT_ERROR

    async def initialize(self) -> bool:
        """
        Initialize the service.

        Returns:
            True if initialization successful, False otherwise.
        """
        if self._initialized:
            return True

        if not LANGGRAPH_AVAILABLE:
            logger.warning("RAGService initialization skipped: LangGraph not available")
            return False

        # Verify StateGraph is compiled
        if not hasattr(canvas_agentic_rag, "ainvoke"):
            logger.error("RAGService: canvas_agentic_rag missing ainvoke method")
            return False

        self._initialized = True
        logger.info("RAGService initialized successfully")
        return True

    def _get_fallback_result(self, fallback_reason: str = "unknown") -> Dict[str, Any]:
        """
        Return a safe fallback result dict.

        Story 12.K.2: Ensures RAG queries never return None.

        Args:
            fallback_reason: Reason for using fallback (for logging/debugging)

        Returns:
            Dict with empty but valid structure for downstream processing
        """
        logger.warning(f"RAGService: Using fallback result, reason: {fallback_reason}")
        return {
            "messages": [],
            "results": [],
            "reranked_results": [],
            "fused_results": [],
            "multimodal_results": [],
            "quality_grade": None,
            "result_count": 0,
            "total_latency_ms": 0.0,
            "latency_ms": {},
            "metadata": {},
            "fallback_used": True,
            "fallback_reason": fallback_reason,
            # CARD-G4-2 (2026-08-28): 第三个「空结果」出口同样带四态 —
            # 走到这里意味着图执行没能产出状态 (如 ainvoke 返回 None),
            # 空载荷不可信 = unavailable, 不是 empty。
            "retrieval_status": "unavailable",
            "retrieval_status_reason": f"rag fallback: {fallback_reason}",
        }

    async def query(
        self,
        query: str,
        canvas_file: Optional[str] = None,
        subject_id: Optional[str] = None,
        cross_subject: bool = False,
        is_review_canvas: bool = False,
        fusion_strategy: Optional[str] = None,
        reranking_strategy: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute RAG query.

        ✅ Verified from LangGraph Skill (Pattern: StateGraph invocation):
        ```python
        result = await graph.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            config=config
        )
        ```

        Args:
            query: User query string
            canvas_file: Optional canvas file path for context
            subject_id: Optional subject for multi-subject scope isolation (Story 1.9)
            cross_subject: Whether to expand search to related subjects via Tag Jaccard
            is_review_canvas: Whether this is a review canvas (affects fusion strategy)
            fusion_strategy: Override fusion strategy
            reranking_strategy: Override reranking strategy
            config: Optional runtime configuration overrides

        Returns:
            Dict containing:
            - messages: Response messages
            - reranked_results: Final ranked results
            - quality_grade: Quality assessment

        Raises:
            RuntimeError: If LangGraph not available

        [Source: docs/stories/23.1.story.md#Step-4-创建rag_service.py]
        [Source: Story 1.9 Task 6 — retrieval scope isolation]
        """
        if not LANGGRAPH_AVAILABLE:
            # CARD-G4-2: 既有诚实单点收编统一四态 (枚举值替代裸字符串)
            from app.models.service_status import ServiceStatus

            log_decision(
                function="RAGService.query",
                input_summary={"query": query[:80]},
                output=ServiceStatus.UNAVAILABLE.value,
                reason=f"LangGraph not available: {_IMPORT_ERROR}",
            )
            raise RAGUnavailableError(
                f"LangGraph not available. Cannot execute RAG query. "
                f"Error: {_IMPORT_ERROR}"
            )

        if not self._initialized:
            await self.initialize()

        # Story 1.9: Resolve subject scope for retrieval isolation.
        # The `subject` field in the LangGraph state is read by retrieve_lancedb
        # and retrieve_graphiti nodes for scoped search.
        effective_subject = subject_id

        # Build initial state
        # ✅ Verified from agentic_rag/state.py: CanvasRAGState schema
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "canvas_file": canvas_file,
            "subject": effective_subject,
            "cross_subject": cross_subject,
            "is_review_canvas": is_review_canvas,
            "fusion_strategy": fusion_strategy
            or ("weighted" if is_review_canvas else "rrf"),
            "reranking_strategy": reranking_strategy or "hybrid_auto",
            "graphiti_results": [],
            "lancedb_results": [],
            "multimodal_results": [],
            "fused_results": [],
            "reranked_results": [],
            "query_rewritten": False,
            "rewrite_count": 0,
        }

        # Merge runtime config
        runtime_config = {**self._config, **(config or {})}

        try:
            # ✅ Verified from LangGraph Skill: ainvoke for async execution
            result = await canvas_agentic_rag.ainvoke(
                initial_state, config=runtime_config
            )

            # ✅ Epic 12.K.2: None value protection - ainvoke may return None
            if result is None:
                logger.warning(
                    f"RAGService: ainvoke returned None for query: {query[:50]}..."
                )
                return self._get_fallback_result(
                    fallback_reason="ainvoke_returned_none"
                )

            return result

        except RAGServiceError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"RAGService query failed: {e}")
            raise RAGServiceError(f"RAG query execution failed: {e}") from e

    async def get_weak_concepts_with_status(
        self, canvas_file: str, limit: int = 10
    ) -> "StatusedResult":
        """CARD-G4-2 (2026-08-28): get_weak_concepts 的四态版本。

        故障不再假装空结果: LangGraph 缺失/记忆客户端失败 → unavailable
        带 reason; 真无学习历史 → empty; 有弱概念 → ok。
        旧 ``get_weak_concepts`` 委托本方法保 list 契约。

        Returns:
            StatusedResult — items 为弱概念 dict 列表。
        """
        from app.models.service_status import StatusedResult

        if not LANGGRAPH_AVAILABLE:
            logger.warning(
                "get_weak_concepts: LangGraph not available (unavailable, not empty)"
            )
            return StatusedResult.unavailable(
                f"LangGraph not available: {_IMPORT_ERROR}"
            )

        # Story 36 fix: Query LearningMemoryClient for low-score concepts
        try:
            from app.clients.graphiti_client import get_learning_memory_client

            memory_client = get_learning_memory_client()
            # CARD-G4-2 Codex round-1 HIGH-9: initialize() 遇到坏 JSON /
            # 权限错误会**返回 False 而不抛异常**, 随后默认 _data 仍产出
            # []， 被报成 empty。检查布尔值即可, 无需动客户端对外契约。
            initialized = await memory_client.initialize()
            if initialized is False:
                return StatusedResult.unavailable(
                    "learning memory client initialize() returned False "
                    "(数据不可读 — 空结果不可信)"
                )

            history = await memory_client.get_learning_history(canvas_file, limit=100)
            if not history:
                logger.info(f"get_weak_concepts: no learning history for {canvas_file}")
                return StatusedResult.from_items([])

            # Aggregate by concept: keep lowest score per concept
            concept_map: Dict[str, Dict[str, Any]] = {}
            for entry in history:
                concept = entry.get("concept", "")
                if not concept:
                    continue
                score = entry.get("score", entry.get("quality_score", 0.5))
                existing = concept_map.get(concept)
                if existing is None or score < existing.get("score", 1.0):
                    concept_map[concept] = {
                        "concept": concept,
                        "score": score,
                        "stability": entry.get("stability", 0.0),
                        "last_review": entry.get(
                            "timestamp", entry.get("created_at", "")
                        ),
                        "review_count": entry.get("review_count", 1),
                        "canvas_file": canvas_file,
                    }

            # Sort by score ascending (weakest first), return top N
            weak = sorted(concept_map.values(), key=lambda x: x.get("score", 1.0))
            return StatusedResult.from_items(weak[:limit])

        except (RuntimeError, ConnectionError, OSError, KeyError, ValueError) as e:
            logger.warning(f"get_weak_concepts: failed to query learning memory: {e}")
            return StatusedResult.unavailable(f"{type(e).__name__}: {e}")

    async def get_weak_concepts(
        self, canvas_file: str, limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Get weak concepts from Temporal Memory for a canvas file.

        Used by review canvas generation to identify concepts needing review.

        CARD-G4-2 (2026-08-28): 兼容委托 — 保 list 契约 (存量调用方直接
        迭代), 状态语义在 ``get_weak_concepts_with_status``。新代码应改用
        状态方法, 本方法的空 list 无法区分「无数据」与「服务故障」。

        Args:
            canvas_file: Canvas file path
            limit: Maximum number of concepts to return

        Returns:
            List of weak concept dicts with stability, last_review, review_count

        [Source: backend/app/api/v1/endpoints/rag.py#get_weak_concepts]
        """
        result = await self.get_weak_concepts_with_status(canvas_file, limit=limit)
        return result.items

    def get_status(self) -> Dict[str, Any]:
        """
        Get RAG service status information.

        Returns:
            Dict with available, initialized, langgraph_available, import_error

        [Source: backend/app/api/v1/endpoints/rag.py#get_rag_status]
        """
        return {
            "available": LANGGRAPH_AVAILABLE,
            "initialized": self._initialized,
            "langgraph_available": LANGGRAPH_AVAILABLE,
            "import_error": _IMPORT_ERROR,
        }

    async def query_with_fallback(
        self, query: str, canvas_file: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Execute RAG query with graceful fallback.

        If LangGraph not available, returns empty result instead of raising.

        Args:
            query: User query string
            canvas_file: Optional canvas file path
            **kwargs: Additional arguments passed to query()

        Returns:
            Query result or empty fallback dict
        """
        # CARD-G4-2 (2026-08-28): fallback dict 加性带四态键 — 调用方可
        # 区分「空结果」和「RAG 挂了」(原 error 键保留, 状态键统一语义)。
        if not LANGGRAPH_AVAILABLE:
            logger.warning(
                f"RAG query fallback: LangGraph not available. Query: {query[:50]}..."
            )
            return {
                "messages": [],
                "results": [],
                "reranked_results": [],
                "multimodal_results": [],
                "quality_grade": None,
                "result_count": 0,
                "total_latency_ms": 0.0,
                "latency_ms": {},
                "metadata": {},
                "error": _IMPORT_ERROR,
                "retrieval_status": "unavailable",
                "retrieval_status_reason": f"LangGraph not available: {_IMPORT_ERROR}",
            }

        try:
            return await self.query(query, canvas_file, **kwargs)
        except Exception as e:
            logger.error(f"RAG query fallback due to error: {e}")
            return {
                "messages": [],
                "results": [],
                "reranked_results": [],
                "multimodal_results": [],
                "quality_grade": None,
                "result_count": 0,
                "total_latency_ms": 0.0,
                "latency_ms": {},
                "metadata": {},
                "error": str(e),
                "retrieval_status": "unavailable",
                "retrieval_status_reason": str(e),
            }


# ============================================================
# Singleton Pattern
# ============================================================

_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get RAG service singleton.

    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


# ============================================================
# Module Exports
# ============================================================

__all__ = [
    "RAGService",
    "RAGServiceError",
    "RAGUnavailableError",
    "get_rag_service",
    "LANGGRAPH_AVAILABLE",
]
