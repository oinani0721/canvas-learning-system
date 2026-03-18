# Canvas Learning System - Edge Rationale Models
# Story 4.2: Edge Dialog — Agent Follow-up & Rationale Recording (AC-2, AC-6)
# Story 4.3: EI+SE Dual Strategy (AC-6 strategy data)
# Story 4.4: Fallback — partial failure response (AC-3, AC-4)
"""
Pydantic schemas for Edge rationale recording.

record_edge_rationale MCP tool parameters and responses.
Supports dual-write (Graphiti + LanceDB) with partial failure semantics.

[Source: _bmad-output/implementation-artifacts/4-2-edge-dialog-agent-reasoning.md#Task 2]
[Source: _bmad-output/implementation-artifacts/4-3-ei-se-dual-strategy.md#Task 4]
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# ═══════════════════════════════════════════════════════════════════════════════
# Request Models
# ═══════════════════════════════════════════════════════════════════════════════


class EdgeRationaleCreate(BaseModel):
    """
    Parameters for record_edge_rationale MCP tool.

    Story 4.2 AC-6: edge_id, source_node_id, target_node_id,
    relation_type, rationale_text, confidence.
    Story 4.3 AC-6: strategies_applied, questioning_rounds,
    explanation_depth_score.
    """

    edge_id: str = Field(..., description="Canvas edge identifier")
    source_node_id: str = Field(..., description="Source node identifier")
    target_node_id: str = Field(..., description="Target node identifier")
    source_concept: str = Field("", description="Source concept name (display label)")
    target_concept: str = Field("", description="Target concept name (display label)")
    relation_type: str = Field(
        ...,
        description="Extracted relationship type (e.g. '是前提条件', '是特殊情况', '相互对比')",
    )
    rationale_text: str = Field(..., description="User's original explanation of the relationship")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Agent's assessment of understanding completeness (0-1)",
    )

    # Story 4.3: EI+SE strategy tracking
    strategies_applied: List[str] = Field(
        default_factory=lambda: ["EI", "SE"],
        description="Learning strategies activated during dialog (e.g. ['EI', 'SE'])",
    )
    questioning_rounds: int = Field(
        default=0,
        ge=0,
        description="Number of Agent follow-up questioning rounds",
    )
    explanation_depth_score: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Agent's internal assessment of explanation depth (1-5)",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class WriteStatus(BaseModel):
    """Status of a single write operation (Graphiti or LanceDB)."""

    success: bool
    error: Optional[str] = None


class EdgeRationaleResponse(BaseModel):
    """
    Response from record_edge_rationale endpoint.

    Story 4.4 AC-3/AC-4: Supports partial success (207) semantics.
    - 200: both writes succeeded
    - 207: one write succeeded, one failed
    - 500: both writes failed
    """

    record_id: str = Field(..., description="Unique record identifier")
    edge_id: str = Field(..., description="Edge that was recorded")
    relation_type: str = Field(..., description="Extracted relation type")
    graphiti_status: WriteStatus = Field(..., description="Graphiti write result")
    lancedb_status: WriteStatus = Field(..., description="LanceDB write result")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Recording timestamp (ISO 8601)",
    )

    @property
    def fully_successful(self) -> bool:
        """Both writes succeeded."""
        return self.graphiti_status.success and self.lancedb_status.success

    @property
    def partially_successful(self) -> bool:
        """Exactly one write succeeded."""
        return self.graphiti_status.success != self.lancedb_status.success
