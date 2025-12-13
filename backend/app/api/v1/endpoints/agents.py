# Canvas Learning System - Agents Router
# Story 15.2: Routing System and APIRouter Configuration
# Story 21.1: 统一位置信息提取 - 连接真实AgentService
"""
Agent invocation router.

Provides 9 endpoints for AI agent operations (decomposition, scoring, explanation).
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents]
[Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md - Story 21.1]
"""

import logging
from typing import Any, Dict, Tuple

from fastapi import APIRouter, HTTPException

from app.dependencies import AgentServiceDep, CanvasServiceDep, ContextEnrichmentServiceDep
from app.models import (
    DecomposeRequest,
    DecomposeResponse,
    ErrorResponse,
    ExplainRequest,
    ExplainResponse,
    NodeRead,
    NodeScore,
    ScoreRequest,
    ScoreResponse,
)

logger = logging.getLogger(__name__)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# APIRouter(prefix, tags, responses) for modular routing
agents_router = APIRouter(
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        404: {"model": ErrorResponse, "description": "Canvas or node not found"},
        500: {"model": ErrorResponse, "description": "Agent service error"},
    }
)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 21.1: 统一位置信息提取函数
# [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-1]
# ═══════════════════════════════════════════════════════════════════════════════

def extract_node_position(node: Dict[str, Any]) -> Tuple[int, int, int, int]:
    """
    统一提取节点位置信息。

    所有Agent端点使用此函数确保位置提取逻辑一致。

    Args:
        node: Canvas节点数据字典

    Returns:
        Tuple[x, y, width, height] - 位置和尺寸信息

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-1]
    """
    x = int(node.get("x", 0))
    y = int(node.get("y", 0))
    width = int(node.get("width", 400))
    height = int(node.get("height", 200))
    return x, y, width, height


async def get_node_from_canvas(
    canvas_service: CanvasServiceDep,
    canvas_name: str,
    node_id: str
) -> Dict[str, Any]:
    """
    从Canvas中获取指定节点。

    Args:
        canvas_service: Canvas服务实例
        canvas_name: Canvas文件名
        node_id: 目标节点ID

    Returns:
        节点数据字典

    Raises:
        HTTPException: Canvas或节点不存在时抛出404

    [Source: docs/prd/EPIC-21-AGENT-E2E-FLOW-FIX.md#story-21-1]
    """
    try:
        canvas_data = await canvas_service.read_canvas(canvas_name)
    except FileNotFoundError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Canvas not found: {canvas_name}"
        ) from err

    nodes = canvas_data.get("nodes", [])
    for node in nodes:
        if node.get("id") == node_id:
            return node

    raise HTTPException(
        status_code=404,
        detail=f"Node not found: {node_id} in canvas {canvas_name}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Decomposition Endpoints (2)
# [Source: specs/api/fastapi-backend-api.openapi.yml#Agent Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════

@agents_router.post(
    "/decompose/basic",
    response_model=DecomposeResponse,
    summary="Basic concept decomposition",
    operation_id="decompose_basic",
)
async def decompose_basic(
    request: DecomposeRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> DecomposeResponse:
    """
    Perform basic concept decomposition on a node.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID to decompose

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1decompose~1basic]
    [Source: specs/data/decompose-request.schema.json]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    try:
        # Story 25.2: Get enriched context (includes textbook references)
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: {request.node_id} in canvas {request.canvas_name}"
        ) from err

    # Story 25.2 AC5: Log textbook context usage
    logger.info(
        f"decompose_basic: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y}), has_textbook_refs={enriched.has_textbook_refs}"
    )

    try:
        # Story 25.2: Pass enriched content with textbook context embedded
        # TODO(Story 25.3): Add context parameter to decompose_basic for full AC3 compliance
        result = await agent_service.decompose_basic(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=f"{enriched.target_content}\n\n{enriched.enriched_context}" if enriched.enriched_context else enriched.target_content,
            source_x=enriched.x,
            source_y=enriched.y,
        )

        # 转换为响应模型
        return DecomposeResponse(
            questions=result.get("questions", []),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except Exception as e:
        logger.error(f"decompose_basic failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


@agents_router.post(
    "/decompose/deep",
    response_model=DecomposeResponse,
    summary="Deep concept decomposition",
    operation_id="decompose_deep",
)
async def decompose_deep(
    request: DecomposeRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> DecomposeResponse:
    """
    Perform deep concept decomposition on a node.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID for deep decomposition

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1decompose~1deep]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    try:
        # Story 25.2: Get enriched context (includes textbook references)
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: {request.node_id} in canvas {request.canvas_name}"
        ) from err

    # Story 25.2 AC5: Log textbook context usage
    logger.info(
        f"decompose_deep: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y}), has_textbook_refs={enriched.has_textbook_refs}"
    )

    try:
        # Story 25.2: Pass enriched content with textbook context embedded
        # TODO(Story 25.3): Add context parameter to decompose_deep for full AC3 compliance
        result = await agent_service.decompose_deep(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=f"{enriched.target_content}\n\n{enriched.enriched_context}" if enriched.enriched_context else enriched.target_content,
            source_x=enriched.x,
            source_y=enriched.y,
        )

        return DecomposeResponse(
            questions=result.get("questions", []),
            created_nodes=[NodeRead(**n) for n in result.get("created_nodes", [])],
        )
    except Exception as e:
        logger.error(f"decompose_deep failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring Endpoint (1)
# [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1score]
# ═══════════════════════════════════════════════════════════════════════════════

@agents_router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score user understanding",
    operation_id="score_understanding",
)
async def score_understanding(
    request: ScoreRequest,
    agent_service: AgentServiceDep,
    canvas_service: CanvasServiceDep,
) -> ScoreResponse:
    """
    Score user's understanding based on their explanations.

    - **canvas_name**: Canvas file name
    - **node_ids**: List of node IDs to score

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1score]
    [Source: specs/data/node-score.schema.json]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    """
    logger.info(f"score_understanding: canvas={request.canvas_name}, nodes={request.node_ids}")

    try:
        result = await agent_service.score_node(
            canvas_name=request.canvas_name,
            node_ids=request.node_ids,
        )

        # 转换为响应模型
        scores = []
        for score_data in result.get("scores", []):
            scores.append(NodeScore(
                node_id=score_data.get("node_id", ""),
                accuracy=score_data.get("accuracy", 0.0),
                imagery=score_data.get("imagery", 0.0),
                completeness=score_data.get("completeness", 0.0),
                originality=score_data.get("originality", 0.0),
                total=score_data.get("total", 0.0),
                new_color=score_data.get("new_color", "3"),
            ))
        return ScoreResponse(scores=scores)
    except Exception as e:
        logger.error(f"score_understanding failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


# ═══════════════════════════════════════════════════════════════════════════════
# Explanation Endpoints (6)
# [Source: specs/api/fastapi-backend-api.openapi.yml#Agent Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════

async def _call_explanation(
    request: ExplainRequest,
    explanation_type: str,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    统一解释调用辅助函数。

    [Story 21.1: 统一位置信息提取]
    [Story 21.2: 使用ContextEnrichmentService获取邻居上下文]
    [Story 25.2: TextbookContextService Integration]
    """
    # Story 25.2: Get enriched context (includes textbook references)
    try:
        enriched = await context_service.enrich_with_adjacent_nodes(
            canvas_name=request.canvas_name,
            node_id=request.node_id
        )
    except ValueError as err:
        raise HTTPException(
            status_code=404,
            detail=f"Node not found: canvas={request.canvas_name}, node_id={request.node_id}"
        ) from err

    # Story 25.2 AC5: Log textbook context usage
    logger.info(
        f"explain_{explanation_type}: canvas={request.canvas_name}, node={request.node_id}, "
        f"pos=({enriched.x},{enriched.y},{enriched.width},{enriched.height}), "
        f"has_textbook_refs={enriched.has_textbook_refs}"
    )

    try:
        # Story 25.2: Pass enriched context to agent (includes textbook refs per AC3)
        result = await agent_service.generate_explanation(
            canvas_name=request.canvas_name,
            node_id=request.node_id,
            content=enriched.target_content,
            adjacent_context=enriched.enriched_context,  # Includes textbook refs per AC3
            explanation_type=explanation_type,
            source_x=enriched.x,
            source_y=enriched.y,
            source_width=enriched.width,
            source_height=enriched.height,
        )

        return ExplainResponse(
            explanation=result.get("explanation", ""),
            created_node_id=result.get("created_node_id", ""),
        )
    except Exception as e:
        logger.error(f"explain_{explanation_type} failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}") from e


@agents_router.post(
    "/explain/oral",
    response_model=ExplainResponse,
    summary="Oral-style explanation",
    operation_id="explain_oral",
)
async def explain_oral(
    request: ExplainRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    Generate oral-style explanation for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1oral]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    return await _call_explanation(request, "oral", agent_service, context_service)


@agents_router.post(
    "/explain/clarification",
    response_model=ExplainResponse,
    summary="Clarification path generation",
    operation_id="explain_clarification",
)
async def explain_clarification(
    request: ExplainRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    Generate clarification path for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1clarification]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    return await _call_explanation(request, "clarification", agent_service, context_service)


@agents_router.post(
    "/explain/comparison",
    response_model=ExplainResponse,
    summary="Comparison table generation",
    operation_id="explain_comparison",
)
async def explain_comparison(
    request: ExplainRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    Generate comparison table for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1comparison]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    return await _call_explanation(request, "comparison", agent_service, context_service)


@agents_router.post(
    "/explain/memory",
    response_model=ExplainResponse,
    summary="Memory anchor generation",
    operation_id="explain_memory",
)
async def explain_memory(
    request: ExplainRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    Generate memory anchor for a concept.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1memory]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    return await _call_explanation(request, "memory", agent_service, context_service)


@agents_router.post(
    "/explain/four-level",
    response_model=ExplainResponse,
    summary="Four-level explanation",
    operation_id="explain_four_level",
)
async def explain_four_level(
    request: ExplainRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    Generate four-level progressive explanation.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1four-level]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    return await _call_explanation(request, "four-level", agent_service, context_service)


@agents_router.post(
    "/explain/example",
    response_model=ExplainResponse,
    summary="Example-based teaching",
    operation_id="explain_example",
)
async def explain_example(
    request: ExplainRequest,
    agent_service: AgentServiceDep,
    context_service: ContextEnrichmentServiceDep,
) -> ExplainResponse:
    """
    Generate example-based teaching content.

    - **canvas_name**: Canvas file name
    - **node_id**: Target node ID

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1agents~1explain~1example]
    [Story 21.1: 统一位置信息提取 - 连接真实AgentService]
    [Story 25.2: TextbookContextService Integration]
    """
    return await _call_explanation(request, "example", agent_service, context_service)
