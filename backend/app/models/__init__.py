# Models Package
# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: response model)
"""Pydantic models for request/response validation."""

# Story 12.G.2: Agent Error Type Enum
# [Source: specs/api/agent-api.openapi.yml:617-627]
from app.models.enums import AgentErrorType

# Story 30.5: Canvas CRUD Event Models
# [Source: specs/data/temporal-event.schema.json]
from app.models.canvas_events import (
    CanvasEvent,
    CanvasEventContext,
    CanvasEventType,
)

# Rollback models (Story 18.1)
# [Source: docs/architecture/rollback-recovery-architecture.md:296-400]
# Review models (Story 24.4)
# [Source: specs/api/review-api.openapi.yml#L725-805]
# Verification History models (Story 31.4)
# [Source: specs/data/verification-history-response.schema.json]
from app.models.review_models import (
    ConceptStatus,
    # Story 34.4: Review History Models
    HistoryDayRecord,
    HistoryPeriod,
    HistoryResponse,
    HistoryReviewRecord,
    HistoryStatistics,
    MultiReviewProgressResponse,
    OverallProgress,
    PaginationInfo,
    PassRateTrend,
    QuestionType,
    ReviewEntry,
    ReviewMode,
    # Story 31.6: Session Progress Models
    SessionPauseResumeResponse,
    SessionProgressResponse,
    TrendAnalysis,
    TrendDirection,
    VerificationHistoryItem,
    VerificationHistoryResponse,
    VerificationStatusEnum,
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
# Story 33.3: Session Management Models
# [Source: specs/data/parallel-task.schema.json]
from app.models.session_models import (
    NodeResult,
    SessionInfo,
    SessionStatus,
    VALID_TRANSITIONS,
    is_valid_transition,
)

# Story 33.1: Intelligent Parallel Processing Models
# [Source: specs/api/parallel-api.openapi.yml]
# [Source: specs/data/parallel-task.schema.json]
from app.models.intelligent_parallel_models import (
    CancelResponse,
    ConfirmRequest,
    GroupExecuteConfig,
    GroupPriority,
    GroupProgress,
    GroupStatus,
    IntelligentParallelRequest,
    IntelligentParallelResponse,
    NodeError,
    NodeGroup,
    NodeInGroup,
    NodeResult as ParallelNodeResult,  # Alias to avoid conflict with session_models
    ParallelErrorResponse,
    ParallelTaskStatus,
    PerformanceMetrics,
    ProgressResponse,
    SessionResponse,
    SingleAgentRequest,
    SingleAgentResponse,
    SingleAgentStatus,
)
# Story 35.1: Multimodal API Schemas
# [Source: docs/stories/35.1.story.md]
# Story 35.2: Multimodal Query/Search API Schemas
# [Source: docs/stories/35.2.story.md]
from app.models.multimodal_schemas import (
    # Story 35.1: Upload/Management
    MultimodalDeleteResponse,
    MultimodalHealthResponse,
    MultimodalListResponse,
    MultimodalMediaType,
    MultimodalMetadataSchema,
    MultimodalResponse,
    MultimodalUpdateRequest,
    MultimodalUploadResponse,
    MultimodalUploadUrlRequest,
    # Story 35.2: Query/Search
    MediaItemResponse,
    MultimodalByConceptResponse,
    MultimodalPaginatedListResponse,
    MultimodalSearchRequest,
    MultimodalSearchResponse,
    PaginationMeta,
)
from app.models.schemas import (
    # Story 31.3: Recommend Action Models
    ActionTrend,
    ActionType,
    AlternativeAgent,
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
    HistoryContext,
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
    # Story 31.3: Recommend Action
    RecommendActionRequest,
    RecommendActionResponse,
    RecordReviewRequest,
    RecordReviewResponse,
    # Story 32.2: FSRS State Response
    FSRSStateResponse,
    # Story 32.3: FSRS State Query Response
    FSRSStateQueryResponse,
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
    # Story 31.3: Recommend Action Models
    "ActionType",
    "ActionTrend",
    "HistoryContext",
    "AlternativeAgent",
    "RecommendActionRequest",
    "RecommendActionResponse",
    # Story 30.5: Canvas CRUD Event Models
    "CanvasEventType",
    "CanvasEvent",
    "CanvasEventContext",
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
    # Story 32.2: FSRS State Response
    "FSRSStateResponse",
    # Story 32.3: FSRS State Query Response
    "FSRSStateQueryResponse",
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
    # Verification History (Story 31.4)
    "QuestionType",
    "VerificationHistoryItem",
    "PaginationInfo",
    "VerificationHistoryResponse",
    # Session Progress (Story 31.6)
    "VerificationStatusEnum",
    "SessionProgressResponse",
    "SessionPauseResumeResponse",
    # Review History (Story 34.4)
    "HistoryPeriod",
    "HistoryReviewRecord",
    "HistoryDayRecord",
    "HistoryStatistics",
    "HistoryResponse",
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
    # Session Management (Story 33.3)
    "SessionStatus",
    "SessionInfo",
    "NodeResult",
    "VALID_TRANSITIONS",
    "is_valid_transition",
    # Intelligent Parallel Processing (Story 33.1)
    "ParallelTaskStatus",
    "GroupStatus",
    "GroupPriority",
    "SingleAgentStatus",
    "IntelligentParallelRequest",
    "NodeInGroup",
    "NodeGroup",
    "GroupExecuteConfig",
    "ConfirmRequest",
    "SingleAgentRequest",
    "IntelligentParallelResponse",
    "SessionResponse",
    "ParallelNodeResult",
    "NodeError",
    "GroupProgress",
    "PerformanceMetrics",
    "ProgressResponse",
    "CancelResponse",
    "SingleAgentResponse",
    "ParallelErrorResponse",
    # Multimodal API (Story 35.1)
    "MultimodalMediaType",
    "MultimodalMetadataSchema",
    "MultimodalUploadUrlRequest",
    "MultimodalUpdateRequest",
    "MultimodalResponse",
    "MultimodalUploadResponse",
    "MultimodalDeleteResponse",
    "MultimodalListResponse",
    "MultimodalHealthResponse",
    # Multimodal Query/Search API (Story 35.2)
    "MediaItemResponse",
    "PaginationMeta",
    "MultimodalByConceptResponse",
    "MultimodalSearchRequest",
    "MultimodalSearchResponse",
    "MultimodalPaginatedListResponse",
]
