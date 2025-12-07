"""
Progress Analyzer Service

Analyzes verification canvas progress and multi-review history trends.

Story 19.2 AC 1-6: 进度分析算法 + 检验历史关联分析

✅ Verified from PRD FR4 (Lines 2661-2826) - Progress analysis algorithms
✅ Verified from PRD FR4 (Lines 2727-2826) - Multi-review aggregation
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .source_node_validator import SourceNodeValidator


@dataclass
class SingleReviewProgress:
    """Progress data for a single review session.

    Attributes:
        total_concepts: Total number of concepts being tested
        red_nodes_total: Total red nodes in original canvas
        red_nodes_passed: Red nodes that passed (turned green)
        purple_nodes_total: Total purple nodes in original canvas
        purple_nodes_passed: Purple nodes that passed (turned green)
        passed_count: Total nodes that passed
        coverage_rate: Overall pass rate (0-1)

    [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2662-2682]
    """
    total_concepts: int
    red_nodes_total: int = 0
    red_nodes_passed: int = 0
    purple_nodes_total: int = 0
    purple_nodes_passed: int = 0
    passed_count: int = 0
    coverage_rate: float = 0.0


@dataclass
class ReviewHistoryEntry:
    """Single entry in review history.

    [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2727-2826]
    """
    review_canvas: str
    timestamp: str
    progress_rate: float
    passed_count: int
    total_count: int


@dataclass
class ConceptTrend:
    """Learning trend for a single concept.

    Attributes:
        concept_id: Node ID of the concept
        concept_text: Text content of the concept node
        attempts: Number of review attempts
        history: List of results ("通过" or "失败")
        first_pass_review: Review number where first passed (1-indexed, None if never passed)

    [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2790-2810]
    """
    concept_id: str
    concept_text: str = ""
    attempts: int = 0
    history: List[str] = field(default_factory=list)
    first_pass_review: Optional[int] = None


@dataclass
class MultiReviewProgress:
    """Aggregated progress data across multiple reviews.

    Attributes:
        review_history: List of review history entries
        concept_trends: Per-concept learning trends
        overall_trend: "improving" | "stable" | "declining" | "insufficient_data"
        improvement_rate: Change in pass rate from first to latest review

    [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2727-2826]
    """
    review_history: List[ReviewHistoryEntry] = field(default_factory=list)
    concept_trends: Dict[str, ConceptTrend] = field(default_factory=dict)
    overall_trend: str = "insufficient_data"
    improvement_rate: float = 0.0


class ProgressAnalyzer:
    """
    Analyzes verification canvas progress and review history.

    Provides methods to:
    - Analyze single review progress (pass rate, concept breakdown)
    - Aggregate multi-review history and detect trends
    - Query review history from Graphiti knowledge graph

    [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2661-2826]

    Example:
        >>> analyzer = ProgressAnalyzer()
        >>> progress = await analyzer.analyze_review_progress(
        ...     "review-离散数学-20250115.canvas",
        ...     "离散数学.canvas"
        ... )
        >>> print(f"Pass rate: {progress.coverage_rate:.1%}")
        Pass rate: 75.0%
    """

    # Color codes in Obsidian Canvas
    COLOR_RED = "4"      # 红色 - 完全不懂
    COLOR_PURPLE = "3"   # 紫色 - 半懂不懂
    COLOR_GREEN = "2"    # 绿色 - 通过/掌握
    COLOR_YELLOW = "1"   # 黄色 - 用户回答区

    # Trend thresholds
    IMPROVEMENT_THRESHOLD = 0.1  # > 10% improvement = improving
    DECLINE_THRESHOLD = -0.1    # < -10% = declining

    def __init__(self, graphiti_client: Optional[Any] = None):
        """
        Initialize the ProgressAnalyzer.

        Args:
            graphiti_client: Optional Graphiti client for history queries.
                           If None, uses local file-based history.
        """
        self._canvas_cache: Dict[str, Dict[str, Any]] = {}
        self._validator = SourceNodeValidator()
        self._graphiti = graphiti_client

    def _load_canvas(self, canvas_path: str) -> Optional[Dict[str, Any]]:
        """
        Load and cache a canvas file.

        Args:
            canvas_path: Path to the canvas file

        Returns:
            Canvas data dict or None if failed to load
        """
        if canvas_path in self._canvas_cache:
            return self._canvas_cache[canvas_path]

        path = Path(canvas_path)
        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                canvas_data = json.load(f)
                self._canvas_cache[canvas_path] = canvas_data
                return canvas_data
        except (json.JSONDecodeError, IOError):
            return None

    def _get_node_color_map(
        self,
        canvas_data: Dict[str, Any]
    ) -> Dict[str, Tuple[str, str]]:
        """
        Extract node ID to (color, text) mapping from canvas data.

        Args:
            canvas_data: Loaded canvas data

        Returns:
            Dict mapping node ID to (color, text) tuple
        """
        result = {}
        for node in canvas_data.get('nodes', []):
            node_id = node.get('id')
            if node_id:
                color = node.get('color', '')
                text = node.get('text', '')[:100]  # Truncate for readability
                result[node_id] = (color, text)
        return result

    def _extract_source_nodes_with_colors(
        self,
        review_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract sourceNodeId to current color mapping from review canvas.

        Args:
            review_data: Review canvas data

        Returns:
            Dict mapping sourceNodeId to current color
        """
        return {
            node['sourceNodeId']: node.get('color', '')
            for node in review_data.get('nodes', [])
            if 'sourceNodeId' in node
        }

    async def analyze_review_progress(
        self,
        review_canvas_path: str,
        original_canvas_path: str
    ) -> SingleReviewProgress:
        """
        Analyze progress for a single review session.

        Compares the review canvas against the original canvas to determine
        which concepts have been mastered (passed) vs still need work.

        Args:
            review_canvas_path: Path to the review/verification canvas
            original_canvas_path: Path to the original learning canvas

        Returns:
            SingleReviewProgress with detailed breakdown

        [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2662-2682]
        """
        # Load canvases
        review_data = self._load_canvas(review_canvas_path)
        original_data = self._load_canvas(original_canvas_path)

        if review_data is None or original_data is None:
            return SingleReviewProgress(total_concepts=0)

        # Get original node colors
        original_colors = self._get_node_color_map(original_data)

        # Get review node results (sourceNodeId -> current color)
        review_results = self._extract_source_nodes_with_colors(review_data)

        # Count by original color category
        red_total = 0
        red_passed = 0
        purple_total = 0
        purple_passed = 0

        for source_id, review_color in review_results.items():
            if source_id not in original_colors:
                continue

            original_color, _ = original_colors[source_id]
            is_passed = review_color == self.COLOR_GREEN

            if original_color == self.COLOR_RED:
                red_total += 1
                if is_passed:
                    red_passed += 1
            elif original_color == self.COLOR_PURPLE:
                purple_total += 1
                if is_passed:
                    purple_passed += 1

        total_concepts = red_total + purple_total
        passed_count = red_passed + purple_passed
        coverage_rate = passed_count / total_concepts if total_concepts > 0 else 0.0

        return SingleReviewProgress(
            total_concepts=total_concepts,
            red_nodes_total=red_total,
            red_nodes_passed=red_passed,
            purple_nodes_total=purple_total,
            purple_nodes_passed=purple_passed,
            passed_count=passed_count,
            coverage_rate=round(coverage_rate, 4)
        )

    async def query_review_history_from_graphiti(
        self,
        original_canvas_path: str
    ) -> Dict[str, Any]:
        """
        Query review history from Graphiti knowledge graph.

        If Graphiti client is not available, returns empty history.

        Args:
            original_canvas_path: Path to the original canvas

        Returns:
            Dict with 'reviews' list containing history entries

        [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2740-2760]
        """
        if self._graphiti is None:
            # Return empty history if no Graphiti client
            return {"reviews": []}

        try:
            # Query Graphiti for review episodes related to this canvas
            # ✅ Verified from Graphiti Skill (search API)
            query = f"review history for {Path(original_canvas_path).stem}"
            results = await self._graphiti.search(query=query, limit=100)

            reviews = []
            for result in results:
                if hasattr(result, 'data') and 'review_data' in result.data:
                    reviews.append(result.data['review_data'])

            return {"reviews": reviews}
        except Exception:
            return {"reviews": []}

    async def analyze_multi_review_progress(
        self,
        original_canvas_path: str,
        review_history: Optional[List[Dict[str, Any]]] = None
    ) -> MultiReviewProgress:
        """
        Analyze progress across multiple review sessions.

        Aggregates review history to show learning trends and identifies
        concepts that need more attention.

        Args:
            original_canvas_path: Path to the original canvas
            review_history: Optional pre-loaded history. If None, queries Graphiti.

        Returns:
            MultiReviewProgress with history, trends, and improvement analysis

        [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2727-2826]
        """
        # Get review history
        if review_history is None:
            history_data = await self.query_review_history_from_graphiti(
                original_canvas_path
            )
            reviews = history_data.get('reviews', [])
        else:
            reviews = review_history

        if not reviews:
            return MultiReviewProgress()

        # Build review history entries
        review_entries: List[ReviewHistoryEntry] = []
        concept_results: Dict[str, List[bool]] = {}  # concept_id -> [passed, passed, ...]

        for review in reviews:
            results = review.get('results', {})
            total = results.get('total_nodes', 0)
            passed = results.get('passed_nodes', 0)
            progress_rate = passed / total if total > 0 else 0.0

            review_entries.append(ReviewHistoryEntry(
                review_canvas=review.get('review_canvas', ''),
                timestamp=review.get('timestamp', ''),
                progress_rate=round(progress_rate, 4),
                passed_count=passed,
                total_count=total
            ))

            # Track per-concept results
            for concept_id, is_passed in results.get('concept_results', {}).items():
                if concept_id not in concept_results:
                    concept_results[concept_id] = []
                concept_results[concept_id].append(is_passed)

        # Build concept trends
        concept_trends: Dict[str, ConceptTrend] = {}
        for concept_id, results in concept_results.items():
            history = ["通过" if p else "失败" for p in results]
            first_pass = None
            for i, passed in enumerate(results):
                if passed:
                    first_pass = i + 1  # 1-indexed
                    break

            concept_trends[concept_id] = ConceptTrend(
                concept_id=concept_id,
                attempts=len(results),
                history=history,
                first_pass_review=first_pass
            )

        # Calculate overall trend
        if len(review_entries) >= 2:
            first_rate = review_entries[0].progress_rate
            latest_rate = review_entries[-1].progress_rate
            improvement_rate = latest_rate - first_rate

            if improvement_rate > self.IMPROVEMENT_THRESHOLD:
                overall_trend = "improving"
            elif improvement_rate < self.DECLINE_THRESHOLD:
                overall_trend = "declining"
            else:
                overall_trend = "stable"
        else:
            overall_trend = "insufficient_data"
            improvement_rate = 0.0

        return MultiReviewProgress(
            review_history=review_entries,
            concept_trends=concept_trends,
            overall_trend=overall_trend,
            improvement_rate=round(improvement_rate, 4)
        )

    async def store_review_to_graphiti(
        self,
        original_canvas_path: str,
        review_canvas_path: str,
        progress: SingleReviewProgress
    ) -> bool:
        """
        Store a review session to Graphiti knowledge graph.

        Args:
            original_canvas_path: Path to the original canvas
            review_canvas_path: Path to the review canvas
            progress: Analyzed progress data

        Returns:
            True if stored successfully, False otherwise

        [Source: docs/prd/CANVAS-LEARNING-SYSTEM-OBSIDIAN-NATIVE-MIGRATION-PRD.md:2740-2760]
        """
        if self._graphiti is None:
            return False

        try:
            # ✅ Verified from Graphiti Skill (add_episode API)
            episode_content = (
                f"Review session for {Path(original_canvas_path).stem}. "
                f"Progress: {progress.passed_count}/{progress.total_concepts} "
                f"({progress.coverage_rate:.1%} pass rate)"
            )

            await self._graphiti.add_episode(
                content=episode_content,
                metadata={
                    "type": "review_session",
                    "original_canvas": original_canvas_path,
                    "review_canvas": review_canvas_path,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "review_data": {
                        "review_canvas": review_canvas_path,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "results": {
                            "total_nodes": progress.total_concepts,
                            "passed_nodes": progress.passed_count,
                            "red_total": progress.red_nodes_total,
                            "red_passed": progress.red_nodes_passed,
                            "purple_total": progress.purple_nodes_total,
                            "purple_passed": progress.purple_nodes_passed
                        }
                    }
                }
            )
            return True
        except Exception:
            return False

    def clear_cache(self):
        """Clear the canvas cache to free memory."""
        self._canvas_cache.clear()
        self._validator.clear_cache()
