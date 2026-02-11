# Canvas Learning System - Helper Method Tests
# Split from test_intelligent_grouping_service.py (EPIC-33 P1-6)
"""Tests for duration, priority, agent recommendation, and cluster mapping."""

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.models.intelligent_parallel_models import (
    GroupPriority,
    NodeGroup,
    NodeInGroup,
)
from app.services.intelligent_grouping_service import (
    DEFAULT_AGENT,
    IntelligentGroupingService,
)


class TestEstimatedDuration:
    """Tests for estimated duration calculation - AC-33.4.4."""

    def test_calculate_estimated_duration_minutes(
        self, service: IntelligentGroupingService
    ):
        """Test duration calculation for small node counts."""
        result = service._calculate_estimated_duration(6)
        assert result == "1分钟"

        result = service._calculate_estimated_duration(12)
        assert result == "2分钟"

        result = service._calculate_estimated_duration(30)
        assert result == "5分钟"

    def test_calculate_estimated_duration_hours(
        self, service: IntelligentGroupingService
    ):
        """Test duration calculation for large node counts."""
        result = service._calculate_estimated_duration(360)
        assert result == "1小时"

        result = service._calculate_estimated_duration(420)
        assert result == "1小时10分钟"

    def test_calculate_estimated_duration_minimum(
        self, service: IntelligentGroupingService
    ):
        """Test minimum duration is 1 minute."""
        result = service._calculate_estimated_duration(1)
        assert result == "1分钟"


class TestPriorityAssignment:
    """Tests for priority assignment logic - AC-33.4.4."""

    def test_priority_urgent_keywords(self, service: IntelligentGroupingService):
        """Test urgent priority for error-related content."""
        keywords = ["概念", "问题"]
        node_texts = {"n1": "这个概念有错误需要修复"}
        result = service._assign_priority(keywords, node_texts, 5)
        assert result == GroupPriority.urgent

    def test_priority_high_keywords(self, service: IntelligentGroupingService):
        """Test high priority for review-related content."""
        keywords = ["复习", "重点"]
        node_texts = {"n1": "考试重点内容"}
        result = service._assign_priority(keywords, node_texts, 5)
        assert result == GroupPriority.high

    def test_priority_low_small_cluster(self, service: IntelligentGroupingService):
        """Test low priority for small clusters."""
        keywords = ["概念"]
        node_texts = {"n1": "普通概念"}
        result = service._assign_priority(keywords, node_texts, 2)
        assert result == GroupPriority.low

    def test_priority_medium_default(self, service: IntelligentGroupingService):
        """Test medium priority as default."""
        keywords = ["概念", "定义"]
        node_texts = {"n1": "普通概念内容", "n2": "另一个定义"}
        result = service._assign_priority(keywords, node_texts, 5)
        assert result == GroupPriority.medium


class TestAgentRecommendation:
    """Tests for agent recommendation based on keywords."""

    def test_recommend_comparison_table(self, service: IntelligentGroupingService):
        """Test comparison-table recommendation for comparison keywords."""
        keywords = ["对比", "区别"]
        node_texts = {"n1": "逆否命题vs否命题的区别"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == "comparison-table"

    def test_recommend_oral_explanation(self, service: IntelligentGroupingService):
        """Test oral-explanation recommendation for definition keywords."""
        keywords = ["定义", "概念"]
        node_texts = {"n1": "什么是命题的定义"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == "oral-explanation"

    def test_recommend_example_teaching(self, service: IntelligentGroupingService):
        """Test example-teaching recommendation for example keywords."""
        keywords = ["举例", "示例"]
        node_texts = {"n1": "请举例说明这个问题"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == "example-teaching"

    def test_recommend_default_agent(self, service: IntelligentGroupingService):
        """Test default agent when no keywords match."""
        keywords = ["随机", "内容"]
        node_texts = {"n1": "一些普通文本"}
        result = service._recommend_agent(keywords, node_texts)
        assert result == DEFAULT_AGENT


class TestClusterMapping:
    """Tests for mapping clusters to NodeGroup schema."""

    def test_map_clusters_to_groups(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """Test cluster to NodeGroup mapping."""
        clusters = mock_clustering_result["clusters"]
        groups = service._map_clusters_to_groups(clusters)

        assert len(groups) == 2

        group1 = groups[0]
        assert isinstance(group1, NodeGroup)
        assert group1.group_id == "group-1"
        assert group1.group_name == "逆否命题、充分条件等概念"
        assert len(group1.nodes) == 2
        assert group1.confidence == 0.85
        assert group1.recommended_agent == "comparison-table"

    def test_map_clusters_creates_node_in_group(
        self, service: IntelligentGroupingService, mock_clustering_result: Dict
    ):
        """Test that NodeInGroup objects are created correctly."""
        clusters = mock_clustering_result["clusters"]
        groups = service._map_clusters_to_groups(clusters)

        group1 = groups[0]
        assert all(isinstance(n, NodeInGroup) for n in group1.nodes)
        assert group1.nodes[0].node_id == "node-001"
        assert "逆否命题" in group1.nodes[0].text
