"""
Agent Pydantic Models for Canvas Learning System API

Provides models for Agent invocation and scoring operations.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Pydantic models)
Models match specs/api/fastapi-backend-api.openapi.yml
"""

from typing import List, Literal

from pydantic import BaseModel, Field

from .canvas import NodeRead


class DecomposeRequest(BaseModel):
    """
    Decompose agent request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/DecomposeRequest
    """
    canvas_name: str = Field(
        ...,
        description="Canvas file name"
    )
    node_id: str = Field(
        ...,
        description="Target node ID"
    )


class DecomposeResponse(BaseModel):
    """
    Decompose agent response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/DecomposeResponse
    """
    questions: List[str] = Field(
        ...,
        description="Generated guiding questions"
    )
    created_nodes: List[NodeRead] = Field(
        ...,
        description="Created new nodes"
    )


class ScoreRequest(BaseModel):
    """
    Scoring agent request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ScoreRequest
    """
    canvas_name: str = Field(
        ...,
        description="Canvas file name"
    )
    node_ids: List[str] = Field(
        ...,
        description="Node IDs to score"
    )


class NodeScore(BaseModel):
    """
    Individual node score model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/NodeScore
    """
    node_id: str = Field(..., description="Node ID")
    accuracy: float = Field(
        ...,
        ge=0,
        le=10,
        description="Accuracy score"
    )
    imagery: float = Field(
        ...,
        ge=0,
        le=10,
        description="Imagery score"
    )
    completeness: float = Field(
        ...,
        ge=0,
        le=10,
        description="Completeness score"
    )
    originality: float = Field(
        ...,
        ge=0,
        le=10,
        description="Originality score"
    )
    total: float = Field(
        ...,
        ge=0,
        le=40,
        description="Total score"
    )
    new_color: Literal["2", "3", "4"] = Field(
        ...,
        description="New color code: 2=绿(>=32), 3=黄(24-31), 4=红(<24)"
    )


class ScoreResponse(BaseModel):
    """
    Scoring agent response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ScoreResponse
    """
    scores: List[NodeScore] = Field(
        ...,
        description="Scores for each node"
    )


class ExplainRequest(BaseModel):
    """
    Explain agent request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ExplainRequest
    """
    canvas_name: str = Field(
        ...,
        description="Canvas file name"
    )
    node_id: str = Field(
        ...,
        description="Target node ID"
    )


class ExplainResponse(BaseModel):
    """
    Explain agent response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ExplainResponse
    """
    explanation: str = Field(
        ...,
        description="Generated explanation content"
    )
    created_node_id: str = Field(
        ...,
        description="Created explanation node ID"
    )
