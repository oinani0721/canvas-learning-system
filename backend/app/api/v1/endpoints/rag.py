# Canvas Learning System - RAG API Endpoints
# Phase 2: LangGraph桥接 - RAG查询端点
"""
RAG (Retrieval-Augmented Generation) API Endpoints

提供智能检索增强生成功能:
- 多源检索 (Graphiti + LanceDB + 多模态)
- 结果融合 (RRF / Weighted / Cascade)
- 质量控制与 Query 重写

[Source: Phase 2 - LangGraph桥接（复用src/）]
"""

import logging
from datetime import datetime, timezone
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.services.rag_service import (
    RAGService,
    RAGServiceError,
    RAGUnavailableError,
    get_rag_service,
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Create router
rag_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class RAGQueryRequest(BaseModel):
    """RAG 查询请求"""
    query: str = Field(..., description="查询字符串", min_length=1, max_length=2000)
    canvas_file: Optional[str] = Field(None, description="Canvas 文件路径 (用于上下文过滤)")
    is_review_canvas: bool = Field(False, description="是否为检验白板场景")
    fusion_strategy: Optional[Literal["rrf", "weighted", "cascade"]] = Field(
        None, description="融合策略 (默认: rrf, 检验白板: weighted)"
    )
    reranking_strategy: Optional[Literal["local", "cohere", "hybrid_auto"]] = Field(
        None, description="Reranking 策略 (默认: hybrid_auto)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "什么是逆否命题？",
                "canvas_file": "离散数学.canvas",
                "is_review_canvas": False
            }
        }
    )


class SearchResultItem(BaseModel):
    """单个检索结果"""
    doc_id: str = Field(..., description="文档ID")
    content: str = Field(..., description="内容")
    score: float = Field(..., description="相关度分数")
    metadata: dict = Field(default_factory=dict, description="元数据")


class MultimodalResultItem(BaseModel):
    """
    多模态检索结果项 (Story 35.8 AC-35.8.1)

    ✅ Verified from OpenAPI: specs/api/fastapi-backend-api.openapi.yml#MultimodalResultItem
    """
    id: str = Field(..., description="内容ID")
    media_type: Literal["image", "pdf", "audio", "video"] = Field(..., description="媒体类型")
    path: str = Field(..., description="文件路径")
    thumbnail: Optional[str] = Field(None, description="缩略图Base64或URL")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="相关度分数 (0-1)")
    metadata: dict = Field(default_factory=dict, description="额外元数据")


class LatencyInfo(BaseModel):
    """延迟信息"""
    graphiti: Optional[float] = Field(None, description="Graphiti 检索延迟 (ms)")
    lancedb: Optional[float] = Field(None, description="LanceDB 检索延迟 (ms)")
    multimodal: Optional[float] = Field(None, description="多模态检索延迟 (ms)")
    fusion: Optional[float] = Field(None, description="融合延迟 (ms)")
    reranking: Optional[float] = Field(None, description="Reranking 延迟 (ms)")


class RAGQueryMetadata(BaseModel):
    """RAG 查询元数据"""
    query_rewritten: bool = Field(False, description="Query 是否被重写")
    rewrite_count: int = Field(0, description="重写次数")
    fusion_strategy: Optional[str] = Field(None, description="使用的融合策略")
    reranking_strategy: Optional[str] = Field(None, description="使用的 Reranking 策略")


class RAGQueryResponse(BaseModel):
    """
    RAG 查询响应 (Story 35.8 - 含multimodal_results)

    ✅ Verified from OpenAPI: specs/api/fastapi-backend-api.openapi.yml#RAGQueryResponse
    """
    results: List[SearchResultItem] = Field(default_factory=list, description="检索结果列表")
    multimodal_results: List[MultimodalResultItem] = Field(
        default_factory=list,
        description="多模态检索结果 (Story 35.8 AC-35.8.1)"
    )
    quality_grade: str = Field("low", description="质量评级 (high/medium/low)")
    result_count: int = Field(0, description="结果数量")
    latency_ms: LatencyInfo = Field(default_factory=LatencyInfo, description="延迟信息")
    total_latency_ms: float = Field(0.0, description="总延迟 (ms)")
    metadata: RAGQueryMetadata = Field(default_factory=RAGQueryMetadata, description="元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "doc_id": "node-123",
                        "content": "逆否命题是将原命题的条件和结论同时取否定...",
                        "score": 0.95,
                        "metadata": {"source": "graphiti", "canvas": "离散数学.canvas"}
                    }
                ],
                "multimodal_results": [
                    {
                        "id": "mm-001",
                        "media_type": "image",
                        "path": "笔记库/images/逆否命题图解.png",
                        "thumbnail": "data:image/png;base64,...",
                        "relevance_score": 0.87,
                        "metadata": {"width": 800, "height": 600}
                    }
                ],
                "quality_grade": "high",
                "result_count": 1,
                "latency_ms": {
                    "graphiti": 45.2,
                    "lancedb": 32.1,
                    "multimodal": 58.5,
                    "fusion": 5.3,
                    "reranking": 12.8
                },
                "total_latency_ms": 153.9,
                "metadata": {
                    "query_rewritten": False,
                    "rewrite_count": 0,
                    "fusion_strategy": "rrf",
                    "reranking_strategy": "hybrid_auto"
                }
            }
        }
    )


class WeakConceptItem(BaseModel):
    """薄弱概念项"""
    concept: str = Field(..., description="概念名称")
    stability: float = Field(..., description="稳定性分数 (0-1)")
    last_review: Optional[str] = Field(None, description="上次复习时间")
    review_count: int = Field(0, description="复习次数")


class WeakConceptsResponse(BaseModel):
    """薄弱概念响应"""
    concepts: List[WeakConceptItem] = Field(default_factory=list, description="薄弱概念列表")
    total_count: int = Field(0, description="总数量")
    canvas_file: str = Field(..., description="Canvas 文件")


class RAGStatusResponse(BaseModel):
    """RAG 服务状态响应"""
    available: bool = Field(..., description="服务是否可用")
    initialized: bool = Field(..., description="是否已初始化")
    langgraph_available: bool = Field(..., description="LangGraph 是否可用")
    import_error: Optional[str] = Field(None, description="导入错误信息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@rag_router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="RAG 智能检索",
    description="执行智能检索查询，支持多源检索、融合和质量控制",
    operation_id="rag_query",
    responses={
        200: {"description": "查询成功", "model": RAGQueryResponse},
        503: {"description": "RAG 服务不可用"},
        500: {"description": "查询执行失败"}
    }
)
async def rag_query(
    request: RAGQueryRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> RAGQueryResponse:
    """
    执行 RAG 智能检索查询

    支持的功能:
    - 多源并行检索 (Graphiti + LanceDB + 多模态)
    - 3种融合算法 (RRF, Weighted, Cascade)
    - 混合 Reranking (Local + Cohere)
    - 质量控制与 Query 重写

    Args:
        request: RAG 查询请求
        rag_service: RAG 服务 (依赖注入)

    Returns:
        RAGQueryResponse: 检索结果

    Raises:
        HTTPException 503: RAG 服务不可用
        HTTPException 500: 查询执行失败
    """
    logger.info(f"RAG query: {request.query[:50]}...")

    try:
        result = await rag_service.query(
            query=request.query,
            canvas_file=request.canvas_file,
            is_review_canvas=request.is_review_canvas,
            fusion_strategy=request.fusion_strategy,
            reranking_strategy=request.reranking_strategy
        )

        # 转换结果格式 (Story 35.8: 含multimodal_results)
        return RAGQueryResponse(
            results=[
                SearchResultItem(
                    doc_id=r.get("doc_id", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata", {})
                )
                for r in result.get("results", [])
            ],
            multimodal_results=[
                MultimodalResultItem(
                    id=mm.get("id", ""),
                    media_type=mm.get("media_type", "image"),
                    path=mm.get("path", mm.get("file_path", "")),
                    thumbnail=mm.get("thumbnail", mm.get("content_preview")),
                    relevance_score=mm.get("relevance_score", 0.0),
                    metadata=mm.get("metadata", {})
                )
                for mm in result.get("multimodal_results", [])
            ],
            quality_grade=result.get("quality_grade", "low"),
            result_count=result.get("result_count", 0),
            latency_ms=LatencyInfo(**result.get("latency_ms", {})),
            total_latency_ms=result.get("total_latency_ms", 0.0),
            metadata=RAGQueryMetadata(**result.get("metadata", {}))
        )

    except RAGUnavailableError as e:
        logger.error(f"RAG service unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e

    except RAGServiceError as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@rag_router.get(
    "/weak-concepts/{canvas_file:path}",
    response_model=WeakConceptsResponse,
    summary="获取薄弱概念",
    description="从 Temporal Memory 获取指定 Canvas 的薄弱概念列表",
    operation_id="get_weak_concepts",
    responses={
        200: {"description": "成功", "model": WeakConceptsResponse},
        503: {"description": "RAG 服务不可用"}
    }
)
async def get_weak_concepts(
    canvas_file: str,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    limit: int = 10
) -> WeakConceptsResponse:
    """
    获取薄弱概念列表

    从 Temporal Memory 获取低稳定性概念，用于生成检验白板。

    Args:
        canvas_file: Canvas 文件路径
        limit: 返回数量限制 (默认: 10)
        rag_service: RAG 服务 (依赖注入)

    Returns:
        WeakConceptsResponse: 薄弱概念列表
    """
    logger.info(f"Getting weak concepts for: {canvas_file}")

    try:
        concepts = await rag_service.get_weak_concepts(
            canvas_file=canvas_file,
            limit=limit
        )

        return WeakConceptsResponse(
            concepts=[
                WeakConceptItem(
                    concept=c.get("concept", ""),
                    stability=c.get("stability", 0.0),
                    last_review=c.get("last_review"),
                    review_count=c.get("review_count", 0)
                )
                for c in concepts
            ],
            total_count=len(concepts),
            canvas_file=canvas_file
        )

    except RAGUnavailableError as e:
        logger.error(f"RAG service unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e


@rag_router.get(
    "/status",
    response_model=RAGStatusResponse,
    summary="RAG 服务状态",
    description="获取 RAG 服务状态信息",
    operation_id="get_rag_status"
)
async def get_rag_status(
    rag_service: Annotated[RAGService, Depends(get_rag_service)]
) -> RAGStatusResponse:
    """
    获取 RAG 服务状态

    返回 RAG 服务的可用性和配置信息。

    Args:
        rag_service: RAG 服务 (依赖注入)

    Returns:
        RAGStatusResponse: 服务状态
    """
    status = rag_service.get_status()

    return RAGStatusResponse(
        available=status.get("available", False),
        initialized=status.get("initialized", False),
        langgraph_available=status.get("langgraph_available", False),
        import_error=status.get("import_error")
    )
