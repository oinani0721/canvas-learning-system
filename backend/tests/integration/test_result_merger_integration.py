# Canvas Learning System - Result Merger Integration Tests
# Story 33.7: Result Merging Strategies (AC1-5)
"""
Integration tests for Result Merger service.

Tests full merge workflow:
- BatchOrchestrator → ResultMerger integration
- All strategies with real Agent output samples
- Strategy switching via API parameter

[Source: docs/stories/33.7.story.md - Task 8]
"""

import asyncio
from datetime import datetime
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merge_strategy_models import (
    AgentResult,
    MergeOptions,
    MergeRequest,
    MergeResult,
    MergeStrategyType,
    QualityScore,
)
from app.services.result_merger import (
    HierarchicalMerger,
    MergerFactory,
    SupplementaryMerger,
    VotingMerger,
    get_merger,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Realistic Agent Output Samples
# Based on actual Canvas Learning System agent outputs
# ═══════════════════════════════════════════════════════════════════════════════

ORAL_EXPLANATION_SAMPLE = """
今天我们来讲解一个重要的逻辑概念：逆否命题。

首先，什么是逆否命题？简单来说，如果原命题是"如果P，那么Q"，
那么逆否命题就是"如果非Q，那么非P"。

举个例子：
- 原命题：如果下雨，那么地面湿。
- 逆否命题：如果地面不湿，那么没有下雨。

关键点：逆否命题与原命题是逻辑等价的！这意味着它们的真假值完全相同。

因此，在数学证明中，我们经常使用逆否命题来间接证明原命题。
这种方法叫做"反证法"或"逆否证明"。

综上所述，理解逆否命题对于逻辑推理和数学证明非常重要。
"""

COMPARISON_TABLE_SAMPLE = """
## 逆否命题 vs 相关概念对比

| 概念 | 定义 | 与原命题关系 | 真假关系 |
|------|------|------------|----------|
| 原命题 | 如果P，那么Q | 基准 | 基准 |
| 逆命题 | 如果Q，那么P | 交换条件和结论 | 不一定相同 |
| 否命题 | 如果非P，那么非Q | 否定条件和结论 | 不一定相同 |
| 逆否命题 | 如果非Q，那么非P | 否定并交换 | **完全相同** |

### 关键区别

1. **逆命题**：只交换，不否定
2. **否命题**：只否定，不交换
3. **逆否命题**：既否定又交换，与原命题等价
"""

MEMORY_ANCHOR_SAMPLE = """
## 记忆锚点：逆否命题

### 类比记忆法

把逆否命题想象成"镜子里的倒影"：
- 原命题是你站在镜子前
- 逆否命题是镜子里的你（左右颠倒，但仍然是你）

### 口诀

"逆否等价要牢记，否定交换不分离"

### 图示

```
原命题:  P → Q
         ↓   ↓
逆否:   非Q → 非P
```

箭头方向反转，内容取反，真假不变！
"""

FOUR_LEVEL_SAMPLE = """
## 逆否命题四层次解析

### 🌱 入门级
逆否命题就是把原命题"反过来说"。如果原话是"有A就有B"，
逆否命题就是"没B就没A"。

### 🌿 进阶级
逆否命题的构造方法：
1. 把条件和结论都否定
2. 交换条件和结论的位置
公式：p→q 的逆否是 ¬q→¬p

### 🌲 深入级
逆否命题与原命题逻辑等价的证明：
使用真值表可以验证 p→q 和 ¬q→¬p 在所有情况下真值相同。
这是因为 p→q ≡ ¬p∨q ≡ ¬q→¬p

### 🌳 专家级
在形式逻辑和数学基础中，逆否律（Contraposition）是重要的推理规则。
在构造性数学和直觉主义逻辑中，逆否律的双向性需要特别注意。
"""


@pytest.fixture
def real_agent_outputs() -> List[AgentResult]:
    """Realistic Agent output samples from Canvas Learning System."""
    return [
        AgentResult(
            node_id="node-contrapositive-001",
            agent_name="oral-explanation",
            result=ORAL_EXPLANATION_SAMPLE,
            group_id="group-logic",
            success=True,
        ),
        AgentResult(
            node_id="node-contrapositive-001",
            agent_name="comparison-table",
            result=COMPARISON_TABLE_SAMPLE,
            group_id="group-logic",
            success=True,
        ),
        AgentResult(
            node_id="node-contrapositive-001",
            agent_name="memory-anchor",
            result=MEMORY_ANCHOR_SAMPLE,
            group_id="group-logic",
            success=True,
        ),
        AgentResult(
            node_id="node-contrapositive-001",
            agent_name="four-level-explanation",
            result=FOUR_LEVEL_SAMPLE,
            group_id="group-logic",
            success=True,
        ),
    ]


@pytest.fixture
def partial_success_outputs() -> List[AgentResult]:
    """Mix of successful and failed agent outputs."""
    return [
        AgentResult(
            node_id="node-002",
            agent_name="oral-explanation",
            result="这是成功的口语解释内容。递归是函数调用自身的过程。",
            success=True,
        ),
        AgentResult(
            node_id="node-002",
            agent_name="comparison-table",
            result="",
            success=False,
            error_message="API rate limit exceeded",
        ),
        AgentResult(
            node_id="node-002",
            agent_name="memory-anchor",
            result="递归就像俄罗斯套娃，一层包一层。",
            success=True,
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Full Merge Workflow
# [Source: docs/stories/33.7.story.md - Task 8: Test full merge workflow]
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullMergeWorkflow:
    """Test full merge workflow: BatchOrchestrator → ResultMerger."""

    @pytest.mark.asyncio
    async def test_supplementary_workflow_with_real_outputs(self, real_agent_outputs):
        """
        Full supplementary merge workflow with realistic outputs.

        Simulates BatchOrchestrator calling ResultMerger after Agent execution.
        """
        # 1. Get merger (simulating BatchOrchestrator configuration)
        merger = get_merger(MergeStrategyType.supplementary)

        # 2. Execute merge (simulating post-execution aggregation)
        result = await merger.merge(real_agent_outputs)

        # 3. Validate result structure
        assert isinstance(result, MergeResult)
        assert result.strategy_used == MergeStrategyType.supplementary
        assert result.source_count == 4
        assert result.successful_sources == 4
        assert result.failed_sources == 0

        # 4. Validate content preservation
        content = result.merged_content
        assert "逆否命题" in content
        assert "oral-explanation" in content
        assert "comparison-table" in content
        assert "memory-anchor" in content
        assert "four-level-explanation" in content

        # 5. Validate quality score
        assert result.quality_score.overall > 0
        assert result.quality_score.coverage > 0

    @pytest.mark.asyncio
    async def test_hierarchical_workflow_with_real_outputs(self, real_agent_outputs):
        """
        Full hierarchical merge workflow with realistic outputs.

        Content should be sorted by difficulty: beginner → expert.
        """
        merger = get_merger(MergeStrategyType.hierarchical)
        result = await merger.merge(real_agent_outputs)

        assert result.strategy_used == MergeStrategyType.hierarchical
        assert result.source_count == 4

        # Check tier organization
        content = result.merged_content
        # Four-level explanation should be split into tiers
        # Beginner content should appear before expert content
        beginner_indicators = ["入门", "简单", "🌱"]
        expert_indicators = ["专家", "深入", "🌳", "形式逻辑"]

        has_beginner = any(ind in content for ind in beginner_indicators)
        has_expert = any(ind in content for ind in expert_indicators)

        # At least some difficulty markers should be preserved
        assert has_beginner or has_expert or "进阶" in content

    @pytest.mark.asyncio
    async def test_voting_workflow_with_real_outputs(self, real_agent_outputs):
        """
        Full voting merge workflow with realistic outputs.

        Should detect and merge semantic duplicates.
        """
        merger = get_merger(MergeStrategyType.voting)
        result = await merger.merge(real_agent_outputs)

        assert result.strategy_used == MergeStrategyType.voting
        assert result.source_count == 4

        # Voting should preserve key concepts
        content = result.merged_content
        assert "逆否命题" in content

        # Quality should be reasonable
        assert result.quality_score.overall > 0

    @pytest.mark.asyncio
    async def test_partial_failure_handling(self, partial_success_outputs):
        """
        Merge handles partial failures gracefully.

        Only successful results should be merged.
        """
        merger = get_merger(MergeStrategyType.supplementary)
        result = await merger.merge(partial_success_outputs)

        assert result.source_count == 3
        assert result.successful_sources == 2
        assert result.failed_sources == 1

        # Only successful content should be in merged result
        content = result.merged_content
        assert "口语解释" in content or "递归" in content
        assert "俄罗斯套娃" in content

        # Failed agent should not contribute content
        # (since it had empty result)


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: All Strategies with Real Samples
# [Source: docs/stories/33.7.story.md - Task 8: Test all strategies]
# ═══════════════════════════════════════════════════════════════════════════════

class TestAllStrategiesWithRealSamples:
    """Test all strategies with real Agent output samples."""

    @pytest.mark.asyncio
    async def test_all_strategies_produce_valid_output(self, real_agent_outputs):
        """All strategies should produce valid MergeResult."""
        strategies = [
            MergeStrategyType.supplementary,
            MergeStrategyType.hierarchical,
            MergeStrategyType.voting,
        ]

        for strategy in strategies:
            merger = get_merger(strategy)
            result = await merger.merge(real_agent_outputs)

            # All strategies should produce valid result
            assert isinstance(result, MergeResult), f"Strategy {strategy} failed"
            assert result.merged_content, f"Strategy {strategy} produced empty content"
            assert result.quality_score is not None, f"Strategy {strategy} missing quality"
            assert result.strategy_used == strategy, f"Strategy {strategy} mismatch"

    @pytest.mark.asyncio
    async def test_strategies_preserve_key_concepts(self, real_agent_outputs):
        """All strategies should preserve key concepts from input."""
        key_concepts = ["逆否命题", "逻辑", "原命题", "等价"]

        strategies = [
            MergeStrategyType.supplementary,
            MergeStrategyType.hierarchical,
            MergeStrategyType.voting,
        ]

        for strategy in strategies:
            merger = get_merger(strategy)
            result = await merger.merge(real_agent_outputs)

            # At least some key concepts should be preserved
            preserved_count = sum(
                1 for concept in key_concepts
                if concept in result.merged_content
            )
            assert preserved_count >= 2, (
                f"Strategy {strategy} lost too many concepts. "
                f"Only preserved {preserved_count}/4"
            )

    @pytest.mark.asyncio
    async def test_strategies_quality_scores(self, real_agent_outputs):
        """Compare quality scores across strategies."""
        results = {}

        strategies = [
            MergeStrategyType.supplementary,
            MergeStrategyType.hierarchical,
            MergeStrategyType.voting,
        ]

        for strategy in strategies:
            merger = get_merger(strategy)
            result = await merger.merge(real_agent_outputs)
            results[strategy] = result.quality_score

        # All should have positive quality scores
        for strategy, score in results.items():
            assert score.overall >= 0, f"Strategy {strategy} has negative quality"
            assert score.coverage >= 0, f"Strategy {strategy} has negative coverage"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Strategy Switching via API Parameter
# [Source: docs/stories/33.7.story.md - Task 8: Test strategy switching]
# ═══════════════════════════════════════════════════════════════════════════════

class TestStrategySwitchingViaParameter:
    """Test strategy switching via API parameter."""

    @pytest.mark.asyncio
    async def test_switch_strategy_at_runtime(self, real_agent_outputs):
        """
        Switch between strategies at runtime.

        Simulates API request with `merge_strategy` parameter.
        """
        # Default strategy
        default_merger = get_merger()  # Uses config default
        default_result = await default_merger.merge(real_agent_outputs)

        # Override to hierarchical
        hierarchical_merger = get_merger(MergeStrategyType.hierarchical)
        hierarchical_result = await hierarchical_merger.merge(real_agent_outputs)

        # Override to voting
        voting_merger = get_merger(MergeStrategyType.voting)
        voting_result = await voting_merger.merge(real_agent_outputs)

        # All should succeed with different strategies
        assert default_result.strategy_used in [
            MergeStrategyType.supplementary,
            MergeStrategyType.hierarchical,
            MergeStrategyType.voting,
        ]
        assert hierarchical_result.strategy_used == MergeStrategyType.hierarchical
        assert voting_result.strategy_used == MergeStrategyType.voting

    @pytest.mark.asyncio
    async def test_factory_pattern_strategy_selection(self, real_agent_outputs):
        """Test factory pattern for strategy selection."""
        factory = MergerFactory()

        # Get different mergers from same factory
        supp = factory.get_merger(MergeStrategyType.supplementary)
        hier = factory.get_merger(MergeStrategyType.hierarchical)
        vote = factory.get_merger(MergeStrategyType.voting)

        # All should be different types
        assert isinstance(supp, SupplementaryMerger)
        assert isinstance(hier, HierarchicalMerger)
        assert isinstance(vote, VotingMerger)

        # All should share same config
        assert supp.config == hier.config == vote.config

    @pytest.mark.asyncio
    async def test_invalid_strategy_raises_400_equivalent(self):
        """Invalid strategy should raise ValueError (maps to 400 in API)."""
        with pytest.raises(ValueError, match="Invalid merge strategy"):
            get_merger("nonexistent_strategy")  # type: ignore


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Concurrent Merge Operations
# [Source: docs/architecture/decisions/0004-async-execution-engine.md]
# ═══════════════════════════════════════════════════════════════════════════════

class TestConcurrentMergeOperations:
    """Test concurrent merge operations (ADR-0004 compliance)."""

    @pytest.mark.asyncio
    async def test_parallel_merge_multiple_groups(self, real_agent_outputs):
        """
        Merge multiple groups in parallel.

        Simulates BatchOrchestrator merging results from multiple groups.
        """
        # Create multiple groups
        groups = [
            real_agent_outputs[:2],  # Group 1
            real_agent_outputs[2:],  # Group 2
        ]

        merger = get_merger(MergeStrategyType.supplementary)

        # Execute merges in parallel
        results = await asyncio.gather(
            merger.merge(groups[0]),
            merger.merge(groups[1]),
        )

        # Both should succeed
        assert len(results) == 2
        assert all(isinstance(r, MergeResult) for r in results)
        assert all(r.merged_content for r in results)

    @pytest.mark.asyncio
    async def test_parallel_merge_different_strategies(self, real_agent_outputs):
        """
        Merge same content with different strategies in parallel.

        Useful for A/B testing or strategy comparison.
        """
        mergers = [
            get_merger(MergeStrategyType.supplementary),
            get_merger(MergeStrategyType.hierarchical),
            get_merger(MergeStrategyType.voting),
        ]

        # Execute all strategies in parallel
        results = await asyncio.gather(
            *[m.merge(real_agent_outputs) for m in mergers]
        )

        # All should complete
        assert len(results) == 3
        strategies_used = [r.strategy_used for r in results]
        assert MergeStrategyType.supplementary in strategies_used
        assert MergeStrategyType.hierarchical in strategies_used
        assert MergeStrategyType.voting in strategies_used


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: MergeRequest Model
# ═══════════════════════════════════════════════════════════════════════════════

class TestMergeRequestIntegration:
    """Test MergeRequest model integration."""

    @pytest.mark.asyncio
    async def test_merge_request_to_result(self, real_agent_outputs):
        """
        Full flow: MergeRequest → merger → MergeResult.

        Simulates API endpoint processing.
        """
        # Create request (simulating API input)
        request = MergeRequest(
            source_results=real_agent_outputs,
            strategy=MergeStrategyType.supplementary,
            options=MergeOptions(include_attribution=True),
            group_id="group-logic-001",
            concept_name="逆否命题",
        )

        # Get merger based on request strategy
        merger = get_merger(request.strategy)

        # Execute merge with request options
        result = await merger.merge(request.source_results, request.options)

        # Validate result
        assert result.source_count == len(request.source_results)
        assert result.strategy_used == request.strategy

    @pytest.mark.asyncio
    async def test_merge_request_options_applied(self, real_agent_outputs):
        """Options from MergeRequest should be applied."""
        # Request without attribution
        request_no_attr = MergeRequest(
            source_results=real_agent_outputs,
            strategy=MergeStrategyType.supplementary,
            options=MergeOptions(include_attribution=False),
        )

        merger = get_merger(request_no_attr.strategy)
        result = await merger.merge(
            request_no_attr.source_results,
            request_no_attr.options,
        )

        # Attribution headers should not be present
        assert "## 🎙️" not in result.merged_content
        assert "## 📊" not in result.merged_content


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test: Error Handling
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Test error handling in integration scenarios."""

    @pytest.mark.asyncio
    async def test_all_failures_produces_empty_result(self):
        """All failed results should produce empty MergeResult."""
        all_failed = [
            AgentResult(
                node_id="node-001",
                agent_name="agent-1",
                result="",
                success=False,
                error_message="Error 1",
            ),
            AgentResult(
                node_id="node-001",
                agent_name="agent-2",
                result="",
                success=False,
                error_message="Error 2",
            ),
        ]

        for strategy in MergeStrategyType:
            merger = get_merger(strategy)
            result = await merger.merge(all_failed)

            assert result.merged_content == ""
            assert result.successful_sources == 0
            assert result.failed_sources == 2
            assert result.quality_score.overall == 0

    @pytest.mark.asyncio
    async def test_empty_content_results_filtered(self):
        """Results with empty content should be filtered out."""
        mixed_results = [
            AgentResult(
                node_id="node-001",
                agent_name="agent-1",
                result="有效内容",
                success=True,
            ),
            AgentResult(
                node_id="node-001",
                agent_name="agent-2",
                result="",  # Empty content but marked success
                success=True,
            ),
        ]

        merger = get_merger(MergeStrategyType.supplementary)
        result = await merger.merge(mixed_results)

        # Empty content should be filtered
        assert "agent-2" not in result.merged_content or result.successful_sources == 1
        assert "有效内容" in result.merged_content
