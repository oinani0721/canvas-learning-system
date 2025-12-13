# Canvas Learning System - Cross Canvas API Endpoints
# Story 20.2: 跨Canvas后端API (Epic 16 Integration)
"""
Cross-Canvas Association API Endpoints

提供跨Canvas关联管理功能:
- Canvas关联CRUD操作
- 知识路径管理
- 概念跨Canvas搜索

[Source: Epic 16 - 跨Canvas关联学习系统]
[Source: Story 20.2 - Plugin集成统一]
"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import CrossCanvasServiceDep
from app.services.cross_canvas_service import (
    CrossCanvasService,
    CrossCanvasAssociation,
    CanvasAssociationSuggestion,
    KnowledgePath,
    KnowledgePathNode,
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Create router
cross_canvas_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════

class CanvasRelationshipType(str):
    """Relationship types between canvases

    [Source: Story 25.3 - Exercise-Lecture Canvas Association]
    """
    PREREQUISITE = "prerequisite"      # A是B的前置知识
    EXTENSION = "extension"            # A是B的延伸扩展
    RELATED = "related"                # A和B相关但无依赖
    SAME_TOPIC = "same_topic"          # A和B讨论同一主题
    # Story 25.3: Exercise-Lecture association types
    EXERCISE_LECTURE = "exercise_lecture"    # 练习Canvas关联到讲座Canvas
    EXERCISE_SOLUTION = "exercise_solution"  # 练习Canvas关联到解答Canvas


class CrossCanvasAssociationCreate(BaseModel):
    """Request to create a cross-canvas association"""
    source_canvas_path: str = Field(..., description="源Canvas文件路径")
    target_canvas_path: str = Field(..., description="目标Canvas文件路径")
    relationship_type: str = Field(..., description="关系类型: prerequisite/extension/related/same_topic")
    common_concepts: Optional[List[str]] = Field(default=None, description="共同概念列表")
    confidence: Optional[float] = Field(default=0.5, ge=0, le=1, description="关联置信度(0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "source_canvas_path": "数学/离散数学.canvas",
                "target_canvas_path": "数学/集合论.canvas",
                "relationship_type": "prerequisite",
                "common_concepts": ["集合", "映射"],
                "confidence": 0.8
            }
        }


class CrossCanvasAssociationUpdate(BaseModel):
    """Request to update a cross-canvas association"""
    relationship_type: Optional[str] = Field(None, description="关系类型")
    common_concepts: Optional[List[str]] = Field(None, description="共同概念列表")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="关联置信度")


class CrossCanvasAssociationResponse(BaseModel):
    """Cross-canvas association response"""
    id: str = Field(..., description="关联ID")
    source_canvas_path: str = Field(..., description="源Canvas路径")
    source_canvas_title: str = Field(..., description="源Canvas标题")
    target_canvas_path: str = Field(..., description="目标Canvas路径")
    target_canvas_title: str = Field(..., description="目标Canvas标题")
    relationship_type: str = Field(..., description="关系类型")
    common_concepts: List[str] = Field(default_factory=list, description="共同概念")
    confidence: float = Field(..., description="置信度")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class KnowledgePathNodeCreate(BaseModel):
    """Node in a knowledge path"""
    canvas_path: str = Field(..., description="Canvas路径")
    order: int = Field(..., ge=1, description="顺序")
    prerequisite_concepts: Optional[List[str]] = Field(default=None, description="前置概念")


class KnowledgePathCreate(BaseModel):
    """Request to create a knowledge path"""
    name: str = Field(..., min_length=1, max_length=100, description="路径名称")
    description: str = Field(default="", max_length=500, description="路径描述")
    nodes: List[KnowledgePathNodeCreate] = Field(..., min_items=1, description="路径节点")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "离散数学学习路径",
                "description": "从集合论到图论的学习路径",
                "nodes": [
                    {"canvas_path": "数学/集合论.canvas", "order": 1},
                    {"canvas_path": "数学/离散数学.canvas", "order": 2},
                    {"canvas_path": "数学/图论.canvas", "order": 3}
                ]
            }
        }


class KnowledgePathNodeResponse(BaseModel):
    """Knowledge path node response"""
    canvas_path: str
    canvas_title: str
    order: int
    prerequisite_concepts: List[str] = Field(default_factory=list)
    mastery_level: float = Field(default=0, ge=0, le=1)
    is_completed: bool = Field(default=False)


class KnowledgePathResponse(BaseModel):
    """Knowledge path response"""
    id: str
    name: str
    description: str
    nodes: List[KnowledgePathNodeResponse]
    completion_progress: float = Field(ge=0, le=1)
    recommended_next: Optional[KnowledgePathNodeResponse] = None


class KnowledgePathMasteryUpdate(BaseModel):
    """Request to update mastery for a path node"""
    mastery_level: float = Field(..., ge=0, le=1, description="掌握程度")
    is_completed: bool = Field(..., description="是否完成")


class CanvasOccurrence(BaseModel):
    """Concept occurrence in a canvas"""
    canvas_path: str
    canvas_title: str
    node_id: str
    node_text: str
    node_color: Optional[str] = None


class ConceptSearchResult(BaseModel):
    """Concept search result across canvases"""
    concept: str
    canvas_occurrences: List[CanvasOccurrence]
    total_count: int


class CrossCanvasStatistics(BaseModel):
    """Cross-canvas statistics"""
    total_associations: int
    total_paths: int
    total_canvases_linked: int
    average_path_completion: float


class CanvasAssociationSuggestionResponse(BaseModel):
    """Suggested canvas association response

    [Source: Story 25.3 AC5 - Batch association suggestions]
    """
    target_canvas_path: str = Field(..., description="目标Canvas路径")
    target_canvas_title: str = Field(..., description="目标Canvas标题")
    relationship_type: str = Field(..., description="建议的关系类型")
    confidence: float = Field(..., ge=0, le=1, description="置信度(0-1)")
    reason: str = Field(..., description="建议原因")


# ═══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _association_to_response(assoc: CrossCanvasAssociation) -> CrossCanvasAssociationResponse:
    """Convert internal CrossCanvasAssociation to API response model."""
    return CrossCanvasAssociationResponse(
        id=assoc.id,
        source_canvas_path=assoc.source_canvas_path,
        source_canvas_title=assoc.source_canvas_title,
        target_canvas_path=assoc.target_canvas_path,
        target_canvas_title=assoc.target_canvas_title,
        relationship_type=assoc.relationship_type,
        common_concepts=assoc.common_concepts,
        confidence=assoc.confidence,
        created_at=assoc.created_at,
        updated_at=assoc.updated_at
    )


def _knowledge_path_node_to_response(node: KnowledgePathNode) -> KnowledgePathNodeResponse:
    """Convert internal KnowledgePathNode to API response model."""
    return KnowledgePathNodeResponse(
        canvas_path=node.canvas_path,
        canvas_title=node.canvas_title,
        order=node.order,
        prerequisite_concepts=node.prerequisite_concepts,
        mastery_level=node.mastery_level,
        is_completed=node.is_completed
    )


def _knowledge_path_to_response(path: KnowledgePath) -> KnowledgePathResponse:
    """Convert internal KnowledgePath to API response model."""
    nodes = [_knowledge_path_node_to_response(n) for n in path.nodes]

    # Find recommended next (first incomplete node)
    recommended_next = next(
        (_knowledge_path_node_to_response(n) for n in path.nodes if not n.is_completed),
        None
    )

    return KnowledgePathResponse(
        id=path.id,
        name=path.name,
        description=path.description,
        nodes=nodes,
        completion_progress=path.completion_progress,
        recommended_next=recommended_next
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Association Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@cross_canvas_router.get(
    "/associations",
    response_model=List[CrossCanvasAssociationResponse],
    summary="获取所有Canvas关联",
    description="返回所有跨Canvas关联，按更新时间倒序排列",
    operation_id="list_associations"
)
async def list_associations(
    cross_canvas_service: CrossCanvasServiceDep,
    canvas_path: Optional[str] = Query(None, description="过滤特定Canvas的关联"),
    relation_type: Optional[str] = Query(None, description="按关联类型过滤")
) -> List[CrossCanvasAssociationResponse]:
    """List all cross-canvas associations"""
    logger.info(f"Listing associations, filter: canvas_path={canvas_path}, relation_type={relation_type}")

    if canvas_path:
        # Use get_associated_canvases for filtered queries
        associations = await cross_canvas_service.get_associated_canvases(
            canvas_path, relation_type
        )
    else:
        # Get all associations
        associations = await cross_canvas_service.list_associations()

    return [_association_to_response(a) for a in associations]


@cross_canvas_router.post(
    "/associations",
    response_model=CrossCanvasAssociationResponse,
    summary="创建Canvas关联",
    description="创建两个Canvas之间的关联关系",
    operation_id="create_association",
    status_code=201
)
async def create_association(
    cross_canvas_service: CrossCanvasServiceDep,
    request: CrossCanvasAssociationCreate
) -> CrossCanvasAssociationResponse:
    """Create a new cross-canvas association"""
    logger.info(f"Creating association: {request.source_canvas_path} -> {request.target_canvas_path}")

    association = await cross_canvas_service.create_association(
        source_canvas_path=request.source_canvas_path,
        target_canvas_path=request.target_canvas_path,
        relationship_type=request.relationship_type,
        common_concepts=request.common_concepts or [],
        confidence=request.confidence or 0.5
    )

    return _association_to_response(association)


@cross_canvas_router.get(
    "/associations/{association_id}",
    response_model=CrossCanvasAssociationResponse,
    summary="获取关联详情",
    description="根据ID获取特定关联的详细信息",
    operation_id="get_association"
)
async def get_association(
    cross_canvas_service: CrossCanvasServiceDep,
    association_id: str
) -> CrossCanvasAssociationResponse:
    """Get a specific association by ID"""
    association = await cross_canvas_service.get_association(association_id)
    if association is None:
        raise HTTPException(status_code=404, detail=f"Association {association_id} not found")
    return _association_to_response(association)


@cross_canvas_router.put(
    "/associations/{association_id}",
    response_model=CrossCanvasAssociationResponse,
    summary="更新关联",
    description="更新现有Canvas关联",
    operation_id="update_association"
)
async def update_association(
    cross_canvas_service: CrossCanvasServiceDep,
    association_id: str,
    request: CrossCanvasAssociationUpdate
) -> CrossCanvasAssociationResponse:
    """Update an existing association"""
    association = await cross_canvas_service.update_association(
        association_id=association_id,
        relationship_type=request.relationship_type,
        common_concepts=request.common_concepts,
        confidence=request.confidence
    )

    if association is None:
        raise HTTPException(status_code=404, detail=f"Association {association_id} not found")

    return _association_to_response(association)


@cross_canvas_router.delete(
    "/associations/{association_id}",
    summary="删除关联",
    description="删除Canvas关联",
    operation_id="delete_association",
    status_code=204
)
async def delete_association(
    cross_canvas_service: CrossCanvasServiceDep,
    association_id: str
) -> None:
    """Delete an association"""
    success = await cross_canvas_service.delete_association(association_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Association {association_id} not found")

    logger.info(f"Deleted association: {association_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# Knowledge Path Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@cross_canvas_router.get(
    "/paths",
    response_model=List[KnowledgePathResponse],
    summary="获取所有知识路径",
    description="返回所有知识学习路径",
    operation_id="list_knowledge_paths"
)
async def list_knowledge_paths(
    cross_canvas_service: CrossCanvasServiceDep
) -> List[KnowledgePathResponse]:
    """List all knowledge paths"""
    logger.info("Listing knowledge paths")
    paths = await cross_canvas_service.list_knowledge_paths()
    return [_knowledge_path_to_response(p) for p in paths]


@cross_canvas_router.post(
    "/paths",
    response_model=KnowledgePathResponse,
    summary="创建知识路径",
    description="创建新的知识学习路径",
    operation_id="create_knowledge_path",
    status_code=201
)
async def create_knowledge_path(
    cross_canvas_service: CrossCanvasServiceDep,
    request: KnowledgePathCreate
) -> KnowledgePathResponse:
    """Create a new knowledge path"""
    logger.info(f"Creating knowledge path: {request.name}")

    # Convert request nodes to dict format expected by service
    nodes = [
        {
            "canvas_path": node.canvas_path,
            "order": node.order,
            "prerequisite_concepts": node.prerequisite_concepts or []
        }
        for node in request.nodes
    ]

    path = await cross_canvas_service.create_knowledge_path(
        name=request.name,
        description=request.description,
        nodes=nodes
    )

    return _knowledge_path_to_response(path)


@cross_canvas_router.get(
    "/paths/{path_id}",
    response_model=KnowledgePathResponse,
    summary="获取知识路径详情",
    description="根据ID获取知识路径详情",
    operation_id="get_knowledge_path"
)
async def get_knowledge_path(
    cross_canvas_service: CrossCanvasServiceDep,
    path_id: str
) -> KnowledgePathResponse:
    """Get a specific knowledge path by ID"""
    path = await cross_canvas_service.get_knowledge_path(path_id)
    if path is None:
        raise HTTPException(status_code=404, detail=f"Knowledge path {path_id} not found")
    return _knowledge_path_to_response(path)


@cross_canvas_router.put(
    "/paths/{path_id}/nodes/{canvas_path:path}/mastery",
    response_model=KnowledgePathResponse,
    summary="更新节点掌握度",
    description="更新知识路径中特定节点的掌握程度",
    operation_id="update_node_mastery"
)
async def update_node_mastery(
    cross_canvas_service: CrossCanvasServiceDep,
    path_id: str,
    canvas_path: str,
    request: KnowledgePathMasteryUpdate
) -> KnowledgePathResponse:
    """Update mastery level for a node in a knowledge path"""
    path = await cross_canvas_service.update_node_mastery(
        path_id=path_id,
        canvas_path=canvas_path,
        mastery_level=request.mastery_level,
        is_completed=request.is_completed
    )

    if path is None:
        raise HTTPException(status_code=404, detail=f"Knowledge path {path_id} or node {canvas_path} not found")

    return _knowledge_path_to_response(path)


@cross_canvas_router.delete(
    "/paths/{path_id}",
    summary="删除知识路径",
    description="删除知识学习路径",
    operation_id="delete_knowledge_path",
    status_code=204
)
async def delete_knowledge_path(
    cross_canvas_service: CrossCanvasServiceDep,
    path_id: str
) -> None:
    """Delete a knowledge path"""
    success = await cross_canvas_service.delete_knowledge_path(path_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Knowledge path {path_id} not found")

    logger.info(f"Deleted knowledge path: {path_id}")


# ═══════════════════════════════════════════════════════════════════════════════
# Search and Statistics Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@cross_canvas_router.get(
    "/search",
    response_model=List[ConceptSearchResult],
    summary="跨Canvas概念搜索",
    description="搜索概念在所有Canvas中的出现位置",
    operation_id="search_concept"
)
async def search_concept(
    query: str = Query(..., min_length=1, description="搜索关键词")
) -> List[ConceptSearchResult]:
    """Search for a concept across all canvases"""
    logger.info(f"Searching concept: {query}")

    # TODO: Implement actual canvas file search
    # For MVP, return empty results - actual implementation requires
    # file system access and canvas parsing
    return []


@cross_canvas_router.get(
    "/statistics",
    response_model=CrossCanvasStatistics,
    summary="获取跨Canvas统计",
    description="获取跨Canvas关联和路径的统计信息",
    operation_id="get_statistics"
)
async def get_statistics(
    cross_canvas_service: CrossCanvasServiceDep
) -> CrossCanvasStatistics:
    """Get cross-canvas statistics"""
    stats = await cross_canvas_service.get_statistics()

    return CrossCanvasStatistics(
        total_associations=stats["total_associations"],
        total_paths=stats["total_paths"],
        total_canvases_linked=stats["total_canvases_linked"],
        average_path_completion=stats["average_path_completion"]
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Suggestion Endpoints (Story 25.3 AC5)
# ═══════════════════════════════════════════════════════════════════════════════

@cross_canvas_router.get(
    "/suggestions",
    response_model=List[CanvasAssociationSuggestionResponse],
    summary="获取Canvas关联建议",
    description="根据概念相似度批量建议Canvas关联 [Story 25.3 AC5]",
    operation_id="get_association_suggestions"
)
async def get_association_suggestions(
    cross_canvas_service: CrossCanvasServiceDep,
    exercise_canvas_path: str = Query(..., description="练习Canvas路径"),
    concept: Optional[str] = Query(None, description="聚焦的概念(可选)")
) -> List[CanvasAssociationSuggestionResponse]:
    """Get association suggestions for an exercise canvas.

    [Source: Story 25.3 AC5 - Batch association suggestions based on concept similarity]

    This endpoint suggests lecture canvases that might be related to an exercise canvas,
    using intelligent matching based on:
    - Subject/topic extraction from canvas names
    - Historical association patterns
    - Concept similarity analysis
    """
    logger.info(f"Getting suggestions for: {exercise_canvas_path}, concept={concept}")

    suggestions = await cross_canvas_service.suggest_lecture_canvas(
        exercise_canvas_path=exercise_canvas_path,
        concept=concept
    )

    return [
        CanvasAssociationSuggestionResponse(
            target_canvas_path=s.target_canvas_path,
            target_canvas_title=s.target_canvas_title,
            relationship_type=s.relationship_type,
            confidence=s.confidence,
            reason=s.reason
        )
        for s in suggestions
    ]
