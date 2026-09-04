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
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.decision_tracker import log_retrieval_status_decision
from app.core.nothrow_logging import nothrow
from app.core.vault_scope import resolve_vault_scope
from app.models.service_status import ServiceStatus
from app.services.rag_service import (
    RAGService,
    RAGServiceError,
    RAGUnavailableError,
    get_rag_service,
)

# CARD-OBS-nothrow-logging: 端点模块的日志调用不得成为业务失败源 ——
# 包装后 logger.<level>(...) 抛错不再改变 HTTP 状态码与 detail (两级降级,
# 诚实边界见 app/core/nothrow_logging.py 模块 docstring)。
logger = nothrow(logging.getLogger(__name__))

# Create router
rag_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class RAGQueryRequest(BaseModel):
    """RAG 查询请求"""

    query: str = Field(..., description="查询字符串", min_length=1, max_length=2000)
    # CARD-G4-4: 显式 VaultScope — 必填 (缺 → 422)。请求 vault 与进程 active
    # vault 不一致时 resolve_vault_scope 抛 409, 禁止静默改写作用域
    # (CARD-G2-2 契约 2)。本端点此前完全没有 vault 作用域, 是 full RAG 链上
    # 最后一个「缺参落默认组」的旁路。
    vault_id: str = Field(
        ...,
        min_length=1,
        description=(
            "Vault 稳定 ID (必填, CARD-G4-4)。检索作用域只落在该 vault 内; "
            "与进程 active vault 不一致 → 409。"
        ),
    )

    @field_validator("vault_id")
    @classmethod
    def _reject_blank_vault_id(cls, v: str) -> str:
        # CARD-G4-4 Codex round-1 HIGH-2: min_length=1 拦不住纯空白串;
        # resolve_vault_scope 把空白当「缺失」走双缺失推导 → 空白请求
        # 会以 active vault 作用域 200 通过, 等于契约被绕过。在模型层
        # fail-closed (422)。
        if not v or not v.strip():
            raise ValueError("vault_id 不能为空白")
        return v
    canvas_file: Optional[str] = Field(
        None, description="Canvas 文件路径 (用于上下文过滤)"
    )
    subject_id: Optional[str] = Field(
        None,
        description="学科 ID, 用于多学科知识图谱隔离 (Story 1.9). 当提供时, 检索范围限定在该学科内.",
    )
    cross_subject: bool = Field(
        False,
        description="是否启用跨学科检索 (Story 1.9 AC-5). 启用后通过 Tag Jaccard 桥接扩展到相似学科.",
    )
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
                "vault_id": "canvas_vault",
                "canvas_file": "离散数学.canvas",
                "subject_id": "math",
                "cross_subject": False,
                "is_review_canvas": False,
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
    media_type: Literal["image", "pdf", "audio", "video"] = Field(
        ..., description="媒体类型"
    )
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

    results: List[SearchResultItem] = Field(
        default_factory=list, description="检索结果列表"
    )
    multimodal_results: List[MultimodalResultItem] = Field(
        default_factory=list, description="多模态检索结果 (Story 35.8 AC-35.8.1)"
    )
    quality_grade: str = Field("low", description="质量评级 (high/medium/low)")
    result_count: int = Field(0, description="结果数量")
    latency_ms: LatencyInfo = Field(default_factory=LatencyInfo, description="延迟信息")
    total_latency_ms: float = Field(0.0, description="总延迟 (ms)")
    metadata: RAGQueryMetadata = Field(
        default_factory=RAGQueryMetadata, description="元数据"
    )

    # ── CARD-G4-3 加性四态字段 (纯透传 CanvasRAGState.retrieval_status) ──
    # 状态由 fuse_results 汇聚层折算 (lib/agentic_rag/nodes.py:589) 或由
    # rag_service 的 fallback 出口给出; 端点只负责搬运, 不参与判定。
    # null 的语义是「本次未产出状态」(state 初值即 None, 图早退时如此),
    # 与 empty 严格区分 —— 把 null 归一成 ok/empty 正是本卡要消灭的伪装。
    retrieval_status: Optional[ServiceStatus] = Field(
        None,
        description=(
            "检索四态 (G4-2 统一枚举): ok / empty / degraded / unavailable。"
            "null=本次未产出状态。注意与 HTTP 503 的分工: 503 表示 RAG 服务"
            "整体不可达, 本字段表示这一次检索结果的可信度。"
        ),
    )
    retrieval_status_reason: Optional[str] = Field(
        None, description="故障说明 — degraded/unavailable 时非空"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [
                    {
                        "doc_id": "node-123",
                        "content": "逆否命题是将原命题的条件和结论同时取否定...",
                        "score": 0.95,
                        "metadata": {"source": "graphiti", "canvas": "离散数学.canvas"},
                    }
                ],
                "multimodal_results": [
                    {
                        "id": "mm-001",
                        "media_type": "image",
                        "path": "笔记库/images/逆否命题图解.png",
                        "thumbnail": "data:image/png;base64,...",
                        "relevance_score": 0.87,
                        "metadata": {"width": 800, "height": 600},
                    }
                ],
                "quality_grade": "high",
                "result_count": 1,
                "latency_ms": {
                    "graphiti": 45.2,
                    "lancedb": 32.1,
                    "multimodal": 58.5,
                    "fusion": 5.3,
                    "reranking": 12.8,
                },
                "total_latency_ms": 153.9,
                "metadata": {
                    "query_rewritten": False,
                    "rewrite_count": 0,
                    "fusion_strategy": "rrf",
                    "reranking_strategy": "hybrid_auto",
                },
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

    concepts: List[WeakConceptItem] = Field(
        default_factory=list, description="薄弱概念列表"
    )
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
        500: {"description": "查询执行失败"},
    },
)
async def rag_query(
    request: RAGQueryRequest,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
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
    # CARD-G4-3 Codex round-3 HIGH-1 → CARD-OBS-nothrow-logging: 这条入口日志
    # 曾在主 try **之外**手写 try/except 兜底 (它抛错会让请求直接 500 且
    # `rag_service.query` 一次都没被调用)。本卡把兜底收敛进 NoThrowLogger 本身
    # (与 log_retrieval_status_decision 同口径: 观测失败最多损失可观测性),
    # 调用点恢复为直接调用 —— call-site 的 try/except 与包装器双层兜底会让
    # test_rag_four_state_api 的注入门测不到包装器 (假绿面)。
    logger.info(
        "RAG query: %s... subject=%s cross=%s",
        request.query[:50],
        request.subject_id,
        request.cross_subject,
    )

    # CARD-G4-4: 每请求恰一次 VaultScope 解析 (chat.py:284-296 范式)。
    # resolve_vault_scope 内部把解析结果注入 ContextVar (group_id, 含
    # subject/canvas 二级), 替代原「subject_id 有值才 set、缺省不注入」的
    # 旁路 —— 本端点从此没有无作用域路径。vault_id 必填由 pydantic 把守
    # (缺 → 422); 请求 vault ≠ 进程 active vault → 409 fail-closed
    # (CARD-G2-2 契约 2), 禁止静默改写作用域。
    _scope = resolve_vault_scope(
        request.vault_id,
        subject_id=request.subject_id,
        canvas_path=request.canvas_file,
    )
    # 与入口日志同口径: 观测失败最多损失可观测性, 不得成为业务失败源
    # (G4-3 round-3 HIGH-1 确立的纪律; 本卡新增日志一律惰性参数)。
    try:
        logger.info(
            "RAG query scope resolved: vault=%s source=%s group=%s",
            _scope.vault_id,
            _scope.source,
            _scope.group_id,
        )
    except Exception:  # noqa: BLE001 — 观测面刻意兜底
        pass

    try:
        result = await rag_service.query(
            query=request.query,
            canvas_file=request.canvas_file,
            subject_id=request.subject_id,
            cross_subject=request.cross_subject,
            is_review_canvas=request.is_review_canvas,
            fusion_strategy=request.fusion_strategy,
            reranking_strategy=request.reranking_strategy,
        )

        # 转换结果格式 (Story 35.8: 含multimodal_results)
        # Map LangGraph state keys → response format
        reranked = result.get("reranked_results", result.get("results", []))

        # CARD-G4-3: 四态纯透传 + 故障态落 trace。
        # 归一与"仅故障态落账"的判断收在 decision_tracker 单点 (memory 端点
        # 共用同一个), 端点这里只负责取值和搬运。
        retrieval_status = result.get("retrieval_status")
        retrieval_status_reason = result.get("retrieval_status_reason")
        log_retrieval_status_decision(
            function="rag_query",
            status=retrieval_status,
            reason=retrieval_status_reason,
            input_summary={
                "query": request.query[:80],
                "subject_id": request.subject_id,
            },
        )

        return RAGQueryResponse(
            results=[
                SearchResultItem(
                    doc_id=r.get("doc_id", ""),
                    content=r.get("content", ""),
                    score=r.get("score", 0.0),
                    metadata=r.get("metadata", {}),
                )
                for r in reranked
            ],
            multimodal_results=[
                MultimodalResultItem(
                    id=mm.get("id", ""),
                    media_type=mm.get("media_type", "image"),
                    path=mm.get("path", mm.get("file_path", "")),
                    thumbnail=mm.get("thumbnail", mm.get("content_preview")),
                    relevance_score=mm.get("relevance_score", 0.0),
                    metadata=mm.get("metadata", {}),
                )
                for mm in result.get("multimodal_results", [])
            ],
            # CARD-G4-3 Codex round-1 BLOCKER-1: 必须是 `or "low"` 而不是
            # `.get(..., "low")`。rag_service 的**三个** fallback 出口
            # (:216 / :481 / :500) 都显式写 `"quality_grade": None`, 而
            # `.get` 的默认值只在**键缺失**时生效, 键存在且为 None 时原样返回
            # None → 撞上 `quality_grade: str` 的响应模型 → 500。
            # 后果: 所有 retrieval_status="unavailable" 的真实路径都返回 500,
            # 「unavailable 仍 200」这条本卡判据在真实入口上根本不成立
            # (本卡新增测试此前用合成 state 固定给 quality_grade="high",
            # 因此是假绿 —— 已补真实 RAGService 回归门)。
            quality_grade=result.get("quality_grade") or "low",
            result_count=len(reranked),
            latency_ms=LatencyInfo(
                graphiti=result.get("graphiti_latency_ms"),
                lancedb=result.get("lancedb_latency_ms"),
                multimodal=result.get("multimodal_latency_ms"),
                fusion=result.get("fusion_latency_ms"),
                reranking=result.get("reranking_latency_ms"),
            ),
            total_latency_ms=sum(
                v
                for v in [
                    result.get("graphiti_latency_ms", 0),
                    result.get("lancedb_latency_ms", 0),
                    result.get("multimodal_latency_ms", 0),
                    result.get("fusion_latency_ms", 0),
                    result.get("reranking_latency_ms", 0),
                    result.get("vault_notes_latency_ms", 0),
                ]
                if v
            ),
            metadata=RAGQueryMetadata(
                query_rewritten=result.get("query_rewritten", False),
                rewrite_count=result.get("rewrite_count", 0),
                fusion_strategy=result.get("fusion_strategy"),
                reranking_strategy=result.get("reranking_strategy"),
            ),
            retrieval_status=retrieval_status,
            retrieval_status_reason=retrieval_status_reason,
        )

    except RAGUnavailableError as e:
        logger.error("RAG service unavailable: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e

    except RAGServiceError as e:
        logger.error("RAG query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@rag_router.get(
    "/weak-concepts/{canvas_file:path}",
    response_model=WeakConceptsResponse,
    summary="获取薄弱概念",
    description="从 Temporal Memory 获取指定 Canvas 的薄弱概念列表",
    operation_id="get_weak_concepts",
    responses={
        200: {"description": "成功", "model": WeakConceptsResponse},
        503: {"description": "RAG 服务不可用"},
    },
)
async def get_weak_concepts(
    canvas_file: str,
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    limit: int = 10,
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
    logger.info("Getting weak concepts for: %s", canvas_file)

    try:
        concepts = await rag_service.get_weak_concepts(
            canvas_file=canvas_file, limit=limit
        )

        return WeakConceptsResponse(
            concepts=[
                WeakConceptItem(
                    concept=c.get("concept", ""),
                    stability=c.get("stability", 0.0),
                    last_review=c.get("last_review"),
                    review_count=c.get("review_count", 0),
                )
                for c in concepts
            ],
            total_count=len(concepts),
            canvas_file=canvas_file,
        )

    except RAGUnavailableError as e:
        logger.error("RAG service unavailable: %s", e)
        raise HTTPException(status_code=503, detail=str(e)) from e


@rag_router.get(
    "/status",
    response_model=RAGStatusResponse,
    summary="RAG 服务状态",
    description="获取 RAG 服务状态信息",
    operation_id="get_rag_status",
)
async def get_rag_status(
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
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
        import_error=status.get("import_error"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 2.11: RAG Configuration API
# ═══════════════════════════════════════════════════════════════════════════════


@rag_router.get(
    "/config",
    summary="获取当前 RAG 配置",
    description="返回当前生效的完整 RAG 管道配置参数",
    operation_id="get_rag_config",
)
async def get_rag_config() -> dict:
    """
    Story 2.11 AC-5: Return current effective RAG config.
    """
    try:
        from agentic_rag.config import merge_config

        config = merge_config()
        return dict(config)
    except Exception as e:
        logger.error("Failed to load RAG config: %s", e)
        raise HTTPException(status_code=500, detail=f"Config load failed: {e}") from e


@rag_router.put(
    "/config",
    summary="更新 RAG 配置",
    description="动态更新 RAG 管道配置，立即生效（无需重启）",
    operation_id="update_rag_config",
)
async def update_rag_config(updates: dict) -> dict:
    """
    Story 2.11 AC-5: Update RAG config and persist to YAML file.
    """
    import os

    try:
        from agentic_rag.config import DEFAULT_CONFIG, validate_config

        # Validate incoming updates against defaults
        test_config = DEFAULT_CONFIG.copy()
        test_config.update(updates)
        validated = validate_config(test_config)

        # Persist to YAML file
        config_path = os.path.join(os.getcwd(), "config", "rag_config.yaml")
        try:
            import yaml

            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # Load existing file config
            existing = {}
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or {}

            # Merge updates
            existing.update(updates)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(existing, f, default_flow_style=False, allow_unicode=True)

            logger.info(
                "[CONFIG] Updated %s params, persisted to %s",
                len(updates),
                config_path,
            )
        except ImportError:
            logger.warning(
                "[CONFIG] pyyaml not installed, config not persisted to file"
            )

        # Log changes
        for param, value in updates.items():
            old_val = DEFAULT_CONFIG.get(param, "N/A")
            logger.info("[CONFIG] Updated %s: %s -> %s", param, old_val, value)

        return {
            "status": "ok",
            "updated_keys": list(updates.keys()),
            "config": dict(validated),
        }

    except Exception as e:
        logger.error("Failed to update RAG config: %s", e)
        raise HTTPException(status_code=400, detail=f"Config update failed: {e}") from e
