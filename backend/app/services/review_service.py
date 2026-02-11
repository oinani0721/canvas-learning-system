# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Review Service - Business logic for verification canvas and review operations.

This service provides async methods for review scheduling and
verification canvas generation, implementing FSRS (Free Spaced Repetition Scheduler)
algorithm for scientifically-optimized, personalized review intervals.

Story 32.2: Migrated from Ebbinghaus fixed intervals to FSRS-4.5 dynamic scheduling.
[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
[Source: docs/stories/32.2.story.md]

# ═══════════════════════════════════════════════════════════════════════════════
# FSRS MIGRATION DOCUMENTATION (Story 32.2 AC-32.2.5)
# ═══════════════════════════════════════════════════════════════════════════════
#
# OVERVIEW:
# This service was migrated from fixed Ebbinghaus intervals to FSRS-4.5 algorithm
# which provides personalized, adaptive spaced repetition scheduling.
#
# KEY CHANGES:
# 1. EbbinghausReviewScheduler → FSRSManager
# 2. Fixed intervals (1, 3, 7, 30 days) → Dynamic intervals based on:
#    - Memory stability (how well the card is remembered)
#    - Card difficulty (1-10 scale)
#    - Review history (reps, lapses)
#    - Desired retention rate (default: 90%)
#
# BACKWARD COMPATIBILITY (AC-32.2.4):
# - score (0-100) is still accepted and auto-converted to FSRS rating (1-4)
# - Conversion logic:
#   * score < 40  → rating 1 (Again/Forgot) - needs immediate relearning
#   * score 40-59 → rating 2 (Hard) - recalled with significant difficulty
#   * score 60-84 → rating 3 (Good) - recalled with some effort
#   * score >= 85 → rating 4 (Easy) - recalled effortlessly
#
# FSRS RATINGS (AC-32.2.2):
# - 1 (Again): Completely forgot, reset to learning state
# - 2 (Hard): Recalled with significant difficulty, shorter interval
# - 3 (Good): Recalled with acceptable effort, optimal interval
# - 4 (Easy): Recalled effortlessly, longer interval + lower difficulty
#
# CARD STATE PERSISTENCE:
# Card states are persisted via:
# 1. In-memory cache (_card_states dict) for fast access during session
# 2. Graphiti knowledge graph for long-term storage (optional)
# 3. API response card_data field for client-side caching
#
# MIGRATION STEPS FOR EXISTING DATA:
# 1. Existing review history is preserved (no data deletion required)
# 2. New cards start as "New" state with default parameters
# 3. First review establishes initial FSRS parameters
# 4. Subsequent reviews use FSRS algorithm for interval calculation
#
# FALLBACK BEHAVIOR:
# If FSRS is unavailable (import error), the service falls back to
# legacy Ebbinghaus fixed intervals for graceful degradation.
#
# ═══════════════════════════════════════════════════════════════════════════════
"""
import asyncio
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path as _Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.exceptions import CanvasNotFoundException, TaskNotFoundError
from app.services.weight_calculator import ConceptWeightData, WeightCalculator

# Story 32.2 AC-32.2.1: Import FSRSManager for FSRS-4.5 algorithm
# [Source: src/memory/temporal/fsrs_manager.py]
try:
    import sys
    from pathlib import Path
    _project_root = Path(__file__).parent.parent.parent.parent
    _src_path = _project_root / "src"
    if str(_src_path) not in sys.path:
        sys.path.insert(0, str(_src_path))

    from memory.temporal.fsrs_manager import FSRSManager, get_rating_from_score, CardState
    FSRS_AVAILABLE = True
except ImportError:
    FSRS_AVAILABLE = False
    FSRSManager = None
    get_rating_from_score = None
    CardState = None

# Story 38.3 AC-3 Code Review M2 Fix: Module-level runtime FSRS status.
# FSRS_AVAILABLE = library importable (compile-time).
# FSRS_RUNTIME_OK = FSRSManager actually initialized (runtime). None = not yet attempted.
FSRS_RUNTIME_OK: Optional[bool] = None

# P0-2: Card state persistence file path (matches learning_memories.json pattern)
_CARD_STATES_FILE = _Path(__file__).parent.parent.parent / "data" / "fsrs_card_states.json"

# H2 fix: Module-level asyncio.Lock for concurrent card_states write protection
_card_states_lock = asyncio.Lock()

# Story 34.8 AC3: Hard cap for show_all=True to prevent memory overflow
MAX_HISTORY_RECORDS = 1000

if TYPE_CHECKING:
    from app.services.background_task_manager import BackgroundTaskManager
    from app.services.canvas_service import CanvasService

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """复习状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ReviewProgress:
    """
    复习进度数据类
    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """
    task_id: str
    canvas_name: str
    total_nodes: int = 0
    reviewed_nodes: int = 0
    green_nodes: int = 0
    purple_nodes: int = 0
    red_nodes: int = 0
    status: ReviewStatus = ReviewStatus.PENDING
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """计算复习进度百分比"""
        if self.total_nodes == 0:
            return self.progress * 100
        return (self.reviewed_nodes / self.total_nodes) * 100

    @property
    def mastery_percentage(self) -> float:
        """计算掌握程度百分比 (绿色节点占比)"""
        if self.total_nodes == 0:
            return 0.0
        return (self.green_nodes / self.total_nodes) * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "canvas_name": self.canvas_name,
            "total_nodes": self.total_nodes,
            "reviewed_nodes": self.reviewed_nodes,
            "green_nodes": self.green_nodes,
            "purple_nodes": self.purple_nodes,
            "red_nodes": self.red_nodes,
            "status": self.status.value if isinstance(self.status, ReviewStatus) else str(self.status),
            "progress": self.progress,
            "progress_percentage": self.progress_percentage,
            "mastery_percentage": self.mastery_percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


def create_fsrs_manager(settings=None) -> Optional[Any]:
    """
    Unified FSRSManager factory. Used by both DI and singleton paths.

    Story 32.8 AC-32.8.3 + AC-32.8.4: Single creation path with USE_FSRS check.

    Args:
        settings: Application settings. If None, loads from get_settings().

    Returns:
        FSRSManager instance or None if FSRS is disabled/unavailable.
    """
    if settings is None:
        try:
            from app.config import get_settings
            settings = get_settings()
        except (ImportError, RuntimeError) as e:
            logger.warning(f"Cannot load settings for FSRSManager: {e}")
            return None

    if not settings.USE_FSRS:
        logger.info("FSRS disabled via USE_FSRS=False")
        return None

    if not FSRS_AVAILABLE or FSRSManager is None:
        logger.warning("FSRS not available (py-fsrs not installed)")
        return None

    try:
        retention = settings.FSRS_DESIRED_RETENTION
        mgr = FSRSManager(desired_retention=retention)
        logger.info(f"FSRSManager created (desired_retention={retention})")
        return mgr
    except (TypeError, ValueError, RuntimeError) as e:
        logger.warning(f"FSRSManager creation failed: {e}")
        return None


class ReviewService:
    """
    Review and verification canvas business logic service.

    Provides async methods for:
    - Generating verification canvases
    - Scheduling reviews based on Ebbinghaus curve
    - Tracking review progress

    [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
    """

    def __init__(
        self,
        canvas_service: "CanvasService",
        task_manager: "BackgroundTaskManager",
        graphiti_client: Optional[Any] = None,
        fsrs_manager: Optional[Any] = None
    ):
        """
        Initialize ReviewService.

        Args:
            canvas_service: CanvasService instance for canvas operations
            task_manager: BackgroundTaskManager instance for async tasks
            graphiti_client: Optional GraphitiEdgeClient for history tracking
            fsrs_manager: Optional FSRSManager for FSRS-4.5 scheduling (Story 32.2)

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: Story 24.1 - Graphiti Integration]
        [Source: Story 32.2 - FSRS Integration]
        """
        self.canvas_service = canvas_service
        self.task_manager = task_manager
        self.graphiti_client = graphiti_client

        # Story 32.2 AC-32.2.1: Initialize FSRSManager with configurable desired_retention
        # Story 32.8 AC-32.8.3: USE_FSRS=False skips FSRSManager initialization
        # Story 38.3 AC-3: Enhanced init logging for FSRS status
        self._fsrs_init_ok = False
        self._fsrs_init_reason: Optional[str] = None
        global FSRS_RUNTIME_OK
        if fsrs_manager is not None:
            self._fsrs_manager = fsrs_manager
            self._fsrs_init_ok = True
            FSRS_RUNTIME_OK = True
            logger.info("FSRS manager initialized successfully")
        else:
            # Story 32.8: Auto-create via unified factory (checks USE_FSRS internally)
            auto_mgr = create_fsrs_manager()
            if auto_mgr is not None:
                self._fsrs_manager = auto_mgr
                self._fsrs_init_ok = True
                FSRS_RUNTIME_OK = True
                logger.info("FSRS manager auto-created via factory")
            else:
                self._fsrs_manager = None
                self._fsrs_init_reason = "FSRS disabled or unavailable"
                FSRS_RUNTIME_OK = False
                logger.warning(f"FSRS manager not initialized: {self._fsrs_init_reason}")

        self._initialized = True
        self._task_canvas_map: Dict[str, str] = {}  # Maps task_id to canvas_name
        # Story 32.2 + P0-2: Card state storage with file persistence
        self._card_states: Dict[str, str] = self._load_card_states()
        # Story 32.10 AC-3: Track fire-and-forget persistence failures
        self._auto_persist_failures: int = 0
        logger.debug("ReviewService initialized")

    @staticmethod
    def _load_card_states() -> Dict[str, str]:
        """P0-2: Load card states from persistent JSON file on startup."""
        try:
            if _CARD_STATES_FILE.exists():
                data = _CARD_STATES_FILE.read_text(encoding="utf-8")
                loaded = json.loads(data)
                if isinstance(loaded, dict):
                    logger.info(f"Loaded {len(loaded)} FSRS card states from {_CARD_STATES_FILE}")
                    return loaded
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to load FSRS card states: {e}")
        return {}

    async def _save_card_states(self) -> None:
        """P0-2: Persist card states to JSON file with concurrency protection.

        H2 fix: Uses asyncio.Lock to prevent concurrent writes and atomic
        write (temp file + rename) to prevent file corruption.
        """
        async with _card_states_lock:
            try:
                _CARD_STATES_FILE.parent.mkdir(parents=True, exist_ok=True)
                data = json.dumps(self._card_states, ensure_ascii=False, indent=2)
                # Atomic write: write to temp file then rename
                tmp_file = _CARD_STATES_FILE.with_suffix(".json.tmp")
                await asyncio.to_thread(tmp_file.write_text, data, "utf-8")
                await asyncio.to_thread(tmp_file.replace, _CARD_STATES_FILE)
                logger.debug(f"Saved {len(self._card_states)} FSRS card states to {_CARD_STATES_FILE}")
            except (OSError, TypeError) as e:
                logger.warning(f"Failed to save FSRS card states: {e}")

    def _extract_question_from_node(self, node: Dict[str, Any]) -> str:
        """
        Extract a question from a node's text content.

        If the text contains a colon, treat the part before as the topic
        and generate a question about it.

        Args:
            node: Node dict with 'text' field

        Returns:
            Generated question string
        """
        text = node.get("text", "")
        if "：" in text:
            # Chinese colon - extract topic
            topic = text.split("：")[0]
            return f"请解释{topic}的概念和含义？"
        elif ":" in text:
            # English colon - extract topic
            topic = text.split(":")[0]
            return f"请解释{topic}的概念和含义？"
        else:
            # No colon - ask about the whole text
            return f"请解释{text}的概念和含义？"

    async def generate_review_canvas(
        self,
        canvas_name: str,
        node_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a verification canvas asynchronously.

        Returns immediately with task_id, actual generation happens in background.

        Args:
            canvas_name: Source canvas name
            node_ids: Optional list of specific node IDs to include

        Returns:
            Dict with task_id and status

        Raises:
            CanvasNotFoundException: If source canvas doesn't exist
        """
        # Check if canvas exists
        if not await self.canvas_service.canvas_exists(canvas_name):
            raise CanvasNotFoundException(f"Canvas not found: {canvas_name}")

        # Create background task
        async def _generate():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
            return {
                "name": f"{canvas_name}-检验白板-{timestamp}",
                "source_canvas": canvas_name,
                "nodes": [],
                "edges": [],
            }

        task_id = await self.task_manager.create_task(
            "review_generation",
            _generate,
            metadata={"canvas_name": canvas_name}
        )

        self._task_canvas_map[task_id] = canvas_name

        return {
            "task_id": task_id,
            "status": "processing",
            "message": f"Generating verification canvas for {canvas_name}",
        }

    async def get_progress(self, task_id: str) -> ReviewProgress:
        """
        Get progress of a review generation task.

        Args:
            task_id: Task ID from generate_review_canvas

        Returns:
            ReviewProgress object

        Raises:
            TaskNotFoundError: If task doesn't exist
        """
        task_info = self.task_manager.get_task_status(task_id)
        canvas_name = self._task_canvas_map.get(task_id, "unknown")

        # Map TaskStatus to ReviewStatus
        from app.services.background_task_manager import TaskStatus
        status_map = {
            TaskStatus.PENDING: ReviewStatus.PENDING,
            TaskStatus.RUNNING: ReviewStatus.RUNNING,
            TaskStatus.COMPLETED: ReviewStatus.COMPLETED,
            TaskStatus.FAILED: ReviewStatus.FAILED,
            TaskStatus.CANCELLED: ReviewStatus.CANCELLED,
        }

        return ReviewProgress(
            task_id=task_id,
            canvas_name=canvas_name,
            status=status_map.get(task_info.status, ReviewStatus.PENDING),
            progress=task_info.progress,
            error=task_info.error,
        )

    async def get_progress_dict(self, task_id: str) -> Dict[str, Any]:
        """
        Get progress as a dictionary.

        Args:
            task_id: Task ID

        Returns:
            Progress dictionary
        """
        progress = await self.get_progress(task_id)
        return progress.to_dict()

    async def cancel_generation(self, task_id: str) -> bool:
        """
        Cancel a running generation task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled, False if already completed
        """
        try:
            return await self.task_manager.cancel_task(task_id)
        except TaskNotFoundError:
            return False

    async def list_tasks(
        self,
        canvas_name: Optional[str] = None,
        status: Optional[ReviewStatus] = None
    ) -> List[ReviewProgress]:
        """
        List review generation tasks.

        Args:
            canvas_name: Optional filter by canvas name
            status: Optional filter by status

        Returns:
            List of ReviewProgress objects
        """
        from app.services.background_task_manager import TaskStatus

        # Get all review tasks from task manager
        tasks = self.task_manager.list_tasks(task_type="review_generation")

        results = []
        for task_info in tasks:
            task_canvas = self._task_canvas_map.get(task_info.task_id, "unknown")

            # Filter by canvas_name if specified
            if canvas_name and task_canvas != canvas_name:
                continue

            # Map TaskStatus to ReviewStatus
            status_map = {
                TaskStatus.PENDING: ReviewStatus.PENDING,
                TaskStatus.RUNNING: ReviewStatus.RUNNING,
                TaskStatus.COMPLETED: ReviewStatus.COMPLETED,
                TaskStatus.FAILED: ReviewStatus.FAILED,
                TaskStatus.CANCELLED: ReviewStatus.CANCELLED,
            }
            review_status = status_map.get(task_info.status, ReviewStatus.PENDING)

            # Filter by status if specified
            if status and review_status != status:
                continue

            results.append(ReviewProgress(
                task_id=task_info.task_id,
                canvas_name=task_canvas,
                status=review_status,
                progress=task_info.progress,
                error=task_info.error,
            ))

        return results

    async def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """
        Get list of pending review items.

        Returns:
            List of review items with due dates and canvas info

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug("Getting pending reviews")
        # Stub implementation
        return []

    async def generate_verification_canvas(
        self,
        source_canvas_name: str,
        mode: str = "fresh",
        weak_weight: float = 0.7,
        mastered_weight: float = 0.3,
        include_colors: Optional[List[str]] = None,
        question_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a verification canvas with mode support.

        ✅ Verified from Story 24.1 Dev Notes (lines 180-220)

        Args:
            source_canvas_name: Name of source canvas to create verification from
            mode: "fresh" for blind test, "targeted" for weakness-focused
            weak_weight: Weight for weak concepts (targeted mode only)
            mastered_weight: Weight for mastered concepts (targeted mode only)
            include_colors: Optional color filter for node selection
            question_count: Optional limit on question count

        Returns:
            Generated verification canvas data with mode metadata

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: Story 24.1 - Mode Support Implementation]
        """
        logger.debug(
            f"Generating verification canvas from: {source_canvas_name} "
            f"(mode={mode}, weak_weight={weak_weight}, mastered_weight={mastered_weight})"
        )

        # Get all eligible concepts from canvas
        if include_colors is None:
            include_colors = ["3", "4"]  # Default: purple and red

        # Load canvas data to get nodes
        canvas_data = await self.canvas_service.get_canvas(source_canvas_name)
        all_nodes = canvas_data.get("nodes", [])

        # Filter by colors
        eligible_nodes = [
            node for node in all_nodes
            if node.get("type") == "text" and node.get("color") in include_colors
        ]

        weak_concepts_data = []
        weight_config = {"weak_weight": weak_weight, "mastered_weight": mastered_weight, "applied": False}
        fallback_used = False  # AC2 of Story 24.6: Track fallback usage

        if mode == "targeted":
            # Query Graphiti for review history (Story 24.3)
            review_history = await self._query_review_history_from_graphiti(source_canvas_name)

            # AC2: Detect fallback scenario (Graphiti unavailable or no history)
            if not review_history:
                fallback_used = True
                logger.warning(
                    f"Targeted mode fallback: No Graphiti history for {source_canvas_name}, "
                    "using equal probability selection for all eligible concepts"
                )

            # Prepare concepts list from eligible nodes
            concepts = [
                {"id": node.get("id", ""), "name": node.get("text", "")}
                for node in eligible_nodes
            ]

            # Calculate weakness scores using WeightCalculator (Story 24.3)
            calculator = WeightCalculator()
            weight_data = await calculator.calculate_weakness_scores(
                concepts,
                review_history
            )

            # Apply weighted selection (Story 24.3)
            target_count = question_count or len(eligible_nodes)
            selected_weight_data = await self._apply_weighted_selection(
                weight_data,
                target_count,
                weak_weight,
                mastered_weight
            )

            # Convert back to node objects for canvas generation
            selected_ids = {c.concept_id for c in selected_weight_data}
            selected_concepts = [
                node for node in eligible_nodes
                if node.get("id", "") in selected_ids
            ]

            # Prepare weak_concepts for response (AC5)
            weak_concepts_data = [
                {
                    "concept_name": c.concept_name,
                    "weakness_score": c.weakness_score,
                    "failure_count": c.failure_count,
                    "avg_rating": c.avg_rating
                }
                for c in weight_data if c.category == "weak"
            ]

            weight_config["applied"] = True

            logger.info(
                f"Targeted mode: selected {len(selected_concepts)} concepts using weighted algorithm "
                f"({sum(1 for c in selected_weight_data if c.category == 'weak')} weak, "
                f"{sum(1 for c in selected_weight_data if c.category == 'mastered')} mastered)"
            )
        else:
            # Fresh mode: equal probability selection from all eligible nodes
            selected_concepts = eligible_nodes
            logger.info(f"Fresh mode: selected {len(selected_concepts)} concepts")

        # Apply question_count limit if specified
        if question_count and len(selected_concepts) > question_count:
            selected_concepts = random.sample(selected_concepts, question_count)

        # Generate verification canvas (simplified stub - actual generation logic elsewhere)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        review_canvas_name = f"{source_canvas_name}-检验白板-{timestamp}"

        # Store relationship in Graphiti
        await self._store_review_relationship(
            source_canvas_name,
            review_canvas_name,
            mode
        )

        result = {
            "review_canvas_name": review_canvas_name,
            "source_canvas_name": source_canvas_name,
            "question_count": len(selected_concepts),
            "mode_used": mode,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "weak_concepts": weak_concepts_data,  # AC5: Enhanced response
            "weight_config": weight_config,  # AC5: Weight configuration
            "fallback_used": fallback_used  # AC2 of Story 24.6: Indicate if fallback was triggered
        }

        logger.info(
            f"Generated verification canvas: {review_canvas_name} "
            f"with {len(selected_concepts)} questions (mode={mode})"
        )

        return result

    async def schedule_review(
        self,
        canvas_name: str,
        concept_id: str = "",
        trigger_point: int = 1,
        card_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule a review using FSRS algorithm (Story 32.2).

        Story 32.2 AC-32.2.3: FSRS calculates dynamic intervals based on
        card state (stability, difficulty) rather than fixed Ebbinghaus intervals.

        Args:
            canvas_name: Canvas to schedule review for
            concept_id: Concept identifier for card tracking
            trigger_point: Legacy parameter (maintained for backward compatibility)
            card_state: Optional serialized FSRS card JSON from previous review

        Returns:
            Review schedule with FSRS-calculated due date and card state

        Migration Path (AC-32.2.5):
        - If card_state is None: Creates new FSRS card (first review)
        - If card_state exists: Deserializes and uses existing card state
        - Existing Ebbinghaus records: Treated as new cards on first FSRS review

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: Story 32.2 - FSRS Integration]
        """
        logger.debug(f"Scheduling FSRS review for {canvas_name}/{concept_id}")

        # Story 32.2: Use FSRS for scheduling if available
        if self._fsrs_manager is not None:
            try:
                # Load or create card (AC-32.2.4 backward compatibility)
                if card_state:
                    card = self._fsrs_manager.deserialize_card(card_state)
                    logger.debug(f"Loaded existing FSRS card for {concept_id}")
                else:
                    # Check in-memory cache
                    cached_state = self._card_states.get(concept_id)
                    if cached_state:
                        card = self._fsrs_manager.deserialize_card(cached_state)
                        logger.debug(f"Loaded cached FSRS card for {concept_id}")
                    else:
                        # New card - immediately due for first review
                        card = self._fsrs_manager.create_card()
                        logger.info(f"Created new FSRS card for {concept_id}")

                # Get due date from card
                due_date = self._fsrs_manager.get_due_date(card)
                retrievability = self._fsrs_manager.get_retrievability(card)

                # Calculate interval in days from now
                if due_date:
                    interval_days = max(0, (due_date - datetime.now(due_date.tzinfo)).days)
                else:
                    interval_days = 0  # New card, due immediately

                return {
                    "canvas_name": canvas_name,
                    "concept_id": concept_id,
                    "scheduled_date": due_date.isoformat() if due_date else (datetime.now(timezone.utc) + timedelta(days=interval_days)).isoformat(),
                    "interval_days": interval_days,
                    "retrievability": retrievability,
                    "fsrs_state": {
                        "stability": getattr(card, "stability", 0.0),
                        "difficulty": getattr(card, "difficulty", 0.0),
                        "state": int(getattr(card, "state", 0).value) if hasattr(getattr(card, "state", 0), "value") else int(getattr(card, "state", 0)),
                        "reps": getattr(card, "reps", 0),
                        "lapses": getattr(card, "lapses", 0)
                    },
                    "card_data": self._fsrs_manager.serialize_card(card),
                    "status": "scheduled",
                    "algorithm": "fsrs-4.5"
                }

            # INTENTIONAL: Third-party py-fsrs library may raise unpredictable errors; fallback to Ebbinghaus
            except Exception as e:
                logger.error(f"FSRS scheduling failed, using fallback: {e}")
                # Fall through to fallback

        # Fallback: Legacy Ebbinghaus fixed intervals
        logger.warning("Using fallback Ebbinghaus scheduling (FSRS unavailable)")
        ebbinghaus_intervals = {1: 1, 2: 7, 3: 30, 4: 90}
        interval = ebbinghaus_intervals.get(trigger_point, 1)

        # Story 32.9 AC-1: scheduled_date must be a future date, not "now"
        scheduled_date = datetime.now(timezone.utc) + timedelta(days=interval)
        return {
            "canvas_name": canvas_name,
            "concept_id": concept_id,
            "trigger_point": trigger_point,
            "scheduled_date": scheduled_date.isoformat(),
            "interval_days": interval,
            "status": "scheduled",
            "algorithm": "ebbinghaus-fallback"
        }

    async def record_review_result(
        self,
        canvas_name: str,
        concept_id: str = "",
        score: Optional[float] = None,
        rating: Optional[int] = None,
        card_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record the result of a review session using FSRS algorithm (Story 32.2).

        Story 32.2 AC-32.2.2: Accepts FSRS ratings (1=Again, 2=Hard, 3=Good, 4=Easy)
        Story 32.2 AC-32.2.3: Returns dynamically calculated next review date
        Story 32.2 AC-32.2.4: Backward compatible with score-based inputs (0-100)

        Args:
            canvas_name: Canvas that was reviewed
            concept_id: Concept identifier for card tracking
            score: Legacy score (0-100), converted to rating if rating not provided
            rating: FSRS rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            card_state: Optional serialized FSRS card JSON from previous review
            details: Optional detailed scoring breakdown

        Returns:
            Recorded review result with FSRS state:
            - next_review: ISO timestamp of next scheduled review
            - interval_days: Days until next review
            - fsrs_state: {stability, difficulty, state, reps, lapses}
            - card_data: Serialized card for persistence

        Rating Conversion (AC-32.2.4 backward compatibility):
            Score 0-39:   Again (1) - forgot
            Score 40-59:  Hard (2) - serious difficulty
            Score 60-84:  Good (3) - remembered with hesitation
            Score 85-100: Easy (4) - easily recalled

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        [Source: Story 32.2 - FSRS Integration]
        """
        logger.debug(f"Recording FSRS review result for {canvas_name}/{concept_id}")

        # Story 32.2 AC-32.2.2/AC-32.2.4: Convert score to rating if needed
        if rating is None and score is not None:
            if get_rating_from_score is not None:
                rating = get_rating_from_score(score)
                logger.debug(f"Converted score {score} to FSRS rating {rating}")
            else:
                # Fallback conversion
                if score < 40:
                    rating = 1  # Again
                elif score < 60:
                    rating = 2  # Hard
                elif score < 85:
                    rating = 3  # Good
                else:
                    rating = 4  # Easy
        elif rating is None:
            rating = 3  # Default to Good if no input provided

        # P0-3: Validate rating - handle non-integer types (e.g. "abc", 5.7)
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            logger.warning(f"Invalid rating value '{rating}', defaulting to 3")
            rating = 3
        rating = max(1, min(4, rating))

        # Story 32.2: Use FSRS for recording if available
        if self._fsrs_manager is not None:
            try:
                # Load or create card (AC-32.2.4 backward compatibility)
                if card_state:
                    card = self._fsrs_manager.deserialize_card(card_state)
                    logger.debug(f"Loaded existing FSRS card for {concept_id}")
                else:
                    # Check in-memory cache
                    cached_state = self._card_states.get(concept_id)
                    if cached_state:
                        card = self._fsrs_manager.deserialize_card(cached_state)
                        logger.debug(f"Loaded cached FSRS card for {concept_id}")
                    else:
                        # New card - existing Ebbinghaus records treated as first FSRS review
                        card = self._fsrs_manager.create_card()
                        logger.info(f"Created new FSRS card for {concept_id} (migration from Ebbinghaus)")

                # Story 32.2 AC-32.2.3: Review card with FSRS algorithm
                updated_card, review_log = self._fsrs_manager.review_card(card, rating)

                # Get next due date (dynamically calculated by FSRS)
                due_date = self._fsrs_manager.get_due_date(updated_card)

                # Calculate interval in days
                if due_date:
                    now = datetime.now(timezone.utc)
                    interval_days = max(0, (due_date - now).days)
                else:
                    interval_days = 1

                # Serialize card for persistence
                card_data = self._fsrs_manager.serialize_card(updated_card)

                # Store in memory cache + persist to file (P0-2)
                if concept_id:
                    self._card_states[concept_id] = card_data
                    await self._save_card_states()
                else:
                    # M3 fix: Warn when concept_id is empty — card state will not be persisted
                    logger.warning(
                        f"Empty concept_id for canvas '{canvas_name}' — "
                        f"FSRS card state computed but NOT persisted"
                    )

                # Extract state value safely
                state_val = getattr(updated_card, "state", 0)
                if hasattr(state_val, "value"):
                    state_int = int(state_val.value)
                elif hasattr(state_val, "__int__"):
                    state_int = int(state_val)
                else:
                    state_int = 0

                return {
                    "canvas_name": canvas_name,
                    "concept_id": concept_id,
                    "rating": rating,
                    "score": score,  # Preserve original score for logging
                    "next_review": due_date.isoformat() if due_date else (datetime.now(timezone.utc) + timedelta(days=interval_days)).isoformat(),
                    "interval_days": interval_days,
                    "fsrs_state": {
                        "stability": float(getattr(updated_card, "stability", 0.0)),
                        "difficulty": float(getattr(updated_card, "difficulty", 0.0)),
                        "state": state_int,
                        "reps": int(getattr(updated_card, "reps", 0)),
                        "lapses": int(getattr(updated_card, "lapses", 0))
                    },
                    "card_data": card_data,
                    "details": details or {},
                    "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "status": "recorded",
                    "algorithm": "fsrs-4.5"
                }

            # INTENTIONAL: Third-party py-fsrs library may raise unpredictable errors; fallback to legacy
            except Exception as e:
                logger.error(f"FSRS recording failed, using fallback: {e}")
                # Fall through to fallback

        # Fallback: Legacy Ebbinghaus fixed intervals
        logger.warning("Using fallback Ebbinghaus recording (FSRS unavailable)")

        # Calculate interval based on score (legacy behavior)
        if score is not None:
            if score >= 85:
                interval = 30
            elif score >= 60:
                interval = 7
            elif score >= 40:
                interval = 3
            else:
                interval = 1
        else:
            # Map rating to interval
            rating_intervals = {1: 1, 2: 3, 3: 7, 4: 30}
            interval = rating_intervals.get(rating, 1)

        # Story 32.9 AC-1: next_review must be a future date, not "now"
        now_utc = datetime.now(timezone.utc)
        next_review_date = now_utc + timedelta(days=interval)
        return {
            "canvas_name": canvas_name,
            "concept_id": concept_id,
            "rating": rating,
            "score": score,
            "next_review": next_review_date.isoformat(),
            "interval_days": interval,
            "details": details or {},
            "recorded_at": now_utc.isoformat(),
            "status": "recorded",
            "algorithm": "ebbinghaus-fallback"
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # Story 34.4: Review History with Pagination
    # [Source: specs/api/review-api.openapi.yml#L185-216]
    # [Source: docs/stories/34.4.story.md]
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_history(
        self,
        days: int = 7,
        canvas_path: Optional[str] = None,
        concept_name: Optional[str] = None,
        limit: Optional[int] = 5
    ) -> Dict[str, Any]:
        """
        Get review history with pagination support.

        Story 34.4 AC1: Default limit=5 records.
        Story 34.4 AC2: limit=None returns all records.
        Story 34.4 AC3: Supports filtering by canvas_path and concept_name.

        Args:
            days: Number of days to look back (7, 30, 90)
            canvas_path: Filter by canvas file path
            concept_name: Filter by concept name
            limit: Maximum records (None = all, default=5)

        Returns:
            Dict with records, statistics, and has_more flag
        """
        from collections import defaultdict

        # Calculate date range
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)

        # Get history from storage/graphiti
        all_records: List[Dict[str, Any]] = []

        # Try to get history from Graphiti first
        if self.graphiti_client:
            try:
                from app.clients.graphiti_client import get_learning_memory_client
                memory_client = get_learning_memory_client()
                await memory_client.initialize()

                # Query all learning history within date range
                raw_history = await memory_client.get_learning_history(
                    canvas_name=canvas_path or "",
                    limit=1000  # Get all records for filtering
                )

                # Filter and convert records
                for memory in raw_history:
                    timestamp_str = memory.get("timestamp", "")
                    try:
                        if isinstance(timestamp_str, str):
                            record_date = datetime.fromisoformat(
                                timestamp_str.replace("Z", "+00:00")
                            ).date()
                        else:
                            record_date = timestamp_str.date() if hasattr(timestamp_str, "date") else end_date
                    except (ValueError, AttributeError):
                        continue

                    # Skip records outside date range
                    if record_date < start_date or record_date > end_date:
                        continue

                    # Filter by canvas_path if specified
                    record_canvas = memory.get("canvas_name", memory.get("canvas_path", ""))
                    if canvas_path and canvas_path not in record_canvas:
                        continue

                    # Filter by concept_name if specified
                    record_concept = memory.get("concept", memory.get("concept_name", ""))
                    if concept_name and concept_name not in record_concept:
                        continue

                    # Convert score (0-100) to rating (1-4)
                    score = memory.get("score", 60)
                    if score >= 85:
                        rating = 4
                    elif score >= 60:
                        rating = 3
                    elif score >= 40:
                        rating = 2
                    else:
                        rating = 1

                    all_records.append({
                        "concept_id": memory.get("concept_id", memory.get("id", "")),
                        "concept_name": record_concept,
                        "canvas_path": record_canvas,
                        "rating": rating,
                        "review_time": timestamp_str,
                        "date": record_date.isoformat()
                    })

                logger.info(f"Found {len(all_records)} history records from Graphiti")

            except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
                logger.error(f"Error querying history from Graphiti: {e}")

        # If no records from Graphiti, try FSRS card states
        if not all_records and self._card_states:
            for key, card_data in self._card_states.items():
                try:
                    # Handle both dict and serialized JSON string formats
                    # (FSRS serialize_card() stores strings, _load_card_states restores as-is)
                    if isinstance(card_data, str):
                        try:
                            card_data = json.loads(card_data)
                        except (json.JSONDecodeError, ValueError):
                            continue
                    if not isinstance(card_data, dict):
                        continue

                    last_review = card_data.get("last_review")
                    if not last_review:
                        continue

                    if isinstance(last_review, str):
                        record_date = datetime.fromisoformat(
                            last_review.replace("Z", "+00:00")
                        ).date()
                    else:
                        record_date = last_review.date() if hasattr(last_review, "date") else end_date

                    if record_date < start_date or record_date > end_date:
                        continue

                    parts = key.split(":")
                    record_canvas = parts[0] if len(parts) > 0 else ""
                    record_concept = parts[1] if len(parts) > 1 else key

                    if canvas_path and canvas_path not in record_canvas:
                        continue
                    if concept_name and concept_name not in record_concept:
                        continue

                    all_records.append({
                        "concept_id": key,
                        "concept_name": record_concept,
                        "canvas_path": record_canvas,
                        "rating": card_data.get("rating", 3),
                        "review_time": last_review,
                        "date": record_date.isoformat()
                    })
                except (ValueError, AttributeError):
                    continue

        # Sort by review_time descending (newest first)
        all_records.sort(key=lambda x: x.get("review_time", ""), reverse=True)

        # Determine if there are more records than limit
        total_count = len(all_records)
        # Code Review H3 Fix: Cap None to MAX_HISTORY_RECORDS to enforce service-level protection
        effective_limit = limit if limit is not None else MAX_HISTORY_RECORDS
        has_more = total_count > effective_limit

        # Code Review H3 Fix: Calculate streak from ALL records BEFORE truncation
        # (streak must reflect true consecutive days, not limited view)
        all_dates: set = set()
        for record in all_records:
            date_key = record.get("date", "")
            if date_key:
                all_dates.add(date_key)

        streak_days = 0
        check_date = end_date
        while check_date >= start_date:
            if check_date.isoformat() in all_dates:
                streak_days += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Apply limit after streak calculation
        limited_records = all_records[:effective_limit]

        # Group limited records by date for response
        records_by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in limited_records:
            date_key = record.get("date", "")
            if date_key:
                records_by_date[date_key].append(record)

        # Build daily records list
        daily_records = []
        for date_key in sorted(records_by_date.keys(), reverse=True):
            daily_records.append({
                "date": date_key,
                "reviews": records_by_date[date_key]
            })

        # Story 34.12 AC3: Calculate retention_rate from rating data
        # retention_rate = count(rating >= 3) / count(total records with rating)
        rated_records = [r for r in all_records if r.get("rating") is not None]
        if rated_records:
            good_count = sum(1 for r in rated_records if r.get("rating", 0) >= 3)
            retention_rate = round(good_count / len(rated_records), 4)
        else:
            retention_rate = None

        return {
            "records": daily_records,
            "total_count": total_count,
            "has_more": has_more,
            "streak_days": streak_days,
            "retention_rate": retention_rate
        }

    async def _query_weak_concepts_from_graphiti(
        self,
        canvas_name: str
    ) -> List[Dict[str, Any]]:
        """
        Query historical weak concepts from Graphiti knowledge graph.

        ✅ Verified from Story 24.1 Dev Notes (lines 224-239)

        Args:
            canvas_name: Canvas file name

        Returns:
            List of weak concept dicts with scores and review counts
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "query_weak_concepts", "graphiti_client", "[]"
            )
            return []

        try:
            # Since we're using GraphitiEdgeClient with JSON storage,
            # we'll query from the learning memories instead
            from app.clients.graphiti_client import get_learning_memory_client
            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get learning history for this canvas
            history = await memory_client.get_learning_history(canvas_name, limit=50)

            # Calculate average scores per concept
            concept_scores: Dict[str, List[float]] = {}
            for memory in history:
                concept = memory.get("concept", "")
                score = memory.get("score")
                if concept and score is not None:
                    if concept not in concept_scores:
                        concept_scores[concept] = []
                    concept_scores[concept].append(score)

            # Build weak concepts list (avg score < 24 out of 40)
            weak_concepts = []
            for concept, scores in concept_scores.items():
                avg_score = sum(scores) / len(scores) if scores else 0
                if avg_score < 24:  # < 60% threshold
                    weak_concepts.append({
                        "concept_name": concept,
                        "avg_score": avg_score,
                        "review_count": len(scores)
                    })

            # Sort by avg_score ascending (weakest first)
            weak_concepts.sort(key=lambda x: (x["avg_score"], -x["review_count"]))

            logger.info(
                f"Found {len(weak_concepts)} weak concepts for {canvas_name}"
            )
            return weak_concepts

        except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
            logger.error(f"Error querying weak concepts: {e}")
            return []

    async def _store_review_relationship(
        self,
        original_canvas: str,
        review_canvas: str,
        mode: str
    ) -> None:
        """
        Store GENERATED_FROM relationship in Graphiti.

        ✅ Verified from Story 24.1 Dev Notes (lines 241-256)

        Args:
            original_canvas: Original canvas name
            review_canvas: Review canvas name
            mode: Mode used (fresh/targeted)
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "store_review_relationship", "graphiti_client", "skip"
            )
            return

        try:
            from app.clients.graphiti_client import EdgeRelationship
            relationship = EdgeRelationship(
                canvas_name=original_canvas,
                from_node=review_canvas,
                to_node=original_canvas,
                label=f"GENERATED_FROM_{mode.upper()}",
                edge_id=None
            )

            await self.graphiti_client.add_edge_relationship(relationship)

            # Also add episode for tracking
            await self.graphiti_client.add_episode_for_edge(
                canvas_name=original_canvas,
                edge={
                    "fromNode": review_canvas,
                    "toNode": original_canvas,
                    "label": f"generated in {mode} mode",
                    "id": f"review_{mode}_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
                }
            )

            logger.info(
                f"Stored review relationship: {review_canvas} --[{mode}]--> {original_canvas}"
            )

        except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
            logger.warning(f"Failed to store review relationship: {e}")

    async def _apply_weighted_selection(
        self,
        weight_data: List[ConceptWeightData],
        question_count: int,
        weak_weight: float = 0.7,
        mastered_weight: float = 0.3
    ) -> List[ConceptWeightData]:
        """
        Apply weighted selection to concept list.

        ✅ Verified from Story 24.3 Dev Notes (lines 345-401)

        AC2: Configurable Weight Distribution
        AC3: Weighted Concept Selection

        Args:
            weight_data: Calculated weight data for all concepts
            question_count: Number of questions to select
            weak_weight: Weight for weak concepts (default 0.7)
            mastered_weight: Weight for mastered concepts (default 0.3)

        Returns:
            Selected concepts based on weight distribution

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        # AC2: Validate weights
        if abs(weak_weight + mastered_weight - 1.0) > 0.01:
            raise ValueError("weak_weight + mastered_weight must equal 1.0")

        # AC3: Categorize concepts
        weak = [c for c in weight_data if c.category == "weak"]
        mastered = [c for c in weight_data if c.category == "mastered"]
        borderline = [c for c in weight_data if c.category == "borderline"]

        # Calculate target counts
        weak_count = int(question_count * weak_weight)
        mastered_count = int(question_count * mastered_weight)
        borderline_count = question_count - weak_count - mastered_count

        selected = []

        # Select from each category (with fallback if insufficient)
        if weak:
            selected.extend(self._weighted_sample(weak, min(weak_count, len(weak))))
        if mastered:
            selected.extend(self._weighted_sample(mastered, min(mastered_count, len(mastered))))
        if borderline:
            selected.extend(self._weighted_sample(borderline, min(borderline_count, len(borderline))))

        # Fill remaining from any category
        remaining = question_count - len(selected)
        if remaining > 0:
            all_remaining = [c for c in weight_data if c not in selected]
            selected.extend(self._weighted_sample(all_remaining, min(remaining, len(all_remaining))))

        logger.info(
            f"Weighted selection complete: {len(selected)} concepts selected "
            f"(target: {question_count}, weights: {weak_weight:.1%} weak / {mastered_weight:.1%} mastered)"
        )

        return selected

    def _weighted_sample(
        self,
        concepts: List[ConceptWeightData],
        count: int
    ) -> List[ConceptWeightData]:
        """
        Sample concepts with weights based on weakness_score.

        ✅ Verified from Story 24.3 Dev Notes (lines 403-445)

        AC3: Selection probability follows weight distribution.

        Args:
            concepts: List of concepts to sample from
            count: Number to sample

        Returns:
            Sampled concepts
        """
        if not concepts or count <= 0:
            return []

        # Use weakness_score as probability weight
        weights = [c.weakness_score for c in concepts]
        total = sum(weights)

        if total == 0:
            # Equal probability if all scores are 0
            return random.sample(concepts, min(count, len(concepts)))

        # Normalize weights
        probabilities = [w / total for w in weights]

        # Weighted sampling without replacement
        selected = []
        remaining = list(zip(concepts, probabilities))

        for _ in range(min(count, len(concepts))):
            if not remaining:
                break

            # Random selection based on probabilities
            r = random.random()
            cumulative = 0
            for i, (concept, prob) in enumerate(remaining):
                cumulative += prob
                if r <= cumulative:
                    selected.append(concept)
                    remaining.pop(i)
                    # Renormalize remaining probabilities
                    if remaining:
                        total_prob = sum(p for _, p in remaining)
                        remaining = [(c, p / total_prob) for c, p in remaining]
                    break

        return selected

    async def _query_review_history_from_graphiti(
        self,
        canvas_name: str
    ) -> List[Dict]:
        """
        Query review history from Graphiti knowledge graph.

        ✅ Verified from Story 24.3 Dev Notes (lines 538-592)

        PRD Reference: v1.1.8 - query_review_history_from_graphiti tool

        Args:
            canvas_name: Canvas file name

        Returns:
            List of review records with: concept_id, rating, timestamp, etc.
        """
        try:
            # Import learning memory client
            from app.clients.graphiti_client import get_learning_memory_client

            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get learning history for this canvas
            history = await memory_client.get_learning_history(
                canvas_name=canvas_name,
                limit=1000  # Get all available history
            )

            logger.info(f"Retrieved {len(history)} review records for {canvas_name}")
            return history

        except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
            logger.warning(f"Graphiti query failed, using empty history: {e}")
            return []

    async def get_multi_review_progress(
        self,
        original_canvas_path: str
    ) -> Dict[str, Any]:
        """
        Get multi-review trend analysis for an original canvas.

        Queries Graphiti for all verification canvases generated from
        this original canvas and calculates trend metrics.

        ✅ Verified from Story 24.4 Dev Notes (lines 230-267)
        [Source: specs/api/review-api.openapi.yml#L346-378]

        Args:
            original_canvas_path: Path to the original canvas file

        Returns:
            MultiReviewProgressResponse dict with reviews and trends

        Raises:
            CanvasNotFoundException: If no review history exists
        """
        # Query Graphiti for review sessions (Story 24.4)
        reviews = await self._query_review_sessions_from_graphiti(original_canvas_path)

        if not reviews:
            raise CanvasNotFoundException(f"No review history for: {original_canvas_path}")

        # Calculate trends
        trends = self._calculate_trend_analysis(reviews)

        return {
            "original_canvas_path": original_canvas_path,
            "review_count": len(reviews),
            "reviews": reviews,
            "trends": trends
        }


    async def _query_review_sessions_from_graphiti(
        self,
        original_canvas_path: str
    ) -> List[Dict[str, Any]]:
        """
        Query Graphiti for all review sessions linked to original canvas.

        ✅ Verified from Story 24.4 Dev Notes (lines 268-316)
        [Source: docs/architecture/decisions/0003-graphiti-memory.md]

        Cypher Query Pattern (for future Neo4j):
        MATCH (review:ReviewCanvas)-[r:GENERATED_FROM]->(original:Canvas {path: $path})
        RETURN review, r.mode, r.generated_at
        ORDER BY r.generated_at DESC

        For now, using JSON storage via GraphitiEdgeClient.

        Args:
            original_canvas_path: Path to the original canvas file

        Returns:
            List of review session dicts
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "get_review_sessions", "graphiti_client", "[]"
            )
            return []

        try:
            # Story 36.7: Uses LearningMemoryClient (supports both JSON and Neo4j backends)
            from app.clients.graphiti_client import get_learning_memory_client
            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get all learning episodes for this canvas
            # Filter for verification canvas pattern: *-检验白板-*
            all_memories = await memory_client.get_learning_history(
                original_canvas_path,
                limit=100
            )

            # Group by verification canvas sessions
            review_sessions: Dict[str, Dict[str, Any]] = {}

            for memory in all_memories:
                # Check if this is from a verification canvas
                source = memory.get("source_canvas", "")
                if "-检验白板-" not in source:
                    continue

                # Extract session info
                if source not in review_sessions:
                    review_sessions[source] = {
                        "review_canvas_path": source,
                        "date": memory.get("timestamp", datetime.now(timezone.utc)),
                        "mode": memory.get("mode", "fresh"),
                        "concepts": [],
                        "scores": []
                    }

                # Add concept score
                score = memory.get("score")
                if score is not None:
                    review_sessions[source]["concepts"].append(
                        memory.get("concept", "")
                    )
                    review_sessions[source]["scores"].append(score)

            # Transform to ReviewEntry format
            reviews = []
            for session_data in review_sessions.values():
                scores = session_data["scores"]
                if not scores:
                    continue

                total_concepts = len(scores)
                passed_concepts = sum(1 for s in scores if s >= 24)  # >= 60% threshold
                pass_rate = passed_concepts / total_concepts if total_concepts > 0 else 0.0

                reviews.append({
                    "review_canvas_path": session_data["review_canvas_path"],
                    "date": session_data["date"],
                    "mode": session_data["mode"],
                    "pass_rate": pass_rate,
                    "total_concepts": total_concepts,
                    "passed_concepts": passed_concepts
                })

            # Sort by date descending (newest first)
            reviews.sort(key=lambda x: x["date"], reverse=True)

            logger.info(
                f"Found {len(reviews)} review sessions for {original_canvas_path}"
            )
            return reviews

        except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
            logger.error(f"Error querying review history: {e}")
            return []

    def _calculate_trend_analysis(
        self,
        reviews: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate trend metrics from review history.

        ✅ Verified from Story 24.4 Dev Notes (lines 317-362)

        Includes:
        - pass_rate_trend: Time series of pass rates
        - weak_concepts_improvement: Per-concept improvement tracking
        - overall_progress: Aggregate progress metrics

        Args:
            reviews: List of review entry dicts

        Returns:
            TrendAnalysis dict or None if insufficient data
        """
        if not reviews:
            return None

        # Pass rate trend (newest first in reviews, reverse for chronological chart)
        pass_rate_trend = [
            {
                "date": r["date"].split("T")[0] if isinstance(r["date"], str) else r["date"].strftime("%Y-%m-%d"),
                "pass_rate": r["pass_rate"]
            }
            for r in reversed(reviews)
        ]

        # Calculate overall progress
        if len(reviews) >= 2:
            first_pass_rate = reviews[-1]["pass_rate"]  # Oldest
            last_pass_rate = reviews[0]["pass_rate"]   # Newest
            progress_rate = last_pass_rate - first_pass_rate

            if progress_rate > 0.05:
                trend_direction = "up"
            elif progress_rate < -0.05:
                trend_direction = "down"
            else:
                trend_direction = "stable"
        else:
            progress_rate = 0.0
            trend_direction = "stable"

        return {
            "pass_rate_trend": pass_rate_trend,
            "weak_concepts_improvement": [],  # Populated by separate query if needed
            "overall_progress": {
                "progress_rate": progress_rate,
                "trend_direction": trend_direction
            }
        }

    async def _query_weak_concepts_improvement(
        self,
        original_canvas_path: str
    ) -> List[Dict[str, Any]]:
        """
        Query Graphiti for weak concept improvement over time.

        ✅ Verified from Story 24.4 Dev Notes (lines 404-456)

        Tracks concepts that were weak (score < 60) in early reviews
        and their current status.

        Args:
            original_canvas_path: Path to the original canvas file

        Returns:
            List of WeakConceptImprovement dicts
        """
        if not self.graphiti_client:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "get_weak_concept_improvement", "graphiti_client", "[]"
            )
            return []

        try:
            from app.clients.graphiti_client import get_learning_memory_client
            memory_client = get_learning_memory_client()
            await memory_client.initialize()

            # Get all verification session memories
            all_memories = await memory_client.get_learning_history(
                original_canvas_path,
                limit=200
            )

            # Filter for verification canvas sessions
            verification_memories = [
                m for m in all_memories
                if "-检验白板-" in m.get("source_canvas", "")
            ]

            # Group by concept
            concept_scores: Dict[str, List[Dict[str, Any]]] = {}
            for memory in verification_memories:
                concept = memory.get("concept", "")
                score = memory.get("score")
                timestamp = memory.get("timestamp")

                if concept and score is not None and timestamp:
                    if concept not in concept_scores:
                        concept_scores[concept] = []
                    concept_scores[concept].append({
                        "score": score,
                        "timestamp": timestamp
                    })

            # Calculate improvement for each concept
            improvements = []
            for concept_name, score_history in concept_scores.items():
                # Sort by timestamp
                score_history.sort(key=lambda x: x["timestamp"])

                first_score = score_history[0]["score"]
                last_score = score_history[-1]["score"]

                # Only include if initially weak (< 60%)
                if first_score < 24:  # 24/40 = 60%
                    improvement_rate = (last_score - first_score) / 40  # Normalize to 0-1

                    # Determine status
                    if last_score >= 32:  # >= 80%
                        status = "mastered"
                    elif last_score > first_score:
                        status = "improving"
                    else:
                        status = "weak"

                    improvements.append({
                        "concept_name": concept_name,
                        "improvement_rate": max(0, improvement_rate),
                        "current_status": status
                    })

            # Sort by improvement_rate descending
            improvements.sort(key=lambda x: x["improvement_rate"], reverse=True)

            return improvements

        except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
            logger.error(f"Error querying weak concept improvement: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 32.2 Task 4: FSRS Card State Persistence
    # [Source: docs/stories/32.2.story.md#Task-4]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def load_card_state(
        self,
        concept_id: str,
        canvas_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Load FSRS card state from persistence layer.

        Story 32.2 AC-32.2.4: Backward compatible - returns None for new concepts.

        Args:
            concept_id: Concept identifier
            canvas_name: Optional canvas name for filtering

        Returns:
            Serialized card JSON string or None if not found
        """
        # Check in-memory cache first
        if concept_id in self._card_states:
            logger.debug(f"Loaded card state from memory cache: {concept_id}")
            return self._card_states[concept_id]

        # Try to load from Graphiti
        if self.graphiti_client:
            try:
                from app.clients.graphiti_client import get_learning_memory_client
                memory_client = get_learning_memory_client()
                await memory_client.initialize()

                # Query for concept's FSRS card state
                history = await memory_client.get_learning_history(
                    canvas_name or "",
                    limit=1
                )

                # Look for card_data in most recent record
                for record in history:
                    if record.get("concept") == concept_id:
                        card_data = record.get("card_data")
                        if card_data:
                            # Cache it + persist (P0-2)
                            self._card_states[concept_id] = card_data
                            await self._save_card_states()
                            logger.debug(f"Loaded card state from Graphiti: {concept_id}")
                            return card_data

            except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to load card state from Graphiti: {e}")

        return None

    async def save_card_state(
        self,
        concept_id: str,
        card_data: str,
        canvas_name: str,
        rating: int,
        score: Optional[float] = None
    ) -> bool:
        """
        Save FSRS card state to persistence layer.

        Story 32.2 AC-32.2.4: Stores card state in review records.

        Args:
            concept_id: Concept identifier
            card_data: Serialized FSRS card JSON
            canvas_name: Canvas file name
            rating: FSRS rating (1-4)
            score: Optional legacy score (0-100)

        Returns:
            True if saved successfully
        """
        # Always update in-memory cache + persist to file (P0-2)
        self._card_states[concept_id] = card_data
        await self._save_card_states()
        logger.debug(f"Saved card state to memory cache: {concept_id}")

        # Try to persist to Graphiti
        if self.graphiti_client:
            try:
                from app.clients.graphiti_client import get_learning_memory_client
                memory_client = get_learning_memory_client()
                await memory_client.initialize()

                # Create learning memory with FSRS data
                memory_data = {
                    "concept": concept_id,
                    "canvas_name": canvas_name,
                    "rating": rating,
                    "score": score,
                    "card_data": card_data,
                    "algorithm": "fsrs-4.5",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                await memory_client.add_learning_memory(memory_data)
                logger.info(f"Saved card state to Graphiti: {concept_id}")
                return True

            except (ConnectionError, TimeoutError, ValueError, KeyError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to save card state to Graphiti: {e}")
                # In-memory cache still valid
                return True

        return True

    def get_cached_card_states(self) -> Dict[str, str]:
        """
        Get all cached card states.

        Returns:
            Dictionary of concept_id -> card_data JSON
        """
        return dict(self._card_states)

    # ═══════════════════════════════════════════════════════════════════════════════
    # Story 32.3: FSRS State Query for Plugin Priority Calculation
    # [Source: docs/stories/32.3.story.md#Task-1]
    # ═══════════════════════════════════════════════════════════════════════════════

    async def get_fsrs_state(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Get FSRS state for a concept for plugin priority calculation.

        Story 32.3 AC-32.3.1: Plugin queries backend for FSRS state.
        Story 32.3 AC-32.3.2: Returns stability, difficulty, state, reps, lapses,
                              retrievability, due.
        Story 32.3 AC-32.3.3: Includes full card_state JSON for plugin caching.

        Args:
            concept_id: Concept identifier (node_id from canvas)

        Returns:
            Dict with FSRS state fields and card_state JSON, or None if not found
        """
        logger.debug(f"Getting FSRS state for concept: {concept_id}")

        # Story 32.3: Try to get card from cache or persistence
        if self._fsrs_manager is None:
            logger.warning(
                "功能 %s 降级运行: %s 为 None，返回默认值 %s",
                "get_fsrs_state", "fsrs_manager", "found=False"
            )
            return {"found": False, "reason": "fsrs_not_initialized"}

        try:
            # Check in-memory cache first
            card_data = self._card_states.get(concept_id)

            if not card_data:
                # Try to load from persistence
                card_data = await self.load_card_state(concept_id)

            if not card_data:
                # Story 38.3 AC-4: Auto-create default FSRS card for new concepts
                logger.info(f"Auto-creating default FSRS card for concept: {concept_id}")
                card = self._fsrs_manager.create_card()
                card_data = self._fsrs_manager.serialize_card(card)
                # Cache the newly created card + persist (P0-2)
                self._card_states[concept_id] = card_data
                await self._save_card_states()
                # Story 38.3 AC-4 + Code Review C1/M3 Fix:
                # Persist auto-created card via fire-and-forget background task.
                # Bypasses self.graphiti_client gate (not injected by dependencies.py)
                # and uses get_learning_memory_client() directly.
                # Story 32.10 AC-3: Capture self for failure counter
                _self_ref = self

                async def _persist_auto_created_card(cid: str, cdata: str) -> None:
                    try:
                        from app.clients.graphiti_client import get_learning_memory_client
                        memory_client = get_learning_memory_client()
                        await memory_client.initialize()
                        memory_data = {
                            "concept": cid,
                            "canvas_name": "auto-created",
                            "rating": 0,
                            "card_data": cdata,
                            "algorithm": "fsrs-4.5",
                            "auto_created": True,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        await memory_client.add_learning_memory(memory_data)
                        logger.info(f"Persisted auto-created card to Graphiti: {cid}")
                    # INTENTIONAL: Fire-and-forget background task must not crash; any error type possible
                    except Exception as e:
                        # Story 32.10 AC-3: Track failure count for observability
                        _self_ref._auto_persist_failures += 1
                        logger.warning(
                            f"Failed to persist auto-created card for {cid} "
                            f"(total failures: {_self_ref._auto_persist_failures}): {e}"
                        )

                asyncio.create_task(_persist_auto_created_card(concept_id, card_data))
            else:
                # Deserialize existing card
                card = self._fsrs_manager.deserialize_card(card_data)

            # Get retrievability (current recall probability)
            retrievability = self._fsrs_manager.get_retrievability(card)

            # Get due date
            due_date = self._fsrs_manager.get_due_date(card)

            # Extract state value safely
            state_val = getattr(card, "state", 0)
            if hasattr(state_val, "value"):
                state_int = int(state_val.value)
            elif hasattr(state_val, "__int__"):
                state_int = int(state_val)
            else:
                state_int = 0

            result = {
                "found": True,
                "stability": float(getattr(card, "stability", 0.0)),
                "difficulty": float(getattr(card, "difficulty", 5.0)),
                "state": state_int,
                "reps": int(getattr(card, "reps", 0)),
                "lapses": int(getattr(card, "lapses", 0)),
                "retrievability": retrievability,
                "due": due_date,
                "last_review": getattr(card, "last_review", None),
                "card_state": card_data  # Full JSON for plugin to cache/deserialize
            }

            logger.debug(
                f"FSRS state for {concept_id}: stability={result['stability']:.2f}, "
                f"difficulty={result['difficulty']:.2f}, retrievability={f'{retrievability:.3f}' if retrievability is not None else 'N/A'}"
            )

            return result

        # INTENTIONAL: API-facing endpoint; third-party FSRS library may raise unpredictable errors
        except Exception as e:
            logger.error(f"Error getting FSRS state for {concept_id}: {e}")
            return {"found": False, "reason": f"error: {e}"}

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        Note: _card_states is NOT cleared here because it is shared persistent state
        that survives across requests. Clearing it would cause unnecessary file re-reads.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        self._task_canvas_map.clear()
        # H1 fix: Do NOT clear _card_states — it's cross-request persistent cache.
        # Clearing here causes data loss when DI yield calls cleanup after each request.
        logger.debug("ReviewService cleanup completed")


# ═══════════════════════════════════════════════════════════════════════════════
# Story 38.9: ReviewService Singleton Factory (canonical entry point)
# Pattern: async double-check lock (aligned with get_memory_service in memory_service.py)
# ═══════════════════════════════════════════════════════════════════════════════

_review_service_singleton: Optional["ReviewService"] = None
_review_service_singleton_lock = asyncio.Lock()


async def get_review_service() -> "ReviewService":
    """Get or create the ReviewService singleton.

    Story 38.9 AC1: Canonical singleton factory with double-check lock.
    All consumers (dependencies.py, review.py endpoints) must use this
    single entry point to ensure DI alignment.

    Dependencies created:
    - CanvasService with memory_client (EPIC-36 P0 fix)
    - BackgroundTaskManager
    - FSRSManager via create_fsrs_manager() (Story 32.8)
    - graphiti_client via get_graphiti_temporal_client() (Story 34.8 AC2)
    """
    global _review_service_singleton
    if _review_service_singleton is not None:
        return _review_service_singleton

    async with _review_service_singleton_lock:
        # Double-check after acquiring lock
        if _review_service_singleton is not None:
            return _review_service_singleton

        from app.config import get_settings
        from app.services.canvas_service import CanvasService
        from app.services.background_task_manager import BackgroundTaskManager

        settings = get_settings()

        # 1. CanvasService with memory_client (EPIC-36 P0 fix alignment)
        memory_client = None
        try:
            from app.services.memory_service import get_memory_service as _get_mem
            memory_client = await _get_mem()
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning(f"MemoryService not available for CanvasService edge sync: {e}")

        canvas_service = CanvasService(
            canvas_base_path=settings.canvas_base_path,
            memory_client=memory_client
        )

        # 2. BackgroundTaskManager
        task_manager = BackgroundTaskManager()

        # 3. FSRSManager (Story 32.8: unified factory)
        fsrs_manager = create_fsrs_manager(settings)

        # 4. graphiti_client (Story 34.8 AC2: explicit injection)
        graphiti_client = None
        try:
            from app.dependencies import get_graphiti_temporal_client
            graphiti_client = get_graphiti_temporal_client()
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning(f"Failed to get graphiti_client for ReviewService: {e}")

        if not graphiti_client:
            logger.warning(
                "Graphiti client not available for ReviewService, "
                "history will use FSRS fallback"
            )

        _review_service_singleton = ReviewService(
            canvas_service=canvas_service,
            task_manager=task_manager,
            graphiti_client=graphiti_client,
            fsrs_manager=fsrs_manager
        )
        logger.info("ReviewService singleton created via services layer factory")
        return _review_service_singleton


def reset_review_service_singleton() -> None:
    """Reset the ReviewService singleton (for test isolation).

    Story 38.9 AC4: Tests call this instead of directly setting
    review._review_service_instance = None.
    """
    global _review_service_singleton
    _review_service_singleton = None
