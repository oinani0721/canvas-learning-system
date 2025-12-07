# ✅ Verified structure from docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层
"""
Review Service - Business logic for verification canvas and review operations.

This service provides async methods for review scheduling and
verification canvas generation, implementing Ebbinghaus spaced repetition.

[Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.core.exceptions import CanvasNotFoundException, TaskNotFoundError

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
        task_manager: "BackgroundTaskManager"
    ):
        """
        Initialize ReviewService.

        Args:
            canvas_service: CanvasService instance for canvas operations
            task_manager: BackgroundTaskManager instance for async tasks

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self.canvas_service = canvas_service
        self.task_manager = task_manager
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
        source_canvas_name: str
    ) -> Dict[str, Any]:
        """
        Generate a verification canvas from a source canvas.

        Creates a new canvas with blank yellow nodes for testing recall.

        Args:
            source_canvas_name: Name of source canvas to create verification from

        Returns:
            Generated verification canvas data

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#Layer-2-服务层]
        """
        logger.debug(f"Generating verification canvas from: {source_canvas_name}")
        # Delegate to generate_review_canvas
        return await self.generate_review_canvas(source_canvas_name)

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

    async def cleanup(self) -> None:
        """
        Cleanup resources when service is no longer needed.

        [Source: docs/architecture/EPIC-11-BACKEND-ARCHITECTURE.md#依赖注入设计]
        """
        self._initialized = False
        self._task_canvas_map.clear()
        logger.debug("ReviewService cleanup completed")
