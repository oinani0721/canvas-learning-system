# Canvas Learning System - Review Router
# Story 15.2: Routing System and APIRouter Configuration
"""
Review system router.

Provides 3 endpoints for Ebbinghaus review system operations.
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review]
"""

from datetime import date, timedelta

from fastapi import APIRouter, status

from app.models import (
    ReviewScheduleResponse,
    ReviewItem,
    GenerateReviewRequest,
    GenerateReviewResponse,
    RecordReviewRequest,
    RecordReviewResponse,
    ErrorResponse,
)

# ✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
# APIRouter(prefix, tags, responses) for modular routing
review_router = APIRouter(
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
    }
)


# ═══════════════════════════════════════════════════════════════════════════════
# Review Endpoints (3)
# [Source: specs/api/fastapi-backend-api.openapi.yml#Review Endpoints]
# ═══════════════════════════════════════════════════════════════════════════════

@review_router.get(
    "/schedule",
    response_model=ReviewScheduleResponse,
    summary="Get review schedule",
    operation_id="get_review_schedule",
)
async def get_review_schedule(days: int = 7) -> ReviewScheduleResponse:
    """
    Get review schedule based on Ebbinghaus forgetting curve.

    - **days**: Number of days to look ahead (default: 7)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1schedule]
    """
    # Placeholder implementation - return empty schedule
    return ReviewScheduleResponse(
        items=[],
        total_count=0,
    )


@review_router.post(
    "/generate",
    response_model=GenerateReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate verification canvas",
    operation_id="generate_verification_canvas",
)
async def generate_verification_canvas(
    request: GenerateReviewRequest,
) -> GenerateReviewResponse:
    """
    Generate verification canvas for review.

    - **source_canvas**: Source Canvas file name
    - **node_ids**: Specific node IDs (optional, defaults to all green nodes)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1generate]
    """
    # Placeholder implementation
    today = date.today().strftime("%Y%m%d")
    return GenerateReviewResponse(
        verification_canvas_name=f"{request.source_canvas}-verification-{today}",
        node_count=0,
    )


@review_router.put(
    "/record",
    response_model=RecordReviewResponse,
    summary="Record review result",
    operation_id="record_review_result",
)
async def record_review_result(request: RecordReviewRequest) -> RecordReviewResponse:
    """
    Record review result and update next review date.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID
    - **score**: Review score (0-40)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1record]
    """
    # Placeholder implementation
    # Calculate next review based on score (simplified Ebbinghaus logic)
    if request.score >= 32:
        interval = 30  # Good understanding -> 30 days
    elif request.score >= 24:
        interval = 7  # Partial understanding -> 7 days
    else:
        interval = 1  # Poor understanding -> 1 day

    return RecordReviewResponse(
        next_review_date=date.today() + timedelta(days=interval),
        new_interval=interval,
    )
