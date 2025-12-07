"""
Services module for Canvas Learning System.

Contains business logic services for progress tracking and validation.

Story 19.1: SourceNodeValidator - sourceNodeId validation API
Story 19.2: ProgressAnalyzer - progress analysis algorithms
"""

from .progress_analyzer import (
    ConceptTrend,
    MultiReviewProgress,
    ProgressAnalyzer,
    ReviewHistoryEntry,
    SingleReviewProgress,
)
from .source_node_validator import (
    BatchValidationResult,
    SourceNodeValidationResult,
    SourceNodeValidator,
)

__all__ = [
    # Story 19.1
    "SourceNodeValidator",
    "SourceNodeValidationResult",
    "BatchValidationResult",
    # Story 19.2
    "ProgressAnalyzer",
    "SingleReviewProgress",
    "MultiReviewProgress",
    "ReviewHistoryEntry",
    "ConceptTrend",
]
