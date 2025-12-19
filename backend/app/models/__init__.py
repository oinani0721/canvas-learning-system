# Models Package
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: response model)
"""Pydantic models for request/response validation."""

# Story 12.G.2: Agent Error Type Enum
# [Source: specs/api/agent-api.openapi.yml:617-627]
from app.models.enums import AgentErrorType

# Rollback models (Story 18.1)
# [Source: docs/architecture/rollback-recovery-architecture.md:296-400]
# Review models (Story 24.4)
# [Source: specs/api/review-api.openapi.yml#L725-805]
from app.models.review_models import (
    ConceptStatus,
    MultiReviewProgressResponse,
    OverallProgress,
    PassRateTrend,
    ReviewEntry,
    ReviewMode,
    TrendAnalysis,
    TrendDirection,
    WeakConceptImprovement,
)
from app.models.rollback import (
    CreateSnapshotRequest,
    DiffResponse,
    GraphSyncStatusEnum,
    OperationDataResponse,
    OperationHistoryResponse,
    OperationMetadataResponse,
    OperationResponse,
    OperationTypeEnum,
    RollbackRequest,
    RollbackResult,
    RollbackTypeEnum,
    SnapshotListResponse,
    SnapshotMetadataResponse,
    SnapshotResponse,
    SnapshotTypeEnum,
)
from app.models.schemas import (
    # Story 12.G.3: Agent Health Check
    AgentHealthCheckResponse,
    AgentHealthChecks,
    AgentHealthStatus,
    ApiTestResult,
    CanvasResponse,
    # Agents
    DecomposeRequest,
    DecomposeResponse,
    EdgeCreate,
    EdgeRead,
    EdgeSide,
    ErrorResponse,
    ExplainRequest,
    ExplainResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    HealthCheckResponse,
    # Common
    HealthStatus,
    NodeColor,
    NodeCreate,
    NodeRead,
    NodeScore,
    # Canvas
    NodeType,
    NodeUpdate,
    PromptTemplateCheck,
    # Story 12.A.6: verification-question and question-decomposition Agents
    QuestionDecomposeRequest,
    QuestionDecomposeResponse,
    RecordReviewRequest,
    RecordReviewResponse,
    # Review
    ReviewItem,
    ReviewScheduleResponse,
    ScoreRequest,
    ScoreResponse,
    SubQuestion,
    VerificationQuestion,
    VerificationQuestionRequest,
    VerificationQuestionResponse,
    WeakConceptData,
    WeightConfig,
)

__all__ = [
    # Common
    "HealthStatus",
    "HealthCheckResponse",
    "ErrorResponse",
    # Story 12.G.2: Agent Error Types
    "AgentErrorType",
    # Story 12.G.3: Agent Health Check
    "AgentHealthStatus",
    "PromptTemplateCheck",
    "ApiTestResult",
    "AgentHealthChecks",
    "AgentHealthCheckResponse",
    # Canvas
    "NodeType",
    "NodeColor",
    "EdgeSide",
    "NodeCreate",
    "NodeUpdate",
    "NodeRead",
    "EdgeCreate",
    "EdgeRead",
    "CanvasResponse",
    # Agents
    "DecomposeRequest",
    "DecomposeResponse",
    "ScoreRequest",
    "ScoreResponse",
    "NodeScore",
    "ExplainRequest",
    "ExplainResponse",
    # Story 12.A.6: verification-question and question-decomposition Agents
    "VerificationQuestionRequest",
    "VerificationQuestion",
    "VerificationQuestionResponse",
    "QuestionDecomposeRequest",
    "SubQuestion",
    "QuestionDecomposeResponse",
    # Review
    "ReviewItem",
    "ReviewScheduleResponse",
    "GenerateReviewRequest",
    "GenerateReviewResponse",
    "WeakConceptData",
    "WeightConfig",
    "RecordReviewRequest",
    "RecordReviewResponse",
    # Multi-Review (Story 24.4)
    "ReviewMode",
    "TrendDirection",
    "ConceptStatus",
    "ReviewEntry",
    "PassRateTrend",
    "WeakConceptImprovement",
    "OverallProgress",
    "TrendAnalysis",
    "MultiReviewProgressResponse",
    # Rollback (Story 18.1-18.5)
    "OperationTypeEnum",
    "OperationDataResponse",
    "OperationMetadataResponse",
    "OperationResponse",
    "OperationHistoryResponse",
    "SnapshotTypeEnum",
    "SnapshotMetadataResponse",
    "SnapshotResponse",
    "SnapshotListResponse",
    "CreateSnapshotRequest",
    "RollbackTypeEnum",
    "RollbackRequest",
    "RollbackResult",
    "GraphSyncStatusEnum",
    "DiffResponse",
]
