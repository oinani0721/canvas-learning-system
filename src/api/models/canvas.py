"""
Canvas Pydantic Models for Canvas Learning System API

Provides models for Canvas operations including nodes and edges.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Pydantic models)
Models match specs/api/fastapi-backend-api.openapi.yml
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# Valid color codes
ColorCode = Literal["1", "2", "3", "4", "5", "6"]
NodeType = Literal["text", "file", "group", "link"]
Side = Literal["top", "bottom", "left", "right"]


class NodeCreate(BaseModel):
    """
    Node creation request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeCreate
    """
    type: NodeType = Field(
        ...,
        description="Node type"
    )
    text: Optional[str] = Field(
        default=None,
        description="Text content (required for type=text)"
    )
    file: Optional[str] = Field(
        default=None,
        description="File path (required for type=file)"
    )
    url: Optional[str] = Field(
        default=None,
        description="URL (required for type=link)"
    )
    x: int = Field(
        ...,
        description="X coordinate"
    )
    y: int = Field(
        ...,
        description="Y coordinate"
    )
    width: int = Field(
        default=250,
        description="Node width"
    )
    height: int = Field(
        default=60,
        description="Node height"
    )
    color: Optional[ColorCode] = Field(
        default=None,
        description="Color code: 1=红, 2=橙, 3=黄, 4=绿, 5=青, 6=紫"
    )


class NodeUpdate(BaseModel):
    """
    Node update request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeUpdate
    """
    text: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    color: Optional[ColorCode] = None


class NodeRead(BaseModel):
    """
    Node response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeRead
    """
    id: str = Field(
        ...,
        description="Node ID",
        pattern="^[a-f0-9]+$"
    )
    type: NodeType = Field(
        ...,
        description="Node type"
    )
    text: Optional[str] = None
    file: Optional[str] = None
    url: Optional[str] = None
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    width: Optional[int] = None
    height: Optional[int] = None
    color: Optional[ColorCode] = None

    model_config = {
        "from_attributes": True
    }


class EdgeCreate(BaseModel):
    """
    Edge creation request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/EdgeCreate
    """
    fromNode: str = Field(
        ...,
        description="Source node ID"
    )
    toNode: str = Field(
        ...,
        description="Target node ID"
    )
    fromSide: Optional[Side] = None
    toSide: Optional[Side] = None
    label: Optional[str] = Field(
        default=None,
        description="Edge label"
    )


class EdgeRead(BaseModel):
    """
    Edge response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/EdgeRead
    """
    id: str = Field(..., description="Edge ID")
    fromNode: str = Field(..., description="Source node ID")
    toNode: str = Field(..., description="Target node ID")
    fromSide: Optional[str] = None
    toSide: Optional[str] = None
    label: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class CanvasResponse(BaseModel):
    """
    Canvas response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/CanvasResponse
    """
    name: str = Field(..., description="Canvas file name")
    nodes: List[NodeRead] = Field(default_factory=list)
    edges: List[EdgeRead] = Field(default_factory=list)
