"""
CanvasRAGConfig Context Schema定义

定义Agentic RAG系统的Runtime配置，通过LangGraph context传递。

✅ Verified from LangGraph Skill:
- Pattern: context_schema=ContextSchema
- Runtime configuration不在state中，通过context传递
- 节点函数通过runtime参数访问: runtime.context["key"]

Story 12.5 AC 5.2:
- ✅ 配置字段: retrieval_batch_size, fusion_strategy, reranking_strategy
- ✅ quality_threshold, max_rewrite_iterations

Story 23.2: LanceDB Embedding Pipeline Configuration
- ✅ AC 4: 向量维度和模型可配置

Author: Canvas Learning System Team
Version: 1.1.0
Created: 2025-11-29
Updated: 2025-12-12 (Story 23.2 - LanceDB Embedding Config)
"""

import os
from typing import Any, Dict, Literal, Optional

from typing_extensions import TypedDict

# ============================================================================
# Story 23.2: LanceDB Embedding Configuration
# ✅ Verified from specs/data/canvas-node.schema.json (Canvas node structure)
# ✅ Verified from sentence-transformers documentation (embedding dimensions)
# ============================================================================

# Supported embedding models with their dimensions
EMBEDDING_MODELS: Dict[str, int] = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,  # Default, fast
    "sentence-transformers/all-mpnet-base-v2": 768,  # Higher quality
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,  # Multilingual
}

# ✅ Story 23.2 AC 4: 向量维度和模型可配置
LANCEDB_CONFIG: Dict[str, Any] = {
    "db_path": os.environ.get("LANCEDB_PATH", "backend/data/lancedb"),
    "table_name": os.environ.get("LANCEDB_TABLE", "canvas_nodes"),
    "embedding_model": os.environ.get(
        "LANCEDB_EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2"
    ),
    "embedding_dim": int(os.environ.get("LANCEDB_EMBEDDING_DIM", "384")),
    "batch_size": int(os.environ.get("LANCEDB_BATCH_SIZE", "100")),
    "timeout_ms": int(os.environ.get("LANCEDB_TIMEOUT_MS", "400")),
}

# LanceDB Canvas Nodes Table Schema
# ✅ Story 23.2 AC 2: Canvas节点批量索引
# ✅ Verified from specs/data/canvas-node.schema.json#/properties
CANVAS_NODES_SCHEMA = {
    "doc_id": str,           # 文档唯一ID
    "content": str,          # 节点文本内容
    "vector": list,          # embedding向量 (384/768维)
    "canvas_file": str,      # Canvas文件路径
    "node_id": str,          # 原始节点ID
    "node_type": str,        # 节点类型 (text/file/group/link)
    "color": str,            # 颜色代码 (1-6)
    "x": int,                # X坐标
    "y": int,                # Y坐标
    "timestamp": str,        # 索引时间
    "metadata_json": str,    # 其他元数据JSON
}


class CanvasRAGConfig(TypedDict, total=False):
    """
    Canvas Agentic RAG Runtime Configuration

    ✅ Verified from LangGraph Skill (Pattern: Runtime context schema)

    通过graph.invoke(state, context=config)传递，
    不存储在state中，节点通过runtime参数访问。

    **检索配置**:
    - retrieval_batch_size: 每次检索返回Top-K结果数
    - graphiti_batch_size: Graphiti专用batch size (默认同上)
    - lancedb_batch_size: LanceDB专用batch size (默认同上)

    **策略配置**:
    - fusion_strategy: 融合算法选择 (rrf, weighted, cascade)
    - reranking_strategy: Reranking策略 (local, cohere, hybrid_auto)

    **质量控制配置**:
    - quality_threshold: 质量评级阈值 (0.7=high, 0.5=medium, <0.5=low)
    - max_rewrite_iterations: 最大Query重写次数 (默认2)

    **成本控制配置**:
    - cohere_monthly_limit: Cohere API月度限额 (默认50)
    - enable_cost_monitoring: 是否启用成本监控 (默认True)

    **性能配置**:
    - timeout_seconds: 检索超时时间 (默认10s)
    - enable_caching: 是否启用结果缓存 (默认True)

    Usage:
    ```python
    config = CanvasRAGConfig(
        retrieval_batch_size=10,
        fusion_strategy="weighted",
        reranking_strategy="cohere",
        quality_threshold=0.7,
        max_rewrite_iterations=2
    )

    result = canvas_agentic_rag.invoke(
        {"messages": [("user", "query")]},
        context=config
    )
    ```
    """

    # 检索配置
    retrieval_batch_size: int  # Top-K结果数 (默认10)
    graphiti_batch_size: Optional[int]  # Graphiti专用 (默认同retrieval_batch_size)
    lancedb_batch_size: Optional[int]  # LanceDB专用 (默认同retrieval_batch_size)

    # 策略配置
    fusion_strategy: Literal["rrf", "weighted", "cascade"]  # 融合算法
    reranking_strategy: Literal["local", "cohere", "hybrid_auto"]  # Reranking策略

    # 质量控制配置
    quality_threshold: float  # 质量阈值 (0.7=high, 0.5=medium)
    max_rewrite_iterations: int  # 最大重写次数 (默认2)

    # 成本控制配置
    cohere_monthly_limit: int  # Cohere月度限额 (默认50)
    enable_cost_monitoring: bool  # 是否启用成本监控 (默认True)

    # 性能配置
    timeout_seconds: float  # 检索超时时间 (默认10s)
    enable_caching: bool  # 是否启用缓存 (默认True)

    # Story 23.4: 多源融合权重配置
    # 各数据源的融合权重，用于加权融合算法
    # 默认值: graphiti=0.25, lancedb=0.25, textbook=0.20, cross_canvas=0.15, multimodal=0.15
    source_weights: Dict[str, float]  # 数据源权重配置

    # Story 23.4: 时间衰减配置 (用于学习历史)
    time_decay_factor: float  # 时间衰减因子 (默认0.05)


# Story 23.4: 默认数据源权重配置
# ✅ Verified from Story 23.4 Dev Notes: Data Sources Overview
DEFAULT_SOURCE_WEIGHTS = {
    "graphiti": 0.25,      # Graphiti知识图谱
    "lancedb": 0.25,       # LanceDB向量检索
    "textbook": 0.20,      # 教材上下文
    "cross_canvas": 0.15,  # 跨Canvas关联
    "multimodal": 0.15     # 多模态检索
}

# 默认配置
DEFAULT_CONFIG = CanvasRAGConfig(
    retrieval_batch_size=10,
    fusion_strategy="rrf",
    reranking_strategy="hybrid_auto",
    quality_threshold=0.7,
    max_rewrite_iterations=2,
    cohere_monthly_limit=50,
    enable_cost_monitoring=True,
    timeout_seconds=10.0,
    enable_caching=True,
    # Story 23.4: 多源融合配置
    source_weights=DEFAULT_SOURCE_WEIGHTS,
    time_decay_factor=0.05,  # 时间衰减因子
)


def merge_config(user_config: Optional[CanvasRAGConfig] = None) -> CanvasRAGConfig:
    """
    合并用户配置与默认配置

    Args:
        user_config: 用户提供的配置 (可选)

    Returns:
        合并后的完整配置

    Example:
        >>> config = merge_config({"fusion_strategy": "weighted"})
        >>> config["fusion_strategy"]
        'weighted'
        >>> config["retrieval_batch_size"]
        10
    """
    if user_config is None:
        return DEFAULT_CONFIG.copy()

    # 合并配置
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_config)
    return merged
