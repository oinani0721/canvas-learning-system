"""
Canvas Router for Canvas Learning System API

Provides endpoints for Canvas file and node operations.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter, path parameters)
"""

import uuid
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from ..models import (
    CanvasResponse,
    EdgeCreate,
    EdgeRead,
    ErrorResponse,
    NodeCreate,
    NodeRead,
    NodeUpdate,
)

router = APIRouter(prefix="/canvas", tags=["Canvas"])

# Mock data for testing (to be replaced with actual canvas_utils.py integration)
MOCK_CANVAS: Dict[str, Dict[str, Any]] = {
    "test-canvas": {
        "nodes": [
            {
                "id": "a1b2c3d4",
                "type": "text",
                "text": "What is contrapositive?",
                "x": 100,
                "y": 200,
                "width": 300,
                "height": 100,
                "color": "1"
            },
            {
                "id": "e5f6a7b8",
                "type": "text",
                "text": "A contrapositive swaps and negates both condition and conclusion",
                "x": 150,
                "y": 360,
                "width": 300,
                "height": 100,
                "color": "6"
            }
        ],
        "edges": [
            {
                "id": "edce0001",
                "fromNode": "a1b2c3d4",
                "toNode": "e5f6a7b8",
                "fromSide": "bottom",
                "toSide": "top"
            }
        ]
    }
}


@router.get(
    "/{canvas_name}",
    response_model=CanvasResponse,
    summary="读取Canvas文件",
    operation_id="read_canvas",
    responses={
        404: {"model": ErrorResponse, "description": "Canvas文件不存在"}
    }
)
async def read_canvas(canvas_name: str) -> CanvasResponse:
    """
    Read Canvas file by name.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}
    """
    if canvas_name not in MOCK_CANVAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )

    canvas_data = MOCK_CANVAS[canvas_name]
    return CanvasResponse(
        name=canvas_name,
        nodes=[NodeRead(**n) for n in canvas_data["nodes"]],
        edges=[EdgeRead(**e) for e in canvas_data["edges"]]
    )


@router.post(
    "/{canvas_name}/nodes",
    response_model=NodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建节点",
    operation_id="create_node",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"},
        404: {"model": ErrorResponse, "description": "Canvas不存在"}
    }
)
async def create_node(canvas_name: str, node: NodeCreate) -> NodeRead:
    """
    Create a new node in Canvas.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes
    """
    if canvas_name not in MOCK_CANVAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )

    # Generate node ID
    node_id = uuid.uuid4().hex[:8]

    # Create node read response
    node_data = node.model_dump()
    node_data["id"] = node_id

    # Add to mock storage
    MOCK_CANVAS[canvas_name]["nodes"].append(node_data)

    return NodeRead(**node_data)


@router.put(
    "/{canvas_name}/nodes/{node_id}",
    response_model=NodeRead,
    summary="更新节点",
    operation_id="update_node",
    responses={
        404: {"model": ErrorResponse, "description": "Canvas或节点不存在"}
    }
)
async def update_node(
    canvas_name: str,
    node_id: str,
    node_update: NodeUpdate
) -> NodeRead:
    """
    Update an existing node.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes~1{node_id}
    """
    if canvas_name not in MOCK_CANVAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )

    # Find node
    canvas_data = MOCK_CANVAS[canvas_name]
    node = next(
        (n for n in canvas_data["nodes"] if n["id"] == node_id),
        None
    )

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found"
        )

    # Apply updates
    update_data = node_update.model_dump(exclude_unset=True)
    node.update(update_data)

    return NodeRead(**node)


@router.delete(
    "/{canvas_name}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除节点",
    operation_id="delete_node",
    responses={
        404: {"model": ErrorResponse, "description": "Canvas或节点不存在"}
    }
)
async def delete_node(canvas_name: str, node_id: str) -> None:
    """
    Delete a node from Canvas.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1nodes~1{node_id}
    """
    if canvas_name not in MOCK_CANVAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )

    canvas_data = MOCK_CANVAS[canvas_name]
    node = next(
        (n for n in canvas_data["nodes"] if n["id"] == node_id),
        None
    )

    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found"
        )

    canvas_data["nodes"].remove(node)


@router.post(
    "/{canvas_name}/edges",
    response_model=EdgeRead,
    status_code=status.HTTP_201_CREATED,
    summary="创建边",
    operation_id="create_edge",
    responses={
        400: {"model": ErrorResponse, "description": "验证错误"}
    }
)
async def create_edge(canvas_name: str, edge: EdgeCreate) -> EdgeRead:
    """
    Create a new edge between nodes.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1edges
    """
    if canvas_name not in MOCK_CANVAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )

    # Generate edge ID
    edge_id = uuid.uuid4().hex[:8]

    edge_data = edge.model_dump()
    edge_data["id"] = edge_id

    MOCK_CANVAS[canvas_name]["edges"].append(edge_data)

    return EdgeRead(**edge_data)


@router.delete(
    "/{canvas_name}/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除边",
    operation_id="delete_edge",
    responses={
        404: {"model": ErrorResponse, "description": "Canvas或边不存在"}
    }
)
async def delete_edge(canvas_name: str, edge_id: str) -> None:
    """
    Delete an edge from Canvas.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1canvas~1{canvas_name}~1edges~1{edge_id}
    """
    if canvas_name not in MOCK_CANVAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas '{canvas_name}' not found"
        )

    canvas_data = MOCK_CANVAS[canvas_name]
    edge = next(
        (e for e in canvas_data["edges"] if e["id"] == edge_id),
        None
    )

    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge '{edge_id}' not found"
        )

    canvas_data["edges"].remove(edge)
