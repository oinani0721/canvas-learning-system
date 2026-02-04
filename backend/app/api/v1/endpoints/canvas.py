# Canvas Learning System - Canvas Router
# Story 15.2: Routing System and APIRouter Configuration
"""
Canvas operations router.

Provides 6 endpoints for Canvas file and node/edge operations.
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas]
"""


from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

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


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Endpoints (6)
# [Source: specs/api/fastapi-backend-api.openapi.yml#Canvas Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════

@canvas_router.get(
    "/{canvas_name}",
    response_model=CanvasResponse,
    summary="Read Canvas file",
    operation_id="read_canvas",
)
async def read_canvas(canvas_name: str) -> CanvasResponse:
    """
    Read a Canvas file and return its contents.

    - **canvas_name**: Canvas file name (without .canvas suffix)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}]
    """
    # Placeholder implementation - will be connected to service layer in future stories
    # Return mock data for now to enable testing of router structure
    return CanvasResponse(
        name=canvas_name,
        nodes=[],
        edges=[],
    )


@canvas_router.post(
    "/{canvas_name}/nodes",
    response_model=NodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create node",
    operation_id="create_node",
)
async def create_node(canvas_name: str, node: NodeCreate) -> NodeRead:
    """
    Create a new node in a Canvas.

    - **canvas_name**: Canvas file name
    - **node**: Node creation data

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes]
    """
    # Placeholder implementation
    import uuid
    return NodeRead(
        id=uuid.uuid4().hex[:16],
        type=node.type,
        text=node.text,
        file=node.file,
        url=node.url,
        x=node.x,
        y=node.y,
        width=node.width,
        height=node.height,
        color=node.color,
    )


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
) -> NodeRead:
    """
    Update an existing node in a Canvas.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID to update
    - **node**: Node update data

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes~1{node_id}]
    """
    # Placeholder implementation
    return NodeRead(
        id=node_id,
        type="text",  # Would be fetched from actual node
        text=node.text,
        x=node.x or 0,
        y=node.y or 0,
        width=node.width,
        height=node.height,
        color=node.color,
    )


@canvas_router.delete(
    "/{canvas_name}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete node",
    operation_id="delete_node",
)
async def delete_node(canvas_name: str, node_id: str) -> Response:
    """
    Delete a node from a Canvas.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID to delete

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes~1{node_id}]
    """
    # Placeholder implementation
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@canvas_router.post(
    "/{canvas_name}/edges",
    response_model=EdgeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create edge",
    operation_id="create_edge",
)
async def create_edge(canvas_name: str, edge: EdgeCreate) -> EdgeRead:
    """
    Create a new edge in a Canvas.

    - **canvas_name**: Canvas file name
    - **edge**: Edge creation data

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1edges]
    """
    # Placeholder implementation
    import uuid
    return EdgeRead(
        id=uuid.uuid4().hex[:16],
        fromNode=edge.fromNode,
        toNode=edge.toNode,
        fromSide=edge.fromSide.value if edge.fromSide else None,
        toSide=edge.toSide.value if edge.toSide else None,
        label=edge.label,
    )


@canvas_router.delete(
    "/{canvas_name}/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete edge",
    operation_id="delete_edge",
)
async def delete_edge(canvas_name: str, edge_id: str) -> Response:
    """
    Delete an edge from a Canvas.

    - **canvas_name**: Canvas file name
    - **edge_id**: Edge ID to delete

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1edges~1{edge_id}]
    """
    # Placeholder implementation
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
        sync_time_ms=summary["sync_time_ms"]
    )
