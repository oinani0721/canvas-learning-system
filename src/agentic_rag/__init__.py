"""
Agentic RAG - Canvas Learning System智能检索增强生成系统

基于LangGraph构建的多层记忆检索与质量控制编排系统。

Architecture:
- Layer 1: Graphiti时序知识图谱 (概念关系 + 学习历史)
- Layer 2: LanceDB向量数据库 (语义检索)
- Layer 3: Temporal Memory (FSRS遗忘曲线 + 学习行为)

Core Features:
- 并行检索 (Send模式)
- 3种融合算法 (RRF, Weighted, Cascade)
- 混合Reranking (Local + Cohere)
- 质量控制循环 (Query重写)

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-11-29
Updated: 2025-12-12
Story: 23.1 - LangGraph导入问题修复
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# ============================================================
# Setup Logging (AC 4: 导入诊断日志)
# ============================================================

logger = logging.getLogger(__name__)

# ============================================================
# Path Configuration (Fix: 确保src/在sys.path中)
# ✅ Verified: 需要将src/目录添加到sys.path才能使用绝对导入
# ============================================================

_src_path = str(Path(__file__).parent.parent)
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
    logger.debug(f"Added {_src_path} to sys.path for agentic_rag imports")

# ============================================================
# Import with Fallback (AC 1, AC 4)
# ============================================================

# Availability flag for external modules to check
AGENTIC_RAG_AVAILABLE: bool = False
_IMPORT_ERROR: Optional[str] = None

# Placeholder exports (will be replaced on successful import)
CanvasRAGState = None
CanvasRAGConfig = None
canvas_agentic_rag = None

try:
    # Step 1: Import state schema
    logger.debug("Importing CanvasRAGState from agentic_rag.state...")
    from agentic_rag.state import CanvasRAGState

    # Step 2: Import config schema
    logger.debug("Importing CanvasRAGConfig from agentic_rag.config...")
    from agentic_rag.config import CanvasRAGConfig

    # Step 3: Import compiled StateGraph
    logger.debug("Importing canvas_agentic_rag from agentic_rag.state_graph...")
    from agentic_rag.state_graph import canvas_agentic_rag

    # All imports successful
    AGENTIC_RAG_AVAILABLE = True
    logger.info("Agentic RAG module loaded successfully. AGENTIC_RAG_AVAILABLE=True")

except ImportError as e:
    AGENTIC_RAG_AVAILABLE = False
    _IMPORT_ERROR = str(e)

    # AC 4: 详细诊断日志
    logger.error(f"Failed to import agentic_rag components: {e}")
    logger.error("=" * 60)
    logger.error("AGENTIC RAG IMPORT DIAGNOSTIC")
    logger.error("=" * 60)
    logger.error(f"Error Type: {type(e).__name__}")
    logger.error(f"Error Message: {e}")
    logger.error("")
    logger.error("Possible causes:")
    logger.error("  1. Missing dependency - run: pip install -r backend/requirements.txt")
    logger.error("  2. LangGraph not installed - run: pip install langgraph>=0.2.0")
    logger.error("  3. langchain-core not installed - run: pip install langchain-core>=0.3.0")
    logger.error("")
    logger.error("Suggested fix:")
    logger.error("  cd backend && pip install -r requirements.txt")
    logger.error("=" * 60)

    # Keep placeholders as None for graceful degradation
    CanvasRAGState = None
    CanvasRAGConfig = None
    canvas_agentic_rag = None

except Exception as e:
    AGENTIC_RAG_AVAILABLE = False
    _IMPORT_ERROR = str(e)

    logger.error(f"Unexpected error importing agentic_rag: {type(e).__name__}: {e}")
    logger.error("Please check the full traceback in debug mode.")

    import traceback
    logger.debug(traceback.format_exc())


# ============================================================
# Utility Functions
# ============================================================

def get_import_error() -> Optional[str]:
    """
    Get the import error message if agentic_rag failed to load.

    Returns:
        Error message string if import failed, None otherwise.

    Example:
        >>> if not AGENTIC_RAG_AVAILABLE:
        ...     print(get_import_error())
    """
    return _IMPORT_ERROR


def check_dependencies() -> dict:
    """
    Check if all required dependencies are installed.

    Returns:
        Dictionary with dependency status.

    Example:
        >>> deps = check_dependencies()
        >>> print(deps)
        {'langgraph': True, 'langchain_core': True, 'lancedb': True, 'neo4j': True}
    """
    dependencies = {
        "langgraph": False,
        "langchain_core": False,
        "lancedb": False,
        "neo4j": False,
        "sentence_transformers": False,
    }

    # ✅ Verified from Python docs: use importlib.util.find_spec for availability check
    import importlib.util

    dependencies["langgraph"] = importlib.util.find_spec("langgraph") is not None
    dependencies["langchain_core"] = importlib.util.find_spec("langchain_core") is not None
    dependencies["lancedb"] = importlib.util.find_spec("lancedb") is not None
    dependencies["neo4j"] = importlib.util.find_spec("neo4j") is not None
    dependencies["sentence_transformers"] = importlib.util.find_spec("sentence_transformers") is not None

    return dependencies


# ============================================================
# Module Exports
# ============================================================

__version__ = "1.1.0"

__all__ = [
    # Core exports (may be None if import failed)
    "CanvasRAGState",
    "CanvasRAGConfig",
    "canvas_agentic_rag",
    # Availability flag
    "AGENTIC_RAG_AVAILABLE",
    # Utility functions
    "get_import_error",
    "check_dependencies",
]
