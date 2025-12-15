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
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ============================================================
# Path Configuration for agentic_rag import
# ✅ Verified: backend needs src/ in sys.path for agentic_rag
# ============================================================

# Add src/ to sys.path if not already present
_project_root = Path(__file__).parent.parent.parent.parent  # backend/app/services/ -> project root
_src_path = str(_project_root / "src")
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
        logger.info("RAGService: LangGraph/Agentic RAG available. LANGGRAPH_AVAILABLE=True")
    else:
        LANGGRAPH_AVAILABLE = False
        _IMPORT_ERROR = get_import_error() or "agentic_rag module loaded but components are None"
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

    [Source: backend/app/api/v1/endpoints/rag.py - 503 response]
    """
    pass


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

    async def query(
        self,
        query: str,
        canvas_file: Optional[str] = None,
        is_review_canvas: bool = False,
        fusion_strategy: Optional[str] = None,
        reranking_strategy: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
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
            is_review_canvas: Whether this is a review canvas (affects fusion strategy)
            config: Optional runtime configuration overrides

        Returns:
            Dict containing:
            - messages: Response messages
            - reranked_results: Final ranked results
            - quality_grade: Quality assessment

        Raises:
            RuntimeError: If LangGraph not available

        [Source: docs/stories/23.1.story.md#Step-4-创建rag_service.py]
        """
        if not LANGGRAPH_AVAILABLE:
            raise RAGUnavailableError(
                f"LangGraph not available. Cannot execute RAG query. "
                f"Error: {_IMPORT_ERROR}"
            )

        if not self._initialized:
            await self.initialize()

        # Build initial state
        # ✅ Verified from agentic_rag/state.py: CanvasRAGState schema
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "canvas_file": canvas_file,
            "is_review_canvas": is_review_canvas,
            "fusion_strategy": fusion_strategy or ("weighted" if is_review_canvas else "rrf"),
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
                initial_state,
                config=runtime_config
            )
            return result

        except RAGServiceError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"RAGService query failed: {e}")
            raise RAGServiceError(f"RAG query execution failed: {e}") from e

    async def get_weak_concepts(
        self,
        canvas_file: str,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Get weak concepts from Temporal Memory for a canvas file.

        Used by review canvas generation to identify concepts needing review.

        Args:
            canvas_file: Canvas file path
            limit: Maximum number of concepts to return

        Returns:
            List of weak concept dicts with stability, last_review, review_count

        [Source: backend/app/api/v1/endpoints/rag.py#get_weak_concepts]
        """
        if not LANGGRAPH_AVAILABLE:
            logger.warning("get_weak_concepts: LangGraph not available, returning empty list")
            return []

        # TODO: Implement actual weak concept retrieval from Temporal Memory
        # For now, return empty list (graceful degradation)
        logger.info(f"get_weak_concepts called for {canvas_file}, limit={limit}")
        return []

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
        self,
        query: str,
        canvas_file: Optional[str] = None,
        **kwargs
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
        if not LANGGRAPH_AVAILABLE:
            logger.warning(
                f"RAG query fallback: LangGraph not available. "
                f"Query: {query[:50]}..."
            )
            return {
                "messages": [],
                "reranked_results": [],
                "quality_grade": None,
                "error": _IMPORT_ERROR,
            }

        try:
            return await self.query(query, canvas_file, **kwargs)
        except Exception as e:
            logger.error(f"RAG query fallback due to error: {e}")
            return {
                "messages": [],
                "reranked_results": [],
                "quality_grade": None,
                "error": str(e),
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
