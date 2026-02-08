# Canvas Learning System - Memory API Endpoints
# Story 22.4: 学习历史存储与查询API
# Story 30.8: 多学科隔离与group_id支持
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter, Depends)
"""
Memory API Endpoints - Learning history storage and query.

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
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import Settings
from app.dependencies import get_settings
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
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter prefix tags)
memory_router = APIRouter()


# =============================================================================
# Dependency Injection - Singleton Pattern for Neo4j Connection Pooling
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies)
# [Source: Story 30.2 - Neo4j connection pool management]
# =============================================================================

# Module-level singleton for MemoryService
# Neo4j driver should persist across requests for connection pooling
_memory_service_instance: Optional[MemoryService] = None


async def get_memory_service(
    settings: Settings = Depends(get_settings)
) -> MemoryService:
    """
    Get MemoryService singleton instance.

    Uses singleton pattern to maintain Neo4j connection pool across requests.
    Driver cleanup is handled by application lifespan events, not per-request.

    ✅ Story 30.2 Fix: Neo4j driver should persist for connection pooling
    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies)

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
    """
    global _memory_service_instance

    if _memory_service_instance is None:
        logger.info("Creating MemoryService singleton instance")
        _memory_service_instance = MemoryService()
        await _memory_service_instance.initialize()
        logger.info("MemoryService singleton initialized")

    return _memory_service_instance


async def cleanup_memory_service() -> None:
    """
    Cleanup MemoryService singleton - called on application shutdown.

    [Source: Story 30.2 - Application lifespan management]
    """
    global _memory_service_instance
    if _memory_service_instance is not None:
        await _memory_service_instance.cleanup()
        _memory_service_instance = None
        logger.info("MemoryService singleton cleaned up")


# Type alias for MemoryService dependency
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
    description="记录用户的学习事件，存储到Neo4j和Graphiti"
)
async def create_learning_episode(
    episode: LearningEpisodeCreate,
    memory_service: MemoryServiceDep
) -> LearningEpisodeResponse:
    """
    记录学习事件

    ✅ Verified from docs/stories/22.4.story.md#create_learning_episode:
    - 调用 memory_service.record_learning_event()
    - 返回 episode_id 和 status

    [Source: docs/stories/22.4.story.md#API端点实现]
    """
    try:
        episode_id = await memory_service.record_learning_event(
            user_id=episode.user_id,
            canvas_path=episode.canvas_path,
            node_id=episode.node_id,
            concept=episode.concept,
            agent_type=episode.agent_type,
            score=episode.score,
            duration_seconds=episode.duration_seconds
        )

        logger.info(f"Created learning episode: {episode_id}")
        return LearningEpisodeResponse(
            episode_id=episode_id,
            status="created"
        )

    except Exception as e:
        logger.error(f"Failed to create learning episode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record learning event: {str(e)}"
        )


# =============================================================================
# GET /episodes - Query learning history (AC-22.4.2, AC-22.4.5)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================

@memory_router.get(
    "/episodes",
    response_model=LearningHistoryResponse,
    summary="查询学习历史",
    description="查询用户的学习历史，支持分页和过滤"
)
async def get_learning_history(
    memory_service: MemoryServiceDep,
    user_id: str = Query(..., description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    concept: Optional[str] = Query(None, description="概念过滤"),
    subject: Optional[str] = Query(None, description="学科过滤 (AC-30.8.3)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小")
) -> LearningHistoryResponse:
    """
    查询学习历史

    ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
    - 支持 start_date 和 end_date 过滤
    - 支持 concept 过滤
    - 支持分页 (page, page_size)

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
    - 支持 subject 查询参数过滤

    [Source: docs/stories/22.4.story.md#API端点实现]
    [Source: docs/stories/30.8.story.md#Task-3.2]
    """
    try:
        result = await memory_service.get_learning_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            concept=concept,
            subject=subject,
            page=page,
            page_size=page_size
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
                timestamp=item.get("timestamp") or ""
            )
            for item in result.get("items", [])
        ]

        return LearningHistoryResponse(
            items=items,
            total=result.get("total", 0),
            page=result.get("page", 1),
            page_size=result.get("page_size", 50),
            pages=result.get("pages", 0)
        )

    except Exception as e:
        logger.error(f"Failed to get learning history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query learning history: {str(e)}"
        )


# =============================================================================
# GET /concepts/{id}/history - Query concept history (AC-22.4.3)
# ✅ Verified from AC-22.4.3
# =============================================================================

@memory_router.get(
    "/concepts/{concept_id}/history",
    response_model=ConceptHistoryResponse,
    summary="查询概念学习历史",
    description="查询特定概念的学习历史，包含时间线和得分变化"
)
async def get_concept_history(
    concept_id: str,
    memory_service: MemoryServiceDep,
    user_id: Optional[str] = Query(None, description="用户ID (optional)"),
    limit: int = Query(50, ge=1, le=200, description="最大返回数量")
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
            concept_id=concept_id,
            user_id=user_id,
            limit=limit
        )

        return ConceptHistoryResponse(**result)

    except Exception as e:
        logger.error(f"Failed to get concept history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query concept history: {str(e)}"
        )


# =============================================================================
# GET /review-suggestions - Get review suggestions (AC-22.4.4)
# ✅ Verified from docs/stories/22.4.story.md#API端点实现
# =============================================================================

@memory_router.get(
    "/review-suggestions",
    response_model=List[ReviewSuggestionResponse],
    summary="获取复习建议",
    description="获取基于艾宾浩斯遗忘曲线的复习建议"
)
async def get_review_suggestions(
    memory_service: MemoryServiceDep,
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    subject: Optional[str] = Query(None, description="学科过滤 (AC-30.8.3)")
) -> List[ReviewSuggestionResponse]:
    """
    获取复习建议

    ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
    - 基于艾宾浩斯遗忘曲线
    - 返回需要复习的概念
    - 包含优先级排序

    ✅ Verified from docs/stories/30.8.story.md#AC-30.8.3:
    - 支持 subject 查询参数过滤

    [Source: docs/stories/22.4.story.md#API端点实现]
    [Source: docs/stories/30.8.story.md#Task-3.2]
    """
    try:
        suggestions = await memory_service.get_review_suggestions(
            user_id=user_id,
            limit=limit,
            subject=subject
        )

        return [
            ReviewSuggestionResponse(
                concept=s.get("concept", ""),
                concept_id=s.get("concept_id", ""),
                last_score=s.get("last_score"),
                review_count=s.get("review_count", 0),
                due_date=s.get("due_date", ""),
                priority=s.get("priority", "medium")
            )
            for s in suggestions
        ]

    except Exception as e:
        logger.error(f"Failed to get review suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review suggestions: {str(e)}"
        )


# =============================================================================
# GET /health - Memory system health check (AC-30.3.5)
# ✅ Verified from Story 30.3
# =============================================================================

@memory_router.get(
    "/health",
    response_model=MemoryHealthResponse,
    summary="Memory系统健康检查",
    description="获取3层记忆系统的健康状态"
)
async def get_memory_health(
    memory_service: MemoryServiceDep
) -> MemoryHealthResponse:
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
            detail=f"Failed to get memory health status: {str(e)}"
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
    description="批量记录Canvas节点颜色变化等学习事件(最多50个)"
)
async def create_batch_episodes(
    request: BatchEpisodesRequest,
    memory_service: MemoryServiceDep
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
                "metadata": event.metadata.model_dump() if event.metadata else {}
            }
            for event in request.events
        ]

        result = await memory_service.record_batch_learning_events(events_data)

        return BatchEpisodesResponse(
            success=result["success"],
            processed=result["processed"],
            failed=result["failed"],
            errors=[BatchErrorItem(**err) for err in result["errors"]],
            timestamp=result["timestamp"]
        )

    except Exception as e:
        logger.error(f"Failed to process batch episodes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process batch episodes: {str(e)}"
        )
