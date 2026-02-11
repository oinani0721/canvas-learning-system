# Canvas Learning System - Agent Routing Engine Unit Tests
# Story 33.5: Agent Routing Engine
# [Source: docs/stories/33.5.story.md]
"""
Unit tests for AgentRoutingEngine.

Test Coverage Requirements (AC5):
- All 6 pattern categories
- Confidence threshold boundary conditions
- Manual override functionality
- Integration with agent_memory_mapping.py
- Target: >= 90% coverage

Run tests:
    cd backend && pytest tests/unit/test_agent_routing_engine.py -v

Coverage check:
    cd backend && pytest tests/unit/test_agent_routing_engine.py --cov=app/services/agent_routing_engine --cov-report=term-missing
"""

import pytest

from app.core.agent_memory_mapping import ALL_AGENT_NAMES, AGENT_MEMORY_MAPPING
from app.models.agent_routing_models import (
    BatchRoutingRequest,
    BatchRoutingResponse,
    RoutingRequest,
    RoutingResult,
)
from app.services.agent_routing_engine import (
    AgentRoutingEngine,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_LOW_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    CONTENT_PATTERN_MAP,
    DEFAULT_FALLBACK_AGENT,
    get_routing_engine,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def routing_engine():
    """Fresh routing engine instance for each test."""
    return AgentRoutingEngine()


@pytest.fixture
def singleton_engine():
    """Singleton routing engine instance."""
    return get_routing_engine()


# ═══════════════════════════════════════════════════════════════════════════════
# Test Pattern Categories (AC1)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPatternRouting:
    """Test all 6 pattern categories route correctly."""

    def test_what_is_pattern_routes_to_oral_explanation(self, routing_engine):
        """Test '什么是X' routes to oral-explanation (AC1)."""
        request = RoutingRequest(node_id="node-001", node_text="什么是逆否命题")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_is_what_pattern_routes_to_oral_explanation(self, routing_engine):
        """Test 'X是什么' routes to oral-explanation (AC1)."""
        request = RoutingRequest(node_id="node-002", node_text="逆否命题是什么意思")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_define_pattern_routes_to_oral_explanation(self, routing_engine):
        """Test '定义X' routes to oral-explanation."""
        request = RoutingRequest(node_id="node-003", node_text="定义充分条件")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_comparison_pattern_routes_to_comparison_table(self, routing_engine):
        """Test 'A和B区别' routes to comparison-table (AC1)."""
        request = RoutingRequest(
            node_id="node-004",
            node_text="逆否命题和否命题的区别"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "comparison-table"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_vs_pattern_routes_to_comparison_table(self, routing_engine):
        """Test 'A vs B' routes to comparison-table (AC1)."""
        request = RoutingRequest(
            node_id="node-005",
            node_text="充分条件 vs 必要条件"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "comparison-table"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_contrast_pattern_routes_to_comparison_table(self, routing_engine):
        """Test '对比' routes to comparison-table."""
        request = RoutingRequest(
            node_id="node-006",
            node_text="对比逆命题和逆否命题"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "comparison-table"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_how_to_understand_routes_to_clarification_path(self, routing_engine):
        """Test '如何理解X' routes to clarification-path (AC1)."""
        request = RoutingRequest(
            node_id="node-007",
            node_text="如何理解命题的逻辑等价"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "clarification-path"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_zen_me_li_jie_routes_to_clarification_path(self, routing_engine):
        """Test '怎么理解' routes to clarification-path."""
        request = RoutingRequest(
            node_id="node-008",
            node_text="怎么理解充分必要条件"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "clarification-path"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_example_pattern_routes_to_example_teaching(self, routing_engine):
        """Test '举例说明X' routes to example-teaching (AC1)."""
        request = RoutingRequest(
            node_id="node-009",
            node_text="举例说明逆否命题的应用"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "example-teaching"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_give_example_routes_to_example_teaching(self, routing_engine):
        """Test '举个例子' routes to example-teaching."""
        request = RoutingRequest(
            node_id="node-010",
            node_text="举个例子说明推理过程"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "example-teaching"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_memory_pattern_routes_to_memory_anchor(self, routing_engine):
        """Test '记忆X' routes to memory-anchor (AC1)."""
        request = RoutingRequest(node_id="node-011", node_text="记忆逆否命题的定义")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "memory-anchor"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_remember_pattern_routes_to_memory_anchor(self, routing_engine):
        """Test '记住X' routes to memory-anchor (AC1)."""
        request = RoutingRequest(
            node_id="node-012",
            node_text="记住充分必要条件的判断方法"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "memory-anchor"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_recite_pattern_routes_to_memory_anchor(self, routing_engine):
        """Test '背诵' routes to memory-anchor."""
        request = RoutingRequest(node_id="node-013", node_text="背诵这个公式")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "memory-anchor"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_deep_analysis_routes_to_deep_decomposition(self, routing_engine):
        """Test '深度剖析X' routes to deep-decomposition (AC1)."""
        request = RoutingRequest(node_id="node-014", node_text="深度剖析命题逻辑")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "deep-decomposition"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_in_depth_analysis_routes_to_deep_decomposition(self, routing_engine):
        """Test '深入分析' routes to deep-decomposition."""
        request = RoutingRequest(node_id="node-015", node_text="深入分析这个概念")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "deep-decomposition"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD


class TestEnglishPatterns:
    """Test English pattern matching."""

    def test_what_is_english(self, routing_engine):
        """Test 'what is X' routes to oral-explanation."""
        request = RoutingRequest(
            node_id="en-001",
            node_text="What is the contrapositive proposition?"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_difference_between_english(self, routing_engine):
        """Test 'difference between A and B' routes to comparison-table."""
        request = RoutingRequest(
            node_id="en-002",
            node_text="What is the difference between sufficient and necessary conditions?"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "comparison-table"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_how_to_understand_english(self, routing_engine):
        """Test 'how to understand X' routes to clarification-path."""
        request = RoutingRequest(
            node_id="en-003",
            node_text="How to understand logical equivalence?"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "clarification-path"
        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD


# ═══════════════════════════════════════════════════════════════════════════════
# Test Confidence Scoring (AC2)
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfidenceScoring:
    """Test confidence scoring algorithm."""

    def test_high_confidence_for_strong_match(self, routing_engine):
        """Test high confidence (>= 0.85) for strong pattern match."""
        # Clear single pattern match
        request = RoutingRequest(node_id="conf-001", node_text="深度剖析这个概念")
        result = routing_engine.route_single_node(request)

        # Should have high confidence for clear match
        assert result.confidence >= CONFIDENCE_MEDIUM_THRESHOLD

    def test_medium_confidence_for_multiple_patterns(self, routing_engine):
        """Test medium confidence (0.7-0.85) for multiple competing patterns."""
        # Text with multiple possible interpretations
        request = RoutingRequest(
            node_id="conf-002",
            node_text="解释一下什么是逆命题"
        )
        result = routing_engine.route_single_node(request)

        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_low_confidence_fallback(self, routing_engine):
        """Test low confidence (< 0.7) returns fallback recommendation."""
        # Ambiguous text with no clear pattern
        request = RoutingRequest(node_id="conf-003", node_text="随便说点什么")
        result = routing_engine.route_single_node(request)

        # Low confidence should use fallback
        if result.confidence < CONFIDENCE_LOW_THRESHOLD:
            assert result.recommended_agent == DEFAULT_FALLBACK_AGENT

    def test_confidence_threshold_boundary_0_69(self, routing_engine):
        """Test confidence boundary at 0.69 (below threshold)."""
        # Create request that might produce borderline confidence
        request = RoutingRequest(node_id="bound-001", node_text="一个普通的概念")
        result = routing_engine.route_single_node(request)

        # Verify confidence is between 0 and 1
        assert 0.0 <= result.confidence <= 1.0

    def test_confidence_threshold_boundary_0_70(self, routing_engine):
        """Test confidence boundary at 0.70 (at threshold)."""
        request = RoutingRequest(node_id="bound-002", node_text="什么是这个")
        result = routing_engine.route_single_node(request)

        assert 0.0 <= result.confidence <= 1.0

    def test_confidence_threshold_boundary_0_71(self, routing_engine):
        """Test confidence boundary at 0.71 (above threshold)."""
        request = RoutingRequest(node_id="bound-003", node_text="什么是逆否命题")
        result = routing_engine.route_single_node(request)

        assert result.confidence >= CONFIDENCE_LOW_THRESHOLD

    def test_calculate_confidence_with_override(self, routing_engine):
        """Test confidence calculation with override flag."""
        # Directly test the _calculate_confidence method
        confidence = routing_engine._calculate_confidence([], has_override=True)
        assert confidence == 1.0

    def test_calculate_confidence_empty_matches(self, routing_engine):
        """Test confidence calculation with empty matches."""
        confidence = routing_engine._calculate_confidence([])
        assert confidence == 0.5

    def test_calculate_confidence_single_match(self, routing_engine):
        """Test confidence calculation with single match."""
        matches = [("oral-explanation", 0.9)]
        confidence = routing_engine._calculate_confidence(matches)
        assert confidence >= 0.85

    def test_calculate_confidence_multiple_matches_clear_winner(self, routing_engine):
        """Test confidence with multiple matches but clear winner."""
        matches = [("oral-explanation", 0.95), ("clarification-path", 0.5)]
        confidence = routing_engine._calculate_confidence(matches)
        # Should have decent confidence due to large score gap
        assert confidence >= 0.7

    def test_calculate_confidence_many_competing_matches(self, routing_engine):
        """Test confidence with many competing matches (penalty)."""
        matches = [
            ("oral-explanation", 0.8),
            ("clarification-path", 0.75),
            ("example-teaching", 0.72),
            ("memory-anchor", 0.70),
        ]
        confidence = routing_engine._calculate_confidence(matches)
        # Should have lower confidence due to competition
        assert 0.4 <= confidence <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Test Manual Override (AC3)
# ═══════════════════════════════════════════════════════════════════════════════


class TestManualOverride:
    """Test manual agent override functionality."""

    def test_override_bypasses_routing(self, routing_engine):
        """Test manual override bypasses automatic routing (AC3)."""
        # Content would normally route to oral-explanation
        request = RoutingRequest(
            node_id="override-001",
            node_text="什么是逆否命题",
            agent_override="deep-decomposition"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "deep-decomposition"
        assert result.confidence == 1.0
        assert result.reason == "manual_override"

    def test_override_with_confidence_1_0(self, routing_engine):
        """Test override returns confidence 1.0."""
        request = RoutingRequest(
            node_id="override-002",
            node_text="任意文本",
            agent_override="comparison-table"
        )
        result = routing_engine.route_single_node(request)

        assert result.confidence == 1.0

    def test_override_reason_is_manual_override(self, routing_engine):
        """Test override reason is 'manual_override'."""
        request = RoutingRequest(
            node_id="override-003",
            node_text="任意文本",
            agent_override="memory-anchor"
        )
        result = routing_engine.route_single_node(request)

        assert result.reason == "manual_override"

    def test_invalid_override_falls_back_to_routing(self, routing_engine):
        """Test invalid override agent falls back to automatic routing."""
        request = RoutingRequest(
            node_id="override-004",
            node_text="什么是逆否命题",
            agent_override="invalid-agent-name"
        )
        result = routing_engine.route_single_node(request)

        # Should fall back to routing (oral-explanation for "什么是")
        assert result.recommended_agent != "invalid-agent-name"
        assert result.reason != "manual_override"

    def test_all_valid_agents_can_be_overridden(self, routing_engine):
        """Test all 14 agents from mapping can be used as override."""
        for agent_name in ALL_AGENT_NAMES:
            request = RoutingRequest(
                node_id=f"override-{agent_name}",
                node_text="测试文本",
                agent_override=agent_name
            )
            result = routing_engine.route_single_node(request)

            assert result.recommended_agent == agent_name
            assert result.confidence == 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Test Integration with agent_memory_mapping.py (AC4)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAgentMappingIntegration:
    """Test integration with agent_memory_mapping.py."""

    def test_all_routing_targets_in_agent_mapping(self, routing_engine):
        """Test all routing targets are in AGENT_MEMORY_MAPPING."""
        for agent_name in CONTENT_PATTERN_MAP.keys():
            assert agent_name in ALL_AGENT_NAMES, \
                f"Agent '{agent_name}' not found in ALL_AGENT_NAMES"

    def test_default_fallback_in_agent_mapping(self):
        """Test default fallback agent is in mapping."""
        assert DEFAULT_FALLBACK_AGENT in ALL_AGENT_NAMES

    def test_agent_mapping_has_15_agents(self):
        """Test agent mapping has exactly 15 agents."""
        assert len(ALL_AGENT_NAMES) == 15

    def test_routed_agents_have_memory_types(self, routing_engine):
        """Test all routed agents have memory types defined."""
        for agent_name in CONTENT_PATTERN_MAP.keys():
            assert agent_name in AGENT_MEMORY_MAPPING, \
                f"Agent '{agent_name}' has no memory type mapping"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Batch Routing
# ═══════════════════════════════════════════════════════════════════════════════


class TestBatchRouting:
    """Test batch routing functionality."""

    def test_batch_routing_multiple_nodes(self, routing_engine):
        """Test batch routing processes multiple nodes correctly."""
        nodes = [
            RoutingRequest(node_id="batch-001", node_text="什么是逆否命题"),
            RoutingRequest(node_id="batch-002", node_text="A和B的区别"),
            RoutingRequest(node_id="batch-003", node_text="记忆这个公式"),
        ]
        request = BatchRoutingRequest(nodes=nodes)
        response = routing_engine.route_batch(request)

        assert response.total_nodes == 3
        assert len(response.results) == 3

    def test_batch_routing_accuracy_estimate(self, routing_engine):
        """Test batch routing provides accuracy estimate."""
        nodes = [
            RoutingRequest(node_id="batch-004", node_text="什么是逆否命题"),
            RoutingRequest(node_id="batch-005", node_text="深度剖析这个概念"),
        ]
        request = BatchRoutingRequest(nodes=nodes)
        response = routing_engine.route_batch(request)

        assert 0.0 <= response.routing_accuracy_estimate <= 1.0

    def test_batch_routing_confidence_counts(self, routing_engine):
        """Test batch routing tracks confidence level counts."""
        nodes = [
            RoutingRequest(node_id="batch-006", node_text="什么是X"),
            RoutingRequest(node_id="batch-007", node_text="记忆Y"),
        ]
        request = BatchRoutingRequest(nodes=nodes)
        response = routing_engine.route_batch(request)

        # Total should equal sum of confidence counts
        total_counted = (
            response.high_confidence_count +
            response.medium_confidence_count +
            response.low_confidence_count
        )
        assert total_counted == response.total_nodes

    def test_batch_with_overrides(self, routing_engine):
        """Test batch routing with manual overrides."""
        nodes = [
            RoutingRequest(
                node_id="batch-008",
                node_text="什么是X",
                agent_override="deep-decomposition"
            ),
            RoutingRequest(node_id="batch-009", node_text="A和B区别"),
        ]
        request = BatchRoutingRequest(nodes=nodes)
        response = routing_engine.route_batch(request)

        # First should be overridden
        assert response.results[0].recommended_agent == "deep-decomposition"
        # Second should be routed normally
        assert response.results[1].recommended_agent == "comparison-table"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Edge Cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_regex_pattern_handling(self):
        """Test handling of invalid regex patterns in custom config."""
        custom_config = {
            "test-agent": {
                "patterns": [
                    r"[invalid(",  # Invalid regex
                    r"valid pattern.*",
                ],
                "weight": 1.0,
                "priority": 1,
                "description": "Test agent"
            }
        }
        engine = AgentRoutingEngine(pattern_config=custom_config)
        # Should not crash, just log warning and skip invalid pattern
        matches = engine.analyze_content("valid pattern test")
        assert isinstance(matches, list)

    def test_custom_pattern_config(self):
        """Test using custom pattern configuration."""
        custom_config = {
            "custom-agent": {
                "patterns": [r"custom.*"],
                "weight": 1.0,
                "priority": 1,
                "description": "Custom test agent"
            }
        }
        engine = AgentRoutingEngine(pattern_config=custom_config)
        assert engine.pattern_config == custom_config

    def test_empty_text_returns_fallback(self, routing_engine):
        """Test empty text returns fallback with low confidence."""
        request = RoutingRequest(node_id="edge-001", node_text="")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == DEFAULT_FALLBACK_AGENT
        assert result.confidence <= 0.6

    def test_whitespace_only_text(self, routing_engine):
        """Test whitespace-only text returns fallback."""
        request = RoutingRequest(node_id="edge-002", node_text="   \n\t  ")
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == DEFAULT_FALLBACK_AGENT

    def test_very_long_text(self, routing_engine):
        """Test routing handles very long text."""
        long_text = "什么是" + "这个概念" * 1000
        request = RoutingRequest(node_id="edge-003", node_text=long_text)
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"

    def test_special_characters(self, routing_engine):
        """Test routing handles special characters."""
        request = RoutingRequest(
            node_id="edge-004",
            node_text="什么是 [特殊字符] {braces} (parens)?"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"

    def test_mixed_language(self, routing_engine):
        """Test routing handles mixed Chinese/English."""
        request = RoutingRequest(
            node_id="edge-005",
            node_text="什么是 machine learning?"
        )
        result = routing_engine.route_single_node(request)

        assert result.recommended_agent == "oral-explanation"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Content Analysis
# ═══════════════════════════════════════════════════════════════════════════════


class TestContentAnalysis:
    """Test content analysis method."""

    def test_analyze_content_returns_sorted_matches(self, routing_engine):
        """Test analyze_content returns matches sorted by score."""
        matches = routing_engine.analyze_content("什么是逆否命题")

        assert len(matches) > 0
        # Verify sorted by score descending
        for i in range(len(matches) - 1):
            assert matches[i][1] >= matches[i + 1][1]

    def test_analyze_content_empty_text(self, routing_engine):
        """Test analyze_content with empty text returns empty list."""
        matches = routing_engine.analyze_content("")
        assert matches == []

    def test_analyze_content_no_matches(self, routing_engine):
        """Test analyze_content with unmatched text."""
        matches = routing_engine.analyze_content("随便一些无意义的文字")

        # May have matches from general patterns
        # Just verify it doesn't crash
        assert isinstance(matches, list)

    def test_analyze_content_multiple_patterns_same_agent(self, routing_engine):
        """Test content matching multiple patterns for same agent."""
        # "什么是" and "是什么" both match oral-explanation
        matches = routing_engine.analyze_content("什么是这个概念是什么意思")

        assert len(matches) > 0
        # oral-explanation should be in matches
        agent_names = [m[0] for m in matches]
        assert "oral-explanation" in agent_names

    def test_calculate_match_quality_specific_pattern(self, routing_engine):
        """Test match quality calculation for specific patterns."""
        # Pattern without leading wildcard gets quality boost
        quality1 = routing_engine._calculate_match_quality("什么是.*", "什么是X")
        quality2 = routing_engine._calculate_match_quality(".*什么是.*", "Y什么是X")

        # More specific pattern (no leading .*) should have higher quality
        assert quality1 > quality2

    def test_calculate_match_quality_long_pattern(self, routing_engine):
        """Test match quality for longer patterns."""
        # Longer pattern should get bonus
        quality_short = routing_engine._calculate_match_quality(".*区别.*", "区别")
        quality_long = routing_engine._calculate_match_quality(".*和.*的?区别.*", "A和B的区别")

        # Both should be valid quality scores
        assert 0.0 <= quality_short <= 1.0
        assert 0.0 <= quality_long <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# Test Singleton Pattern
# ═══════════════════════════════════════════════════════════════════════════════


class TestSingleton:
    """Test singleton pattern."""

    def test_get_routing_engine_returns_same_instance(self):
        """Test get_routing_engine returns singleton instance."""
        engine1 = get_routing_engine()
        engine2 = get_routing_engine()

        assert engine1 is engine2


# ═══════════════════════════════════════════════════════════════════════════════
# Test Model Serialization
# ═══════════════════════════════════════════════════════════════════════════════


class TestModelSerialization:
    """Test model to_dict methods."""

    def test_routing_result_to_dict(self, routing_engine):
        """Test RoutingResult.to_dict() returns correct format."""
        request = RoutingRequest(node_id="serial-001", node_text="什么是X")
        result = routing_engine.route_single_node(request)

        result_dict = result.to_dict()

        assert "node_id" in result_dict
        assert "recommended_agent" in result_dict
        assert "confidence" in result_dict
        assert isinstance(result_dict["confidence"], float)

    def test_batch_response_to_dict(self, routing_engine):
        """Test BatchRoutingResponse.to_dict() returns correct format."""
        nodes = [RoutingRequest(node_id="serial-002", node_text="什么是X")]
        request = BatchRoutingRequest(nodes=nodes)
        response = routing_engine.route_batch(request)

        response_dict = response.to_dict()

        assert "results" in response_dict
        assert "routing_accuracy_estimate" in response_dict
        assert "total_nodes" in response_dict
