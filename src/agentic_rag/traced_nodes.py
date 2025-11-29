"""
带 LangSmith 追踪的节点实现

Story 12.12: LangSmith可观测性集成

包装原有节点函数，添加:
- @traceable 装饰器追踪
- 延迟监控
- Token/成本追踪

使用方式:
    # 使用带追踪的节点 (推荐生产环境)
    from agentic_rag.traced_nodes import (
        traced_retrieve_graphiti,
        traced_retrieve_lancedb,
        traced_fuse_results,
        traced_rerank_results,
        traced_check_quality,
    )

    # 使用原始节点 (无追踪)
    from agentic_rag.nodes import retrieve_graphiti, ...

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29

# ✅ Verified from LangSmith SDK (Context7):
# @traceable(name="...", run_type="chain", tags=[...])
# async def my_function(...):
#     ...
"""

import functools
import time
from typing import Any, Dict

from langgraph.runtime import Runtime

from agentic_rag.config import CanvasRAGConfig
from agentic_rag.nodes import (
    check_quality as _check_quality,
)
from agentic_rag.nodes import (
    fuse_results as _fuse_results,
)
from agentic_rag.nodes import (
    rerank_results as _rerank_results,
)

# Import original node functions
from agentic_rag.nodes import (
    retrieve_graphiti as _retrieve_graphiti,
)
from agentic_rag.nodes import (
    retrieve_lancedb as _retrieve_lancedb,
)
from agentic_rag.nodes import (
    retrieve_weak_concepts as _retrieve_weak_concepts,
)
from agentic_rag.nodes import (
    update_learning_behavior as _update_learning_behavior,
)
from agentic_rag.observability.config import LANGSMITH_AVAILABLE, is_tracing_enabled
from agentic_rag.observability.metrics import track_latency
from agentic_rag.state import CanvasRAGState

# Conditionally import traceable
if LANGSMITH_AVAILABLE:
    from langsmith import traceable
else:
    def traceable(**kwargs):
        """No-op decorator when LangSmith is not available"""
        def decorator(func):
            return func
        return decorator


def _create_traced_node(
    original_func,
    node_name: str,
    run_type: str = "chain",
    tags: list = None,
):
    """
    创建带追踪的节点包装器

    Args:
        original_func: 原始节点函数
        node_name: 节点名称
        run_type: LangSmith运行类型
        tags: 标签列表

    Returns:
        包装后的函数
    """
    tags = tags or []

    @functools.wraps(original_func)
    async def traced_wrapper(
        state: CanvasRAGState,
        runtime: Runtime[CanvasRAGConfig]
    ) -> Dict[str, Any]:
        """带追踪的节点包装器"""
        start_time = time.perf_counter()
        error = None

        try:
            # 调用原始函数
            result = await original_func(state, runtime)
            return result
        except Exception as e:
            error = str(e)
            raise
        finally:
            # 记录延迟
            duration_ms = (time.perf_counter() - start_time) * 1000
            track_latency(
                node_name=node_name,
                duration_ms=duration_ms,
                success=(error is None),
                error=error,
            )

    # 应用 @traceable 装饰器 (如果可用且启用)
    if LANGSMITH_AVAILABLE and is_tracing_enabled():
        traced_wrapper = traceable(
            name=node_name,
            run_type=run_type,
            tags=["canvas", "agentic-rag"] + tags,
        )(traced_wrapper)

    return traced_wrapper


# ========================================
# Traced Retrieval Nodes
# ========================================

traced_retrieve_graphiti = _create_traced_node(
    _retrieve_graphiti,
    node_name="retrieve_graphiti",
    run_type="retriever",
    tags=["retrieval", "graphiti", "knowledge-graph"],
)
"""
Graphiti 知识图谱检索 (带追踪)

✅ Verified from LangSmith SDK:
- run_type="retriever" for retrieval operations
- Automatic input/output capture
"""


traced_retrieve_lancedb = _create_traced_node(
    _retrieve_lancedb,
    node_name="retrieve_lancedb",
    run_type="retriever",
    tags=["retrieval", "lancedb", "vector-search"],
)
"""
LanceDB 向量检索 (带追踪)

✅ Verified from LangSmith SDK:
- run_type="retriever" for retrieval operations
"""


traced_retrieve_weak_concepts = _create_traced_node(
    _retrieve_weak_concepts,
    node_name="retrieve_weak_concepts",
    run_type="retriever",
    tags=["retrieval", "temporal", "weak-concepts"],
)
"""
Temporal Memory 薄弱概念检索 (带追踪)
"""


# ========================================
# Traced Processing Nodes
# ========================================

traced_fuse_results = _create_traced_node(
    _fuse_results,
    node_name="fuse_results",
    run_type="chain",
    tags=["fusion", "processing"],
)
"""
结果融合节点 (带追踪)

支持 RRF/Weighted/Cascade 算法
"""


traced_rerank_results = _create_traced_node(
    _rerank_results,
    node_name="rerank_results",
    run_type="chain",
    tags=["reranking", "processing"],
)
"""
重排序节点 (带追踪)

支持 Local/Cohere/Hybrid 策略
"""


traced_check_quality = _create_traced_node(
    _check_quality,
    node_name="check_quality",
    run_type="chain",
    tags=["quality-control", "processing"],
)
"""
质量评估节点 (带追踪)

评估结果质量等级: high/medium/low
"""


traced_update_learning_behavior = _create_traced_node(
    _update_learning_behavior,
    node_name="update_learning_behavior",
    run_type="tool",
    tags=["temporal", "update", "fsrs"],
)
"""
学习行为更新节点 (带追踪)

更新 FSRS 卡片状态
"""


# ========================================
# Export All Traced Nodes
# ========================================

__all__ = [
    "traced_retrieve_graphiti",
    "traced_retrieve_lancedb",
    "traced_retrieve_weak_concepts",
    "traced_fuse_results",
    "traced_rerank_results",
    "traced_check_quality",
    "traced_update_learning_behavior",
]
