# Canvas Learning System - Pydantic Schemas
# Story 15.2: Routing System and APIRouter Configuration
# Source: specs/api/fastapi-backend-api.openapi.yml
"""
Pydantic Models for Canvas Learning System API.

All models are derived from the OpenAPI specification:
[Source: specs/api/fastapi-backend-api.openapi.yml]
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Common Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatus(str, Enum):
    """Health status enum."""
    healthy = "healthy"
    unhealthy = "unhealthy"


class HealthCheckResponse(BaseModel):
    """
    Health check response model.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/HealthCheckResponse]
    """
    status: HealthStatus = Field(..., description="Application health status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Check timestamp")


class ErrorResponse(BaseModel):
    """
    Standard error response model.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ErrorResponse]
    """
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# ═══════════════════════════════════════════════════════════════════════════════
# Canvas Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class NodeType(str, Enum):
    """Node type enum."""
    text = "text"
    file = "file"
    group = "group"
    link = "link"


class NodeColor(str, Enum):
    """
    Node color codes.
    1=red, 2=orange, 3=yellow, 4=green, 5=cyan, 6=purple
    """
    red = "1"
    orange = "2"
    yellow = "3"
    green = "4"
    cyan = "5"
    purple = "6"


class EdgeSide(str, Enum):
    """Edge connection side."""
    top = "top"
    bottom = "bottom"
    left = "left"
    right = "right"


class NodeCreate(BaseModel):
    """
    Request model for creating a new node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeCreate]
    """
    type: NodeType = Field(..., description="Node type")
    text: Optional[str] = Field(None, description="Text content (required for type=text)")
    file: Optional[str] = Field(None, description="File path (required for type=file)")
    url: Optional[str] = Field(None, description="Link URL (required for type=link)")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    width: int = Field(default=250, description="Node width")
    height: int = Field(default=60, description="Node height")
    color: Optional[NodeColor] = Field(None, description="Node color code")


class NodeUpdate(BaseModel):
    """
    Request model for updating a node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeUpdate]
    """
    text: Optional[str] = Field(None, description="Text content")
    x: Optional[int] = Field(None, description="X position")
    y: Optional[int] = Field(None, description="Y position")
    width: Optional[int] = Field(None, description="Node width")
    height: Optional[int] = Field(None, description="Node height")
    color: Optional[NodeColor] = Field(None, description="Node color code")


class NodeRead(BaseModel):
    """
    Response model for a node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeRead]
    """
    id: str = Field(..., description="Node ID", pattern=r"^[a-f0-9]+$")
    type: NodeType = Field(..., description="Node type")
    text: Optional[str] = Field(None, description="Text content")
    file: Optional[str] = Field(None, description="File path")
    url: Optional[str] = Field(None, description="Link URL")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    width: Optional[int] = Field(None, description="Node width")
    height: Optional[int] = Field(None, description="Node height")
    color: Optional[NodeColor] = Field(None, description="Node color code")


class EdgeCreate(BaseModel):
    """
    Request model for creating an edge.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/EdgeCreate]
    """
    fromNode: str = Field(..., description="Source node ID")
    toNode: str = Field(..., description="Target node ID")
    fromSide: Optional[EdgeSide] = Field(None, description="Source side")
    toSide: Optional[EdgeSide] = Field(None, description="Target side")
    label: Optional[str] = Field(None, description="Edge label")


class EdgeRead(BaseModel):
    """
    Response model for an edge.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/EdgeRead]
    """
    id: str = Field(..., description="Edge ID")
    fromNode: str = Field(..., description="Source node ID")
    toNode: str = Field(..., description="Target node ID")
    fromSide: Optional[str] = Field(None, description="Source side")
    toSide: Optional[str] = Field(None, description="Target side")
    label: Optional[str] = Field(None, description="Edge label")


class CanvasResponse(BaseModel):
    """
    Response model for a Canvas.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/CanvasResponse]
    """
    name: str = Field(..., description="Canvas file name")
    nodes: List[NodeRead] = Field(..., description="List of nodes")
    edges: List[EdgeRead] = Field(..., description="List of edges")


# ═══════════════════════════════════════════════════════════════════════════════
# Agent Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class DecomposeRequest(BaseModel):
    """
    Request model for concept decomposition.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/DecomposeRequest]
    [Source: specs/data/decompose-request.schema.json]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Target node ID")


class DecomposeResponse(BaseModel):
    """
    Response model for concept decomposition.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/DecomposeResponse]
    [Source: specs/data/decompose-response.schema.json]
    """
    questions: List[str] = Field(..., description="Generated guiding questions")
    created_nodes: List[NodeRead] = Field(..., description="Created nodes")


class ScoreRequest(BaseModel):
    """
    Request model for scoring understanding.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ScoreRequest]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_ids: List[str] = Field(..., description="Node IDs to score")


class NodeScore(BaseModel):
    """
    Score result for a single node.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeScore]
    [Source: specs/data/node-score.schema.json]
    """
    node_id: str = Field(..., description="Node ID")
    accuracy: float = Field(..., ge=0, le=10, description="Accuracy score")
    imagery: float = Field(..., ge=0, le=10, description="Imagery score")
    completeness: float = Field(..., ge=0, le=10, description="Completeness score")
    originality: float = Field(..., ge=0, le=10, description="Originality score")
    total: float = Field(..., ge=0, le=40, description="Total score")
    new_color: str = Field(..., description="New node color: 2=green(>=32), 3=yellow(24-31), 4=red(<24)")


class ScoreResponse(BaseModel):
    """
    Response model for scoring.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ScoreResponse]
    """
    scores: List[NodeScore] = Field(..., description="Score results")


class ExplainRequest(BaseModel):
    """
    Request model for explanation generation.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ExplainRequest]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Target node ID")


class ExplainResponse(BaseModel):
    """
    Response model for explanation generation.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ExplainResponse]
    """
    explanation: str = Field(..., description="Generated explanation")
    created_node_id: str = Field(..., description="Created explanation node ID")


# ═══════════════════════════════════════════════════════════════════════════════
# Review Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewItem(BaseModel):
    """
    Single review item in schedule.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ReviewItem]
    [Source: specs/data/review-item.schema.json]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID")
    concept: str = Field(..., description="Concept name")
    due_date: date = Field(..., description="Due date for review")
    interval_days: int = Field(..., description="Current review interval (1/7/30 days)")


class ReviewScheduleResponse(BaseModel):
    """
    Response model for review schedule.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ReviewScheduleResponse]
    """
    items: List[ReviewItem] = Field(..., description="Review items")
    total_count: int = Field(..., description="Total item count")


class GenerateReviewRequest(BaseModel):
    """
    Request model for generating verification canvas.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewRequest]
    """
    source_canvas: str = Field(..., description="Source Canvas file name")
    node_ids: Optional[List[str]] = Field(
        None,
        description="Specific node IDs (optional, defaults to all green nodes)"
    )


class GenerateReviewResponse(BaseModel):
    """
    Response model for generated verification canvas.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewResponse]
    """
    verification_canvas_name: str = Field(..., description="Generated verification canvas name")
    node_count: int = Field(..., description="Number of verification nodes")


class RecordReviewRequest(BaseModel):
    """
    Request model for recording review result.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewRequest]
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID")
    score: float = Field(..., ge=0, le=40, description="Review score (0-40)")


class RecordReviewResponse(BaseModel):
    """
    Response model for recorded review result.

    [Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewResponse]
    """
    next_review_date: date = Field(..., description="Next review date")
    new_interval: int = Field(..., description="New review interval in days")
