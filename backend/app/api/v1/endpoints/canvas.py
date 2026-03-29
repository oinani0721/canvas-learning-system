# Canvas Learning System - Canvas Router
# Story 15.2: Routing System and APIRouter Configuration
"""
Canvas operations router.

All 6 CRUD endpoints are connected to CanvasService which reads/writes
real .canvas JSON files and triggers memory events + Neo4j sync.

[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas]
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app.core.exceptions import CanvasNotFoundException, NodeNotFoundException
from app.dependencies import CanvasServiceDep
from app.models import (
    CanvasResponse,
    EdgeCreate,
    EdgeRead,
    ErrorResponse,
    NodeCreate,
    NodeRead,
    NodeUpdate,
)
from app.models.recommendation_models import (
    DismissedPairsRequest,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models (Story 36.4)
# =============================================================================


class SyncEdgesSummaryResponse(BaseModel):
    """
    Edge sync summary response.

    Story 36.4: Canvas打开时全量Edge同步
    [Source: docs/stories/36.4.story.md#Task-2]
    """

    canvas_path: str
    total_edges: int
    synced_count: int
    failed_count: int
    skipped_count: int
    sync_time_ms: float


# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# APIRouter(prefix, tags, responses) for modular routing
canvas_router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        400: {"model": ErrorResponse, "description": "Validation error"},
    }
)


# =============================================================================
# Helper: dict -> Pydantic model conversion
# =============================================================================


def _parse_nodes(raw_nodes: List[dict]) -> List[NodeRead]:
    """Convert raw node dicts from .canvas JSON to NodeRead models."""
    result: List[NodeRead] = []
    for n in raw_nodes:
        try:
            result.append(
                NodeRead(
                    id=n["id"],
                    type=n.get("type", "text"),
                    text=n.get("text"),
                    file=n.get("file"),
                    url=n.get("url"),
                    x=n.get("x", 0),
                    y=n.get("y", 0),
                    width=n.get("width"),
                    height=n.get("height"),
                    color=n.get("color"),
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Skipping malformed node %s: %s", n.get("id"), exc)
    return result


def _parse_edges(raw_edges: List[dict]) -> List[EdgeRead]:
    """Convert raw edge dicts from .canvas JSON to EdgeRead models."""
    result: List[EdgeRead] = []
    for e in raw_edges:
        try:
            result.append(
                EdgeRead(
                    id=e["id"],
                    fromNode=e["fromNode"],
                    toNode=e["toNode"],
                    fromSide=e.get("fromSide"),
                    toSide=e.get("toSide"),
                    label=e.get("label"),
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Skipping malformed edge %s: %s", e.get("id"), exc)
    return result


def _node_dict_to_read(d: dict) -> NodeRead:
    """Convert a single node dict returned by CanvasService to NodeRead."""
    return NodeRead(
        id=d["id"],
        type=d.get("type", "text"),
        text=d.get("text"),
        file=d.get("file"),
        url=d.get("url"),
        x=d.get("x", 0),
        y=d.get("y", 0),
        width=d.get("width"),
        height=d.get("height"),
        color=d.get("color"),
    )


def _edge_dict_to_read(d: dict) -> EdgeRead:
    """Convert a single edge dict returned by CanvasService to EdgeRead."""
    return EdgeRead(
        id=d["id"],
        fromNode=d["fromNode"],
        toNode=d["toNode"],
        fromSide=d.get("fromSide"),
        toSide=d.get("toSide"),
        label=d.get("label"),
    )


def _serialize_enum_values(data: dict) -> dict:
    """Ensure any enum values in the dict are serialized to their string values."""
    out = {}
    for k, v in data.items():
        if hasattr(v, "value"):
            out[k] = v.value
        else:
            out[k] = v
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Endpoints (6) — connected to CanvasService
# [Source: specs/api/fastapi-backend-api.openapi.yml#Canvas Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════


@canvas_router.get(
    "/{canvas_name}",
    response_model=CanvasResponse,
    summary="Read Canvas file",
    operation_id="read_canvas",
)
async def read_canvas(
    canvas_name: str,
    canvas_service: CanvasServiceDep,
) -> CanvasResponse:
    """
    Read a Canvas file and return its contents (nodes + edges).

    - **canvas_name**: Canvas file name (without .canvas suffix)

    Reads the real .canvas JSON file from disk via CanvasService.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}]
    """
    try:
        canvas_data = await canvas_service.read_canvas(canvas_name)
    except CanvasNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found",
        ) from exc

    nodes = _parse_nodes(canvas_data.get("nodes", []))
    edges = _parse_edges(canvas_data.get("edges", []))

    return CanvasResponse(
        name=canvas_data.get("name", canvas_name),
        nodes=nodes,
        edges=edges,
    )


@canvas_router.post(
    "/{canvas_name}/nodes",
    response_model=NodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create node",
    operation_id="create_node",
)
async def create_node(
    canvas_name: str,
    node: NodeCreate,
    canvas_service: CanvasServiceDep,
) -> NodeRead:
    """
    Create a new node in a Canvas.

    - **canvas_name**: Canvas file name
    - **node**: Node creation data

    Writes the node to the real .canvas file and triggers memory events.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes]
    """
    try:
        node_data = _serialize_enum_values(node.model_dump(exclude_none=True))
        created = await canvas_service.add_node(canvas_name, node_data)
    except CanvasNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found",
        ) from exc

    return _node_dict_to_read(created)


@canvas_router.put(
    "/{canvas_name}/nodes/{node_id}",
    response_model=NodeRead,
    summary="Update node",
    operation_id="update_node",
)
async def update_node(
    canvas_name: str,
    node_id: str,
    node: NodeUpdate,
    canvas_service: CanvasServiceDep,
) -> NodeRead:
    """
    Update an existing node in a Canvas.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID to update
    - **node**: Node update data (partial update - only provided fields are changed)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes~1{node_id}]
    """
    try:
        update_data = _serialize_enum_values(node.model_dump(exclude_none=True))
        updated = await canvas_service.update_node(canvas_name, node_id, update_data)
    except CanvasNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found",
        ) from exc
    except NodeNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found in canvas '{canvas_name}'",
        ) from exc

    return _node_dict_to_read(updated)


@canvas_router.delete(
    "/{canvas_name}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete node",
    operation_id="delete_node",
)
async def delete_node(
    canvas_name: str,
    node_id: str,
    canvas_service: CanvasServiceDep,
) -> Response:
    """
    Delete a node from a Canvas. Also removes all edges connected to this node.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID to delete

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes~1{node_id}]
    """
    try:
        deleted = await canvas_service.delete_node(canvas_name, node_id)
    except CanvasNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found in canvas '{canvas_name}'",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@canvas_router.post(
    "/{canvas_name}/edges",
    response_model=EdgeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create edge",
    operation_id="create_edge",
)
async def create_edge(
    canvas_name: str,
    edge: EdgeCreate,
    canvas_service: CanvasServiceDep,
) -> EdgeRead:
    """
    Create a new edge in a Canvas. Also triggers Neo4j sync (fire-and-forget).

    - **canvas_name**: Canvas file name
    - **edge**: Edge creation data

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1edges]
    """
    try:
        edge_data = _serialize_enum_values(edge.model_dump(exclude_none=True))
        created = await canvas_service.add_edge(canvas_name, edge_data)
    except CanvasNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found",
        ) from exc

    return _edge_dict_to_read(created)


@canvas_router.delete(
    "/{canvas_name}/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete edge",
    operation_id="delete_edge",
)
async def delete_edge(
    canvas_name: str,
    edge_id: str,
    canvas_service: CanvasServiceDep,
) -> Response:
    """
    Delete an edge from a Canvas. Also triggers Neo4j deletion sync (fire-and-forget).

    - **canvas_name**: Canvas file name
    - **edge_id**: Edge ID to delete

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1edges~1{edge_id}]
    """
    try:
        deleted = await canvas_service.delete_edge(canvas_name, edge_id)
    except CanvasNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found",
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge '{edge_id}' not found in canvas '{canvas_name}'",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════════════════
# Layer4-Knowledge Endpoints (Story 36.4)
# [Source: docs/stories/36.4.story.md]
# ═══════════════════════════════════════════════════════════════════════════════


@canvas_router.post(
    "/{canvas_name}/sync-edges",
    response_model=SyncEdgesSummaryResponse,
    summary="Sync all Canvas edges to Neo4j",
    operation_id="sync_canvas_edges",
    tags=["Layer4-Knowledge"],
)
async def sync_edges(
    canvas_name: str,
    canvas_service: CanvasServiceDep,
) -> SyncEdgesSummaryResponse:
    """
    Sync all Canvas edges to Neo4j knowledge graph.

    - **canvas_name**: Canvas file name (without .canvas extension)
    - Idempotent: repeated calls do not create duplicate relationships (MERGE semantics)
    - Concurrent: up to 12 edges synced in parallel
    - Partial failure handling: single edge failure does not block batch

    Story 36.4: Canvas打开时全量Edge同步
    [Source: docs/stories/36.4.story.md#AC-1]
    """
    summary = await canvas_service.sync_all_edges_to_neo4j(canvas_name)
    return SyncEdgesSummaryResponse(
        canvas_path=summary["canvas_path"],
        total_edges=summary["total_edges"],
        synced_count=summary["synced_count"],
        failed_count=summary["failed_count"],
        skipped_count=summary["skipped_count"],
        sync_time_ms=summary["sync_time_ms"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 1.7: Concept-Relation Recommendations
# [Source: _bmad-output/implementation-artifacts/1-7-concept-relation-recommendation.md]
# ═══════════════════════════════════════════════════════════════════════════════


@canvas_router.post(
    "/{canvas_id}/recommendations",
    response_model=RecommendationResponse,
    summary="Get concept-relation recommendations for a canvas",
    operation_id="get_canvas_recommendations",
)
async def get_recommendations(
    canvas_id: str,
    request: DismissedPairsRequest,
) -> RecommendationResponse:
    """
    Analyze a canvas and return concept-relation recommendations.

    Uses two-layer analysis:
    - L1: bge-m3 text similarity between unconnected nodes
    - L2: Neo4j 2-hop neighbor co-occurrence patterns

    Returns up to 5 recommendations, filtered by dismissed pairs.
    Timeout: 5s -- returns empty list on timeout (non-blocking).

    Story 1.7 AC-1, AC-2, AC-6
    """
    try:
        from app.clients.neo4j_client import get_neo4j_client
        from app.services.recommendation_service import RecommendationService

        neo4j_client = get_neo4j_client()
        service = RecommendationService(neo4j_client)
        return await service.generate_recommendations(
            canvas_id=canvas_id,
            dismissed_pairs=request.dismissed_pairs,
        )
    except Exception as e:
        logger.warning(f"Recommendation endpoint error: {e}")
        return RecommendationResponse(
            recommendations=[],
            canvas_id=canvas_id,
        )
