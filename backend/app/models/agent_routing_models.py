# Canvas Learning System - Agent Routing Models
# Story 33.5: Agent Routing Engine
# [Source: docs/stories/33.5.story.md]
"""
Pydantic models for Agent Routing Engine.

This module defines request/response models for content-based agent routing.
The routing engine analyzes node content to recommend the most suitable agent
for batch processing.

Model Structure:
- RoutingRequest: Single node routing request
- RoutingResult: Single node routing result with confidence
- BatchRoutingRequest: Batch of nodes for routing
- BatchRoutingResponse: Batch routing results with accuracy estimate

[Source: specs/api/parallel-api.openapi.yml#L301-L313]
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RoutingRequest(BaseModel):
    """Single node routing request.

    Attributes:
        node_id: Unique identifier for the node
        node_text: Text content of the node to analyze
        agent_override: Optional manual agent override (bypasses routing logic)
    """
    node_id: str = Field(..., description="Unique node identifier")
    node_text: str = Field(..., description="Node text content for analysis")
    agent_override: Optional[str] = Field(
        None,
        description="Manual agent override (bypasses routing logic)"
    )


class RoutingResult(BaseModel):
    """Single node routing result.

    Attributes:
        node_id: Node identifier
        recommended_agent: The agent recommended for this node
        confidence: Confidence score (0.0 - 1.0)
        patterns_matched: List of patterns that matched
        fallback_agent: Backup agent if primary unavailable
        reason: Explanation for the routing decision

    [Source: specs/api/parallel-api.openapi.yml#L301-L313]
    """
    node_id: str = Field(..., description="Node identifier")
    recommended_agent: str = Field(
        ...,
        description="Recommended agent type",
        examples=["oral-explanation", "comparison-table"]
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    patterns_matched: List[str] = Field(
        default_factory=list,
        description="Patterns that matched in the content"
    )
    fallback_agent: Optional[str] = Field(
        None,
        description="Fallback agent if primary unavailable"
    )
    reason: str = Field(
        default="",
        description="Explanation for routing decision"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "node_id": self.node_id,
            "recommended_agent": self.recommended_agent,
            "confidence": round(self.confidence, 2),
            "patterns_matched": self.patterns_matched,
            "fallback_agent": self.fallback_agent,
            "reason": self.reason,
        }


class BatchRoutingRequest(BaseModel):
    """Batch routing request for multiple nodes.

    Attributes:
        nodes: List of routing requests for batch processing
    """
    nodes: List[RoutingRequest] = Field(
        ...,
        description="List of nodes for batch routing",
        min_length=1
    )


class BatchRoutingResponse(BaseModel):
    """Batch routing response with results and accuracy estimate.

    Attributes:
        results: List of routing results for each node
        routing_accuracy_estimate: Estimated routing accuracy (0.0-1.0)
        total_nodes: Total number of nodes processed
        high_confidence_count: Count of results with confidence >= 0.85
        medium_confidence_count: Count of results with confidence 0.7-0.85
        low_confidence_count: Count of results with confidence < 0.7
    """
    results: List[RoutingResult] = Field(
        ...,
        description="Routing results for each node"
    )
    routing_accuracy_estimate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated overall routing accuracy"
    )
    total_nodes: int = Field(..., description="Total nodes processed")
    high_confidence_count: int = Field(
        default=0,
        description="Count of high confidence results (>= 0.85)"
    )
    medium_confidence_count: int = Field(
        default=0,
        description="Count of medium confidence results (0.7-0.85)"
    )
    low_confidence_count: int = Field(
        default=0,
        description="Count of low confidence results (< 0.7)"
    )

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "results": [r.to_dict() for r in self.results],
            "routing_accuracy_estimate": round(self.routing_accuracy_estimate, 2),
            "total_nodes": self.total_nodes,
            "high_confidence_count": self.high_confidence_count,
            "medium_confidence_count": self.medium_confidence_count,
            "low_confidence_count": self.low_confidence_count,
        }


__all__ = [
    "RoutingRequest",
    "RoutingResult",
    "BatchRoutingRequest",
    "BatchRoutingResponse",
]
