# Canvas Learning System - Memory API Endpoints
# Story 22.4: 学习历史存储与查询API
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter, Depends)
"""
Memory API Endpoints - Learning history storage and query.

Story 22.4 Implementation:
- POST /episodes: Record learning events (AC-22.4.1)
- GET /episodes: Query learning history (AC-22.4.2)
- GET /concepts/{id}/history: Query concept history (AC-22.4.3)
- GET /review-suggestions: Get review suggestions (AC-22.4.4)

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#API端点实现]
"""

import logging
from datetime import datetime
from typing import Annotated, AsyncGenerator, List, Optional

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import Settings
from app.dependencies import get_settings
from app.models.memory_schemas import (
    ConceptHistoryResponse,
    LearningEpisodeCreate,
    LearningEpisodeResponse,
    LearningHistoryItem,
    LearningHistoryResponse,
    ReviewSuggestionResponse,
)
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter prefix tags)
memory_router = APIRouter()


# =============================================================================
# Dependency Injection
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies with yield)
# =============================================================================

async def get_memory_service(
    settings: Settings = Depends(get_settings)
) -> AsyncGenerator[MemoryService, None]:
    """
    Get MemoryService instance with automatic resource cleanup.

    Uses yield syntax to support resource cleanup after request completion.

    ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: dependencies-with-yield)

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
    """
    logger.debug("Creating MemoryService instance")
    service = MemoryService()
    try:
        await service.initialize()
        yield service
    finally:
        await service.cleanup()
        logger.debug("MemoryService cleanup completed")


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
    user_id: str = Query(..., description="用户ID"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    concept: Optional[str] = Query(None, description="概念过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    memory_service: MemoryServiceDep = None
) -> LearningHistoryResponse:
    """
    查询学习历史

    ✅ Verified from docs/stories/22.4.story.md#get_learning_history:
    - 支持 start_date 和 end_date 过滤
    - 支持 concept 过滤
    - 支持分页 (page, page_size)

    [Source: docs/stories/22.4.story.md#API端点实现]
    """
    try:
        result = await memory_service.get_learning_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            concept=concept,
            page=page,
            page_size=page_size
        )

        # Convert items to LearningHistoryItem models
        items = [
            LearningHistoryItem(
                episode_id=item.get("episode_id", ""),
                user_id=item.get("user_id", ""),
                canvas_path=item.get("canvas_path", ""),
                node_id=item.get("node_id", ""),
                concept=item.get("concept", ""),
                agent_type=item.get("agent_type", ""),
                score=item.get("score"),
                duration_seconds=item.get("duration_seconds"),
                timestamp=item.get("timestamp", "")
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
    user_id: Optional[str] = Query(None, description="用户ID (optional)"),
    limit: int = Query(50, ge=1, le=200, description="最大返回数量"),
    memory_service: MemoryServiceDep = None
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
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    memory_service: MemoryServiceDep = None
) -> List[ReviewSuggestionResponse]:
    """
    获取复习建议

    ✅ Verified from docs/stories/22.4.story.md#get_review_suggestions:
    - 基于艾宾浩斯遗忘曲线
    - 返回需要复习的概念
    - 包含优先级排序

    [Source: docs/stories/22.4.story.md#API端点实现]
    """
    try:
        suggestions = await memory_service.get_review_suggestions(
            user_id=user_id,
            limit=limit
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
