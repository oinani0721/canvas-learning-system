"""
LangSmith 追踪装饰器

Story 12.12: 追踪装饰器和上下文管理

提供:
- traceable_node: 节点追踪装饰器
- traceable_retrieval: 检索追踪装饰器
- traceable_fusion: 融合追踪装饰器
- traceable_reranking: 重排序追踪装饰器
- trace_context: 追踪上下文

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29

# ✅ Verified from LangSmith SDK (Context7):
# @traceable(name="...", run_type="chain")
# def my_function(...):
#     ...
"""

import functools
import random
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

from .config import LANGSMITH_AVAILABLE, get_langsmith_config, is_tracing_enabled

# Check LangSmith availability
if LANGSMITH_AVAILABLE:
    from langsmith import traceable
else:
    traceable = None

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


def traceable_node(
    name: Optional[str] = None,
    run_type: str = "chain",
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None,
) -> Callable[[F], F]:
    """
    节点追踪装饰器

    ✅ Verified from LangSmith SDK:
    ```python
    @traceable(name="process_document", run_type="chain")
    def process_document(doc_id: str, operation: str) -> dict:
        ...
    ```

    Args:
        name: 追踪名称 (默认使用函数名)
        run_type: 运行类型 ("chain", "llm", "tool", "retriever")
        tags: 标签列表
        metadata: 额外元数据

    Returns:
        装饰后的函数
    """
    def decorator(func: F) -> F:
        if not LANGSMITH_AVAILABLE or not is_tracing_enabled():
            return func

        # Apply sampling
        config = get_langsmith_config()

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check sampling rate
            if config.sampling_rate < 1.0 and random.random() > config.sampling_rate:
                return await func(*args, **kwargs)

            # Create traceable wrapper
            trace_name = name or func.__name__
            trace_tags = (tags or []) + config.tags

            traced_func = traceable(
                name=trace_name,
                run_type=run_type,
                tags=trace_tags,
                metadata=metadata or {},
            )(func)

            return await traced_func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check sampling rate
            if config.sampling_rate < 1.0 and random.random() > config.sampling_rate:
                return func(*args, **kwargs)

            # Create traceable wrapper
            trace_name = name or func.__name__
            trace_tags = (tags or []) + config.tags

            traced_func = traceable(
                name=trace_name,
                run_type=run_type,
                tags=trace_tags,
                metadata=metadata or {},
            )(func)

            return traced_func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if _is_async_function(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator


def traceable_retrieval(
    source: str,
    tags: Optional[list[str]] = None,
) -> Callable[[F], F]:
    """
    检索节点追踪装饰器

    特化版本，添加检索相关元数据

    Args:
        source: 检索源 ("graphiti", "lancedb", "temporal")
        tags: 额外标签

    Returns:
        装饰后的函数
    """
    return traceable_node(
        name=f"retrieve_{source}",
        run_type="retriever",
        tags=["retrieval", source] + (tags or []),
        metadata={"source": source, "node_type": "retrieval"},
    )


def traceable_fusion(
    algorithm: str = "rrf",
    tags: Optional[list[str]] = None,
) -> Callable[[F], F]:
    """
    融合节点追踪装饰器

    Args:
        algorithm: 融合算法 ("rrf", "weighted", "cascade")
        tags: 额外标签

    Returns:
        装饰后的函数
    """
    return traceable_node(
        name=f"fuse_results_{algorithm}",
        run_type="chain",
        tags=["fusion", algorithm] + (tags or []),
        metadata={"algorithm": algorithm, "node_type": "fusion"},
    )


def traceable_reranking(
    strategy: str = "local",
    tags: Optional[list[str]] = None,
) -> Callable[[F], F]:
    """
    重排序节点追踪装饰器

    Args:
        strategy: 重排序策略 ("local", "cohere", "hybrid")
        tags: 额外标签

    Returns:
        装饰后的函数
    """
    return traceable_node(
        name=f"rerank_results_{strategy}",
        run_type="chain",
        tags=["reranking", strategy] + (tags or []),
        metadata={"strategy": strategy, "node_type": "reranking"},
    )


@contextmanager
def trace_context(
    name: str,
    run_type: str = "chain",
    inputs: Optional[dict] = None,
    tags: Optional[list[str]] = None,
):
    """
    追踪上下文管理器

    用于手动追踪代码块

    ✅ Verified from LangSmith SDK:
    ```python
    with tracing_context(enabled=True):
        ...
    ```

    Args:
        name: 追踪名称
        run_type: 运行类型
        inputs: 输入数据
        tags: 标签

    Yields:
        追踪上下文 (包含 start_time 等)
    """
    if not LANGSMITH_AVAILABLE or not is_tracing_enabled():
        yield {"name": name, "start_time": time.time()}
        return

    config = get_langsmith_config()

    # Check sampling
    if config.sampling_rate < 1.0 and random.random() > config.sampling_rate:
        yield {"name": name, "start_time": time.time(), "sampled_out": True}
        return

    start_time = time.time()
    context = {
        "name": name,
        "run_type": run_type,
        "start_time": start_time,
        "inputs": inputs or {},
        "tags": (tags or []) + config.tags,
    }

    try:
        yield context
    finally:
        context["end_time"] = time.time()
        context["duration_ms"] = (context["end_time"] - start_time) * 1000


def _is_async_function(func: Callable) -> bool:
    """检查函数是否为异步函数"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# ========================================
# Convenience Decorators for Node Types
# ========================================

def trace_graphiti_retrieval(func: F) -> F:
    """Graphiti 检索追踪装饰器"""
    return traceable_retrieval(source="graphiti")(func)


def trace_lancedb_retrieval(func: F) -> F:
    """LanceDB 检索追踪装饰器"""
    return traceable_retrieval(source="lancedb")(func)


def trace_temporal_retrieval(func: F) -> F:
    """Temporal Memory 检索追踪装饰器"""
    return traceable_retrieval(source="temporal")(func)


def trace_rrf_fusion(func: F) -> F:
    """RRF 融合追踪装饰器"""
    return traceable_fusion(algorithm="rrf")(func)


def trace_weighted_fusion(func: F) -> F:
    """Weighted 融合追踪装饰器"""
    return traceable_fusion(algorithm="weighted")(func)


def trace_cascade_fusion(func: F) -> F:
    """Cascade 融合追踪装饰器"""
    return traceable_fusion(algorithm="cascade")(func)


def trace_local_reranking(func: F) -> F:
    """Local 重排序追踪装饰器"""
    return traceable_reranking(strategy="local")(func)


def trace_cohere_reranking(func: F) -> F:
    """Cohere 重排序追踪装饰器"""
    return traceable_reranking(strategy="cohere")(func)


def trace_hybrid_reranking(func: F) -> F:
    """Hybrid 重排序追踪装饰器"""
    return traceable_reranking(strategy="hybrid")(func)
