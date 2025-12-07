"""
Review Router for Canvas Learning System API

Provides endpoints for Ebbinghaus review system operations.

✅ Verified from Context7:/websites/fastapi_tiangolo (topic: APIRouter)
"""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, status

from ..models import (
    ErrorResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    RecordReviewRequest,
    RecordReviewResponse,
    ReviewItem,
    ReviewScheduleResponse,
)

router = APIRouter(prefix="/review", tags=["Review"])


@router.get(
    "/schedule",
    response_model=ReviewScheduleResponse,
    summary="获取复习计划",
    description="基于艾宾浩斯遗忘曲线返回待复习项目",
    operation_id="get_review_schedule"
)
async def get_review_schedule(days: int = 7) -> ReviewScheduleResponse:
    """
    Get review schedule.

    Returns items due for review based on Ebbinghaus forgetting curve.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1schedule

    Args:
        days: Number of days to look ahead (default: 7)

    Returns:
        ReviewScheduleResponse with review items
    """
    # Mock review items
    today = date.today()
    items = [
        ReviewItem(
            canvas_name="离散数学",
            node_id="a1b2c3d4",
            concept="逆否命题",
            due_date=today,
            interval_days=1
        ),
        ReviewItem(
            canvas_name="离散数学",
            node_id="e5f6g7h8",
            concept="充分必要条件",
            due_date=today + timedelta(days=2),
            interval_days=7
        ),
        ReviewItem(
            canvas_name="线性代数",
            node_id="i9j0k1l2",
            concept="矩阵乘法",
            due_date=today + timedelta(days=5),
            interval_days=30
        )
    ]

    # Filter by days parameter
    end_date = today + timedelta(days=days)
    filtered_items = [item for item in items if item.due_date <= end_date]

    return ReviewScheduleResponse(
        items=filtered_items,
        total_count=len(filtered_items)
    )


@router.post(
    "/generate",
    response_model=GenerateReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成检验白板",
    description="为指定Canvas生成检验白板用于复习",
    operation_id="generate_verification_canvas",
    responses={
        404: {"model": ErrorResponse, "description": "源Canvas不存在"}
    }
)
async def generate_verification_canvas(
    request: GenerateReviewRequest
) -> GenerateReviewResponse:
    """
    Generate verification canvas.

    Creates a verification canvas from source canvas for review.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1generate
    """
    # Validate source canvas exists (mock check)
    valid_canvases = ["test-canvas", "离散数学", "线性代数"]
    if request.source_canvas not in valid_canvases:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source canvas '{request.source_canvas}' not found"
        )

    # Generate verification canvas name
    today = date.today().strftime("%Y%m%d")
    verification_name = f"{request.source_canvas}-检验白板-{today}"

    # Calculate node count
    if request.node_ids:
        node_count = len(request.node_ids)
    else:
        # Default: all green nodes (mock count)
        node_count = 5

    return GenerateReviewResponse(
        verification_canvas_name=verification_name,
        node_count=node_count
    )


@router.put(
    "/record",
    response_model=RecordReviewResponse,
    summary="记录复习结果",
    description="记录用户复习完成情况，更新下次复习时间",
    operation_id="record_review_result"
)
async def record_review_result(
    request: RecordReviewRequest
) -> RecordReviewResponse:
    """
    Record review result.

    Records user's review completion and updates next review date.

    Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1record
    """
    # Calculate next review based on score
    # Ebbinghaus intervals: 1 -> 7 -> 30 days
    # Score affects interval: high score = longer interval

    if request.score >= 32:
        # Good performance: extend interval
        new_interval = 30
    elif request.score >= 24:
        # Medium performance: standard interval
        new_interval = 7
    else:
        # Poor performance: short interval
        new_interval = 1

    next_review = date.today() + timedelta(days=new_interval)

    return RecordReviewResponse(
        next_review_date=next_review,
        new_interval=new_interval
    )
