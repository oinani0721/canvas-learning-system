# Canvas Learning System - Review Router
# Story 15.2: Routing System and APIRouter Configuration
# ✅ Updated: Connected to real EbbinghausReviewScheduler (P0 Task #1)
# ✅ Updated: Implemented real verification canvas generation (P0 Task #7)
"""
Review system router.

Provides 3 endpoints for Ebbinghaus review system operations.
[Source: specs/api/fastapi-backend-api.openapi.yml#/paths/~1api~1v1~1review]
"""

import asyncio
import json
import logging
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Query, status

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
    # EPIC-31: Interactive Verification Session Models
    StartSessionRequest,
    StartSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
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
    logger.warning(f"EbbinghausReviewScheduler not available: {e}")


# Story 38.9 AC3: ReviewService singleton now lives in services layer.
# Import the canonical factory instead of maintaining a duplicate here.
from app.services.review_service import (
    get_review_service as _get_review_service_singleton,
    reset_review_service_singleton as _reset_review_service_singleton,
)


# Code Review H1 Fix: Module-level VerificationService singleton with full DI.
# The old _get_vs_singleton() created VerificationService() with zero args,
# causing all AI scoring, RAG, difficulty adaptation to silently degrade.
_verification_service_instance = None


async def _get_or_create_verification_service():
    """Get or create VerificationService singleton with complete dependency injection.

    Code Review H1 Fix: Replaces broken _get_vs_singleton() that created
    VerificationService() with zero parameters, causing all 8 optional
    dependencies to be None and all AI features to silently degrade to
    mock/default values.

    This function mirrors the DI chain in dependencies.py:get_verification_service()
    but as a persistent singleton (required because VerificationService stores
    active sessions in memory dicts).
    """
    global _verification_service_instance
    if _verification_service_instance is not None:
        return _verification_service_instance

    from app.config import get_settings
    from app.services.verification_service import VerificationService

    settings = get_settings()

    # 1. RAG service (Story 24.5)
    rag_service = None
    try:
        from app.dependencies import get_rag_service
        rag_service = get_rag_service()
    except Exception as e:
        logger.warning(f"RAG service not available for VerificationService: {e}")

    # 2. Cross-canvas service (Story 24.5)
    cross_canvas_service = None
    try:
        from app.dependencies import get_cross_canvas_service
        cross_canvas_service = get_cross_canvas_service()
    except Exception as e:
        logger.warning(f"CrossCanvas service not available: {e}")

    # 3. Textbook context service (Story 24.5 AC4)
    textbook_service = None
    try:
        from app.services.textbook_context_service import (
            TextbookContextService, TextbookContextConfig
        )
        textbook_config = TextbookContextConfig(timeout=3.0)
        textbook_service = TextbookContextService(
            canvas_base_path=settings.canvas_base_path,
            config=textbook_config
        )
    except Exception as e:
        logger.warning(f"TextbookContext service not available: {e}")

    # 4. Graphiti client (Story 31.4 - question deduplication)
    graphiti_client = None
    try:
        from app.dependencies import get_graphiti_temporal_client
        graphiti_client = get_graphiti_temporal_client()
    except Exception as e:
        logger.warning(f"Graphiti client not available for deduplication: {e}")

    # 5. Memory service (Story 31.5 - difficulty adaptation, async)
    memory_service = None
    try:
        from app.services.memory_service import get_memory_service
        memory_service = await get_memory_service()
    except Exception as e:
        logger.warning(f"MemoryService not available for difficulty adaptation: {e}")

    # 6. Agent service (Story 31.1 - AI scoring + question generation)
    agent_service = None
    try:
        from app.dependencies import get_neo4j_client_dep
        from app.clients.gemini_client import GeminiClient
        from app.services.agent_service import AgentService

        gemini_client = None
        if settings.AI_API_KEY:
            gemini_client = GeminiClient(
                api_key=settings.AI_API_KEY,
                model=settings.AI_MODEL_NAME,
                base_url=settings.AI_BASE_URL if settings.AI_BASE_URL else None
            )
        neo4j_client = get_neo4j_client_dep()
        agent_service = AgentService(
            gemini_client=gemini_client,
            neo4j_client=neo4j_client
        )
    except Exception as e:
        logger.warning(f"AgentService not available for AI scoring: {e}")

    # 7. Canvas service (EPIC-36 P0 Fix - concept extraction)
    canvas_service = None
    try:
        from app.services.canvas_service import CanvasService
        canvas_service = CanvasService(canvas_base_path=settings.canvas_base_path)
    except Exception as e:
        logger.warning(f"CanvasService not available for concept extraction: {e}")

    _verification_service_instance = VerificationService(
        rag_service=rag_service,
        cross_canvas_service=cross_canvas_service,
        textbook_context_service=textbook_service,
        graphiti_client=graphiti_client,
        memory_service=memory_service,
        agent_service=agent_service,
        canvas_service=canvas_service,
        canvas_base_path=str(settings.canvas_base_path) if settings.canvas_base_path else None
    )

    logger.info(
        f"VerificationService singleton created with full DI: "
        f"rag={'Y' if rag_service else 'N'}, "
        f"agent={'Y' if agent_service else 'N'}, "
        f"graphiti={'Y' if graphiti_client else 'N'}, "
        f"memory={'Y' if memory_service else 'N'}, "
        f"canvas={'Y' if canvas_service else 'N'}"
    )

    return _verification_service_instance


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
    logger.warning("QuestionGenerator/TopicClusterer not available, using fallback")

# AI-enhanced question generation for verification canvas
try:
    from app.services.agent_service import AgentService, AgentType
    from app.clients.gemini_client import GeminiClient
    from app.core.config import get_settings
    _ai_question_available = True
except ImportError:
    _ai_question_available = False
    logger.info("AgentService not available, canvas uses template questions only")

# Story 31.2+31.5: Difficulty adaptation for one-click canvas generation
try:
    from app.services.verification_service import (
        calculate_full_difficulty_result,
        DifficultyResult,
        DifficultyLevel,
    )
    _difficulty_available = True
except ImportError:
    _difficulty_available = False
    logger.info("Difficulty adaptation not available, canvas uses uniform questions")


async def _get_difficulty_data(
    nodes_to_review: List[Dict],
    source_canvas: str
) -> Optional[Dict[str, "DifficultyResult"]]:
    """
    Query historical scores for all nodes and compute difficulty results.

    Story 31.2+31.5: Parallel query with 5s total timeout, graceful degradation.

    Args:
        nodes_to_review: List of canvas node dicts (must have "id" and "text")
        source_canvas: Source canvas name for score history lookup

    Returns:
        Dict mapping node_id -> DifficultyResult, or None on failure
    """
    if not _difficulty_available:
        return None

    try:
        from app.services.memory_service import get_memory_service
        memory_service = await get_memory_service()

        # H1 fix: Guard against Neo4j not configured (memory_service.neo4j is None)
        if not hasattr(memory_service, 'neo4j') or memory_service.neo4j is None:
            logger.info("Difficulty data skipped: Neo4j not configured (graceful degradation)")
            return None

        async def _query_one(node: Dict) -> tuple:
            """Query score history for a single node."""
            node_id = node.get("id", "")
            if not node_id:
                return (node_id, None)
            try:
                history = await memory_service.get_concept_score_history(
                    concept_id=node_id,
                    canvas_name=source_canvas,
                    limit=5
                )
                if history and history.scores:
                    recent = history.scores[-1]  # M3 fix: scores guaranteed non-empty here
                    result = calculate_full_difficulty_result(history.scores, recent)
                    return (node_id, result)
                return (node_id, None)
            except Exception as e:
                logger.debug(f"Score history query failed for {node_id}: {e}")
                return (node_id, None)

        # Parallel query all nodes with 5s total timeout
        tasks = [_query_one(n) for n in nodes_to_review]
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=5.0
        )

        difficulty_map: Dict[str, "DifficultyResult"] = {}
        for r in results:
            if isinstance(r, Exception):
                # H3 fix: Log exceptions from gather(return_exceptions=True)
                logger.warning(f"Difficulty query task failed: {r}")
            elif isinstance(r, tuple) and len(r) == 2:
                nid, diff = r
                if nid and diff is not None:
                    difficulty_map[nid] = diff

        if difficulty_map:
            logger.info(
                f"Difficulty data retrieved for {len(difficulty_map)}/{len(nodes_to_review)} nodes"
            )
            return difficulty_map

        return None

    except Exception as e:
        logger.warning(f"Difficulty data retrieval failed (graceful degradation): {e}", exc_info=True)
        return None


def _get_difficulty_enhanced_question_text(
    original_text: str,
    node_color: str,
    node_id: str,
    difficulty_map: Optional[Dict[str, "DifficultyResult"]] = None
) -> str:
    """
    Generate difficulty-enhanced question text for fallback (non-AI) questions.

    Story 31.2+31.5: Adapts question template based on difficulty level.

    Args:
        original_text: Original node text content
        node_color: Node color code ("4"=red, "3"=purple)
        node_id: Node ID for difficulty lookup
        difficulty_map: Optional difficulty data map

    Returns:
        Question text string with appropriate difficulty framing
    """
    if difficulty_map and node_id in difficulty_map:
        diff = difficulty_map[node_id]
        forgetting_prefix = ""
        if diff.forgetting_status and diff.forgetting_status.needs_review:
            forgetting_prefix = "⚠️ 检测到遗忘趋势 | "

        # M1 note: EASY = student finds concept easy → challenge with breakthrough question
        # HARD = student struggles → give applied/contextual question for deeper engagement
        if diff.level == DifficultyLevel.EASY:
            return f"{forgetting_prefix}🔴 突破型：请用自己的话解释 {original_text}"
        elif diff.level == DifficultyLevel.HARD:
            return f"{forgetting_prefix}🔵 应用型：请分析 {original_text} 在实际场景中的应用"
        else:  # MEDIUM
            return f"{forgetting_prefix}🟣 验证型：请详细描述 {original_text} 并举例说明"

    # No difficulty data: original color-based fallback
    if node_color == "4":  # Red - breakthrough
        return f"🔴 突破型问题：请用自己的话解释 {original_text}"
    else:  # Purple - verification
        return f"🟣 检验型问题：请详细描述 {original_text}"


async def _generate_ai_questions(
    nodes_to_review: List[Dict],
    difficulty_map: Optional[Dict[str, "DifficultyResult"]] = None
) -> Optional[Dict[str, str]]:
    """
    Generate AI-powered questions for verification canvas using verification-question-agent.

    Makes a single batch Gemini call with all nodes, returns a mapping of
    source node ID -> rich question text. Falls back to None on any failure.

    Args:
        nodes_to_review: List of canvas node dicts
        difficulty_map: Optional difficulty data for each node (Story 31.2+31.5)
    """
    if not _ai_question_available or not nodes_to_review:
        return None

    try:
        import asyncio as asyncio
        settings = get_settings()
        if not settings.AI_API_KEY:
            return None

        gemini_client = GeminiClient(
            api_key=settings.AI_API_KEY,
            model=settings.AI_MODEL_NAME,
            base_url=settings.AI_BASE_URL if settings.AI_BASE_URL else None
        )
        agent_service = AgentService(gemini_client=gemini_client)

        # Build prompt matching verification-question-agent.md input format
        nodes_data = []
        for node in nodes_to_review:
            node_id = node.get("id", "")
            if not node_id:
                continue
            content = node.get("text", "").strip()
            color = node.get("color", "3")
            node_type = "red" if color == "4" else "purple"

            node_entry = {
                "id": node_id,
                "content": content,
                "type": node_type,
                "related_yellow": [],
                "parent_content": ""
            }

            # Story 31.2+31.5: Inject difficulty context for AI question generation
            if difficulty_map and node_id in difficulty_map:
                diff = difficulty_map[node_id]
                node_entry["difficulty_level"] = diff.level.value
                node_entry["question_type_hint"] = diff.question_type.value
                if diff.forgetting_status and diff.forgetting_status.needs_review:
                    node_entry["forgetting_detected"] = True

            nodes_data.append(node_entry)

        if not nodes_data:
            return None

        prompt = json.dumps({"nodes": nodes_data}, ensure_ascii=False, indent=2)

        # Single batch call - all nodes in one request (20s timeout)
        result = await asyncio.wait_for(
            agent_service.call_agent(AgentType.VERIFICATION_QUESTION, prompt),
            timeout=20.0
        )

        if result and result.success and result.data:
            questions = result.data.get("questions", [])
            question_map: Dict[str, str] = {}
            for q in questions:
                src_id = q.get("source_node_id", "")
                text = q.get("question_text", "")
                q_type = q.get("question_type", "")
                guidance = q.get("guidance", "")

                if src_id and text:
                    type_emoji = {
                        "突破型": "🔴", "基础型": "🔴",
                        "检验型": "🟣", "应用型": "🔵", "综合型": "🟢",
                    }.get(q_type, "❓")
                    full_text = f"{type_emoji} {q_type}：{text}"
                    if guidance and guidance.strip():
                        full_text += f"\n\n{guidance}"
                    question_map[src_id] = full_text

            if question_map:
                logger.info(
                    f"AI generated {len(question_map)}/{len(nodes_data)} questions for canvas"
                )
                return question_map

        return None

    except Exception as e:
        logger.warning(f"AI question generation failed for canvas: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# Canvas File Operations (P0 Task #7)
# [Source: Plan - P0 Task #7: Implement real verification canvas generation]
# ═══════════════════════════════════════════════════════════════════════════════

def _read_canvas(canvas_path: Path) -> Optional[Dict[str, Any]]:
    """Read Canvas JSON file and return data."""
    try:
        if not canvas_path.exists():
            logger.error(f"Canvas file not found: {canvas_path}")
            return None
        with open(canvas_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading canvas {canvas_path}: {e}")
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
        logger.error(f"Error writing canvas {canvas_path}: {e}")
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
    logger.info("GET /review/schedule days=%d", days)
    # ✅ Connected to real EbbinghausReviewScheduler (P0 Task #1)
    if not _scheduler_available or _scheduler is None:
        logger.warning("EbbinghausReviewScheduler not available, returning empty schedule")
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
        logger.error(f"Error getting review schedule: {e}")
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
    days: int = Query(7, ge=1, le=365, description="Number of days to look back (1-365)"),
    canvas_path: Optional[str] = None,
    concept_name: Optional[str] = None,
    limit: int = Query(5, ge=1, le=100, description="Maximum records to return (1-100)"),
    show_all: bool = Query(False, description="If true, return all records up to hard cap")
) -> HistoryResponse:
    """
    Get review history with pagination support.

    Story 34.4 AC1: Default display shows most recent 5 records (limit=5).
    Story 34.4 AC2: show_all=True loads complete history.
    Story 34.4 AC3: API supports `limit` and `show_all` parameters.

    - **days**: Number of days to look back (1-365, default 7)
    - **canvas_path**: Filter by canvas file path
    - **concept_name**: Filter by concept name
    - **limit**: Maximum records to return (default: 5, Story 34.4 AC1)
    - **show_all**: If True, ignore limit and return all records (Story 34.4 AC2)

    [Source: specs/api/review-api.openapi.yml#L185-216]
    [Source: docs/stories/34.4.story.md]
    """
    from datetime import date, datetime as dt, timedelta

    logger.info("GET /review/history days=%d limit=%d show_all=%s concept=%s", days, limit, show_all, concept_name)
    # Story 34.8 AC4: days validated by Query(ge=1, le=365) — no hardcoded whitelist

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Story 38.9 AC3: Use canonical singleton from services layer
    review_service = await _get_review_service_singleton()

    try:
        # Story 34.8 AC3: show_all uses hard cap instead of unlimited
        from app.services.review_service import MAX_HISTORY_RECORDS
        effective_limit = MAX_HISTORY_RECORDS if show_all else limit
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
        # Story 34.8 AC3: has_more must reflect real truncation status,
        # even when show_all=True (cap at MAX_HISTORY_RECORDS may truncate)
        has_more = result.get("has_more", False)
        pagination = PaginationInfo(
            limit=effective_limit,
            offset=0,
            has_more=has_more
        )

        # Story 34.8 AC3: total_reviews must reflect real total count
        # (not affected by limit truncation)
        real_total = result.get("total_count", total_reviews)

        return HistoryResponse(
            period=HistoryPeriod(
                start=start_date.isoformat(),
                end=end_date.isoformat()
            ),
            total_reviews=real_total,
            records=records,
            statistics=statistics,
            pagination=pagination
        )

    except Exception as e:
        logger.error(f"Error getting review history: {e}")
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
    logger.info("POST /review/generate source=%s mode=%s node_count=%d", request.source_canvas, request.mode, len(request.node_ids or []))
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
            logger.error(f"Source canvas not found: {request.source_canvas}")
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
        logger.warning(f"No red/purple nodes found in {request.source_canvas} (mode={review_mode})")
        return GenerateReviewResponse(
            verification_canvas_name=verification_canvas_name,
            node_count=0,
            mode_used=review_mode  # ✅ Story 24.1
        )

    # Step 3.5: Query difficulty data for all nodes (Story 31.2+31.5)
    difficulty_map = None
    skipped_mastered_count = 0
    if _difficulty_available:
        difficulty_map = await _get_difficulty_data(nodes_to_review, request.source_canvas)

    # Step 3.6: Filter mastered concepts if requested (Story 31.5)
    if request.skip_mastered and difficulty_map:
        pre_filter_count = len(nodes_to_review)
        nodes_to_review = [
            n for n in nodes_to_review
            if not (n.get("id") in difficulty_map and difficulty_map[n.get("id")].is_mastered)
        ]
        skipped_mastered_count = pre_filter_count - len(nodes_to_review)
        if skipped_mastered_count > 0:
            logger.info(f"Skipped {skipped_mastered_count} mastered concepts")

        if not nodes_to_review:
            logger.info(f"All concepts mastered in {request.source_canvas}, nothing to review")
            return GenerateReviewResponse(
                verification_canvas_name=verification_canvas_name,
                node_count=0,
                mode_used=review_mode,
                skipped_mastered_count=skipped_mastered_count,
                difficulty_adapted=difficulty_map is not None,
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

    # Step 4.5: AI-enhanced question generation (batch call)
    # Try to generate personalized questions via Gemini + verification-question-agent
    # Story 31.2+31.5: Pass difficulty_map for difficulty-aware AI prompts
    ai_questions = None
    if _ai_question_available:
        ai_questions = await _generate_ai_questions(nodes_to_review, difficulty_map)
        if ai_questions:
            logger.info(f"Using AI-generated questions for {len(ai_questions)} nodes")
        else:
            logger.info("AI question generation unavailable, using templates")

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
            # Priority: AI questions > QuestionGenerator templates > basic fallback
            original_text = source_node.get("text", "")
            node_color = source_node.get("color", "3")
            source_id = source_node.get("id", "")

            if ai_questions and source_id and source_id in ai_questions:
                # AI-generated personalized question (highest quality)
                question_text = ai_questions[source_id]
            elif question_gen:
                # Template-based question generation
                questions = question_gen.generate_questions(source_node)
                question_text = questions[0] if questions else f"请解释：{original_text}"
            else:
                # Fallback: difficulty-enhanced or simple question format
                # Story 31.2+31.5: Use difficulty data if available
                question_text = _get_difficulty_enhanced_question_text(
                    original_text, node_color, source_id, difficulty_map
                )

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
        logger.error(f"Failed to save verification canvas: {verification_canvas_name}")
        return GenerateReviewResponse(
            verification_canvas_name=verification_canvas_name,
            node_count=0,
            mode_used=review_mode,
            skipped_mastered_count=skipped_mastered_count,
            difficulty_adapted=difficulty_map is not None,
        )

    # [Story 12.I.4] Removed emoji to fix Windows GBK encoding
    logger.info(
        f"SUCCESS: Generated verification canvas: {verification_canvas_name} "
        f"with {len(nodes_to_review)} concepts in {len(clusters)} topic groups (mode={review_mode})"
    )

    # ✅ Story 24.1: Include mode_used in response (AC5)
    # ✅ Story 31.2+31.5: Include difficulty adaptation metadata
    return GenerateReviewResponse(
        verification_canvas_name=verification_canvas_name,
        node_count=len(nodes_to_review),
        mode_used=review_mode,
        skipped_mastered_count=skipped_mastered_count,
        difficulty_adapted=difficulty_map is not None,
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
    from datetime import date, timedelta

    logger.info("POST /review/record canvas=%s node=%s rating=%s score=%s", request.canvas_name, request.node_id, request.rating, request.score)
    # Story 38.9 AC3: Use canonical singleton from services layer
    review_service = await _get_review_service_singleton()

    try:
        # Call record_review_result with new FSRS-enabled parameters
        # EPIC-32 Fix: review_duration is not a direct parameter of record_review_result,
        # pass it via details dict to avoid TypeError
        details = {}
        if request.review_duration is not None:
            details["review_duration"] = request.review_duration
        result = await review_service.record_review_result(
            canvas_name=request.canvas_name,
            concept_id=request.node_id,
            rating=request.rating,
            score=request.score,
            card_state=request.card_state,
            details=details if details else None
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
        logger.error(f"Error recording review with FSRS: {e}")
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
    logger.info("GET /review/multi-progress canvas=%s", original_canvas_path)
    # Import here to avoid circular dependency
    from app.core.exceptions import CanvasNotFoundException

    try:
        # Story 38.9 AC3: Use canonical singleton from services layer
        review_service = await _get_review_service_singleton()
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
    logger.info("GET /verification/history concept=%s limit=%d offset=%d", concept, limit, offset)
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
        logger.warning("Graphiti client not available for verification history query")
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
        # Story 31.4 AC-31.4.3: Use search_verification_questions method
        # H2 fix: Fetch enough results to cover offset + limit + 1 (for has_more check)
        # H3 fix: Use total fetched count (before slicing) as total_count
        fetch_limit = offset + limit + 1
        raw_results = await graphiti_client.search_verification_questions(
            concept=concept,
            canvas_name=canvas_name,
            group_id=group_id,
            limit=fetch_limit
        )

        # H3 fix: total_count reflects all available results (capped at fetch_limit)
        total_count = len(raw_results)

        # H2 fix: Apply offset slicing, then limit
        offset_results = raw_results[offset:]
        has_more = len(offset_results) > limit
        results = offset_results[:limit] if has_more else offset_results

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
            total_count=total_count,
            items=items,
            pagination=PaginationInfo(
                limit=limit,
                offset=offset,
                has_more=has_more
            )
        )

    except Exception as e:
        logger.error(f"Error querying verification history for '{concept}': {e}")
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
    logger.info("GET /review/fsrs-state concept_id=%s", concept_id)
    # Story 38.9 AC3: Use canonical singleton from services layer
    try:
        review_service = await _get_review_service_singleton()
        result = await review_service.get_fsrs_state(concept_id)

        if not result or not result.get("found"):
            # No card exists for this concept - return empty state with reason
            return FSRSStateQueryResponse(
                concept_id=concept_id,
                fsrs_state=None,
                card_state=None,
                found=False,
                reason=result.get("reason") if result else "unknown"
            )

        # Build FSRSStateResponse with all fields including retrievability and due
        fsrs_state = FSRSStateResponse(
            stability=result.get("stability", 0.0),
            difficulty=result.get("difficulty", 5.0),
            state=result.get("state", 0),
            reps=result.get("reps", 0),
            lapses=result.get("lapses", 0),
            retrievability=result.get("retrievability"),
            due=result.get("due"),
            last_review=result.get("last_review")
        )

        return FSRSStateQueryResponse(
            concept_id=concept_id,
            fsrs_state=fsrs_state,
            card_state=result.get("card_state"),
            found=True
        )

    except Exception as e:
        logger.error(f"Error getting FSRS state for '{concept_id}': {e}")
        # Story 32.3 AC-32.3.5: Graceful degradation - return not found instead of error
        return FSRSStateQueryResponse(
            concept_id=concept_id,
            fsrs_state=None,
            card_state=None,
            found=False,
            reason=f"error: {e}"
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
    logger.info("GET /session/%s/progress", session_id)
    from fastapi import HTTPException

    try:
        # H1 Fix: Use properly-injected singleton instead of zero-param _get_vs_singleton()
        verification_service = await _get_or_create_verification_service()
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
        logger.error(f"Error getting session progress for '{session_id}': {e}")
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
    logger.info("POST /session/%s/pause", session_id)
    from fastapi import HTTPException

    try:
        # H1 Fix: Use properly-injected singleton
        verification_service = await _get_or_create_verification_service()
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
        logger.error(f"Error pausing session '{session_id}': {e}")
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
    logger.info("POST /session/%s/resume", session_id)
    from fastapi import HTTPException

    try:
        # H1 Fix: Use properly-injected singleton
        verification_service = await _get_or_create_verification_service()
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
        logger.error(f"Error resuming session '{session_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume session: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EPIC-31: Interactive Verification Session Endpoints
# Bridges VerificationService.start_session() and process_answer() to HTTP
# ═══════════════════════════════════════════════════════════════════════════════

@review_router.post(
    "/session/start",
    response_model=StartSessionResponse,
    summary="Start interactive verification session",
    operation_id="start_verification_session",
    responses={
        200: {"model": StartSessionResponse, "description": "Session started"},
        404: {"model": ErrorResponse, "description": "Canvas not found"},
        504: {"model": ErrorResponse, "description": "AI timeout"},
    },
    tags=["verification-session"]
)
async def start_verification_session(
    request: StartSessionRequest,
) -> StartSessionResponse:
    """
    Start an interactive verification session for a canvas.

    EPIC-31: Calls VerificationService.start_session() which reads the canvas,
    extracts red/purple concepts, and generates the first AI question.

    - **canvas_name**: Source canvas name (without .canvas extension)
    - **node_ids**: Optional specific node IDs to verify
    - **include_mastered**: Whether to include already-mastered concepts (default: true)

    Returns session_id and first_question for the frontend modal.
    """
    logger.info("POST /verification/start canvas=%s node_ids=%s", request.canvas_name, request.node_ids)
    from fastapi import HTTPException

    try:
        # H1 Fix: Use properly-injected singleton
        verification_service = await _get_or_create_verification_service()

        # Build canvas_path from canvas_name + _canvas_base_path
        canvas_path = str(_canvas_base_path / f"{request.canvas_name}.canvas")

        result = await verification_service.start_session(
            canvas_name=request.canvas_name,
            node_ids=request.node_ids,
            canvas_path=canvas_path,
            include_mastered=request.include_mastered,
        )

        if result["total_concepts"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No verifiable concepts found in canvas '{request.canvas_name}'"
            )

        return StartSessionResponse(
            session_id=result["session_id"],
            total_concepts=result["total_concepts"],
            first_question=result["first_question"],
            current_concept=result.get("current_concept", ""),
            status=VerificationStatusEnum(result.get("status", "in_progress")),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI question generation timed out"
        )
    except Exception as e:
        logger.error(f"Error starting verification session: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start session: {str(e)}"
        )


@review_router.post(
    "/session/{session_id}/answer",
    response_model=SubmitAnswerResponse,
    summary="Submit answer for current concept",
    operation_id="submit_verification_answer",
    responses={
        200: {"model": SubmitAnswerResponse, "description": "Answer evaluated"},
        404: {"model": ErrorResponse, "description": "Session not found"},
        504: {"model": ErrorResponse, "description": "AI scoring timeout"},
    },
    tags=["verification-session"]
)
async def submit_verification_answer(
    session_id: str,
    request: SubmitAnswerRequest,
) -> SubmitAnswerResponse:
    """
    Submit an answer for the current concept in an interactive verification session.

    EPIC-31: Calls VerificationService.process_answer() which evaluates the answer
    via scoring-agent and returns quality, score, and the next action (hint/next/complete).

    - **session_id**: Active session identifier
    - **user_answer**: User's answer text

    Returns scoring result and updated progress.
    """
    logger.info("POST /session/%s/answer len=%d", session_id, len(request.user_answer))
    from fastapi import HTTPException

    try:
        # H1 Fix: Use properly-injected singleton
        verification_service = await _get_or_create_verification_service()

        result = await verification_service.process_answer(
            session_id=session_id,
            user_answer=request.user_answer,
        )

        # Convert the progress dict from dataclass to Pydantic model
        progress_data = result["progress"]
        progress_response = SessionProgressResponse(
            session_id=progress_data["session_id"],
            canvas_name=progress_data["canvas_name"],
            total_concepts=progress_data["total_concepts"],
            completed_concepts=progress_data["completed_concepts"],
            current_concept=progress_data["current_concept"],
            current_concept_idx=progress_data["current_concept_idx"],
            green_count=progress_data["green_count"],
            yellow_count=progress_data["yellow_count"],
            purple_count=progress_data["purple_count"],
            red_count=progress_data["red_count"],
            status=VerificationStatusEnum(progress_data["status"]),
            progress_percentage=progress_data["progress_percentage"],
            mastery_percentage=progress_data["mastery_percentage"],
            hints_given=progress_data["hints_given"],
            max_hints=progress_data["max_hints"],
            started_at=progress_data["started_at"],
            updated_at=progress_data["updated_at"],
        )

        return SubmitAnswerResponse(
            quality=result["quality"],
            score=result["score"],
            degraded=result.get("degraded", False),
            degraded_reason=result.get("degraded_reason"),
            degraded_warning=result.get("degraded_warning"),
            action=result["action"],
            hint=result.get("hint"),
            next_question=result.get("next_question"),
            current_concept=result["current_concept"],
            progress=progress_response,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI scoring timed out"
        )
    except Exception as e:
        logger.error(f"Error processing answer for session '{session_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )
