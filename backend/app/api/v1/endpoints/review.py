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
    GenerateReviewRequest,
    GenerateReviewResponse,
    MultiReviewProgressResponse,
    RecordReviewRequest,
    RecordReviewResponse,
    ReviewItem,
    ReviewScheduleResponse,
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

    PRD Requirements:
    - 红色(color="1"): 不理解的内容 → 突破型问题
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

    # PRD F8: Extract RED (color="1") and PURPLE (color="3") nodes
    # ✅ FIXED: Previously extracted GREEN (color="4") - WRONG
    target_colors = {"1", "3"}  # Red=1, Purple=3

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
        red_nodes = [n for n in all_target_nodes if n.get("color") == "1"]
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
    # ✅ FIXED: Now extracts RED (color="1") + PURPLE (color="3") instead of GREEN
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
                if node_color == "1":  # Red - breakthrough
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
                "color": "3",  # Yellow - personal understanding area
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

    logging.info(
        f"✅ Generated verification canvas: {verification_canvas_name} "
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
    Record review result and update next review date.

    - **canvas_name**: Canvas file name
    - **node_id**: Node ID
    - **score**: Review score (0-40)

    [Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review~1record]
    """
    # ✅ Connected to real EbbinghausReviewScheduler (P0 Task #1)
    if _scheduler_available and _scheduler is not None:
        try:
            # Convert score to scheduler format (0-40 -> 0-5 rating)
            rating = min(5, max(1, int(request.score / 8) + 1))
            confidence = min(1.0, request.score / 40.0)

            # Try to record via scheduler
            success = _scheduler.complete_review(
                schedule_id=f"{request.canvas_name}_{request.node_id}",
                score=rating,
                confidence=confidence,
                time_minutes=5,  # Default review time
                notes=f"Recorded via API, original score: {request.score}"
            )
            if success:
                logging.info(f"Review recorded for {request.canvas_name}/{request.node_id}")
        except Exception as e:
            logging.warning(f"Could not record via scheduler: {e}")

    # Calculate next review based on score (Ebbinghaus curve)
    if request.score >= 32:
        interval = 30  # Good understanding -> 30 days
    elif request.score >= 24:
        interval = 7  # Partial understanding -> 7 days
    elif request.score >= 16:
        interval = 3  # Moderate understanding -> 3 days
    else:
        interval = 1  # Poor understanding -> 1 day

    return RecordReviewResponse(
        next_review_date=date.today() + timedelta(days=interval),
        new_interval=interval,
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
