"""
Review System Pydantic Models for Canvas Learning System API

Provides models for Ebbinghaus review system operations.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: Pydantic models)
Models match specs/api/fastapi-backend-api.openapi.yml
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ReviewItem(BaseModel):
    """
    Individual review item model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ReviewItem
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID")
    concept: str = Field(..., description="Concept name")
    due_date: date = Field(..., description="Due date for review")
    interval_days: int = Field(
        ...,
        description="Current review interval (1/7/30 days)"
    )


class ReviewScheduleResponse(BaseModel):
    """
    Review schedule response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/ReviewScheduleResponse
    """
    items: List[ReviewItem] = Field(
        default_factory=list,
        description="Review items list"
    )
    total_count: int = Field(
        ...,
        description="Total items count"
    )


class GenerateReviewRequest(BaseModel):
    """
    Generate verification canvas request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewRequest
    """
    source_canvas: str = Field(
        ...,
        description="Source Canvas file name"
    )
    node_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific node IDs (optional, default: all green nodes)"
    )


class GenerateReviewResponse(BaseModel):
    """
    Generate verification canvas response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/GenerateReviewResponse
    """
    verification_canvas_name: str = Field(
        ...,
        description="Generated verification canvas file name"
    )
    node_count: int = Field(
        ...,
        description="Number of verification nodes"
    )


class RecordReviewRequest(BaseModel):
    """
    Record review result request model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewRequest
    """
    canvas_name: str = Field(..., description="Canvas file name")
    node_id: str = Field(..., description="Node ID")
    score: float = Field(
        ...,
        ge=0,
        le=40,
        description="Review score (0-40)"
    )


class RecordReviewResponse(BaseModel):
    """
    Record review result response model.

    Source: specs/api/fastapi-backend-api.openapi.yml#/components/schemas/RecordReviewResponse
    """
    next_review_date: date = Field(
        ...,
        description="Next review date"
    )
    new_interval: int = Field(
        ...,
        description="New review interval in days"
    )
