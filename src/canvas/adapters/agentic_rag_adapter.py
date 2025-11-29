"""
AgenticRAGAdapter - Canvas检验白板生成的Agentic RAG适配器

将LangGraph Agentic RAG StateGraph封装为Canvas检验白板生成可用的简化接口。

核心功能:
1. 封装canvas_agentic_rag.ainvoke()调用
2. 自动配置检验白板场景参数 (weighted融合 + cohere reranking)
3. 错误处理和降级机制 (RAG失败 -> LanceDB only)
4. 性能监控 (检索延迟 <400ms)

✅ Verified from Story 12.10 (docs/epics/EPIC-12-STORY-MAP.md lines 1262-1316):
- AC 10.1: 集成Agentic RAG到generate_verification_canvas
- AC 10.4: 性能不退化 (<5s总时间, <400ms检索延迟)
- AC 10.5: 错误处理和降级

Author: Canvas Learning System Team
Version: 1.0.0
Created: 2025-11-29
Story: 12.10 - Canvas检验白板生成集成
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from loguru import logger
    LOGURU_ENABLED = True
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    LOGURU_ENABLED = False

# ✅ Verified imports from agentic_rag package
from agentic_rag import canvas_agentic_rag, CanvasRAGConfig, CanvasRAGState


@dataclass
class VerificationContext:
    """检验白板生成上下文

    封装检验白板生成所需的输入信息。

    Attributes:
        canvas_file: 源Canvas文件路径
        red_purple_nodes: 红色/紫色节点列表 (需要生成检验题的概念)
        output_canvas_file: 输出检验白板文件路径
        max_questions_per_node: 每个节点生成的检验题数量 (默认2-3)
    """
    canvas_file: str
    red_purple_nodes: List[Dict[str, Any]]
    output_canvas_file: str
    max_questions_per_node: int = 3


@dataclass
class RAGRetrievalResult:
    """Agentic RAG检索结果

    封装Agentic RAG返回的检索结果。

    Attributes:
        reranked_results: Reranking后的最终结果 (List[SearchResult])
        quality_grade: 结果质量评级 (high/medium/low)
        fusion_strategy_used: 实际使用的融合策略
        reranking_strategy_used: 实际使用的Reranking策略
        total_latency_ms: 总检索延迟 (ms)
        is_fallback: 是否为降级结果 (True表示RAG失败,使用fallback)
    """
    reranked_results: List[Dict[str, Any]]
    quality_grade: str
    fusion_strategy_used: str
    reranking_strategy_used: str
    total_latency_ms: float
    is_fallback: bool = False
    error_message: Optional[str] = None


class AgenticRAGAdapter:
    """
    Agentic RAG适配器 - 检验白板生成专用

    封装Agentic RAG StateGraph为检验白板生成可用的简化接口。

    ✅ Verified from Story 12.10 AC 10.1:
    - 替换现有单一检索逻辑
    - 调用: canvas_agentic_rag.ainvoke(...)
    - 传递: is_review_canvas=True (触发Weighted融合 + Cohere Rerank)

    ✅ Verified from Story 12.10 AC 10.5:
    - 错误处理: Agentic RAG失败 -> 降级到单一检索 (LanceDB only)
    - 日志: 记录降级事件

    Usage:
        >>> adapter = AgenticRAGAdapter()
        >>> context = VerificationContext(
        ...     canvas_file="test.canvas",
        ...     red_purple_nodes=[{"id": "node1", "text": "逆否命题"}],
        ...     output_canvas_file="test-检验白板.canvas"
        ... )
        >>> result = await adapter.retrieve_for_verification(context)
        >>> print(result.quality_grade)
        'high'
    """

    def __init__(
        self,
        fallback_retriever: Optional[Any] = None,
        enable_performance_monitoring: bool = True
    ):
        """
        初始化AgenticRAGAdapter

        Args:
            fallback_retriever: 降级检索器 (可选, 用于RAG失败时降级)
                                如果未提供, 降级时返回空结果
            enable_performance_monitoring: 是否启用性能监控 (默认True)
        """
        self.fallback_retriever = fallback_retriever
        self.enable_performance_monitoring = enable_performance_monitoring

        # 检验白板场景的默认配置
        # ✅ Verified from Story 12.10 (lines 1280-1284):
        # - fusion_strategy="weighted" (薄弱点权重70%)
        # - reranking_strategy="cohere" (检验白板用Cohere)
        self.verification_canvas_config = CanvasRAGConfig(
            fusion_strategy="weighted",
            reranking_strategy="cohere",
            retrieval_batch_size=10,
            quality_threshold=0.7,
            max_rewrite_iterations=2,
        )

        if LOGURU_ENABLED:
            logger.info(
                "AgenticRAGAdapter initialized: "
                f"fusion=weighted, reranking=cohere, batch_size=10"
            )

    async def retrieve_for_verification(
        self,
        context: VerificationContext,
        custom_config: Optional[CanvasRAGConfig] = None
    ) -> RAGRetrievalResult:
        """
        为检验白板生成执行Agentic RAG检索

        ✅ Verified from Story 12.10 AC 10.1:
        - 调用canvas_agentic_rag.ainvoke(...)
        - 传递is_review_canvas=True

        ✅ Verified from Story 12.10 AC 10.4:
        - 检索延迟 <400ms

        ✅ Verified from Story 12.10 AC 10.5:
        - 错误处理和降级 (try-except包裹)

        Args:
            context: 检验白板生成上下文
            custom_config: 自定义配置 (可选, 覆盖默认配置)

        Returns:
            RAGRetrievalResult: 检索结果

        Raises:
            不会抛出异常，失败时自动降级
        """
        start_time = time.time()

        # 合并配置
        config = custom_config if custom_config else self.verification_canvas_config

        # 提取概念列表 (用于检索)
        concepts = [node.get("text", "") for node in context.red_purple_nodes]
        query = f"检索Canvas薄弱点: {', '.join(concepts[:3])}..."  # 限制query长度

        # 构造StateGraph输入
        initial_state = {
            "messages": [{"role": "user", "content": query}],
            "canvas_file": context.canvas_file,
            "is_review_canvas": True,  # ✅ 触发Weighted融合 + Cohere Rerank
            "fusion_strategy": config["fusion_strategy"],
            "reranking_strategy": config["reranking_strategy"],
            "query_rewritten": False,
            "rewrite_count": 0,
        }

        try:
            # ✅ Verified from Story 12.10 (lines 1287-1296):
            # 调用Agentic RAG StateGraph
            result_state = await canvas_agentic_rag.ainvoke(
                initial_state,
                config={"configurable": config}  # LangGraph context传递
            )

            # 提取结果
            reranked_results = result_state.get("reranked_results", [])
            quality_grade = result_state.get("quality_grade", "medium")

            # 计算延迟
            total_latency_ms = (time.time() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.success(
                    f"Agentic RAG retrieval success: "
                    f"quality={quality_grade}, "
                    f"results={len(reranked_results)}, "
                    f"latency={total_latency_ms:.2f}ms"
                )

            # ✅ AC 10.4 验证: 检索延迟应 <400ms
            if total_latency_ms > 400 and LOGURU_ENABLED:
                logger.warning(
                    f"Retrieval latency exceeded 400ms threshold: {total_latency_ms:.2f}ms"
                )

            return RAGRetrievalResult(
                reranked_results=reranked_results,
                quality_grade=quality_grade,
                fusion_strategy_used=config["fusion_strategy"],
                reranking_strategy_used=config["reranking_strategy"],
                total_latency_ms=total_latency_ms,
                is_fallback=False,
            )

        except Exception as e:
            # ✅ Verified from Story 12.10 AC 10.5:
            # 错误处理: Agentic RAG失败 -> 降级到单一检索
            total_latency_ms = (time.time() - start_time) * 1000

            if LOGURU_ENABLED:
                logger.warning(
                    f"Agentic RAG failed, falling back to simple retrieval: {e}"
                )

            # 降级到单一检索 (如果提供了fallback_retriever)
            fallback_results = []
            if self.fallback_retriever:
                try:
                    fallback_results = await self._fallback_lancedb_search(
                        context.canvas_file,
                        concepts
                    )
                except Exception as fb_error:
                    if LOGURU_ENABLED:
                        logger.error(f"Fallback retrieval also failed: {fb_error}")

            return RAGRetrievalResult(
                reranked_results=fallback_results,
                quality_grade="low",  # 降级结果质量标记为low
                fusion_strategy_used="none_fallback",
                reranking_strategy_used="none_fallback",
                total_latency_ms=total_latency_ms,
                is_fallback=True,
                error_message=str(e),
            )

    async def _fallback_lancedb_search(
        self,
        canvas_file: str,
        concepts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        降级检索: 仅使用LanceDB (无融合,无Reranking)

        ✅ Verified from Story 12.10 AC 10.5:
        - 降级后仍能生成检验白板 (质量可能降低)

        Args:
            canvas_file: Canvas文件路径
            concepts: 概念列表

        Returns:
            简单检索结果 (List[SearchResult格式的字典])
        """
        if not self.fallback_retriever:
            return []

        # TODO: 实际实现需要调用LanceDB客户端
        # 这里返回占位结果
        if LOGURU_ENABLED:
            logger.debug(
                f"Executing fallback LanceDB search for {len(concepts)} concepts"
            )

        # Placeholder: 返回空结果
        # 实际实现应调用: self.fallback_retriever.search(...)
        return []

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            性能统计字典 (平均延迟, 降级次数等)
        """
        # TODO: 实现性能统计收集
        return {
            "average_latency_ms": 0.0,
            "fallback_count": 0,
            "total_requests": 0,
        }
