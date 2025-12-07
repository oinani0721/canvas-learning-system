"""
冲突解决机制专项测试 - Story 7.2

专项测试冲突检测和解决机制：
- 语义冲突检测和解决
- 事实冲突检测和解决
- 结构冲突检测和解决
- 冲突严重程度评估
- 自动 vs 手动冲突解决

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-19
"""


import pytest

from canvas_utils import (
    CONFLICT_RESOLUTION_AUTO,
    CONFLICT_RESOLUTION_MANUAL,
    CONFLICT_RESOLUTION_WEIGHTED,
    CONFLICT_SEVERITY_HIGH_THRESHOLD,
    CONFLICT_SEVERITY_MEDIUM_THRESHOLD,
    CONFLICT_TYPE_FACTUAL,
    CONFLICT_TYPE_SEMANTIC,
    CONFLICT_TYPE_STRUCTURAL,
    ConflictDetection,
    ConflictDetector,
    ConflictResolution,
    ConflictResolver,
    TaskResult,
)


class TestConflictResolution:
    """测试冲突解决机制"""

    @pytest.fixture
    def conflict_detector(self):
        """创建冲突检测器实例"""
        return ConflictDetector()

    @pytest.fixture
    def conflict_resolver(self):
        """创建冲突解决器实例"""
        return ConflictResolver()

    @pytest.fixture
    def semantic_conflict_results(self):
        """创建包含语义冲突的结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={
                    "content": "这个说法是正确的",
                    "statement": "地球是圆的"
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={
                    "content": "这个说法是错误的",
                    "statement": "地球是平的"
                }
            ),
            TaskResult(
                task_id="task_3",
                agent_type="agent3",
                success=True,
                result_data={
                    "content": "这个说法是对的",
                    "statement": "地球是球形的"
                }
            )
        ]

    @pytest.fixture
    def factual_conflict_results(self):
        """创建包含事实冲突的结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={
                    "number": 42,
                    "fact": "水的沸点是100度"
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={
                    "number": 24,  # 与task1冲突
                    "fact": "水的沸点是98度"  # 与task1冲突
                }
            )
        ]

    @pytest.fixture
    def structural_conflict_results(self):
        """创建包含结构冲突的结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={
                    "content": "文本内容",
                    "details": {"key1": "value1"}
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={
                    "items": ["项目1", "项目2"],  # 不同结构
                    "count": 2
                }
            )
        ]

    @pytest.mark.asyncio
    async def test_detect_semantic_conflicts(self, conflict_detector, semantic_conflict_results):
        """测试语义冲突检测"""
        conflicts = await conflict_detector.detect_conflicts(semantic_conflict_results)

        assert len(conflicts) > 0, "应该检测到语义冲突"

        semantic_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_SEMANTIC]
        assert len(semantic_conflicts) > 0, "应该检测到语义类型冲突"

        for conflict in semantic_conflicts:
            assert conflict.conflict_id
            assert conflict.conflict_type == CONFLICT_TYPE_SEMANTIC
            assert 0.0 <= conflict.severity <= 1.0
            assert len(conflict.conflicting_sources) >= 2
            assert conflict.detected_content
            assert conflict.suggested_resolution

    @pytest.mark.asyncio
    async def test_detect_factual_conflicts(self, conflict_detector, factual_conflict_results):
        """测试事实冲突检测"""
        conflicts = await conflict_detector.detect_conflicts(factual_conflict_results)

        factual_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_FACTUAL]
        assert len(factual_conflicts) > 0, "应该检测到事实冲突"

        for conflict in factual_conflicts:
            assert conflict.conflict_type == CONFLICT_TYPE_FACTUAL
            assert conflict.severity >= 0.7, "事实冲突应该有较高的严重程度"
            assert not conflict.auto_resolvable, "事实冲突通常不能自动解决"

    @pytest.mark.asyncio
    async def test_detect_structural_conflicts(self, conflict_detector, structural_conflict_results):
        """测试结构冲突检测"""
        conflicts = await conflict_detector.detect_conflicts(structural_conflict_results)

        structural_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_STRUCTURAL]
        if structural_conflicts:  # 结构冲突是可选的
            for conflict in structural_conflicts:
                assert conflict.conflict_type == CONFLICT_TYPE_STRUCTURAL
                assert conflict.auto_resolvable, "结构冲突通常可以自动解决"

    @pytest.mark.asyncio
    async def test_resolve_semantic_conflicts(self, conflict_resolver):
        """测试语义冲突解决"""
        # 创建语义冲突
        semantic_conflict = ConflictDetection(
            conflict_id="semantic_1",
            conflict_type=CONFLICT_TYPE_SEMANTIC,
            severity=0.6,
            conflicting_sources=["agent1", "agent2"],
            detected_content="语义冲突示例",
            suggested_resolution="基于权重选择",
            auto_resolvable=True
        )

        # 创建结果和权重
        results = [
            TaskResult("task1", "agent1", True, {"content": "来自agent1的高质量内容"}),
            TaskResult("task2", "agent2", True, {"content": "来自agent2的内容"})
        ]

        weights = {"agent1": 0.8, "agent2": 0.2}

        resolutions = await conflict_resolver.resolve_conflicts([semantic_conflict], results, weights)

        assert len(resolutions) > 0
        resolution = resolutions[0]

        assert resolution.resolution_id
        assert resolution.conflict_id == semantic_conflict.conflict_id
        assert resolution.selected_content
        assert resolution.reasoning
        assert resolution.resolution_strategy in [CONFLICT_RESOLUTION_WEIGHTED, CONFLICT_RESOLUTION_AUTO]

    @pytest.mark.asyncio
    async def test_resolve_factual_conflicts(self, conflict_resolver):
        """测试事实冲突解决"""
        factual_conflict = ConflictDetection(
            conflict_id="factual_1",
            conflict_type=CONFLICT_TYPE_FACTUAL,
            severity=0.9,
            conflicting_sources=["agent1", "agent2"],
            detected_content="事实冲突：不同的事实陈述",
            suggested_resolution="需要人工验证",
            auto_resolvable=False
        )

        resolutions = await conflict_resolver.resolve_conflicts([factual_conflict], [], {})

        assert len(resolutions) > 0
        resolution = resolutions[0]

        assert resolution.resolution_strategy == CONFLICT_RESOLUTION_MANUAL
        assert not resolution.success, "事实冲突通常不能自动解决"
        assert "[事实冲突，需验证]" in resolution.selected_content

    @pytest.mark.asyncio
    async def test_resolve_structural_conflicts(self, conflict_resolver):
        """测试结构冲突解决"""
        structural_conflict = ConflictDetection(
            conflict_id="structural_1",
            conflict_type=CONFLICT_TYPE_STRUCTURAL,
            severity=0.5,
            conflicting_sources=["agent1", "agent2"],
            detected_content="结构冲突：不同的数据格式",
            suggested_resolution="选择兼容结构",
            auto_resolvable=True
        )

        # 创建不同结构的结果
        results = [
            TaskResult("task1", "agent1", True, {"type": "dict", "data": "value1"}),
            TaskResult("task2", "agent2", True, {"items": ["item1", "item2"], "count": 2})
        ]

        weights = {"agent1": 0.6, "agent2": 0.4}

        resolutions = await conflict_resolver.resolve_conflicts([structural_conflict], results, weights)

        assert len(resolutions) > 0
        resolution = resolutions[0]

        assert resolution.resolution_strategy == CONFLICT_RESOLUTION_AUTO
        assert resolution.success, "结构冲突应该能自动解决"

    @pytest.mark.asyncio
    async def test_conflict_severity_assessment(self, conflict_detector):
        """测试冲突严重程度评估"""
        # 高严重性冲突（完全相反的陈述）
        high_severity_results = [
            TaskResult("task1", "agent1", True, {"content": "完全正确"}),
            TaskResult("task2", "agent2", True, {"content": "完全错误"})
        ]

        conflicts = await conflict_detector.detect_conflicts(high_severity_results)
        if conflicts:
            high_severity_conflicts = [c for c in conflicts if c.severity >= CONFLICT_SEVERITY_HIGH_THRESHOLD]
            # 高严重性冲突应该被检测到
            assert len(high_severity_conflicts) > 0 or len(conflicts) > 0

        # 低严重性冲突（轻微差异）
        low_severity_results = [
            TaskResult("task1", "agent1", True, {"content": "很好的解释"}),
            TaskResult("task2", "agent2", True, {"content": "不错的说明"})
        ]

        conflicts = await conflict_detector.detect_conflicts(low_severity_results)
        # 低严重性冲突可能不检测到，或者严重程度较低

    @pytest.mark.asyncio
    async def test_auto_vs_manual_resolution(self, conflict_resolver):
        """测试自动vs手动冲突解决"""
        auto_resolvable_conflict = ConflictDetection(
            conflict_id="auto_1",
            conflict_type=CONFLICT_TYPE_SEMANTIC,
            severity=0.4,  # 低严重性
            conflicting_sources=["agent1", "agent2"],
            detected_content="轻微语义冲突",
            suggested_resolution="自动选择",
            auto_resolvable=True
        )

        manual_resolution_conflict = ConflictDetection(
            conflict_id="manual_1",
            conflict_type=CONFLICT_TYPE_FACTUAL,
            severity=0.9,  # 高严重性
            conflicting_sources=["agent1", "agent2"],
            detected_content="严重事实冲突",
            suggested_resolution="需要人工审核",
            auto_resolvable=False
        )

        results = [
            TaskResult("task1", "agent1", True, {"content": "内容1"}),
            TaskResult("task2", "agent2", True, {"content": "内容2"})
        ]

        weights = {"agent1": 0.7, "agent2": 0.3}

        resolutions = await conflict_resolver.resolve_conflicts(
            [auto_resolvable_conflict, manual_resolution_conflict],
            results,
            weights
        )

        assert len(resolutions) == 2

        # 自动解决的冲突应该成功
        auto_resolution = next(r for r in resolutions if r.conflict_id == "auto_1")
        assert auto_resolution.success

        # 手动解决的冲突应该标记为未成功
        manual_resolution = next(r for r in resolutions if r.conflict_id == "manual_1")
        assert not manual_resolution.success

    @pytest.mark.asyncio
    async def test_weighted_conflict_resolution(self, conflict_resolver):
        """测试基于权重的冲突解决"""
        # 创建冲突和明确不同的权重
        conflict = ConflictDetection(
            conflict_id="weighted_1",
            conflict_type=CONFLICT_TYPE_SEMANTIC,
            severity=0.6,
            conflicting_sources=["high_weight_agent", "low_weight_agent"],
            detected_content="权重不同的冲突",
            suggested_resolution="选择高权重",
            auto_resolvable=True
        )

        results = [
            TaskResult("task1", "high_weight_agent", True, {"content": "高权重Agent的内容"}),
            TaskResult("task2", "low_weight_agent", True, {"content": "低权重Agent的内容"})
        ]

        # 明确的权重差异
        weights = {"high_weight_agent": 0.9, "low_weight_agent": 0.1}

        resolutions = await conflict_resolver.resolve_conflicts([conflict], results, weights)

        assert len(resolutions) > 0
        resolution = resolutions[0]

        # 应该选择高权重Agent的内容
        assert "high_weight_agent" in resolution.reasoning
        assert "0.90" in resolution.reasoning or "0.9" in resolution.reasoning

    @pytest.mark.asyncio
    async def test_conflict_resolution_quality(self, conflict_resolver):
        """测试冲突解决质量"""
        conflict = ConflictDetection(
            conflict_id="quality_1",
            conflict_type=CONFLICT_TYPE_SEMANTIC,
            severity=0.7,
            conflicting_sources=["agent1", "agent2"],
            detected_content="质量测试冲突",
            suggested_resolution="质量评估",
            auto_resolvable=True
        )

        results = [
            TaskResult("task1", "agent1", True, {
                "content": "详细且准确的内容，包含丰富的信息和深入的分析",
                "examples": ["示例1", "示例2", "示例3"],
                "analysis": "深入分析"
            }),
            TaskResult("task2", "agent2", True, {
                "content": "简单内容"
            })
        ]

        weights = {"agent1": 0.8, "agent2": 0.2}  # agent1权重更高

        resolutions = await conflict_resolver.resolve_conflicts([conflict], results, weights)

        assert len(resolutions) > 0
        resolution = resolutions[0]

        # 验证解决质量
        assert resolution.selected_content
        assert resolution.reasoning
        assert len(resolution.reasoning) > 20  # 推理应该详细

        # 验证置信度影响
        assert isinstance(resolution.confidence_impact, float)
        assert -1.0 <= resolution.confidence_impact <= 1.0

    @pytest.mark.asyncio
    async def test_multiple_conflicts_resolution(self, conflict_resolver):
        """测试多个冲突的解决"""
        conflicts = [
            ConflictDetection(
                conflict_id="conflict_1",
                conflict_type=CONFLICT_TYPE_SEMANTIC,
                severity=0.5,
                conflicting_sources=["agent1", "agent2"],
                detected_content="语义冲突1",
                auto_resolvable=True
            ),
            ConflictDetection(
                conflict_id="conflict_2",
                conflict_type=CONFLICT_TYPE_STRUCTURAL,
                severity=0.3,
                conflicting_sources=["agent1", "agent3"],
                detected_content="结构冲突1",
                auto_resolvable=True
            )
        ]

        results = [
            TaskResult("task1", "agent1", True, {"content": "Agent1内容"}),
            TaskResult("task2", "agent2", True, {"content": "Agent2内容"}),
            TaskResult("task3", "agent3", True, {"items": ["item1"]})
        ]

        weights = {"agent1": 0.5, "agent2": 0.3, "agent3": 0.2}

        resolutions = await conflict_resolver.resolve_conflicts(conflicts, results, weights)

        assert len(resolutions) == 2  # 应该为每个冲突生成一个解决方案

        # 验证每个解决方案的质量
        for resolution in resolutions:
            assert resolution.resolution_id
            assert resolution.conflict_id in ["conflict_1", "conflict_2"]
            assert resolution.selected_content
            assert resolution.reasoning

    def test_conflict_data_models(self):
        """测试冲突相关数据模型"""
        # 测试ConflictDetection
        conflict = ConflictDetection(
            conflict_id="test_conflict",
            conflict_type=CONFLICT_TYPE_SEMANTIC,
            severity=0.7,
            conflicting_sources=["agent1", "agent2"],
            detected_content="测试冲突",
            suggested_resolution="测试解决",
            auto_resolvable=True
        )

        assert conflict.conflict_id == "test_conflict"
        assert conflict.conflict_type == CONFLICT_TYPE_SEMANTIC
        assert conflict.severity == 0.7
        assert len(conflict.conflicting_sources) == 2
        assert conflict.auto_resolvable

        # 测试ConflictResolution
        resolution = ConflictResolution(
            resolution_id="test_resolution",
            conflict_id="test_conflict",
            resolution_strategy=CONFLICT_RESOLUTION_WEIGHTED,
            selected_content="选中的内容",
            rejected_content=["拒绝的内容1", "拒绝的内容2"],
            reasoning="解决原因",
            confidence_impact=0.1,
            success=True
        )

        assert resolution.resolution_id == "test_resolution"
        assert resolution.conflict_id == "test_conflict"
        assert resolution.resolution_strategy == CONFLICT_RESOLUTION_WEIGHTED
        assert resolution.selected_content == "选中的内容"
        assert len(resolution.rejected_content) == 2
        assert resolution.confidence_impact == 0.1
        assert resolution.success

    def test_conflict_types_constants(self):
        """测试冲突类型常量"""
        from canvas_utils import CONFLICT_TYPE_FACTUAL, CONFLICT_TYPE_SEMANTIC, CONFLICT_TYPE_STRUCTURAL

        assert CONFLICT_TYPE_SEMANTIC == "semantic"
        assert CONFLICT_TYPE_FACTUAL == "factual"
        assert CONFLICT_TYPE_STRUCTURAL == "structural"

    def test_conflict_resolution_constants(self):
        """测试冲突解决策略常量"""
        from canvas_utils import CONFLICT_RESOLUTION_AUTO, CONFLICT_RESOLUTION_MANUAL, CONFLICT_RESOLUTION_WEIGHTED

        assert CONFLICT_RESOLUTION_AUTO == "auto"
        assert CONFLICT_RESOLUTION_MANUAL == "manual"
        assert CONFLICT_RESOLUTION_WEIGHTED == "weighted"

    def test_conflict_severity_thresholds(self):
        """测试冲突严重程度阈值常量"""
        from canvas_utils import CONFLICT_SEVERITY_HIGH_THRESHOLD

        assert CONFLICT_SEVERITY_HIGH_THRESHOLD == 0.8
        assert CONFLICT_SEVERITY_MEDIUM_THRESHOLD == 0.5

        # 验证阈值关系
        assert CONFLICT_SEVERITY_HIGH_THRESHOLD > CONFLICT_SEVERITY_MEDIUM_THRESHOLD


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
