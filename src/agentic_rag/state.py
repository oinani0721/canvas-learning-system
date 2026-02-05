"""
CanvasRAGState Schema定义

定义Agentic RAG系统的State TypedDict，继承自LangGraph MessagesState。

✅ Verified from LangGraph Skill:
- Pattern: class State(MessagesState)
- MessagesState自动管理messages列表
- 自定义字段扩展状态

Story 12.5 AC 5.1:
- ✅ 继承MessagesState
- ✅ 包含graphiti_results, lancedb_results, fused_results, reranked_results
- ✅ 策略字段: fusion_strategy, reranking_strategy
- ✅ 质量控制字段: quality_grade, query_rewritten, rewrite_count

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
"""

from typing import Annotated, Any, Dict, List, Literal, Optional

from langgraph.graph import MessagesState
from typing_extensions import TypedDict


def add_dicts(left: Optional[Dict[str, float]], right: Optional[Dict[str, float]]) -> Dict[str, float]:
    """
    Reducer function for merging dictionaries in parallel updates

    ✅ Verified from LangGraph Skill (Pattern: Annotated with reducer)
    Used for retrieval_latency_ms field to handle concurrent updates
    from parallel retrieval nodes.
    """
    if left is None:
        left = {}
    if right is None:
        right = {}
    return {**left, **right}


class SearchResult(TypedDict):
    """检索结果单元

    统一格式，兼容Graphiti和LanceDB结果。
    """
    doc_id: str
    content: str
    score: float  # 原始相似度/相关度分数
    metadata: Dict[str, Any]  # 可选: source, timestamp, etc.


# ✅ Verified from LangGraph Skill:
# When extending MessagesState, use class definition (NOT TypedDict)
# Pattern: class State(MessagesState): field: Annotated[type, reducer]
class CanvasRAGState(MessagesState):
    """
    Canvas Agentic RAG State Schema

    ✅ Verified from LangGraph Skill (Pattern: MessagesState extension)

    继承MessagesState，自动管理:
    - messages: List[BaseMessage] (自动累加)

    自定义字段:

    **检索结果字段**:
    - graphiti_results: Graphiti知识图谱检索结果
    - lancedb_results: LanceDB向量检索结果
    - fused_results: 融合算法输出结果
    - reranked_results: Reranking后的最终结果

    **策略配置字段**:
    - fusion_strategy: 融合算法选择 (rrf, weighted, cascade)
    - reranking_strategy: Reranking策略 (local, cohere, hybrid_auto)

    **质量控制字段**:
    - quality_grade: 结果质量评级 (high, medium, low)
    - query_rewritten: Query是否已重写 (bool)
    - rewrite_count: 当前重写次数 (0-2)

    **上下文字段**:
    - canvas_file: 当前Canvas文件路径
    - is_review_canvas: 是否为检验白板场景 (触发Weighted融合 + Cohere Rerank)
    """

    # 检索结果字段 (List[SearchResult])
    graphiti_results: Annotated[List[SearchResult], "Graphiti知识图谱检索结果"]
    lancedb_results: Annotated[List[SearchResult], "LanceDB向量检索结果"]
    # Story 6.8: 多模态检索结果
    multimodal_results: Annotated[List[SearchResult], "多模态检索结果 (图片、PDF等)"]
    # Story 23.4: 教材和跨Canvas检索结果
    textbook_results: Annotated[List[SearchResult], "教材上下文检索结果"]
    cross_canvas_results: Annotated[List[SearchResult], "跨Canvas关联检索结果"]
    fused_results: Annotated[List[SearchResult], "融合算法输出结果"]
    reranked_results: Annotated[List[SearchResult], "Reranking后的最终结果"]

    # 策略配置字段
    fusion_strategy: Annotated[
        Literal["rrf", "weighted", "cascade"],
        "融合算法选择",
    ]
    reranking_strategy: Annotated[
        Literal["local", "cohere", "hybrid_auto"],
        "Reranking策略选择",
    ]

    # 质量控制字段
    quality_grade: Annotated[
        Optional[Literal["high", "medium", "low"]],
        "结果质量评级",
    ]
    query_rewritten: Annotated[bool, "Query是否已重写"]
    rewrite_count: Annotated[int, "当前重写次数 (最大2次)"]

    # 上下文字段
    canvas_file: Annotated[Optional[str], "Canvas文件路径"]
    subject: Annotated[Optional[str], "学科标识(用于LanceDB隔离)"]
    is_review_canvas: Annotated[bool, "是否为检验白板场景"]

    # 原始Query (用于重写)
    original_query: Annotated[Optional[str], "原始用户查询"]

    # 性能监控字段 (Optional) - Separate keys to avoid concurrent update conflicts
    graphiti_latency_ms: Annotated[Optional[float], "Graphiti检索延迟 (ms)"]
    lancedb_latency_ms: Annotated[Optional[float], "LanceDB检索延迟 (ms)"]
    # Story 6.8: 多模态检索延迟
    multimodal_latency_ms: Annotated[Optional[float], "多模态检索延迟 (ms)"]
    # Story 23.4: 教材和跨Canvas检索延迟
    textbook_latency_ms: Annotated[Optional[float], "教材检索延迟 (ms)"]
    cross_canvas_latency_ms: Annotated[Optional[float], "跨Canvas检索延迟 (ms)"]
    fusion_latency_ms: Annotated[Optional[float], "融合算法延迟 (ms)"]
    reranking_latency_ms: Annotated[Optional[float], "Reranking延迟 (ms)"]
