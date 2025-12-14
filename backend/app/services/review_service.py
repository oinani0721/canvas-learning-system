# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Review Service - Business logic for verification canvas and review operations.

This service provides async methods for review scheduling and
verification canvas generation, implementing Ebbinghaus spaced repetition.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
"""
import asyncio
import logging
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.exceptions import CanvasNotFoundException, TaskNotFoundError
from app.services.weight_calculator import ConceptWeightData, WeightCalculator

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
        graphiti_client: Optional[Any] = None
    ):
        """
        Initialize ReviewService.

        Args:
            canvas_service: CanvasService instance for canvas operations
            task_manager: BackgroundTaskManager instance for async tasks
            graphiti_client: Optional GraphitiEdgeClient for history tracking

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        [Source: Story 24.1 - Graphiti Integration]
        """
        self.canvas_service = canvas_service
        self.task_manager = task_manager
        self.graphiti_client = graphiti_client
        self._initialized = True
        self._task_canvas_map: Dict[str, str] = {}  # Maps task_id to canvas_name
        logger.debug("ReviewService initialized")

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
            await asyncio.sleep(0.2)  # Simulate work
            timestamp = datetime.now().strftime("%Y%m%d")
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

        if mode == "targeted":
            # Query Graphiti for review history (Story 24.3)
            review_history = await self._query_review_history_from_graphiti(source_canvas_name)

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
        timestamp = datetime.now().strftime("%Y%m%d")
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
            "generated_at": datetime.now().isoformat(),
            "weak_concepts": weak_concepts_data,  # AC5: Enhanced response
            "weight_config": weight_config  # AC5: Weight configuration
        }

        logger.info(
            f"Generated verification canvas: {review_canvas_name} "
            f"with {len(selected_concepts)} questions (mode={mode})"
        )

        return result

    async def schedule_review(
        self,
        canvas_name: str,
        trigger_point: int = 1
    ) -> Dict[str, Any]:
        """
        Schedule a review for a canvas based on Ebbinghaus curve.

        Args:
            canvas_name: Canvas to schedule review for
            trigger_point: Ebbinghaus trigger point (1=24h, 2=7d, 3=30d, 4=custom)

        Returns:
            Review schedule information

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Scheduling review for {canvas_name} at trigger point {trigger_point}")
        # Stub implementation
        return {
            "canvas_name": canvas_name,
            "trigger_point": trigger_point,
            "scheduled_date": datetime.now().isoformat(),
            "status": "scheduled"
        }

    async def record_review_result(
        self,
        canvas_name: str,
        score: float,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record the result of a review session.

        Args:
            canvas_name: Canvas that was reviewed
            score: Overall review score (0-100)
            details: Optional detailed scoring breakdown

        Returns:
            Recorded review result

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Recording review result for {canvas_name}: {score}")
        # Stub implementation
        return {
            "canvas_name": canvas_name,
            "score": score,
            "details": details or {},
            "recorded_at": datetime.now().isoformat(),
            "status": "recorded"
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
            logger.warning("Graphiti client not available, returning empty weak concepts")
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

        except Exception as e:
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
            logger.debug("Graphiti client not available, skipping relationship storage")
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
                    "id": f"review_{mode}_{datetime.now().strftime('%Y%m%d')}"
                }
            )

            logger.info(
                f"Stored review relationship: {review_canvas} --[{mode}]--> {original_canvas}"
            )

        except Exception as e:
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

        except Exception as e:
            logger.warning(f"Graphiti query failed, using empty history: {e}")
            return []

    async def _apply_weighted_selection(
        self,
        weight_data: List[ConceptWeightData],
        question_count: int,
        weak_weight: float = 0.7,
        mastered_weight: float = 0.3
    ) -> List[ConceptWeightData]:
        """
        Apply weighted selection to concept list.

        Verified from Story 24.3 Dev Notes (lines 345-401)

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

        Verified from Story 24.3 Dev Notes (lines 403-445)

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

        Verified from Story 24.3 Dev Notes (lines 538-592)

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

        except Exception as e:
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
        # Query Graphiti for review relationships
        reviews = await self._query_review_history_from_graphiti(original_canvas_path)

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


    async def _query_review_history_from_graphiti(
        self,
        original_canvas_path: str
    ) -> List[Dict[str, Any]]:
        """
        Query Graphiti for all verification canvases linked to original.

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
            List of review entry dicts
        """
        if not self.graphiti_client:
            logger.warning("Graphiti client not available, returning empty review history")
            return []

        try:
            # Using JSON storage fallback for now
            # TODO: Replace with real Neo4j query when Graphiti is fully integrated
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
                        "date": memory.get("timestamp", datetime.now()),
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

        except Exception as e:
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

        except Exception as e:
            logger.error(f"Error querying weak concept improvement: {e}")
            return []

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        self._task_canvas_map.clear()
        logger.debug("ReviewService cleanup completed")

    # ═══════════════════════════════════════════════════════════════════════════════
