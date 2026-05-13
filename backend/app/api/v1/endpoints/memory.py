# Canvas Learning System - Memory API Endpoints
# Story 22.4: 学习历史存储与查询API
# Story 30.8: 多学科隔离与group_id支持
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter, Depends)
"""
Memory API Endpoints - Learning history storage and query.

NOTE: All endpoints delegate to MemoryService which requires a live Neo4j
connection. When Neo4j is unavailable, endpoints will return 500 errors.
Endpoint logic is real (not stubbed), but depends on MemoryService health.

Story 22.4 Implementation:
- POST /episodes: Record learning events (AC-22.4.1)
- GET /episodes: Query learning history (AC-22.4.2)
- GET /concepts/{id}/history: Query concept history (AC-22.4.3)
- GET /review-suggestions: Get review suggestions (AC-22.4.4)

Story 30.8 Implementation:
- GET /episodes: Added subject query parameter (AC-30.8.3)
- GET /review-suggestions: Added subject query parameter (AC-30.8.3)

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#API端点实现]
[Source: docs/stories/30.8.story.md#Task-3.2]
"""

import logging
from datetime import datetime
from typing import Annotated, List, Optional

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.models.memory_schemas import (
    BatchEpisodesRequest,
    BatchEpisodesResponse,
    BatchErrorItem,
    ConceptHistoryResponse,
    LearningEpisodeCreate,
    LearningEpisodeResponse,
    LearningHistoryItem,
    LearningHistoryResponse,
    MemoryHealthResponse,
    ReviewSuggestionResponse,
)
from app.services.memory_service import (
    MemoryService,
    get_memory_service,
)

logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter prefix tags)
memory_router = APIRouter()


# Wave-5 Stage B (2026-05-12) — Multi-vault ContextVar 注入辅助.
# 3 memory endpoints 此前无 vault_id 隔离 → 跨 vault 学习历史串库 (P0).
def _resolve_vault_group_id(
    vault_id: Optional[str],
    subject_id: Optional[str] = None,
    canvas_path: Optional[str] = None,
    legacy_group_id: Optional[str] = None,
) -> str:
    """Wave-5 Stage B — vault_id → ContextVar 注入 + 派生 group_id."""
    from app.config import DEFAULT_GROUP_ID, sanitize_vault_id
    from app.core.subject_config import (
        build_vault_group_id,
        canonical_group_id,
        set_current_subject_id,
    )

    if vault_id and vault_id.strip():
        sanitized = sanitize_vault_id(vault_id)
        derived = build_vault_group_id(
            sanitized,
            subject_id=subject_id,
            canvas_path=canvas_path,
        )
    elif legacy_group_id and legacy_group_id.strip():
        logger.warning(
            "Wave-5 Stage B: memory endpoint vault_id missing, "
            "falling back to deprecated group_id=%s",
            legacy_group_id,
        )
        derived = canonical_group_id(legacy_group_id)
    else:
        logger.warning(
            "Wave-5 Stage B: memory endpoint both vault_id and group_id missing, "
            "falling back to DEFAULT_GROUP_ID"
        )
        derived = DEFAULT_GROUP_ID

    set_current_subject_id(derived)
    return derived


# =============================================================================
# Dependency Injection - Singleton Pattern for Neo4j Connection Pooling
# Singleton lives in app.services.memory_service (single source of truth).
# This module re-exports for FastAPI Depends() usage.
# =============================================================================

# Type alias for MemoryService dependency — delegates to service-layer singleton
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]


# =============================================================================
# POST /episodes - Record learning event (AC-22.4.1)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


@memory_router.post(
    "/episodes",
    response_model=LearningEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="记录学习事件",
    description="记录用户的学习事件，存储到Neo4j和Graphiti",
)
async def create_learning_episode(
    episode: LearningEpisodeCreate, memory_service: MemoryServiceDep
) -> LearningEpisodeResponse:
    """
    记录学习事件

    ✅ Verified from docs/stories/22.4.story.md#create_learning_episode:
    - 调用 memory_service.record_learning_event()
    - 返回 episode_id 和 status

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - episode.vault_id 必填, 注入 ContextVar 防跨 vault 学习记录串库.

    [Source: docs/stories/22.4.story.md#API端点实现]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        episode.vault_id,
        subject_id=episode.subject_id,
        canvas_path=episode.canvas_path,
    )

    try:
        episode_id = await memory_service.record_learning_event(
            user_id=episode.user_id,
            canvas_path=episode.canvas_path,
            node_id=episode.node_id,
            concept=episode.concept,
            agent_type=episode.agent_type,
            score=episode.score,
            duration_seconds=episode.duration_seconds,
        )

        logger.info(f"Created learning episode: {episode_id}")
        return LearningEpisodeResponse(episode_id=episode_id, status="created")

    except Exception as e:
        logger.error(f"Failed to create learning episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record learning event: {str(e)}",
        )


# =============================================================================
# GET /episodes - Query learning history (AC-22.4.2, AC-22.4.5)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


@memory_router.get(
    "/episodes",
    response_model=LearningHistoryResponse,
    summary="查询学习历史",
    description="查询用户的学习历史，支持分页和过滤",
)
async def get_learning_history(
    memory_service: MemoryServiceDep,
    user_id: str = Query(..., description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    concept: Optional[str] = Query(None, description="概念过滤"),
    subject: Optional[str] = Query(None, description="学科过滤 (AC-30.8.3)"),
    canvas_path: Optional[str] = Query(
        None, description="Canvas路径 (Epic 6: canvas-scoped filtering)"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description=(
            "Multi-vault P0-2 (Wave-5 Stage B) — 推荐必填. 注入 ContextVar 防跨 vault 历史串库. "
            "Plugin 端 inferVaultId(app.vault.getName()) 取."
        ),
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None,
        deprecated=True,
        description="Deprecated — 改用 vault_id.",
    ),
) -> LearningHistoryResponse:
    """
    查询学习历史

    ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
    - 支持 start_date 和 end_date 过滤
    - 支持 concept 过滤
    - 支持分页 (page, page_size)

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
    - 支持 subject 查询参数过滤

    ✅ Epic 6: 支持 canvas_path 查询参数进行 canvas 级别过滤

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 防跨 vault 历史串库.

    [Source: docs/stories/22.4.story.md#API端点实现]
    [Source: docs/stories/30.8.story.md#Task-3.2]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=group_id,
    )

    try:
        result = await memory_service.get_learning_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            concept=concept,
            subject=subject,
            canvas_path=canvas_path,
            page=page,
            page_size=page_size,
        )

        # Convert items to LearningHistoryItem models
        # Note: Use `or ""` instead of default param to handle None values
        # from legacy data where agent_type may be stored as null
        items = [
            LearningHistoryItem(
                episode_id=item.get("episode_id") or "",
                user_id=item.get("user_id") or "",
                canvas_path=item.get("canvas_path") or "",
                node_id=item.get("node_id") or "",
                concept=item.get("concept") or "",
                agent_type=item.get("agent_type") or "unknown",
                score=item.get("score"),
                duration_seconds=item.get("duration_seconds"),
                timestamp=item.get("timestamp") or "",
            )
            for item in result.get("items", [])
        ]

        return LearningHistoryResponse(
            items=items,
            total=result.get("total", 0),
            page=result.get("page", 1),
            page_size=result.get("page_size", 50),
            pages=result.get("pages", 0),
        )

    except Exception as e:
        logger.error(f"Failed to get learning history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query learning history: {str(e)}",
        )


# =============================================================================
# GET /concepts/{id}/history - Query concept history (AC-22.4.3)
# ✅ Verified from AC-22.4.3
# =============================================================================


@memory_router.get(
    "/concepts/{concept_id}/history",
    response_model=ConceptHistoryResponse,
    summary="查询概念学习历史",
    description="查询特定概念的学习历史，包含时间线和得分变化",
)
async def get_concept_history(
    concept_id: str,
    memory_service: MemoryServiceDep,
    user_id: Optional[str] = Query(None, description="用户ID (optional)"),
    limit: int = Query(50, ge=1, le=200, description="最大返回数量"),
) -> ConceptHistoryResponse:
    """
    查询概念学习历史

    ✅ Verified from AC-22.4.3:
    - 按概念ID查询学习历史
    - 返回时间线数据
    - 包含得分变化

    [Source: docs/stories/22.4.story.md#Dev-Notes]
    """
    try:
        result = await memory_service.get_concept_history(
            concept_id=concept_id, user_id=user_id, limit=limit
        )

        return ConceptHistoryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to get concept history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query concept history: {str(e)}",
        )


# =============================================================================
# GET /review-suggestions - Get review suggestions (AC-22.4.4)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================


@memory_router.get(
    "/review-suggestions",
    response_model=List[ReviewSuggestionResponse],
    summary="获取复习建议",
    description="获取基于艾宾浩斯遗忘曲线的复习建议",
)
async def get_review_suggestions(
    memory_service: MemoryServiceDep,
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    subject: Optional[str] = Query(None, description="学科过滤 (AC-30.8.3)"),
    canvas_path: Optional[str] = Query(
        None, description="Canvas路径 (Epic 6: canvas-scoped filtering)"
    ),
    vault_id: Optional[str] = Query(
        default=None,
        min_length=1,
        description="Multi-vault P0-2 — 推荐必填. 注入 ContextVar 防跨 vault 复习建议串库.",
    ),
    subject_id: Optional[str] = Query(default=None),
    group_id: Optional[str] = Query(
        default=None, deprecated=True, description="Deprecated — 改用 vault_id."
    ),
) -> List[ReviewSuggestionResponse]:
    """
    获取复习建议

    ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
    - 基于艾宾浩斯遗忘曲线
    - 返回需要复习的概念
    - 包含优先级排序

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
    - 支持 subject 查询参数过滤

    ✅ Epic 6: 支持 canvas_path 查询参数进行 canvas 级别过滤

    Wave-5 Stage B (2026-05-12) — Multi-vault P0-2:
    - vault_id 推荐必填, 注入 ContextVar 防跨 vault 复习建议串库.

    [Source: docs/stories/22.4.story.md#API端点实现]
    [Source: docs/stories/30.8.story.md#Task-3.2]
    """
    # Wave-5 Stage B — vault_id ContextVar 注入
    _resolve_vault_group_id(
        vault_id,
        subject_id=subject_id,
        canvas_path=canvas_path,
        legacy_group_id=group_id,
    )

    try:
        suggestions = await memory_service.get_review_suggestions(
            user_id=user_id, limit=limit, subject=subject, canvas_path=canvas_path
        )

        return [
            ReviewSuggestionResponse(
                concept=s.get("concept", ""),
                concept_id=s.get("concept_id", ""),
                last_score=s.get("last_score"),
                review_count=s.get("review_count", 0),
                due_date=s.get("due_date", ""),
                priority=s.get("priority", "medium"),
            )
            for s in suggestions
        ]

    except Exception as e:
        logger.error(f"Failed to get review suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review suggestions: {str(e)}",
        )


# =============================================================================
# GET /health - Memory system health check (AC-30.3.5)
# ✅ Verified from Story 30.3
# =============================================================================


@memory_router.get(
    "/health",
    response_model=MemoryHealthResponse,
    summary="Memory系统健康检查",
    description="获取3层记忆系统的健康状态",
)
async def get_memory_health(memory_service: MemoryServiceDep) -> MemoryHealthResponse:
    """
    获取Memory系统健康状态

    ✅ Verified from Story 30.3 AC-30.3.5:
    - 返回 Temporal (FSRS/SQLite) 层状态
    - 返回 Graphiti (Neo4j) 层状态
    - 返回 Semantic (LanceDB) 层状态
    - 整体状态: healthy/degraded/unhealthy

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.5]
    """
    try:
        health_status = await memory_service.get_health_status()
        return MemoryHealthResponse(**health_status)

    except Exception as e:
        logger.error(f"Failed to get memory health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory health status: {str(e)}",
        )


# =============================================================================
# POST /episodes/batch - Batch record learning events (AC-30.3.10)
# ✅ Verified from Story 30.3
# =============================================================================


@memory_router.post(
    "/episodes/batch",
    response_model=BatchEpisodesResponse,
    status_code=status.HTTP_200_OK,
    summary="批量记录学习事件",
    description="批量记录Canvas节点颜色变化等学习事件(最多50个)",
)
async def create_batch_episodes(
    request: BatchEpisodesRequest, memory_service: MemoryServiceDep
) -> BatchEpisodesResponse:
    """
    批量记录学习事件

    ✅ Verified from Story 30.3 AC-30.3.10:
    - 支持最多50个事件批量提交
    - 返回 processed, failed 计数
    - 错误详情包含失败的事件索引和错误信息

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.10]
    """
    try:
        # Convert Pydantic models to dicts for service
        events_data = [
            {
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "canvas_path": event.canvas_path,
                "node_id": event.node_id,
                "metadata": event.metadata.model_dump() if event.metadata else {},
            }
            for event in request.events
        ]

        result = await memory_service.record_batch_learning_events(events_data)

        return BatchEpisodesResponse(
            success=result["success"],
            processed=result["processed"],
            failed=result["failed"],
            errors=[BatchErrorItem(**err) for err in result["errors"]],
            timestamp=result["timestamp"],
        )

    except Exception as e:
        logger.error(f"Failed to process batch episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch episodes: {str(e)}",
        )


# =============================================================================
# POST /extract-conversation - Sidecar fallback learning extraction
# =============================================================================

import os
from typing import Optional

from fastapi import Header
from pydantic import BaseModel, Field


def _require_observer_token(
    request: Request,
    x_canvas_observer_token: Optional[str] = Header(default=None),
) -> None:
    """
    audit-2026-04-07/p0-2 + ChatGPT-DR-2026-05-13 P0-1 (Wave-6 hardening):
    Gate /extract-conversation behind a shared token. **Default fail-closed**.

    Threat model rationale (ChatGPT Deep Research 2026-05-13):
        Previous default-open behavior allowed any reachable client to POST
        misconceptions into Graphiti when SIDECAR_OBSERVER_TOKEN was unset.
        This is a memory poisoning attack vector — attackers could weaponize
        the personal memory pipeline by injecting bogus misconceptions, which
        would later drive AI exam questions based on attacker-controlled
        misunderstandings ("the personal memory weaponization scenario").

    Auth decision matrix:
        - SIDECAR_OBSERVER_TOKEN set + header matches              → allow
        - SIDECAR_OBSERVER_TOKEN set + header mismatch             → 401
        - SIDECAR_OBSERVER_TOKEN unset + ALLOW_LOCAL_OBSERVER_BYPASS=true
          AND client.host ∈ {127.0.0.1, ::1}                       → allow + warning log
        - SIDECAR_OBSERVER_TOKEN unset + (not loopback OR bypass disabled) → 503

    Local dev bypass requires BOTH (a) explicit env opt-in AND (b) loopback
    client.host check — neither alone is sufficient. Pairs with sidecar
    header set in frontend/sidecar/sidecar.js (CANVAS_OBSERVER_TOKEN).
    """
    expected = (os.environ.get("SIDECAR_OBSERVER_TOKEN") or "").strip()
    provided = (x_canvas_observer_token or "").strip()

    if expected:
        # Production path — token configured, must match
        if provided != expected:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Canvas-Observer-Token",
            )
        return

    # Token unset — fail-closed unless explicit local bypass
    bypass_env = (os.environ.get("ALLOW_LOCAL_OBSERVER_BYPASS") or "").lower() == "true"
    client_host = request.client.host if request.client else None
    is_loopback = client_host in {"127.0.0.1", "::1"}

    if bypass_env and is_loopback:
        logger.warning(
            "observer_token_bypass_local: client=%s reason=ALLOW_LOCAL_OBSERVER_BYPASS=true "
            "on loopback. Configure SIDECAR_OBSERVER_TOKEN for production.",
            client_host,
        )
        return

    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            "Observer auth not configured. Set SIDECAR_OBSERVER_TOKEN env "
            "for production, or ALLOW_LOCAL_OBSERVER_BYPASS=true for loopback dev."
        ),
    )


class ExtractConversationRequest(BaseModel):
    """Request for sidecar fallback conversation extraction."""

    node_id: str = Field(..., description="Canvas node identifier")
    session_id: str = Field("", description="Dialogue session identifier")
    messages: List[dict] = Field(
        ..., description="List of {role, content} message dicts"
    )
    # audit-2026-04-07/p0-2: callers may now scope the extraction to a real
    # canvas/subject instead of falling back to the global DEFAULT_GROUP_ID.
    group_id: Optional[str] = Field(
        default=None,
        description="Explicit Graphiti group_id. Overrides canvas_path inference.",
    )
    canvas_path: Optional[str] = Field(
        default=None,
        description=(
            "Canvas file path (e.g. '数学/微积分.canvas'). Used to derive "
            "group_id via subject_config helpers when group_id is not set."
        ),
    )


class ExtractConversationResponse(BaseModel):
    """Response from fallback extraction."""

    extracted: bool = False
    extracted_count: int = 0
    status: str = "ok"
    message: str = ""
    group_id: Optional[str] = None


@memory_router.post(
    "/extract-conversation",
    response_model=ExtractConversationResponse,
    summary="Extract learning events from conversation (sidecar fallback)",
    description=(
        "Called by sidecar when a conversation turn completes without "
        "record_learning_memory being invoked. Uses ConversationDistiller "
        "(Ollama Tier1) to extract structured learning data and write to Graphiti."
    ),
    dependencies=[Depends(_require_observer_token)],
)
async def extract_conversation_learning(
    request: ExtractConversationRequest,
    memory_service: MemoryServiceDep,
) -> ExtractConversationResponse:
    try:
        from app.services.conversation_distiller import ConversationDistiller
        from app.config import DEFAULT_GROUP_ID
        from app.core.subject_config import (
            build_group_id,
            extract_canvas_name,
            extract_subject_from_canvas_path,
        )

        # audit-2026-04-07/p0-2: resolve target group_id with graceful fallback.
        # Priority:
        #   1. explicit request.group_id (caller knows best)
        #   2. derived from canvas_path (subject + canvas filename)
        #   3. DEFAULT_GROUP_ID (legacy / unknown caller)
        if request.group_id:
            resolved_group_id = request.group_id
        elif request.canvas_path:
            subject = extract_subject_from_canvas_path(request.canvas_path)
            canvas_name = extract_canvas_name(request.canvas_path)
            resolved_group_id = build_group_id(subject, canvas_name)
        else:
            resolved_group_id = DEFAULT_GROUP_ID

        distiller = ConversationDistiller()
        result = await distiller.distill(
            messages=request.messages,
            node_id=request.node_id,
        )

        extracted_count = 0

        for tip in result.tips:
            await memory_service.record_knowledge_entity(
                event_type="learning_tip",
                content=f"[Tip] {tip.title}: {tip.content}",
                metadata={
                    "node_id": request.node_id,
                    "source": "sidecar_fallback",
                    "tags": tip.tags,
                },
                group_id=resolved_group_id,
            )
            extracted_count += 1

        for error in result.errors:
            await memory_service.record_knowledge_entity(
                event_type="misconception",
                content=f"[Error] {error.description}",
                metadata={
                    "node_id": request.node_id,
                    "source": "sidecar_fallback",
                    "error_type": error.error_type,
                },
                group_id=resolved_group_id,
            )
            extracted_count += 1

        logger.info(
            f"[Observer-Fallback] Extracted {extracted_count} items "
            f"for node {request.node_id} into group {resolved_group_id}"
        )

        return ExtractConversationResponse(
            extracted=extracted_count > 0,
            extracted_count=extracted_count,
            status="ok",
            message=f"Extracted {extracted_count} learning items",
            group_id=resolved_group_id,
        )

    except Exception as e:
        logger.error(f"[Observer-Fallback] extract-conversation error: {e}")
        return ExtractConversationResponse(
            extracted=False,
            status="error",
            message=str(e)[:200],
        )
