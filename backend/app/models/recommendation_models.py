# Canvas Learning System - Recommendation Models
# Story 1.7: Concept-relation recommendation (AC-2, AC-4)
"""
Pydantic models for concept-relation recommendation API.

[Source: _bmad-output/implementation-artifacts/1-7-concept-relation-recommendation.md#Task 2]
"""

from datetime import datetime
from typing import List, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class DismissedPair(BaseModel):
    """A node pair that the user has dismissed."""

    node_id_a: str
    node_id_b: str


class DismissedPairsRequest(BaseModel):
    """Request body containing dismissed node pairs."""

    dismissed_pairs: List[DismissedPair] = Field(default_factory=list)


class RecommendationCandidate(BaseModel):
    """Internal candidate before title resolution."""

    source_node_id: str
    target_node_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_type: Literal["text_similarity", "graph_pattern"]
    reason: str


class Recommendation(BaseModel):
    """A single recommendation returned to the frontend."""

    id: str = Field(default_factory=lambda: uuid4().hex[:16])
    source_node_id: str
    source_node_title: str
    target_node_id: str
    target_node_title: str
    confidence: float
    reason: str
    suggested_label: str


class RecommendationResponse(BaseModel):
    """API response wrapping a list of recommendations."""

    recommendations: List[Recommendation]
    canvas_id: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
