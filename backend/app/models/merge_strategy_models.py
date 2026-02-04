# Canvas Learning System - Result Merger Models
# Story 33.7: Result Merging Strategies
# ✅ Internal service models (not exposed via REST API)
"""
Pydantic Models for Result Merging Strategies.

These models are internal to the BatchOrchestrator and not exposed via REST API.
[Source: docs/stories/33.7.story.md - Dev Notes]
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# [Source: docs/stories/33.7.story.md - AC4]
# ═══════════════════════════════════════════════════════════════════════════════

class MergeStrategyType(str, Enum):
    """
    Merge strategy type enum.

    [Source: docs/stories/33.7.story.md - Task 1]
    - supplementary: Concatenates all outputs with separators (AC1)
    - hierarchical: Organizes by difficulty level (AC2)
    - voting: Deduplicates and keeps most relevant (AC3)
    """
    supplementary = "supplementary"
    hierarchical = "hierarchical"
    voting = "voting"


class DifficultyLevel(str, Enum):
    """
    Content difficulty level for hierarchical merging.

    [Source: docs/stories/33.7.story.md - AC2]
    Sort order: beginner → intermediate → advanced → expert
    """
    beginner = "beginner"       # 入门
    intermediate = "intermediate"  # 进阶
    advanced = "advanced"       # 深入
    expert = "expert"          # 专家


# ═══════════════════════════════════════════════════════════════════════════════
# Input Models
# [Source: docs/stories/33.7.story.md - Task 1]
# ═══════════════════════════════════════════════════════════════════════════════

class AgentResult(BaseModel):
    """
    Single Agent execution result (input to merger).

    [Source: docs/stories/33.7.story.md - Dev Notes > Previous Story Insights]
    Structure matches BatchOrchestrator output from Story 33.6.
    """
    node_id: str = Field(..., description="Processed node ID", examples=["node-001"])
    agent_name: str = Field(
        ...,
        description="Agent that produced this result",
        examples=["oral-explanation"]
    )
    result: str = Field(..., description="Agent output content")
    group_id: Optional[str] = Field(
        None,
        description="Group ID if processed as part of batch",
        examples=["group-1"]
    )
    success: bool = Field(default=True, description="Whether execution succeeded")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata from agent execution"
    )


class MergeOptions(BaseModel):
    """
    Optional configuration for merge operation.

    [Source: docs/stories/33.7.story.md - Task 1]
    """
    include_attribution: bool = Field(
        default=True,
        description="Include agent attribution headers"
    )
    max_content_length: Optional[int] = Field(
        None,
        description="Maximum merged content length (chars)",
        ge=100
    )
    dedup_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="Cosine similarity threshold for duplicate detection (Voting strategy)"
    )
    preserve_formatting: bool = Field(
        default=True,
        description="Preserve original markdown formatting"
    )


class MergeRequest(BaseModel):
    """
    Request model for result merging.

    [Source: docs/stories/33.7.story.md - Task 1]
    """
    source_results: List[AgentResult] = Field(
        ...,
        description="List of Agent results to merge"
    )
    strategy: MergeStrategyType = Field(
        default=MergeStrategyType.supplementary,
        description="Merge strategy to use"
    )
    options: Optional[MergeOptions] = Field(
        None,
        description="Optional merge configuration"
    )
    group_id: Optional[str] = Field(
        None,
        description="Group ID for the merged content"
    )
    concept_name: Optional[str] = Field(
        None,
        description="Concept name for context"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Output Models
# [Source: docs/stories/33.7.story.md - AC5, Task 1]
# ═══════════════════════════════════════════════════════════════════════════════

class QualityScore(BaseModel):
    """
    Quality metrics for merged result.

    [Source: docs/stories/33.7.story.md - AC5]
    Metrics:
    - coverage: concepts covered / expected concepts (0-100)
    - redundancy: duplicate content ratio (0-100, lower is better)
    - coherence: flow and logical connection (0-100)
    - overall: weighted average
    """
    coverage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Coverage score: concepts covered / expected concepts",
        examples=[85.0]
    )
    redundancy: float = Field(
        ...,
        ge=0,
        le=100,
        description="Redundancy score: duplicate content ratio (lower is better)",
        examples=[12.0]
    )
    coherence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Coherence score: flow and logical connection",
        examples=[78.0]
    )
    overall: float = Field(
        ...,
        ge=0,
        le=100,
        description="Overall quality score (weighted average)",
        examples=[83.7]
    )

    @classmethod
    def empty(cls) -> "QualityScore":
        """Create empty quality score for edge cases."""
        return cls(coverage=0, redundancy=0, coherence=0, overall=0)

    @classmethod
    def calculate(
        cls,
        coverage: float,
        redundancy: float,
        coherence: float,
    ) -> "QualityScore":
        """
        Calculate overall score from individual metrics.

        Formula: coverage*0.4 + (100-redundancy)*0.3 + coherence*0.3
        [Source: docs/stories/33.7.story.md - Technical Details > Quality Scoring Algorithm]
        """
        overall = (coverage * 0.4) + ((100 - redundancy) * 0.3) + (coherence * 0.3)
        return cls(
            coverage=coverage,
            redundancy=redundancy,
            coherence=coherence,
            overall=round(overall, 2),
        )


class MergeResult(BaseModel):
    """
    Result of merge operation.

    [Source: docs/stories/33.7.story.md - Dev Notes > Response Format]
    NOTE: Internal model, not exposed via REST API.
    """
    merged_content: str = Field(
        ...,
        description="Merged content from all agents"
    )
    strategy_used: MergeStrategyType = Field(
        ...,
        description="Strategy that was applied"
    )
    source_count: int = Field(
        ...,
        ge=0,
        description="Number of source results merged"
    )
    quality_score: QualityScore = Field(
        ...,
        description="Quality metrics for merged result"
    )
    merge_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When merge was performed"
    )
    # Optional fields for tracking
    successful_sources: int = Field(
        default=0,
        description="Number of successful source results included"
    )
    failed_sources: int = Field(
        default=0,
        description="Number of failed source results excluded"
    )
    group_id: Optional[str] = Field(
        None,
        description="Group ID if applicable"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings generated during merge"
    )

    @classmethod
    def empty(cls, strategy: MergeStrategyType = MergeStrategyType.supplementary) -> "MergeResult":
        """
        Create empty result for edge case (no input results).

        [Source: docs/stories/33.7.story.md - Task 2]
        """
        return cls(
            merged_content="",
            strategy_used=strategy,
            source_count=0,
            quality_score=QualityScore.empty(),
            successful_sources=0,
            failed_sources=0,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Configuration Models
# [Source: docs/stories/33.7.story.md - AC4]
# ═══════════════════════════════════════════════════════════════════════════════

class MergeConfig(BaseModel):
    """
    Merge configuration from environment variables.

    [Source: docs/stories/33.7.story.md - AC4, Implementation Notes]
    """
    default_strategy: MergeStrategyType = Field(
        default=MergeStrategyType.supplementary,
        description="Default merge strategy (MERGE_STRATEGY env var)"
    )
    quality_threshold: int = Field(
        default=60,
        ge=0,
        le=100,
        description="Quality threshold for warnings (MERGE_QUALITY_THRESHOLD env var)"
    )
    dedup_threshold: float = Field(
        default=0.8,
        ge=0.5,
        le=1.0,
        description="TF-IDF cosine similarity threshold for duplicate detection"
    )
