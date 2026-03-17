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
    vault_notes_results: Annotated[List[SearchResult], "Vault .md 笔记检索结果"]
    fused_results: Annotated[List[SearchResult], "融合算法输出结果"]
    reranked_results: Annotated[List[SearchResult], "Reranking后的最终结果"]

    # 策略配置字段
    fusion_strategy: Annotated[
        Literal["rrf", "weighted", "cascade", "layered_rrf"],
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

    # Story 2.4: 课程/标签过滤字段
    course_id: Annotated[Optional[str], "课程ID (用于按课程过滤搜索范围)"]
    tags: Annotated[Optional[List[str]], "标签列表 (用于按标签过滤搜索范围, OR 匹配)"]

    # 原始Query (用于重写)
    original_query: Annotated[Optional[str], "原始用户查询"]

    # Story 2.6: CRAG 质量门控与安全降级
    safe_degradation: Annotated[bool, "是否触发安全降级 (2次重试后仍 low)"]
    degradation_reason: Annotated[Optional[str], "降级原因 (如 retrieval_quality_insufficient)"]
    quality_history: Annotated[
        List[Dict[str, Any]],
        "质量评分历史 [{iteration, grade, top3_scores, query, binary_grading}]",
    ]
    query_intent: Annotated[
        Optional[str],
        "L1 路由识别的查询意图 (knowledge_point/learning_history/file_locate/comprehensive)",
    ]
    routing_strategy: Annotated[Optional[str], "L1 路由选择的检索策略"]
    binary_grading_used: Annotated[bool, "是否使用了 LLM 二元评分 (vs 数值阈值降级)"]

    # Story 7.1: Faithfulness 忠实度检查字段
    faithfulness_score: Annotated[Optional[float], "Faithfulness忠实度评分 (0.0-1.0)"]
    faithfulness_details: Annotated[Optional[Dict[str, Any]], "Faithfulness检查详情 (claims + NLI结果)"]
    faithfulness_degraded: Annotated[Optional[bool], "是否触发忠实度安全降级"]

    # 性能监控字段 (Optional) - Separate keys to avoid concurrent update conflicts
    graphiti_latency_ms: Annotated[Optional[float], "Graphiti检索延迟 (ms)"]
    lancedb_latency_ms: Annotated[Optional[float], "LanceDB检索延迟 (ms)"]
    # Story 6.8: 多模态检索延迟
    multimodal_latency_ms: Annotated[Optional[float], "多模态检索延迟 (ms)"]
    # Story 23.4: 教材和跨Canvas检索延迟
    textbook_latency_ms: Annotated[Optional[float], "教材检索延迟 (ms)"]
    cross_canvas_latency_ms: Annotated[Optional[float], "跨Canvas检索延迟 (ms)"]
    vault_notes_latency_ms: Annotated[Optional[float], "Vault笔记检索延迟 (ms)"]
    fusion_latency_ms: Annotated[Optional[float], "融合算法延迟 (ms)"]
    reranking_latency_ms: Annotated[Optional[float], "Reranking延迟 (ms)"]


def create_initial_state(**overrides: Any) -> Dict[str, Any]:
    """
    Story 2.7 AC-8: Factory function to create a CanvasRAGState with safe defaults.

    All fields have sensible initial values so that pipeline execution
    never raises KeyError on missing state fields.

    Args:
        **overrides: Any field values to override defaults.

    Returns:
        Dict with all CanvasRAGState fields populated.
    """
    defaults: Dict[str, Any] = {
        "messages": [],
        # Retrieval results
        "graphiti_results": [],
        "lancedb_results": [],
        "multimodal_results": [],
        "textbook_results": [],
        "cross_canvas_results": [],
        "vault_notes_results": [],
        "fused_results": [],
        "reranked_results": [],
        # Strategy
        "fusion_strategy": "layered_rrf",
        "reranking_strategy": "hybrid_auto",
        # Quality control
        "quality_grade": None,
        "query_rewritten": False,
        "rewrite_count": 0,
        # Context
        "canvas_file": None,
        "subject": None,
        "is_review_canvas": False,
        # Filters
        "course_id": None,
        "tags": None,
        # Original query
        "original_query": None,
        # Story 7.1 Faithfulness
        "faithfulness_score": None,
        "faithfulness_details": None,
        "faithfulness_degraded": None,
        # Latency
        "graphiti_latency_ms": None,
        "lancedb_latency_ms": None,
        "multimodal_latency_ms": None,
        "textbook_latency_ms": None,
        "cross_canvas_latency_ms": None,
        "vault_notes_latency_ms": None,
        "fusion_latency_ms": None,
        "reranking_latency_ms": None,
        # Story 2.6 CRAG quality gate
        "safe_degradation": False,
        "degradation_reason": None,
        "quality_history": [],
        "query_intent": None,
        "routing_strategy": None,
        "binary_grading_used": False,
    }
    defaults.update(overrides)
    return defaults


# ═══════════════════════════════════════════════════════════════════════════════
# Phase 3: Agent RAG State — LLM-controlled retrieval + generation
# [Source: Agent Architecture Upgrade Plan - Phase 3]
#
# Unlike CanvasRAGState (pipeline-oriented, 6-way parallel retrieval),
# AgentRAGState is agent-oriented: the LLM decides what to search and
# evaluates whether results are sufficient.
# ═══════════════════════════════════════════════════════════════════════════════


class AgentRAGState(MessagesState):
    """
    State for LLM-controlled Agentic RAG (Phase 3).

    The LLM drives the retrieval process:
    1. Analyzes user intent
    2. Decides whether to search (and what to search for)
    3. Evaluates retrieved document relevance
    4. Rewrites queries if results are insufficient
    5. Generates the final answer with citations

    This coexists with CanvasRAGState — simple questions use Phase 2
    function calling, complex questions use this full agent graph.
    """

    # ── Intent Analysis ──
    user_intent: Annotated[Optional[str], "LLM分析的用户意图"]
    has_specific_request: Annotated[bool, "用户是否有具体请求（如列出笔记）"]

    # ── LLM-generated Search Queries ──
    search_queries: Annotated[List[str], "LLM生成的搜索查询列表（可能多个角度）"]

    # ── Retrieved Documents ──
    retrieved_documents: Annotated[List[SearchResult], "当前迭代检索到的文档"]

    # ── LLM Document Grading ──
    document_grades: Annotated[List[str], "LLM对每个文档的相关性评分: relevant / irrelevant"]
    relevant_documents: Annotated[List[SearchResult], "LLM判断为相关的文档子集"]

    # ── Generation Control ──
    retry_count: Annotated[int, "当前重试计数（最大3次）"]
    generation_complete: Annotated[bool, "是否已完成回答生成"]

    # ── Output ──
    final_answer: Annotated[Optional[str], "LLM生成的最终回答"]
    citations: Annotated[List[Dict[str, Any]], "引用列表: [{source, content_snippet, line_range}]"]

    # ── Agent Configuration (passed at invocation) ──
    agent_type: Annotated[Optional[str], "Agent类型（如oral-explanation）"]
    user_prompt: Annotated[Optional[str], "原始用户prompt（JSON格式）"]
    system_prompt: Annotated[Optional[str], "Agent系统prompt模板"]
    pre_fetched_context: Annotated[Optional[str], "预检索的RAG上下文（Phase 1兼容）"]
