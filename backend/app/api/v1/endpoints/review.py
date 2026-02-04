# Canvas Learning System - Review Router
# Story 15.2: Routing System and APIRouter Configuration
# ✅ Updated: Connected to real EbbinghausReviewScheduler (P0 Task #1)
# ✅ Updated: Implemented real verification canvas generation (P0 Task #7)
"""
Review system router.

Provides 3 endpoints for Ebbinghaus review system operations.
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review]
"""

import json
import logging
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, status

from app.models import (
    ErrorResponse,
    FSRSStateResponse,
    # Story 32.3: FSRS State Query Response
    FSRSStateQueryResponse,
    GenerateReviewRequest,
    GenerateReviewResponse,
    # Story 34.4: Review History Models
    HistoryDayRecord,
    HistoryPeriod,
    HistoryResponse,
    HistoryReviewRecord,
    HistoryStatistics,
    MultiReviewProgressResponse,
    PaginationInfo,
    QuestionType,
    RecordReviewRequest,
    RecordReviewResponse,
    ReviewItem,
    ReviewScheduleResponse,
    # Story 31.6: Session Progress Models
    SessionPauseResumeResponse,
    SessionProgressResponse,
    VerificationHistoryItem,
    VerificationHistoryResponse,
    VerificationStatusEnum,
)

# ✅ Add src directory to Python path for EbbinghausReviewScheduler import
# [Source: Plan - P0 Task #1: Connect review API to EbbinghausScheduler]
_project_root = Path(__file__).parent.parent.parent.parent.parent
_src_path = _project_root / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# ✅ Canvas base path configuration (P0 Task #7)
# [Source: src/agentic_rag/env_config.py - canvas_base_path]
_canvas_base_path = _project_root / "笔记库"

# ✅ Import real EbbinghausReviewScheduler
try:
    from ebbinghaus_review import EbbinghausReviewScheduler
    _scheduler = EbbinghausReviewScheduler()
    _scheduler_available = True
except ImportError as e:
    _scheduler = None
    _scheduler_available = False
    logging.warning(f"EbbinghausReviewScheduler not available: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Import Question Generator and Topic Clustering Services
# [Source: PRD F8, Story 4.2, Story 4.3]
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from app.services.question_generator import QuestionGenerator
    from app.services.topic_clustering import TopicClusterer
    _services_available = True
except ImportError:
    _services_available = False
    logging.warning("QuestionGenerator/TopicClusterer not available, using fallback")

# ═══════════════════════════════════════════════════════════════════════════════
# Canvas File Operations (P0 Task #7)
# [Source: Plan - P0 Task #7: Implement real verification canvas generation]
# ═══════════════════════════════════════════════════════════════════════════════

def _read_canvas(canvas_path: Path) -> Optional[Dict[str, Any]]:
    """Read Canvas JSON file and return data."""
    try:
        if not canvas_path.exists():
            logging.error(f"Canvas file not found: {canvas_path}")
            return None
        with open(canvas_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading canvas {canvas_path}: {e}")
        return None


def _write_canvas(canvas_path: Path, canvas_data: Dict[str, Any]) -> bool:
    """Write Canvas JSON data to file with backup."""
    try:
        # Create backup if file exists
        if canvas_path.exists():
            backup_path = canvas_path.with_suffix(".canvas.bak")
            import shutil
            shutil.copy2(canvas_path, backup_path)

        # Write new data
        with open(canvas_path, "w", encoding="utf-8") as f:
            json.dump(canvas_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error writing canvas {canvas_path}: {e}")
        return False


def _generate_node_id() -> str:
    """Generate unique node ID for Canvas."""
    return uuid.uuid4().hex[:16]


def _extract_review_nodes(
    source_nodes: List[Dict],
    node_ids: Optional[List[str]],
    mode: str = "fresh"
) -> List[Dict]:
    """
    Extract nodes for verification canvas based on PRD F8 + Story 4.1.

    PRD Requirements (修复颜色代码 - docs/issues/canvas-layout-lessons-learned.md):
    - 红色(color="4"): 不理解的内容 → 突破型问题
    - 紫色(color="3"): 似懂非懂的内容 → 检验型问题

    Modes (v1.1.8):
    - fresh: 提取所有红色+紫色节点
    - targeted: 70%薄弱点 + 30%已掌握概念

    [Source: docs/prd/FULL-PRD-REFERENCE.md - Story 4.1]
    [Source: docs/prd/sections/v118-检验白板历史关联与可选复习模式-2025-11-14-必读.md]
    """
    # If specific node IDs provided, use those
    if node_ids:
        node_id_set = set(node_ids)
        return [n for n in source_nodes if n.get("id") in node_id_set]

    # PRD F8: Extract RED (color="4") and PURPLE (color="3") nodes
    # 修复: "4"才是红色, "1"是灰色 (docs/issues/canvas-layout-lessons-learned.md)
    target_colors = {"4", "3"}  # Red=4, Purple=3

    # Filter text nodes with target colors
    all_target_nodes = [
        n for n in source_nodes
        if n.get("type") == "text" and n.get("color") in target_colors
    ]

    if mode == "fresh":
        # Fresh mode: Return all red + purple nodes
        return all_target_nodes

    elif mode == "targeted":
        # Targeted mode: 70% weak (red) + 30% partial (purple)
        red_nodes = [n for n in all_target_nodes if n.get("color") == "4"]
        purple_nodes = [n for n in all_target_nodes if n.get("color") == "3"]

        # Calculate counts
        red_count = max(1, int(len(red_nodes) * 0.7)) if red_nodes else 0
        purple_count = max(1, int(len(purple_nodes) * 0.3)) if purple_nodes else 0

        return red_nodes[:red_count] + purple_nodes[:purple_count]

    # Default: return all target nodes
    return all_target_nodes

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
    # ✅ Connected to real EbbinghausReviewScheduler (P0 Task #1)
    if not _scheduler_available or _scheduler is None:
        logging.warning("EbbinghausReviewScheduler not available, returning empty schedule")
        return ReviewScheduleResponse(items=[], total_count=0)

    try:
        # Get today's reviews from the scheduler
        raw_reviews = _scheduler.get_today_reviews()

        # Convert to ReviewItem format
        items = []
        for review in raw_reviews:
            items.append(ReviewItem(
                canvas_name=review.get("canvas_name", "unknown"),
                node_id=review.get("node_id", ""),
                concept=review.get("concept", review.get("content", "")),
                due_date=date.today(),
                interval_days=review.get("interval", 1),
            ))

        return ReviewScheduleResponse(
            items=items,
            total_count=len(items),
        )
    except Exception as e:
        logging.error(f"Error getting review schedule: {e}")
        return ReviewScheduleResponse(items=[], total_count=0)


# ═══════════════════════════════════════════════════════════════════════════════
# Story 34.4: Review History Endpoint with Pagination
# [Source: specs/api/review-api.openapi.yml#L185-216]
# [Source: docs/stories/34.4.story.md]
# ═══════════════════════════════════════════════════════════════════════════════

@review_router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get review history",
    operation_id="get_review_history",
    responses={
        404: {"model": ErrorResponse, "description": "No history found"}
    }
)
async def get_review_history(
    days: int = 7,
    canvas_path: Optional[str] = None,
    concept_name: Optional[str] = None,
    limit: int = 5,
    show_all: bool = False
) -> HistoryResponse:
    """
    Get review history with pagination support.

    Story 34.4 AC1: Default display shows most recent 5 records (limit=5).
    Story 34.4 AC2: show_all=True loads complete history.
    Story 34.4 AC3: API supports `limit` and `show_all` parameters.

    - **days**: Number of days to look back (7, 30, or 90)
    - **canvas_path**: Filter by canvas file path
    - **concept_name**: Filter by concept name
    - **limit**: Maximum records to return (default: 5, Story 34.4 AC1)
    - **show_all**: If True, ignore limit and return all records (Story 34.4 AC2)

    [Source: specs/api/review-api.openapi.yml#L185-216]
    [Source: docs/stories/34.4.story.md]
    """
    from datetime import datetime as dt

    from app.dependencies import get_review_service

    # Validate days parameter
    if days not in [7, 30, 90]:
        days = 7

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get review service
    review_service = get_review_service()

    try:
        # Get history from service with pagination
        effective_limit = None if show_all else limit
        result = await review_service.get_history(
            days=days,
            canvas_path=canvas_path,
            concept_name=concept_name,
            limit=effective_limit
        )

        # Build response
        records = []
        total_reviews = 0
        all_ratings = []
        canvas_counts: Dict[str, int] = {}

        for day_data in result.get("records", []):
            day_reviews = []
            for review in day_data.get("reviews", []):
                day_reviews.append(HistoryReviewRecord(
                    concept_id=review.get("concept_id", ""),
                    concept_name=review.get("concept_name", ""),
                    canvas_path=review.get("canvas_path", ""),
                    rating=review.get("rating", 3),
                    review_time=review.get("review_time", dt.now())
                ))
                all_ratings.append(review.get("rating", 3))
                canvas = review.get("canvas_path", "")
                canvas_counts[canvas] = canvas_counts.get(canvas, 0) + 1

            records.append(HistoryDayRecord(
                date=day_data.get("date", ""),
                reviews=day_reviews
            ))
            total_reviews += len(day_reviews)

        # Calculate statistics
        avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else None
        statistics = HistoryStatistics(
            average_rating=round(avg_rating, 2) if avg_rating else None,
            retention_rate=result.get("retention_rate"),
            streak_days=result.get("streak_days", 0),
            by_canvas=canvas_counts if canvas_counts else None
        )

        # Build pagination info
        has_more = result.get("has_more", False)
        pagination = PaginationInfo(
            limit=limit,
            offset=0,
            has_more=has_more and not show_all
        )

        return HistoryResponse(
            period=HistoryPeriod(
                start=start_date.isoformat(),
                end=end_date.isoformat()
            ),
            total_reviews=total_reviews,
            records=records,
            statistics=statistics,
            pagination=pagination
        )

    except Exception as e:
        logging.error(f"Error getting review history: {e}")
        # Return empty response on error
        return HistoryResponse(
            period=HistoryPeriod(
                start=start_date.isoformat(),
                end=end_date.isoformat()
            ),
            total_reviews=0,
            records=[],
            statistics=None,
            pagination=PaginationInfo(limit=limit, offset=0, has_more=False)
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
    - **node_ids**: Specific node IDs (optional)
    - **mode**: "fresh" (all red+purple) or "targeted" (70% weak + 30% partial)
    - **weak_weight**: Weight for weak concepts in targeted mode (default: 0.7)
    - **mastered_weight**: Weight for mastered concepts in targeted mode (default: 0.3)

    PRD F8: Extract red+purple nodes, generate questions, topic clustering
    [Source: docs/prd/FULL-PRD-REFERENCE.md - F8, Story 4.1-4.4]
    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1generate]
    [Source: Story 24.1 - Mode Support]
    """
    # ✅ PRD Compliant Implementation (Epic 4)
    # [Source: docs/prd/FULL-PRD-REFERENCE.md - F8, Story 4.1-4.9]
    # ✅ Story 24.1: Mode parameter support added

    today = date.today().strftime("%Y%m%d")
    verification_canvas_name = f"{request.source_canvas}-检验白板-{today}"

    # Step 1: Build source canvas path
    source_canvas_path = _canvas_base_path / f"{request.source_canvas}.canvas"
    if not source_canvas_path.exists():
        # Try without .canvas extension (user might have included it)
        source_canvas_path = _canvas_base_path / request.source_canvas
        if not source_canvas_path.exists():
            logging.error(f"Source canvas not found: {request.source_canvas}")
            return GenerateReviewResponse(
                verification_canvas_name=verification_canvas_name,
                node_count=0,
                mode_used=request.mode  # ✅ Story 24.1
            )

    # Step 2: Read source canvas
    canvas_data = _read_canvas(source_canvas_path)
    if canvas_data is None:
        return GenerateReviewResponse(
            verification_canvas_name=verification_canvas_name,
            node_count=0,
            mode_used=request.mode  # ✅ Story 24.1
        )

    # Step 3: Extract nodes to review (PRD F8 + Story 4.1)
    # ✅ FIXED: Now extracts RED (color="4") + PURPLE (color="3")
    # ✅ Story 24.1: Use mode from request (default: "fresh")
    source_nodes = canvas_data.get("nodes", [])
    review_mode = request.mode  # Now comes from GenerateReviewRequest schema

    nodes_to_review = _extract_review_nodes(
        source_nodes,
        request.node_ids,
        mode=review_mode
    )

    if not nodes_to_review:
        logging.warning(f"No red/purple nodes found in {request.source_canvas} (mode={review_mode})")
        return GenerateReviewResponse(
            verification_canvas_name=verification_canvas_name,
            node_count=0,
            mode_used=review_mode  # ✅ Story 24.1
        )

    # Step 4: Topic Clustering (PRD Story 4.3)
    # ✅ NEW: Group nodes by topic for better organization
    if _services_available:
        clusterer = TopicClusterer()
        question_gen = QuestionGenerator()
        clusters = clusterer.cluster_nodes(nodes_to_review)
    else:
        # Fallback: single cluster
        clusters = {"概念检验": nodes_to_review}
        question_gen = None

    # Step 5: Generate verification canvas structure with clustering
    verification_nodes = []
    verification_edges = []

    node_width = 400
    question_height = 100
    answer_height = 150
    node_padding = 50
    group_padding = 100
    nodes_per_row = 3

    current_y = 0

    for topic, topic_nodes in clusters.items():
        # Calculate group dimensions
        num_rows = (len(topic_nodes) + nodes_per_row - 1) // nodes_per_row
        num_cols = min(len(topic_nodes), nodes_per_row)
        pair_height = question_height + answer_height + 30  # Q + A + gap

        group_width = num_cols * (node_width + node_padding) + node_padding
        group_height = num_rows * (pair_height + node_padding) + node_padding + 60  # +60 for label

        # Create Group node (PRD Story 4.3)
        group_id = _generate_node_id()
        group_node = {
            "id": group_id,
            "type": "group",
            "x": 0,
            "y": current_y,
            "width": group_width,
            "height": group_height,
            "label": f"🎯 {topic}",
        }
        verification_nodes.append(group_node)

        # Create question-answer pairs within group
        for i, source_node in enumerate(topic_nodes):
            col = i % nodes_per_row
            row = i // nodes_per_row

            x = node_padding + col * (node_width + node_padding)
            y = current_y + 60 + node_padding + row * (pair_height + node_padding)

            # Generate question text (PRD Story 4.2)
            original_text = source_node.get("text", "")
            node_color = source_node.get("color", "3")

            if question_gen:
                # Use QuestionGenerator for proper question generation
                questions = question_gen.generate_questions(source_node)
                question_text = questions[0] if questions else f"请解释：{original_text}"
            else:
                # Fallback: simple question format
                # Color codes: "4"=red, "3"=purple (docs/issues/canvas-layout-lessons-learned.md)
                if node_color == "4":  # Red - breakthrough
                    question_text = f"🔴 突破型问题：请用自己的话解释 {original_text}"
                else:  # Purple - verification
                    question_text = f"🟣 检验型问题：请详细描述 {original_text}"

            # Create question node (Cyan color="5")
            question_node_id = _generate_node_id()
            question_node = {
                "id": question_node_id,
                "type": "text",
                "x": x,
                "y": y,
                "width": node_width,
                "height": question_height,
                "text": question_text,
                "color": "5",  # Cyan - question/prompt color
            }
            verification_nodes.append(question_node)

            # Create blank yellow answer node (PRD F8: 预留黄色节点供用户输出)
            answer_node_id = _generate_node_id()
            answer_node = {
                "id": answer_node_id,
                "type": "text",
                "x": x,
                "y": y + question_height + 20,
                "width": node_width,
                "height": answer_height,
                "text": "",  # Blank for user to fill
                "color": "6",  # Yellow - personal understanding area (修复: '6'=Yellow, '3'=Purple)
            }
            verification_nodes.append(answer_node)

            # Create edge connecting question to answer
            edge = {
                "id": _generate_node_id(),
                "fromNode": question_node_id,
                "fromSide": "bottom",
                "toNode": answer_node_id,
                "toSide": "top",
            }
            verification_edges.append(edge)

        # Move to next group position
        current_y += group_height + group_padding

    # Step 6: Create verification canvas data
    verification_canvas_data = {
        "nodes": verification_nodes,
        "edges": verification_edges,
    }

    # Step 7: Save verification canvas
    verification_canvas_path = _canvas_base_path / f"{verification_canvas_name}.canvas"
    success = _write_canvas(verification_canvas_path, verification_canvas_data)

    if not success:
        logging.error(f"Failed to save verification canvas: {verification_canvas_name}")
        return GenerateReviewResponse(
            verification_canvas_name=verification_canvas_name,
            node_count=0,
            mode_used=review_mode  # ✅ Story 24.1: Include mode in response
        )

    # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
    logging.info(
        f"SUCCESS: Generated verification canvas: {verification_canvas_name} "
        f"with {len(nodes_to_review)} concepts in {len(clusters)} topic groups (mode={review_mode})"
    )

    # ✅ Story 24.1: Include mode_used in response (AC5)
    return GenerateReviewResponse(
        verification_canvas_name=verification_canvas_name,
        node_count=len(nodes_to_review),
        mode_used=review_mode
    )


@review_router.put(
    "/record",
    response_model=RecordReviewResponse,
    summary="Record review result",
    operation_id="record_review_result",
)
async def record_review_result(request: RecordReviewRequest) -> RecordReviewResponse:
    """
    Record review result and update next review date using FSRS-4.5 algorithm.

    Story 32.2: FSRS Integration for optimal spaced repetition intervals.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID (maps to concept_id)
    - **rating**: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy) - preferred
    - **score**: Legacy score (0-100) - auto-converted to rating
    - **card_state**: Optional serialized FSRS card JSON for persistence
    - **review_duration**: Optional review time in seconds

    Rating Conversion (Story 32.2 AC-32.2.4):
    - score < 40 → rating 1 (Again/Forgot)
    - score 40-59 → rating 2 (Hard)
    - score 60-84 → rating 3 (Good)
    - score >= 85 → rating 4 (Easy)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1record]
    [Source: docs/stories/32.2.story.md - FSRS Integration]
    """
    from app.dependencies import get_review_service

    # Get ReviewService with FSRS support
    review_service = get_review_service()

    try:
        # Call record_review_result with new FSRS-enabled parameters
        result = await review_service.record_review_result(
            canvas_name=request.canvas_name,
            concept_id=request.node_id,
            rating=request.rating,
            score=request.score,
            card_state=request.card_state,
            review_duration=request.review_duration
        )

        # Build response with FSRS state if available
        fsrs_state = None
        if result.get("fsrs_state"):
            state = result["fsrs_state"]
            fsrs_state = FSRSStateResponse(
                stability=state.get("stability", 0.0),
                difficulty=state.get("difficulty", 5.0),
                state=state.get("state", 0),
                reps=state.get("reps", 0),
                lapses=state.get("lapses", 0)
            )

        return RecordReviewResponse(
            next_review_date=result.get("next_review_date", date.today() + timedelta(days=1)),
            new_interval=result.get("new_interval", 1),
            fsrs_state=fsrs_state,
            card_data=result.get("card_data"),
            algorithm=result.get("algorithm", "fsrs-4.5")
        )

    except Exception as e:
        logging.error(f"Error recording review with FSRS: {e}")
        # Fallback to legacy Ebbinghaus calculation
        score = request.score or 50.0  # Default score if only rating provided
        if request.rating:
            # Convert rating back to approximate score for fallback
            score = {1: 20.0, 2: 50.0, 3: 75.0, 4: 95.0}.get(request.rating, 50.0)

        if score >= 85:
            interval = 30
        elif score >= 60:
            interval = 7
        elif score >= 40:
            interval = 3
        else:
            interval = 1

        return RecordReviewResponse(
            next_review_date=date.today() + timedelta(days=interval),
            new_interval=interval,
            algorithm="ebbinghaus-fallback"
        )

@review_router.get(
    "/progress/multi/{original_canvas_path:path}",
    response_model=MultiReviewProgressResponse,
    summary="Get multi-review trend analysis",
    operation_id="get_multi_review_progress",
    responses={
        404: {"model": ErrorResponse, "description": "No review history"}
    }
)
async def get_multi_review_progress(
    original_canvas_path: str
) -> MultiReviewProgressResponse:
    """
    Get trend analysis for multiple verification canvas sessions.

    Returns:
    - List of all verification canvases for this original canvas
    - Pass rate trend over time
    - Weak concept improvement tracking
    - Overall progress metrics

    [Source: specs/api/review-api.openapi.yml#L346-378]
    [Source: Story 24.4 - Multi-Review Trend Analysis]
    """
    # Import here to avoid circular dependency
    from app.core.exceptions import CanvasNotFoundException
    from app.dependencies import get_review_service

    try:
        review_service = get_review_service()
        result = await review_service.get_multi_review_progress(original_canvas_path)
        return MultiReviewProgressResponse(**result)
    except CanvasNotFoundException as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"无检验历史: {original_canvas_path}"
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# Story 31.4: Verification History Endpoint
# [Source: specs/api/review-api.openapi.yml#/verification/history/{concept}]
# [Source: docs/stories/31.4.story.md#Task-4]
# ═══════════════════════════════════════════════════════════════════════════════

@review_router.get(
    "/verification/history/{concept}",
    response_model=VerificationHistoryResponse,
    summary="Get verification question history",
    operation_id="get_verification_history",
    responses={
        404: {"model": ErrorResponse, "description": "No history found"}
    },
    tags=["verification"]
)
async def get_verification_history(
    concept: str,
    canvas_name: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    group_id: Optional[str] = None
) -> VerificationHistoryResponse:
    """
    Get verification question history for a concept.

    Story 31.4 AC-31.4.3: New endpoint for querying verification question history.
    Story 31.4 AC-31.4.4: Returns question, answer, score, timestamp for each record.

    - **concept**: Concept name to query history for
    - **canvas_name**: Optional filter by canvas name
    - **limit**: Number of items per page (default: 20, max: 100)
    - **offset**: Offset for pagination (default: 0)
    - **group_id**: Optional group ID for multi-subject isolation

    Returns:
    - Total count of history records
    - List of verification history items
    - Pagination metadata

    [Source: specs/api/review-api.openapi.yml#/verification/history/{concept}]
    [Source: docs/stories/31.4.story.md#Task-4]
    """
    from datetime import datetime as dt

    from fastapi import HTTPException

    from app.dependencies import get_graphiti_temporal_client

    # Validate pagination parameters
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be non-negative"
        )

    # Get Graphiti client
    graphiti_client = get_graphiti_temporal_client()

    if not graphiti_client:
        logging.warning("Graphiti client not available for verification history query")
        # Return empty response when Graphiti is unavailable
        return VerificationHistoryResponse(
            concept=concept,
            total_count=0,
            items=[],
            pagination=PaginationInfo(
                limit=limit,
                offset=offset,
                has_more=False
            )
        )

    try:
        # Query verification questions from Graphiti
        # Story 31.4 AC-31.4.1: Use search_verification_questions method
        raw_results = await graphiti_client.search_verification_questions(
            concept=concept,
            canvas_name=canvas_name,
            group_id=group_id,
            limit=limit + 1  # Fetch one extra to check has_more
        )

        # Determine if there are more results
        has_more = len(raw_results) > limit
        results = raw_results[:limit] if has_more else raw_results

        # Convert to response format
        items = []
        for record in results:
            # Parse question_type to enum
            q_type_str = record.get("question_type", "standard")
            try:
                q_type = QuestionType(q_type_str)
            except ValueError:
                q_type = QuestionType.standard

            # Parse timestamp
            asked_at_str = record.get("asked_at")
            if isinstance(asked_at_str, str):
                try:
                    asked_at = dt.fromisoformat(asked_at_str.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    asked_at = dt.now()
            elif isinstance(asked_at_str, dt):
                asked_at = asked_at_str
            else:
                asked_at = dt.now()

            items.append(VerificationHistoryItem(
                question_id=record.get("question_id", ""),
                question_text=record.get("question_text", ""),
                question_type=q_type,
                user_answer=record.get("user_answer"),
                score=record.get("score"),
                canvas_name=record.get("canvas_name", canvas_name or ""),
                asked_at=asked_at
            ))

        return VerificationHistoryResponse(
            concept=concept,
            total_count=len(items),
            items=items,
            pagination=PaginationInfo(
                limit=limit,
                offset=offset,
                has_more=has_more
            )
        )

    except Exception as e:
        logging.error(f"Error querying verification history for '{concept}': {e}")
        # Return empty response on error (graceful degradation)
        return VerificationHistoryResponse(
            concept=concept,
            total_count=0,
            items=[],
            pagination=PaginationInfo(
                limit=limit,
                offset=offset,
                has_more=False
            )
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 32.3: FSRS State Query Endpoint
# [Source: specs/api/review-api.openapi.yml#/review/fsrs-state/{concept_id}]
# [Source: docs/stories/32.3.story.md#Task-1]
# ═══════════════════════════════════════════════════════════════════════════════

@review_router.get(
    "/fsrs-state/{concept_id}",
    response_model=FSRSStateQueryResponse,
    summary="Get FSRS state for a concept",
    operation_id="get_fsrs_state",
    responses={
        200: {"model": FSRSStateQueryResponse, "description": "FSRS state found"},
        404: {"model": ErrorResponse, "description": "Concept not found"}
    },
    tags=["fsrs"]
)
async def get_fsrs_state(concept_id: str) -> FSRSStateQueryResponse:
    """
    Get FSRS card state for a concept.

    Story 32.3 AC-32.3.1: Plugin queries backend for FSRS state before calculating priority.
    Story 32.3 AC-32.3.2: Returns stability, difficulty, state, reps, lapses, retrievability, due.
    Story 32.3 AC-32.3.3: Includes full card_state JSON for plugin-side deserialization.

    - **concept_id**: Concept identifier (node_id from canvas)

    Returns:
    - FSRS state with all algorithm parameters
    - card_state: Serialized FSRS card JSON for local caching
    - found: Boolean indicating if a card exists

    [Source: specs/api/review-api.openapi.yml#/review/fsrs-state/{concept_id}]
    [Source: docs/stories/32.3.story.md#Task-1]
    """
    from app.dependencies import get_review_service

    try:
        review_service = get_review_service()
        result = await review_service.get_fsrs_state(concept_id)

        if not result or not result.get("found"):
            # No card exists for this concept - return empty state
            return FSRSStateQueryResponse(
                concept_id=concept_id,
                fsrs_state=None,
                card_state=None,
                found=False
            )

        # Build FSRSStateResponse with all fields including retrievability and due
        fsrs_state = FSRSStateResponse(
            stability=result.get("stability", 0.0),
            difficulty=result.get("difficulty", 5.0),
            state=result.get("state", 0),
            reps=result.get("reps", 0),
            lapses=result.get("lapses", 0),
            retrievability=result.get("retrievability"),
            due=result.get("due")
        )

        return FSRSStateQueryResponse(
            concept_id=concept_id,
            fsrs_state=fsrs_state,
            card_state=result.get("card_state"),
            found=True
        )

    except Exception as e:
        logging.error(f"Error getting FSRS state for '{concept_id}': {e}")
        # Story 32.3 AC-32.3.5: Graceful degradation - return not found instead of error
        return FSRSStateQueryResponse(
            concept_id=concept_id,
            fsrs_state=None,
            card_state=None,
            found=False
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Story 31.6: Real-time Verification Session Progress Tracking
# [Source: docs/stories/31.6.story.md]
# [Source: specs/api/review-api.openapi.yml#/review/session/{session_id}/progress]
# ═══════════════════════════════════════════════════════════════════════════════

@review_router.get(
    "/session/{session_id}/progress",
    response_model=SessionProgressResponse,
    summary="Get verification session progress",
    operation_id="get_session_progress",
    responses={
        200: {"model": SessionProgressResponse, "description": "Session progress"},
        404: {"model": ErrorResponse, "description": "Session not found"}
    },
    tags=["verification-session"]
)
async def get_session_progress(session_id: str) -> SessionProgressResponse:
    """
    Get real-time progress for a verification session.

    Story 31.6 AC-31.6.1: Frontend displays "已验证 X/Y 个概念" progress bar.
    Story 31.6 AC-31.6.2: Color distribution real-time updates (green/yellow/purple/red).
    Story 31.6 AC-31.6.3: Mastery percentage = green / total * 100%.

    - **session_id**: Unique session identifier

    Returns:
    - Session progress with concept counts, color distribution, and status
    - progress_percentage: Completion rate (0-100)
    - mastery_percentage: Mastery rate (0-100)

    [Source: docs/stories/31.6.story.md#Task-2]
    """
    from app.dependencies import get_verification_service
    from fastapi import HTTPException

    try:
        verification_service = get_verification_service()
        progress = await verification_service.get_progress(session_id)

        if progress is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_id}' not found"
            )

        # Convert VerificationProgress dataclass to Pydantic response
        progress_dict = progress.to_dict()
        return SessionProgressResponse(
            session_id=progress_dict["session_id"],
            canvas_name=progress_dict["canvas_name"],
            total_concepts=progress_dict["total_concepts"],
            completed_concepts=progress_dict["completed_concepts"],
            current_concept=progress_dict["current_concept"],
            current_concept_idx=progress_dict["current_concept_idx"],
            green_count=progress_dict["green_count"],
            yellow_count=progress_dict["yellow_count"],
            purple_count=progress_dict["purple_count"],
            red_count=progress_dict["red_count"],
            status=VerificationStatusEnum(progress_dict["status"]),
            progress_percentage=progress_dict["progress_percentage"],
            mastery_percentage=progress_dict["mastery_percentage"],
            hints_given=progress_dict["hints_given"],
            max_hints=progress_dict["max_hints"],
            started_at=progress.started_at,
            updated_at=progress.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting session progress for '{session_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session progress: {str(e)}"
        )


@review_router.post(
    "/session/{session_id}/pause",
    response_model=SessionPauseResumeResponse,
    summary="Pause verification session",
    operation_id="pause_session",
    responses={
        200: {"model": SessionPauseResumeResponse, "description": "Session paused"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Session cannot be paused"}
    },
    tags=["verification-session"]
)
async def pause_session(session_id: str) -> SessionPauseResumeResponse:
    """
    Pause an active verification session.

    Story 31.6 AC-31.6.4: Support pause/resume session functionality.

    - **session_id**: Session identifier to pause

    Returns:
    - New session status (paused)
    - Operation result message

    [Source: docs/stories/31.6.story.md#Task-3]
    """
    from app.dependencies import get_verification_service
    from fastapi import HTTPException

    try:
        verification_service = get_verification_service()
        success = await verification_service.pause_session(session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session '{session_id}' cannot be paused (not found or not in active state)"
            )

        return SessionPauseResumeResponse(
            session_id=session_id,
            status=VerificationStatusEnum.paused,
            message="Session paused successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error pausing session '{session_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause session: {str(e)}"
        )


@review_router.post(
    "/session/{session_id}/resume",
    response_model=SessionPauseResumeResponse,
    summary="Resume verification session",
    operation_id="resume_session",
    responses={
        200: {"model": SessionPauseResumeResponse, "description": "Session resumed"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        400: {"model": ErrorResponse, "description": "Session cannot be resumed"}
    },
    tags=["verification-session"]
)
async def resume_session(session_id: str) -> SessionPauseResumeResponse:
    """
    Resume a paused verification session.

    Story 31.6 AC-31.6.4: Support pause/resume session functionality.

    - **session_id**: Session identifier to resume

    Returns:
    - New session status (in_progress)
    - Operation result message

    [Source: docs/stories/31.6.story.md#Task-3]
    """
    from app.dependencies import get_verification_service
    from fastapi import HTTPException

    try:
        verification_service = get_verification_service()
        success = await verification_service.resume_session(session_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session '{session_id}' cannot be resumed (not found or not paused)"
            )

        return SessionPauseResumeResponse(
            session_id=session_id,
            status=VerificationStatusEnum.in_progress,
            message="Session resumed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error resuming session '{session_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume session: {str(e)}"
        )
