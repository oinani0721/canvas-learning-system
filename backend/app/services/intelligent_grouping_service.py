# Canvas Learning System - Intelligent Grouping Service
# Story 33.4: Intelligent Grouping Service
# ✅ Verified from specs/api/parallel-api.openapi.yml
# ✅ Verified from specs/data/parallel-task.schema.json
# ✅ Integrates cluster_canvas_nodes() from src/canvas_utils.py:11564-11827
"""
IntelligentGroupingService - TF-IDF + K-Means clustering for Canvas nodes.

This service integrates the existing clustering algorithm from canvas_utils.py
and adds subject isolation, priority calculation, and estimated duration features.

Acceptance Criteria:
- AC-33.4.1: Integrates cluster_canvas_nodes() with jieba Chinese tokenization
- AC-33.4.2: Auto optimal K determination (3-10 clusters) using Silhouette Score
- AC-33.4.3: Silhouette Score quality evaluation (warn if < 0.3)
- AC-33.4.4: Estimated processing time and priority calculation
- AC-33.4.5: group_id parameter for subject isolation (依赖30.8)

[Source: docs/stories/33.4.story.md]
[Source: src/canvas_utils.py:11564-11827]
[Source: backend/app/core/subject_config.py]
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.subject_config import (
    build_group_id,
    extract_subject_from_canvas_path,
)
from app.models.intelligent_parallel_models import (
    GroupPriority,
    IntelligentParallelResponse,
    NodeGroup,
    NodeInGroup,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# [Source: docs/stories/33.4.story.md#Implementation Notes]
# ═══════════════════════════════════════════════════════════════════════════════

# Average agent processing time per node (seconds)
# Used for estimated_duration calculation
AVERAGE_AGENT_PROCESSING_SECONDS = 10

# Silhouette Score quality threshold
# Recommend re-clustering if below this value
# [Source: docs/stories/33.4.story.md#AC-33.4.3]
SILHOUETTE_QUALITY_THRESHOLD = 0.3

# Priority keywords for assignment
# [Source: docs/stories/33.4.story.md#Implementation Notes - Priority Assignment Rules]
URGENT_KEYWORDS = ["错误", "失败", "问题", "bug", "error", "urgent"]
HIGH_KEYWORDS = ["复习", "重点", "考试", "重要", "review", "exam"]

# Agent recommendation keyword mapping
# [Source: docs/stories/33.4.story.md#Implementation Notes - Agent Recommendation Mapping]
AGENT_KEYWORD_MAPPING = {
    "comparison-table": ["对比", "区别", "比较", "不同", "vs", "versus"],
    "oral-explanation": ["什么是", "定义", "是什么", "概念", "解释"],
    "example-teaching": ["举例", "例子", "示例", "instance", "example"],
    "clarification-path": ["理解", "为什么", "原因", "how", "why"],
    "memory-anchor": ["记忆", "记住", "背诵", "remember"],
    "deep-decomposition": ["深度", "剖析", "分析", "深入"],
}
DEFAULT_AGENT = "four-level-explanation"

# Group emoji mapping based on recommended agent
GROUP_EMOJI_MAPPING = {
    "comparison-table": "📊",
    "oral-explanation": "📖",
    "example-teaching": "🎯",
    "clarification-path": "🔍",
    "memory-anchor": "🧠",
    "deep-decomposition": "🔬",
    "four-level-explanation": "📚",
    "basic-decomposition": "📋",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════════════════

class IntelligentGroupingError(Exception):
    """Base exception for intelligent grouping errors."""
    pass


class CanvasNotFoundError(IntelligentGroupingError):
    """Canvas file not found."""
    pass


class InsufficientNodesError(IntelligentGroupingError):
    """Not enough nodes for clustering."""
    pass


class ClusteringFailedError(IntelligentGroupingError):
    """Clustering algorithm failed."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Service Class
# ═══════════════════════════════════════════════════════════════════════════════

class IntelligentGroupingService:
    """
    Service for intelligent grouping of Canvas nodes using TF-IDF + K-Means.

    Integrates the existing clustering algorithm from canvas_utils.py
    and adds subject isolation for multi-subject learning environments.

    [Source: docs/stories/33.4.story.md]
    """

    def __init__(self, canvas_base_path: Optional[str] = None) -> None:
        """
        Initialize IntelligentGroupingService.

        Args:
            canvas_base_path: Base path for resolving canvas files.
                              If None, uses current directory.

        [Source: docs/stories/33.4.story.md#Task-1.1]
        """
        self.canvas_base_path = Path(canvas_base_path) if canvas_base_path else Path.cwd()
        logger.info(f"IntelligentGroupingService initialized with base_path: {self.canvas_base_path}")

    async def analyze_canvas(
        self,
        canvas_path: str,
        target_color: str = "3",
        max_groups: Optional[int] = None,
        min_nodes_per_group: int = 2,
    ) -> IntelligentParallelResponse:
        """
        Analyze canvas and return intelligent groupings with agent recommendations.

        Uses TF-IDF vectorization + K-Means clustering to semantically group nodes,
        then recommends appropriate agents based on cluster keywords.

        [Source: docs/stories/33.4.story.md#AC-33.4.1 - AC-33.4.5]
        [Source: specs/api/parallel-api.openapi.yml#/paths/~1canvas~1intelligent-parallel/post]

        Args:
            canvas_path: Path to canvas file (relative to base_path or absolute)
            target_color: Target node color to cluster ("1"-"6", default "3" for purple)
            max_groups: Maximum number of groups (optional, auto-determined if None)
            min_nodes_per_group: Minimum nodes per group (default 2)

        Returns:
            IntelligentParallelResponse with grouped nodes, subject isolation info,
            clustering quality metrics, and estimated duration.

        Raises:
            CanvasNotFoundError: If canvas file not found
            InsufficientNodesError: If not enough nodes for clustering
            ClusteringFailedError: If clustering algorithm fails
        """
        logger.info(
            f"analyze_canvas called: path={canvas_path}, color={target_color}, "
            f"max_groups={max_groups}, min_nodes={min_nodes_per_group}"
        )

        # AC-33.4.5: Extract subject and build group_id (依赖30.8)
        subject = extract_subject_from_canvas_path(canvas_path)
        canvas_name = Path(canvas_path).stem
        subject_group_id = build_group_id(subject, canvas_name)
        logger.debug(f"Subject isolation: subject={subject}, group_id={subject_group_id}")

        # Resolve canvas path
        full_canvas_path = self._resolve_canvas_path(canvas_path)

        # Check canvas exists
        if not full_canvas_path.exists():
            raise CanvasNotFoundError(f"Canvas file '{canvas_path}' not found")

        # Run clustering in thread pool (sync code wrapped for async)
        # [Source: docs/stories/33.4.story.md#Task-2.3 - asyncio.to_thread]
        clustering_result = await asyncio.to_thread(
            self._perform_clustering,
            full_canvas_path,
            target_color,
            max_groups,
            min_nodes_per_group,
        )

        # Extract clustering metrics
        silhouette_score = clustering_result.get("optimization_stats", {}).get("clustering_accuracy", 0.0)
        recommended_k = clustering_result.get("clustering_parameters", {}).get("n_clusters", 0)
        clusters = clustering_result.get("clusters", [])

        # Check quality threshold
        if silhouette_score < SILHOUETTE_QUALITY_THRESHOLD:
            logger.warning(
                f"Low clustering quality: silhouette={silhouette_score:.3f} < {SILHOUETTE_QUALITY_THRESHOLD}. "
                f"Consider re-clustering with different parameters."
            )

        # Map clusters to NodeGroup schema
        groups = self._map_clusters_to_groups(clusters)

        # Calculate total nodes
        total_nodes = sum(len(g.nodes) for g in groups)

        # AC-33.4.4: Calculate estimated duration
        estimated_duration = self._calculate_estimated_duration(total_nodes)

        # Generate resource warning if many nodes
        resource_warning = None
        if total_nodes > 50:
            resource_warning = f"大量节点({total_nodes}个)，建议分批处理或降低并发数"

        return IntelligentParallelResponse(
            canvas_path=canvas_path,
            total_nodes=total_nodes,
            groups=groups,
            estimated_duration=estimated_duration,
            resource_warning=resource_warning,
            # AC-33.4.5: Subject isolation fields
            subject=subject,
            subject_group_id=subject_group_id,
            # AC-33.4.3: Clustering quality metrics
            silhouette_score=silhouette_score,
            recommended_k=recommended_k,
        )

    def _resolve_canvas_path(self, canvas_path: str) -> Path:
        """
        Resolve canvas path to absolute path.

        Args:
            canvas_path: Relative or absolute canvas path

        Returns:
            Resolved absolute Path
        """
        path = Path(canvas_path)
        if path.is_absolute():
            return path
        return self.canvas_base_path / canvas_path

    def _perform_clustering(
        self,
        canvas_path: Path,
        target_color: str,
        max_groups: Optional[int],
        min_nodes_per_group: int,
    ) -> Dict[str, Any]:
        """
        Perform TF-IDF + K-Means clustering on canvas nodes.

        This method runs synchronously and should be called via asyncio.to_thread().

        [Source: docs/stories/33.4.story.md#AC-33.4.1 - AC-33.4.2]
        [Source: src/canvas_utils.py:11564-11827]

        Args:
            canvas_path: Absolute path to canvas file
            target_color: Target node color to filter
            max_groups: Maximum number of clusters (None for auto)
            min_nodes_per_group: Minimum nodes per cluster

        Returns:
            Clustering result dictionary from canvas_utils.cluster_canvas_nodes()

        Raises:
            InsufficientNodesError: If not enough nodes
            ClusteringFailedError: If clustering fails
        """
        # Import CanvasBusinessLogic (heavy import, do it lazily)
        try:
            # Add src directory to path if needed
            src_path = Path(__file__).parent.parent.parent.parent / "src"
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))

            from canvas_utils import CanvasBusinessLogic
        except ImportError as e:
            logger.error(f"Failed to import CanvasBusinessLogic: {e}")
            raise ClusteringFailedError(f"Cannot import clustering module: {e}")

        try:
            # Initialize canvas business logic
            logic = CanvasBusinessLogic(str(canvas_path))

            # Filter nodes by target color first
            filtered_nodes = []
            for node in logic.canvas_data.get("nodes", []):
                if (node.get("type") == "text" and
                    node.get("color") == target_color and
                    node.get("text", "").strip()):
                    filtered_nodes.append(node)

            if len(filtered_nodes) < min_nodes_per_group:
                raise InsufficientNodesError(
                    f"Not enough nodes with color '{target_color}'. "
                    f"Found {len(filtered_nodes)}, need at least {min_nodes_per_group}"
                )

            # Store original nodes and temporarily replace for clustering
            original_nodes = logic.canvas_data["nodes"]
            logic.canvas_data["nodes"] = filtered_nodes

            try:
                # AC-33.4.2: Auto-K selection when max_groups is None
                # The cluster_canvas_nodes() method handles this internally
                result = logic.cluster_canvas_nodes(
                    n_clusters=max_groups,  # None = auto-determine
                    similarity_threshold=SILHOUETTE_QUALITY_THRESHOLD,
                    create_groups=False,  # Don't create visual groups, just cluster
                    min_cluster_size=min_nodes_per_group,
                )

                # Add node texts to clusters for mapping
                for cluster in result.get("clusters", []):
                    cluster["node_texts"] = {}
                    for node_id in cluster.get("nodes", []):
                        for node in filtered_nodes:
                            if node["id"] == node_id:
                                cluster["node_texts"][node_id] = node.get("text", "")
                                break

                return result

            finally:
                # Restore original nodes
                logic.canvas_data["nodes"] = original_nodes

        except InsufficientNodesError:
            raise
        except ValueError as e:
            # Catch ValueError from cluster_canvas_nodes
            if "节点数量不足" in str(e) or "insufficient" in str(e).lower():
                raise InsufficientNodesError(str(e))
            raise ClusteringFailedError(f"Clustering failed: {e}")
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            raise ClusteringFailedError(f"Clustering failed: {e}")

    def _map_clusters_to_groups(self, clusters: List[Dict[str, Any]]) -> List[NodeGroup]:
        """
        Map clustering results to NodeGroup schema.

        [Source: docs/stories/33.4.story.md#Task-2.4]
        [Source: specs/api/parallel-api.openapi.yml#/components/schemas/NodeGroup]

        Args:
            clusters: Clustering result from canvas_utils.cluster_canvas_nodes()

        Returns:
            List of NodeGroup models
        """
        groups = []

        for i, cluster in enumerate(clusters):
            cluster_id = cluster.get("id", f"cluster-{i+1}")
            cluster_label = cluster.get("label", f"分组{i+1}")
            keywords = cluster.get("top_keywords", [])
            confidence = cluster.get("confidence", 0.0)
            node_ids = cluster.get("nodes", [])
            node_texts = cluster.get("node_texts", {})

            # Build NodeInGroup list
            nodes = []
            for node_id in node_ids:
                text = node_texts.get(node_id, "")
                nodes.append(NodeInGroup(node_id=node_id, text=text))

            # Recommend agent based on keywords
            recommended_agent = self._recommend_agent(keywords, node_texts)

            # Assign priority based on content
            priority = self._assign_priority(keywords, node_texts, len(nodes))

            # Get emoji for agent
            emoji = GROUP_EMOJI_MAPPING.get(recommended_agent, "📚")

            groups.append(NodeGroup(
                group_id=f"group-{i+1}",
                group_name=cluster_label,
                group_emoji=emoji,
                nodes=nodes,
                recommended_agent=recommended_agent,
                confidence=confidence,
                priority=priority,
            ))

        return groups

    def _recommend_agent(
        self,
        keywords: List[str],
        node_texts: Dict[str, str],
    ) -> str:
        """
        Recommend appropriate agent based on cluster keywords and content.

        [Source: docs/stories/33.4.story.md#Implementation Notes - Agent Recommendation Mapping]

        Args:
            keywords: Top keywords from cluster
            node_texts: Node ID to text mapping

        Returns:
            Recommended agent name
        """
        # Combine keywords and node texts for matching
        all_text = " ".join(keywords)
        all_text += " " + " ".join(node_texts.values())
        all_text_lower = all_text.lower()

        # Check each agent's keywords
        for agent, agent_keywords in AGENT_KEYWORD_MAPPING.items():
            for keyword in agent_keywords:
                if keyword.lower() in all_text_lower:
                    return agent

        return DEFAULT_AGENT

    def _assign_priority(
        self,
        keywords: List[str],
        node_texts: Dict[str, str],
        node_count: int,
    ) -> GroupPriority:
        """
        Assign priority based on cluster content and size.

        [Source: docs/stories/33.4.story.md#Implementation Notes - Priority Assignment Rules]

        Priority rules:
        - urgent: Contains error-related keywords
        - high: Contains review/exam keywords
        - medium: Default for most clusters
        - low: Small clusters (< 3 nodes)

        Args:
            keywords: Top keywords from cluster
            node_texts: Node ID to text mapping
            node_count: Number of nodes in cluster

        Returns:
            GroupPriority enum value
        """
        # Combine text for keyword search
        all_text = " ".join(keywords)
        all_text += " " + " ".join(node_texts.values())
        all_text_lower = all_text.lower()

        # Check for urgent keywords
        for keyword in URGENT_KEYWORDS:
            if keyword in all_text_lower:
                return GroupPriority.urgent

        # Check for high priority keywords
        for keyword in HIGH_KEYWORDS:
            if keyword in all_text_lower:
                return GroupPriority.high

        # Low priority for small clusters
        if node_count < 3:
            return GroupPriority.low

        # Default to medium
        return GroupPriority.medium

    def _calculate_estimated_duration(self, total_nodes: int) -> str:
        """
        Calculate estimated processing duration.

        [Source: docs/stories/33.4.story.md#AC-33.4.4]
        [Source: docs/stories/33.4.story.md#Implementation Notes - Estimated Duration Calculation]

        Args:
            total_nodes: Total number of nodes to process

        Returns:
            Human-readable duration string in Chinese (e.g., "2分钟")
        """
        seconds = total_nodes * AVERAGE_AGENT_PROCESSING_SECONDS
        minutes = max(1, seconds // 60)

        if minutes < 60:
            return f"{minutes}分钟"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes > 0:
                return f"{hours}小时{remaining_minutes}分钟"
            return f"{hours}小时"


# ═══════════════════════════════════════════════════════════════════════════════
# Factory Function
# ═══════════════════════════════════════════════════════════════════════════════

def get_intelligent_grouping_service(
    canvas_base_path: Optional[str] = None,
) -> IntelligentGroupingService:
    """
    Factory function for creating IntelligentGroupingService instances.

    Args:
        canvas_base_path: Base path for canvas files

    Returns:
        Configured IntelligentGroupingService instance
    """
    return IntelligentGroupingService(canvas_base_path=canvas_base_path)
