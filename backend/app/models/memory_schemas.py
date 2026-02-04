# Canvas Learning System - Memory API Pydantic Schemas
# Story 22.4: 学习历史存储与查询API
# ✅ Verified from docs/stories/22.4.story.md#Pydantic模型
"""
Pydantic Models for Memory API.

Story 22.4 Implementation:
- LearningEpisodeCreate: Request for creating learning episodes
- LearningEpisodeResponse: Response for created episodes
- LearningHistoryResponse: Paginated learning history
- ReviewSuggestionResponse: Review suggestion with priority

[Source: docs/prd/EPIC-22-MEMORY-SYSTEM-NEO4J-GRAPHITI.md#Story-22.4]
[Source: docs/stories/22.4.story.md#Pydantic模型]
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Learning Episode Schemas
# [Source: docs/stories/22.4.story.md#Pydantic模型]
# =============================================================================

class LearningEpisodeCreate(BaseModel):
    """
    Request model for creating a learning episode.

    ✅ Verified from docs/stories/22.4.story.md#LearningEpisodeCreate:
    - user_id: 用户ID (required)
    - canvas_path: Canvas文件路径 (required)
    - node_id: Canvas节点ID (required)
    - concept: 学习概念 (required)
    - agent_type: 使用的Agent类型 (required)
    - score: 得分 (optional, 0-100)
    - duration_seconds: 学习时长 (optional)

    [Source: docs/stories/22.4.story.md#Pydantic模型]
    """
    user_id: str = Field(..., description="用户ID")
    canvas_path: str = Field(..., description="Canvas文件路径")
    node_id: str = Field(..., description="Canvas节点ID")
    concept: str = Field(..., description="学习概念")
    agent_type: str = Field(..., description="使用的Agent类型")
    score: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="得分 (0-100)"
    )
    duration_seconds: Optional[int] = Field(
        None,
        ge=0,
        description="学习时长 (秒)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "canvas_path": "离散数学.canvas",
                "node_id": "node-abc123",
                "concept": "逆否命题",
                "agent_type": "basic-decomposition",
                "score": 85,
                "duration_seconds": 300
            }
        }
    )


class LearningEpisodeResponse(BaseModel):
    """
    Response model for created learning episode.

    ✅ Verified from docs/stories/22.4.story.md#LearningEpisodeResponse:
    - episode_id: 生成的Episode ID
    - status: 状态 ("created")

    [Source: docs/stories/22.4.story.md#Pydantic模型]
    """
    episode_id: str = Field(..., description="Episode唯一标识")
    status: str = Field(..., description="状态")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "episode_id": "episode-a1b2c3d4e5f67890",
                "status": "created"
            }
        }
    )


# =============================================================================
# Learning History Schemas
# [Source: docs/stories/22.4.story.md#API规范]
# =============================================================================

class LearningHistoryItem(BaseModel):
    """
    Single item in learning history.

    [Source: docs/stories/22.4.story.md#API规范 - GET /episodes response]
    """
    episode_id: str = Field(..., description="Episode ID")
    user_id: str = Field(..., description="用户ID")
    canvas_path: str = Field(..., description="Canvas文件路径")
    node_id: str = Field(..., description="Canvas节点ID")
    concept: str = Field(..., description="学习概念")
    agent_type: str = Field(..., description="使用的Agent类型")
    score: Optional[int] = Field(None, description="得分")
    duration_seconds: Optional[int] = Field(None, description="学习时长")
    timestamp: str = Field(..., description="时间戳 (ISO format)")


class LearningHistoryResponse(BaseModel):
    """
    Paginated response for learning history.

    ✅ Verified from docs/stories/22.4.story.md#API规范:
    - items: 学习历史列表
    - total: 总数
    - page: 当前页
    - page_size: 每页大小
    - pages: 总页数

    [Source: docs/stories/22.4.story.md#API规范]
    """
    items: List[LearningHistoryItem] = Field(..., description="学习历史列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "episode_id": "episode-a1b2c3d4e5f67890",
                        "user_id": "user-123",
                        "canvas_path": "离散数学.canvas",
                        "node_id": "node-abc123",
                        "concept": "逆否命题",
                        "agent_type": "basic-decomposition",
                        "score": 85,
                        "duration_seconds": 300,
                        "timestamp": "2025-12-12T10:30:00"
                    }
                ],
                "total": 100,
                "page": 1,
                "page_size": 50,
                "pages": 2
            }
        }
    )


# =============================================================================
# Concept History Schemas
# [Source: AC-22.4.3: GET /api/v1/memory/concepts/{id}/history]
# =============================================================================

class ConceptHistoryTimeline(BaseModel):
    """
    Single timeline entry for concept history.

    [Source: AC-22.4.3]
    """
    timestamp: Optional[str] = Field(None, description="时间戳")
    score: Optional[int] = Field(None, description="得分")
    user_id: Optional[str] = Field(None, description="用户ID")
    concept: Optional[str] = Field(None, description="概念名称")
    review_count: int = Field(0, description="复习次数")


class ScoreTrend(BaseModel):
    """
    Score trend analysis for concept history.

    [Source: AC-22.4.3]
    """
    first: Optional[int] = Field(None, description="首次得分")
    last: Optional[int] = Field(None, description="最近得分")
    average: Optional[float] = Field(None, description="平均得分")
    improvement: Optional[int] = Field(None, description="分数提升")


class ConceptHistoryResponse(BaseModel):
    """
    Response for concept learning history.

    ✅ Verified from AC-22.4.3: GET /api/v1/memory/concepts/{id}/history

    [Source: docs/stories/22.4.story.md#Dev-Notes]
    """
    concept_id: str = Field(..., description="概念ID")
    timeline: List[ConceptHistoryTimeline] = Field(..., description="时间线数据")
    score_trend: ScoreTrend = Field(..., description="得分趋势")
    total_reviews: int = Field(..., description="总复习次数")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "concept_id": "concept-123",
                "timeline": [
                    {
                        "timestamp": "2025-12-12T10:30:00",
                        "score": 85,
                        "user_id": "user-123",
                        "concept": "逆否命题",
                        "review_count": 3
                    }
                ],
                "score_trend": {
                    "first": 60,
                    "last": 85,
                    "average": 72.5,
                    "improvement": 25
                },
                "total_reviews": 5
            }
        }
    )


# =============================================================================
# Memory Health Schemas
# [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.5]
# =============================================================================

class LayerStatus(str, Enum):
    """Layer status values."""
    ok = "ok"
    error = "error"


class OverallStatus(str, Enum):
    """Overall system status values."""
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"


class LayerHealthStatus(BaseModel):
    """Health status for a single memory layer."""
    status: LayerStatus = Field(..., description="层状态: ok/error")
    backend: Optional[str] = Field(None, description="后端类型")
    node_count: Optional[int] = Field(None, description="节点数量(graphiti层)")
    vector_count: Optional[int] = Field(None, description="向量数量(semantic层)")
    error: Optional[str] = Field(None, description="错误信息(仅error时)")


class MemoryLayersStatus(BaseModel):
    """Status of all 3 memory layers."""
    temporal: LayerHealthStatus = Field(..., description="Temporal层状态")
    graphiti: LayerHealthStatus = Field(..., description="Graphiti层状态")
    semantic: LayerHealthStatus = Field(..., description="Semantic层状态")


class MemoryHealthResponse(BaseModel):
    """
    Response model for memory health check.

    ✅ Verified from Story 30.3 AC-30.3.5:
    - 返回 Temporal (FSRS/SQLite) 层状态
    - 返回 Graphiti (Neo4j) 层状态
    - 返回 Semantic (LanceDB) 层状态
    - 整体状态: healthy/degraded/unhealthy

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.5]
    """
    status: OverallStatus = Field(..., description="整体状态")
    layers: MemoryLayersStatus = Field(..., description="3层系统状态")
    timestamp: str = Field(..., description="检查时间戳")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "layers": {
                    "temporal": {"status": "ok", "backend": "sqlite"},
                    "graphiti": {"status": "ok", "backend": "neo4j", "node_count": 1234},
                    "semantic": {"status": "ok", "backend": "lancedb", "vector_count": 5678}
                },
                "timestamp": "2026-01-16T10:00:00Z"
            }
        }
    )


# =============================================================================
# Batch Episodes Schemas
# [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.10]
# =============================================================================

class MasteryLevel(str, Enum):
    """Mastery level values for color changes."""
    not_understood = "not_understood"
    learning = "learning"
    mastered = "mastered"
    pending_verification = "pending_verification"


class ColorCode(str, Enum):
    """Canvas color codes (1-6)."""
    color_1 = "1"
    color_2 = "2"
    color_3 = "3"
    color_4 = "4"
    color_5 = "5"
    color_6 = "6"


class BatchEventMetadata(BaseModel):
    """Metadata for batch learning events."""
    old_color: Optional[ColorCode] = Field(None, description="变化前颜色代码")
    new_color: Optional[ColorCode] = Field(None, description="变化后颜色代码")
    old_level: Optional[MasteryLevel] = Field(None, description="变化前掌握等级")
    new_level: Optional[MasteryLevel] = Field(None, description="变化后掌握等级")


class BatchEventItem(BaseModel):
    """Single event item in batch request."""
    event_type: str = Field(..., description="事件类型")
    timestamp: str = Field(..., description="事件时间戳 (ISO format)")
    canvas_path: str = Field(..., description="Canvas文件路径")
    node_id: str = Field(..., description="节点ID")
    metadata: Optional[BatchEventMetadata] = Field(None, description="事件元数据")


class BatchEpisodesRequest(BaseModel):
    """
    Request model for batch learning episodes.

    ✅ Verified from Story 30.3 AC-30.3.10:
    - 最多50个事件
    - 每个事件包含 event_type, timestamp, canvas_path, node_id
    - 可选 metadata 包含颜色变化信息

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.10]
    """
    events: List[BatchEventItem] = Field(
        ...,
        max_length=50,
        description="批量事件列表(最多50个)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "events": [
                    {
                        "event_type": "color_changed",
                        "timestamp": "2026-01-16T12:00:00Z",
                        "canvas_path": "离散数学/命题逻辑.canvas",
                        "node_id": "b33c50660173e5d3",
                        "metadata": {
                            "old_color": "1",
                            "new_color": "2",
                            "old_level": "not_understood",
                            "new_level": "mastered"
                        }
                    }
                ]
            }
        }
    )


class BatchErrorItem(BaseModel):
    """Error detail for failed batch event."""
    index: int = Field(..., description="失败事件在请求数组中的索引")
    error: str = Field(..., description="错误信息")


class BatchEpisodesResponse(BaseModel):
    """
    Response model for batch learning episodes.

    ✅ Verified from Story 30.3 AC-30.3.10:
    - success: 整体操作是否成功
    - processed: 成功处理的事件数量
    - failed: 处理失败的事件数量
    - errors: 错误详情列表

    [Source: docs/stories/30.3.memory-api-health-endpoints.story.md#AC-30.3.10]
    """
    success: bool = Field(..., description="整体操作是否成功")
    processed: int = Field(..., ge=0, description="成功处理的事件数量")
    failed: int = Field(..., ge=0, description="处理失败的事件数量")
    errors: List[BatchErrorItem] = Field(
        default_factory=list,
        description="错误详情列表"
    )
    timestamp: str = Field(..., description="响应时间戳")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "processed": 5,
                "failed": 0,
                "errors": [],
                "timestamp": "2026-01-16T12:00:00Z"
            }
        }
    )


# =============================================================================
# Review Suggestion Schemas
# [Source: docs/stories/22.4.story.md#ReviewSuggestionResponse]
# =============================================================================

class ReviewPriority(str, Enum):
    """Review priority levels."""
    high = "high"
    medium = "medium"
    low = "low"


class ReviewSuggestionResponse(BaseModel):
    """
    Response model for review suggestion.

    ✅ Verified from docs/stories/22.4.story.md#ReviewSuggestionResponse:
    - concept: 概念名称
    - concept_id: 概念ID
    - last_score: 最近得分
    - review_count: 复习次数
    - due_date: 到期日期
    - priority: 优先级 (high/medium/low)

    [Source: docs/stories/22.4.story.md#Pydantic模型]
    """
    concept: str = Field(..., description="概念名称")
    concept_id: str = Field(..., description="概念ID")
    last_score: Optional[int] = Field(None, description="最近得分")
    review_count: int = Field(..., description="复习次数")
    due_date: str = Field(..., description="到期日期 (ISO format)")
    priority: str = Field(..., description="优先级: high, medium, low")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "concept": "逆否命题",
                "concept_id": "concept-123",
                "last_score": 75,
                "review_count": 2,
                "due_date": "2025-12-12T00:00:00",
                "priority": "high"
            }
        }
    )


# =============================================================================
# Exported Models
# =============================================================================

__all__ = [
    "LearningEpisodeCreate",
    "LearningEpisodeResponse",
    "LearningHistoryItem",
    "LearningHistoryResponse",
    "ConceptHistoryTimeline",
    "ScoreTrend",
    "ConceptHistoryResponse",
    "LayerStatus",
    "OverallStatus",
    "LayerHealthStatus",
    "MemoryLayersStatus",
    "MemoryHealthResponse",
    "MasteryLevel",
    "ColorCode",
    "BatchEventMetadata",
    "BatchEventItem",
    "BatchEpisodesRequest",
    "BatchErrorItem",
    "BatchEpisodesResponse",
    "ReviewPriority",
    "ReviewSuggestionResponse",
]
