# Canvas Learning System - Topic Clustering Service
# PRD Story 4.3: Topic Clustering and Grouping
# [Source: docs/prd/FULL-PRD-REFERENCE.md - Story 4.3]
"""
Topic Clustering Service for Verification Canvas.

Automatically clusters nodes by topic and creates Group nodes
to organize questions in the verification canvas.

[Source: PRD F8 + Story 4.3]
"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple


class TopicClusterer:
    """
    PRD Story 4.3: Topic Clustering and Grouping

    - 自动识别主题分类 (Automatic topic identification)
    - 创建Group节点按主题组织问题 (Create Group nodes by topic)
    - 主题标签清晰 (Clear topic labels)
    """

    # Common topic keywords for Chinese educational content
    TOPIC_KEYWORDS = {
        "定义": ["定义", "概念", "是什么", "含义"],
        "原理": ["原理", "机制", "原因", "为什么"],
        "方法": ["方法", "步骤", "如何", "怎么"],
        "应用": ["应用", "实例", "例子", "场景"],
        "比较": ["区别", "对比", "不同", "相同"],
        "公式": ["公式", "计算", "求", "等于"],
        "性质": ["性质", "特点", "特征", "属性"],
    }

    def __init__(self):
        """Initialize the topic clusterer."""
        pass

    def cluster_nodes(
        self,
        nodes: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Cluster nodes by topic.

        Args:
            nodes: List of Canvas nodes to cluster

        Returns:
            Dict[topic_name, List[nodes]] - Nodes grouped by topic

        PRD Story 4.3 AC:
        - 自动识别主题分类
        - 相似内容归类在一起
        """
        clusters: Dict[str, List[Dict]] = defaultdict(list)

        for node in nodes:
            topic = self._identify_topic(node)
            clusters[topic].append(node)

        # Sort clusters by number of nodes (largest first)
        sorted_clusters = dict(
            sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        )

        return sorted_clusters

    def _identify_topic(self, node: Dict) -> str:
        """
        Identify the topic of a node from its content.

        Uses multiple strategies:
        1. Keyword matching from TOPIC_KEYWORDS
        2. First line extraction (often contains topic)
        3. Fallback to "其他" (Other)
        """
        text = node.get("text", "").strip()

        if not text:
            return "其他"

        # Strategy 1: Keyword matching
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return topic

        # Strategy 2: Extract topic from first line
        first_line = text.split('\n')[0].strip()

        # Remove markdown headers
        first_line = re.sub(r'^#+\s*', '', first_line)

        # Try to extract a short topic (first phrase or segment)
        # Look for common separators
        separators = ['：', ':', '—', '-', '，', ',']
        for sep in separators:
            if sep in first_line:
                potential_topic = first_line.split(sep)[0].strip()
                if 2 <= len(potential_topic) <= 15:
                    return potential_topic

        # If first line is short enough, use it as topic
        if 2 <= len(first_line) <= 15:
            return first_line

        # Truncate if too long
        if len(first_line) > 15:
            return first_line[:12] + "..."

        # Fallback
        return "其他"

    def get_cluster_statistics(
        self,
        clusters: Dict[str, List[Dict]]
    ) -> Dict[str, int]:
        """
        Get statistics about the clusters.

        Returns:
            Dict with topic names and node counts
        """
        return {topic: len(nodes) for topic, nodes in clusters.items()}

    def create_group_layout(
        self,
        clusters: Dict[str, List[Dict]],
        start_x: int = 0,
        start_y: int = 0,
        group_padding: int = 100,
        node_width: int = 400,
        node_height: int = 250,
        node_padding: int = 50
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Create Canvas Group nodes and position child nodes.

        Args:
            clusters: Topic clusters from cluster_nodes()
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            group_padding: Padding between groups
            node_width: Width of each question/answer pair
            node_height: Height of each question/answer pair
            node_padding: Padding between nodes within group

        Returns:
            Tuple of (group_nodes, positioned_nodes_info)

        PRD Story 4.3 AC:
        - 创建Group节点按主题组织问题
        - 主题标签清晰
        """
        import uuid

        group_nodes = []
        node_positions = []

        current_y = start_y

        for topic, topic_nodes in clusters.items():
            # Calculate group dimensions based on number of nodes
            nodes_per_row = 3
            num_rows = (len(topic_nodes) + nodes_per_row - 1) // nodes_per_row
            num_cols = min(len(topic_nodes), nodes_per_row)

            group_width = num_cols * (node_width + node_padding) + node_padding
            group_height = num_rows * (node_height + node_padding) + node_padding + 50  # +50 for label

            # Create Group node
            group_id = uuid.uuid4().hex[:16]
            group_node = {
                "id": group_id,
                "type": "group",
                "x": start_x,
                "y": current_y,
                "width": group_width,
                "height": group_height,
                "label": topic,
            }
            group_nodes.append(group_node)

            # Position child nodes within group
            for i, node in enumerate(topic_nodes):
                col = i % nodes_per_row
                row = i // nodes_per_row

                node_x = start_x + node_padding + col * (node_width + node_padding)
                node_y = current_y + 50 + node_padding + row * (node_height + node_padding)  # +50 for label

                node_positions.append({
                    "original_node": node,
                    "x": node_x,
                    "y": node_y,
                    "width": node_width,
                    "height": node_height,
                    "group_id": group_id,
                    "topic": topic,
                })

            # Move to next group position
            current_y += group_height + group_padding

        return group_nodes, node_positions
