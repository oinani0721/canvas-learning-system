"""
Pydantic Models Package for Canvas Learning System API

Exports all models for use in API routers.
"""

from .common import HealthCheckResponse, ErrorResponse
from .canvas import (
    NodeCreate,
    NodeUpdate,
    NodeRead,
    EdgeCreate,
    EdgeRead,
    CanvasResponse,
)
from .agent import (
    DecomposeRequest,
    DecomposeResponse,
    ScoreRequest,
    NodeScore,
    ScoreResponse,
    ExplainRequest,
    ExplainResponse,
)
from .review import (
    ReviewItem,
    ReviewScheduleResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    RecordReviewRequest,
    RecordReviewResponse,
)

__all__ = [
    # Common
    "HealthCheckResponse",
    "ErrorResponse",
    # Canvas
    "NodeCreate",
    "NodeUpdate",
    "NodeRead",
    "EdgeCreate",
    "EdgeRead",
    "CanvasResponse",
    # Agent
    "DecomposeRequest",
    "DecomposeResponse",
    "ScoreRequest",
    "NodeScore",
    "ScoreResponse",
    "ExplainRequest",
    "ExplainResponse",
    # Review
    "ReviewItem",
    "ReviewScheduleResponse",
    "GenerateReviewRequest",
    "GenerateReviewResponse",
    "RecordReviewRequest",
    "RecordReviewResponse",
]
