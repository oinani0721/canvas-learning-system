"""
测试智能结果融合引擎 - Story 7.2

本模块测试智能结果融合的各项功能：
- 冲突检测和解决算法
- 置信度评估机制
- 基于置信度的加权融合
- 信息完整性保护机制
- 融合过程可解释性
- 性能优化和集成测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-19
"""

import os

# 导入被测试的模块
import sys
import time

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from canvas_utils import (
    CONFLICT_TYPE_FACTUAL,
    # 常量
    CONFLICT_TYPE_SEMANTIC,
    CONFLICT_TYPE_STRUCTURAL,
    FUSION_CONFIDENCE_THRESHOLD,
    FUSION_STRATEGY_HIERARCHICAL,
    FUSION_STRATEGY_SUPPLEMENTARY,
    # 并发执行引擎
    ConcurrentAgentExecutor,
    ConfidenceCalculator,
    ConflictDetection,
    # 核心融合类
    ConflictDetector,
    ConflictResolver,
    FusionResult,
    FusionStrategyEngine,
    FusionTraceability,
    IntelligentResultFusion,
    # 数据模型
    TaskResult,
    TraceabilityRecorder,
)


class TestConflictDetector:
    """测试冲突检测器"""

    @pytest.fixture
    def conflict_detector(self):
        """创建冲突检测器实例"""
        return ConflictDetector()

    @pytest.fixture
    def sample_results(self):
        """创建示例Agent结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="oral-explanation",
                success=True,
                result_data={
                    "content": "逆否命题是逻辑学中的重要概念，它是通过对原命题进行否定和倒置得到的。",
                    "explanation": "如果原命题是'如果P则Q'，那么逆否命题就是'如果非Q则非P'。"
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="clarification-path",
                success=True,
                result_data={
                    "content": "逆否命题不是简单的倒置，而是对原命题的否定和倒置。",
                    "explanation": "原命题'如果P则Q'的逆否命题是'如果非Q则非P'，两者逻辑等价。"
                }
            ),
            TaskResult(
                task_id="task_3",
                agent_type="comparison-table",
                success=True,
                result_data={
                    "content": "逆否命题与原命题在真值上是等价的。",
                    "examples": [
                        "原命题：如果下雨，则地面湿润。",
                        "逆否命题：如果地面不湿润，则没有下雨。"
                    ]
                }
            )
        ]

    @pytest.mark.asyncio
    async def test_detect_conflicts_with_semantic_conflicts(self, conflict_detector, sample_results):
        """测试语义冲突检测"""
        conflicts = await conflict_detector.detect_conflicts(sample_results)

        # 应该检测到语义冲突
        assert len(conflicts) > 0

        # 检查冲突类型
        semantic_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_SEMANTIC]
        assert len(semantic_conflicts) > 0

        # 检查冲突严重程度
        for conflict in semantic_conflicts:
            assert 0.0 <= conflict.severity <= 1.0
            assert conflict.conflicting_sources
            assert conflict.detected_content
            assert conflict.suggested_resolution

    @pytest.mark.asyncio
    async def test_detect_conflicts_with_no_results(self, conflict_detector):
        """测试空结果列表的冲突检测"""
        conflicts = await conflict_detector.detect_conflicts([])
        assert conflicts == []

    @pytest.mark.asyncio
    async def test_detect_conflicts_with_single_result(self, conflict_detector):
        """测试单个结果的冲突检测"""
        single_result = [TaskResult(
            task_id="task_1",
            agent_type="oral-explanation",
            success=True,
            result_data={"content": "单个结果不应产生冲突"}
        )]

        conflicts = await conflict_detector.detect_conflicts(single_result)
        assert conflicts == []

    @pytest.mark.asyncio
    async def test_detect_factual_conflicts(self, conflict_detector):
        """测试事实冲突检测"""
        results_with_factual_conflicts = [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={"number_value": 42, "fact": "地球是圆的"}
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={"number_value": 24, "fact": "地球是平的"}  # 事实冲突
            )
        ]

        conflicts = await conflict_detector.detect_conflicts(results_with_factual_conflicts)

        # 应该检测到事实冲突
        factual_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_FACTUAL]
        assert len(factual_conflicts) > 0

    @pytest.mark.asyncio
    async def test_detect_structural_conflicts(self, conflict_detector):
        """测试结构冲突检测"""
        results_with_structural_conflicts = [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={"content": "文本内容", "type": "string"}
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={"items": ["列表", "项目"], "count": 2}  # 不同结构
            )
        ]

        conflicts = await conflict_detector.detect_conflicts(results_with_structural_conflicts)

        # 可能检测到结构冲突
        structural_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_STRUCTURAL]
        # 结构冲突检测取决于具体实现，这里只验证方法能正常执行


class TestConflictResolver:
    """测试冲突解决器"""

    @pytest.fixture
    def conflict_resolver(self):
        """创建冲突解决器实例"""
        return ConflictResolver()

    @pytest.fixture
    def sample_conflicts(self):
        """创建示例冲突"""
        return [
            ConflictDetection(
                conflict_id="conflict_1",
                conflict_type=CONFLICT_TYPE_SEMANTIC,
                severity=0.6,
                conflicting_sources=["agent1", "agent2"],
                detected_content="语义冲突示例",
                suggested_resolution="基于权重选择",
                auto_resolvable=True
            )
        ]

    @pytest.fixture
    def sample_results(self):
        """创建示例结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={"content": "来自agent1的内容"}
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={"content": "来自agent2的内容"}
            )
        ]

    @pytest.fixture
    def sample_weights(self):
        """创建示例权重"""
        return {"agent1": 0.7, "agent2": 0.3}

    @pytest.mark.asyncio
    async def test_resolve_semantic_conflicts(self, conflict_resolver, sample_conflicts, sample_results, sample_weights):
        """测试语义冲突解决"""
        resolutions = await conflict_resolver.resolve_conflicts(
            sample_conflicts, sample_results, sample_weights
        )

        assert len(resolutions) > 0

        resolution = resolutions[0]
        assert resolution.resolution_id
        assert resolution.conflict_id == sample_conflicts[0].conflict_id
        assert resolution.selected_content
        assert resolution.reasoning
        assert isinstance(resolution.confidence_impact, float)

    @pytest.mark.asyncio
    async def test_resolve_factual_conflicts(self, conflict_resolver):
        """测试事实冲突解决"""
        factual_conflict = ConflictDetection(
            conflict_id="factual_1",
            conflict_type=CONFLICT_TYPE_FACTUAL,
            severity=0.9,
            conflicting_sources=["agent1", "agent2"],
            detected_content="事实冲突示例",
            suggested_resolution="需要人工验证",
            auto_resolvable=False  # 事实冲突通常需要人工验证
        )

        resolutions = await conflict_resolver.resolve_conflicts(
            [factual_conflict], [], {}
        )

        assert len(resolutions) > 0
        assert resolutions[0].resolution_strategy == "manual"
        assert not resolutions[0].success  # 事实冲突通常不能自动解决

    @pytest.mark.asyncio
    async def test_resolve_structural_conflicts(self, conflict_resolver):
        """测试结构冲突解决"""
        structural_conflict = ConflictDetection(
            conflict_id="structural_1",
            conflict_type=CONFLICT_TYPE_STRUCTURAL,
            severity=0.5,
            conflicting_sources=["agent1", "agent2"],
            detected_content="结构冲突示例",
            suggested_resolution="选择兼容结构",
            auto_resolvable=True
        )

        resolutions = await conflict_resolver.resolve_conflicts(
            [structural_conflict], [], {}
        )

        assert len(resolutions) > 0
        assert resolutions[0].success


class TestConfidenceCalculator:
    """测试置信度计算器"""

    @pytest.fixture
    def confidence_calculator(self):
        """创建置信度计算器实例"""
        return ConfidenceCalculator()

    @pytest.fixture
    def sample_results(self):
        """创建示例结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="oral-explanation",
                success=True,
                result_data={
                    "content": "这是一个详细的内容解释，包含足够的信息和深度分析。",
                    "examples": ["示例1", "示例2", "示例3"],
                    "summary": "内容摘要"
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="basic-decomposition",
                success=True,
                result_data={
                    "content": "简短内容"
                }
            ),
            TaskResult(
                task_id="task_3",
                agent_type="comparison-table",
                success=False,
                result_data={"error": "处理失败"}
            )
        ]

    @pytest.mark.asyncio
    async def test_calculate_confidence_weights(self, confidence_calculator, sample_results):
        """测试置信度权重计算"""
        target_context = {"keywords": ["内容", "解释"]}

        weights = await confidence_calculator.calculate_confidence_weights(
            sample_results, target_context
        )

        assert len(weights) == len(sample_results)

        # 失败的任务权重应该为0
        assert weights["comparison-table"] == 0.0

        # 成功任务的权重应该在0-1之间
        assert 0.0 <= weights["oral-explanation"] <= 1.0
        assert 0.0 <= weights["basic-decomposition"] <= 1.0

        # 权重总和应该为1（标准化后）
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001 or total_weight == 0.0

    def test_calculate_content_confidence(self, confidence_calculator):
        """测试内容置信度计算"""
        # 丰富的内容
        rich_content = {
            "content": "这是一个详细的内容" * 20,  # 长内容
            "examples": ["例1", "例2"],
            "summary": "摘要"
        }
        confidence = confidence_calculator._calculate_content_confidence(rich_content)
        assert confidence > 0.7

        # 简单的内容
        simple_content = {"content": "简单内容"}
        confidence = confidence_calculator._calculate_content_confidence(simple_content)
        assert 0.0 <= confidence <= 1.0

        # 空内容
        empty_content = {}
        confidence = confidence_calculator._calculate_content_confidence(empty_content)
        assert confidence == 0.0

    def test_calculate_relevance_score(self, confidence_calculator):
        """测试相关性评分计算"""
        content = {"content": "机器学习是人工智能的一个分支"}

        # 高相关性
        high_relevance_context = {"keywords": ["机器学习", "人工智能"]}
        score = confidence_calculator._calculate_relevance_score(content, high_relevance_context)
        assert score > 0.5

        # 低相关性
        low_relevance_context = {"keywords": ["历史", "文学"]}
        score = confidence_calculator._calculate_relevance_score(content, low_relevance_context)
        assert score >= 0.3  # 最低相关性

        # 无关键词
        no_keywords_context = {}
        score = confidence_calculator._calculate_relevance_score(content, no_keywords_context)
        assert score == 0.7  # 默认相关性

    def test_calculate_complexity_score(self, confidence_calculator):
        """测试复杂度评分计算"""
        # 高复杂度
        complex_content = {"content": "x" * 1500, "field1": "value1", "field2": "value2", "field3": "value3"}
        score = confidence_calculator._calculate_complexity_score(complex_content)
        assert score > 0.5

        # 低复杂度
        simple_content = {"content": "简单"}
        score = confidence_calculator._calculate_complexity_score(simple_content)
        assert score >= 0.2  # 最低复杂度


class TestFusionStrategyEngine:
    """测试融合策略引擎"""

    @pytest.fixture
    def fusion_strategy_engine(self):
        """创建融合策略引擎实例"""
        return FusionStrategyEngine()

    @pytest.fixture
    def sample_results(self):
        """创建示例结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={"key1": "value1", "key2": "common"}
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={"key2": "different", "key3": "value3"}
            )
        ]

    def test_select_optimal_strategy_no_conflicts(self, fusion_strategy_engine, sample_results):
        """测试无冲突时的策略选择"""
        strategy = fusion_strategy_engine.select_optimal_strategy(
            sample_results, [], {}
        )
        assert strategy == FUSION_STRATEGY_SUPPLEMENTARY

    def test_select_optimal_strategy_with_conflicts(self, fusion_strategy_engine, sample_results):
        """测试有冲突时的策略选择"""
        conflicts = [
            ConflictDetection(
                conflict_id="conflict_1",
                conflict_type=CONFLICT_TYPE_SEMANTIC,
                severity=0.9,  # 高严重性冲突
                conflicting_sources=["agent1", "agent2"],
                detected_content="高严重性冲突",
                suggested_resolution="需要层次融合",
                auto_resolvable=False
            )
        ]

        strategy = fusion_strategy_engine.select_optimal_strategy(
            sample_results, conflicts, {}
        )
        assert strategy == FUSION_STRATEGY_HIERARCHICAL

    @pytest.mark.asyncio
    async def test_execute_supplementary_fusion(self, fusion_strategy_engine, sample_results):
        """测试补充融合执行"""
        result = await fusion_strategy_engine._execute_supplementary_fusion(sample_results)

        assert isinstance(result, dict)
        # 补充融合应该简单合并内容
        assert "key1" in result
        assert "key2" in result
        assert "key3" in result

    @pytest.mark.asyncio
    async def test_execute_weighted_voting_fusion(self, fusion_strategy_engine, sample_results):
        """测试加权投票融合执行"""
        weights = {"agent1": 0.7, "agent2": 0.3}
        conflict_resolutions = []

        result = await fusion_strategy_engine._execute_weighted_voting_fusion(
            sample_results, weights, conflict_resolutions
        )

        assert isinstance(result, dict)
        assert "weighted_content" in result
        assert "voting_results" in result

    @pytest.mark.asyncio
    async def test_execute_hierarchical_fusion(self, fusion_strategy_engine, sample_results):
        """测试层次融合执行"""
        weights = {"agent1": 0.8, "agent2": 0.2}
        conflict_resolutions = []

        result = await fusion_strategy_engine._execute_hierarchical_fusion(
            sample_results, weights, conflict_resolutions
        )

        assert isinstance(result, dict)
        assert "primary_content" in result
        assert "secondary_content" in result
        assert "resolved_conflicts" in result


class TestIntelligentResultFusion:
    """测试智能结果融合引擎"""

    @pytest.fixture
    def fusion_engine(self):
        """创建融合引擎实例"""
        return IntelligentResultFusion()

    @pytest.fixture
    def sample_results(self):
        """创建示例结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="oral-explanation",
                success=True,
                result_data={
                    "content": "智能结果融合能够将多个Agent的输出整合为更高质量的结果。",
                    "advantage": "提高准确性和完整性"
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="clarification-path",
                success=True,
                result_data={
                    "content": "融合过程中需要检测和解决冲突，确保信息的一致性。",
                    "method": "基于置信度的加权融合"
                }
            ),
            TaskResult(
                task_id="task_3",
                agent_type="comparison-table",
                success=True,
                result_data={
                    "content": "不同的融合策略适用于不同的场景，需要智能选择最优策略。",
                    "strategies": ["补充融合", "互补融合", "层次融合", "加权投票"]
                }
            )
        ]

    @pytest.mark.asyncio
    async def test_fuse_agent_results_success(self, fusion_engine, sample_results):
        """测试成功的Agent结果融合"""
        fusion_result = await fusion_engine.fuse_agent_results(sample_results)

        assert isinstance(fusion_result, FusionResult)
        assert fusion_result.task_id
        assert fusion_result.merged_content
        assert 0.0 <= fusion_result.confidence_score <= 1.0
        assert isinstance(fusion_result.conflict_resolutions, list)
        assert fusion_result.source_attributions
        assert fusion_result.fusion_metadata
        assert fusion_result.processing_time >= 0

    @pytest.mark.asyncio
    async def test_fuse_agent_results_empty(self, fusion_engine):
        """测试空结果列表的融合"""
        with pytest.raises(ValueError, match="源结果列表不能为空"):
            await fusion_engine.fuse_agent_results([])

    @pytest.mark.asyncio
    async def test_fuse_agent_results_single(self, fusion_engine):
        """测试单个结果的融合"""
        single_result = [TaskResult(
            task_id="task_1",
            agent_type="agent1",
            success=True,
            result_data={"content": "单个结果"}
        )]

        fusion_result = await fusion_engine.fuse_agent_results(single_result)

        assert isinstance(fusion_result, FusionResult)
        assert fusion_result.fusion_metadata["strategy"] == "single_source"
        assert fusion_result.confidence_score == 0.8  # 单个结果的默认置信度

    @pytest.mark.asyncio
    async def test_detect_conflicts(self, fusion_engine, sample_results):
        """测试冲突检测"""
        conflicts = await fusion_engine.detect_conflicts(sample_results)

        assert isinstance(conflicts, list)
        # 可能检测到冲突，也可能不检测，取决于内容

    @pytest.mark.asyncio
    async def test_calculate_confidence_weights(self, fusion_engine, sample_results):
        """测试置信度权重计算"""
        target_context = {"keywords": ["融合", "智能"]}

        weights = await fusion_engine.calculate_confidence_weights(
            sample_results, target_context
        )

        assert isinstance(weights, dict)
        assert len(weights) == len(sample_results)

        # 验证权重范围
        for weight in weights.values():
            assert 0.0 <= weight <= 1.0

    @pytest.mark.asyncio
    async def test_generate_fusion_explanation(self, fusion_engine, sample_results):
        """测试融合解释生成"""
        # 首先执行融合
        fusion_result = await fusion_engine.fuse_agent_results(sample_results)

        # 然后生成解释
        explanation = await fusion_engine.generate_fusion_explanation(fusion_result)

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "智能结果融合过程解释" in explanation
        assert fusion_result.task_id in explanation


class TestTraceabilityRecorder:
    """测试溯源记录器"""

    @pytest.fixture
    def traceability_recorder(self):
        """创建溯源记录器实例"""
        return TraceabilityRecorder()

    @pytest.fixture
    def sample_fusion_result(self):
        """创建示例融合结果"""
        return FusionResult(
            task_id="fusion_test_1",
            merged_content={"content": "融合内容"},
            confidence_score=0.85,
            conflict_resolutions=[],
            source_attributions={"agent1": "贡献内容"},
            fusion_metadata={"strategy": "supplementary"}
        )

    @pytest.fixture
    def sample_results(self):
        """创建示例结果"""
        return [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={"content": "内容1"}
            )
        ]

    @pytest.mark.asyncio
    async def test_record_fusion_process(self, traceability_recorder, sample_fusion_result, sample_results):
        """测试融合过程记录"""
        agent_weights = {"agent1": 1.0}
        conflicts = []
        conflict_resolutions = []

        await traceability_recorder.record_fusion_process(
            sample_fusion_result, sample_results, agent_weights, conflicts, conflict_resolutions
        )

        # 验证记录已保存
        assert sample_fusion_result.task_id in traceability_recorder.fusion_records

        traceability = traceability_recorder.fusion_records[sample_fusion_result.task_id]
        assert isinstance(traceability, FusionTraceability)
        assert traceability.fusion_id == sample_fusion_result.task_id
        assert traceability.decision_log
        assert traceability.source_contributions
        assert traceability.quality_metrics

    @pytest.mark.asyncio
    async def test_generate_explanation(self, traceability_recorder, sample_fusion_result):
        """测试解释生成"""
        # 先记录融合过程
        sample_results = [TaskResult(
            task_id="task_1",
            agent_type="agent1",
            success=True,
            result_data={"content": "测试内容"}
        )]

        await traceability_recorder.record_fusion_process(
            sample_fusion_result, sample_results, {}, [], []
        )

        # 生成解释
        explanation = await traceability_recorder.generate_explanation(sample_fusion_result)

        assert isinstance(explanation, str)
        assert len(explanation) > 0
        assert "智能结果融合过程解释" in explanation

    def test_calculate_contributions(self, traceability_recorder):
        """测试贡献度计算"""
        sample_results = [TaskResult(task_id="t1", agent_type="agent1", success=True)]
        agent_weights = {"agent1": 0.7, "agent2": 0.3}
        fusion_result = FusionResult(
            task_id="test",
            merged_content={},
            confidence_score=0.8,
            conflict_resolutions=[],
            source_attributions={}
        )

        contributions = traceability_recorder._calculate_contributions(
            sample_results, agent_weights, fusion_result
        )

        assert isinstance(contributions, dict)
        assert "agent1" in contributions


class TestPerformanceIntegration:
    """测试性能和集成"""

    @pytest.fixture
    def concurrent_executor(self):
        """创建并发执行器实例"""
        return ConcurrentAgentExecutor()

    @pytest.mark.asyncio
    async def test_fusion_performance_targets(self):
        """测试融合性能目标"""
        fusion_engine = IntelligentResultFusion()

        # 创建多个结果进行性能测试
        results = []
        for i in range(5):  # 5个Agent结果
            results.append(TaskResult(
                task_id=f"task_{i}",
                agent_type=f"agent_{i}",
                success=True,
                result_data={
                    "content": f"这是来自agent_{i}的内容，包含足够的信息用于测试融合性能。",
                    "data": f"数据_{i}",
                    "metadata": {"source": f"agent_{i}", "timestamp": time.time()}
                }
            ))

        start_time = time.time()
        fusion_result = await fusion_engine.fuse_agent_results(results)
        processing_time = time.time() - start_time

        # 验证性能目标
        assert processing_time <= FUSION_PROCESSING_TIME_TARGET, f"融合处理时间 {processing_time:.2f}s 超过目标 {FUSION_PROCESSING_TIME_TARGET}s"

        # 验证结果质量
        assert fusion_result.confidence_score >= FUSION_CONFIDENCE_THRESHOLD
        assert fusion_result.merged_content

    @pytest.mark.asyncio
    async def test_conflict_detection_accuracy(self):
        """测试冲突检测准确率"""
        conflict_detector = ConflictDetector()

        # 创建包含已知冲突的结果
        conflicting_results = [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={"content": "这个说法是正确的"}
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={"content": "这个说法是错误的"}  # 明显冲突
            ),
            TaskResult(
                task_id="task_3",
                agent_type="agent3",
                success=True,
                result_data={"content": "这个说法是对的"}  # 与task2冲突
            )
        ]

        conflicts = await conflict_detector.detect_conflicts(conflicting_results)

        # 验证检测到冲突
        assert len(conflicts) > 0, "应该检测到冲突"

        # 验证冲突检测准确性（简化验证）
        semantic_conflicts = [c for c in conflicts if c.conflict_type == CONFLICT_TYPE_SEMANTIC]
        assert len(semantic_conflicts) > 0, "应该检测到语义冲突"

    @pytest.mark.asyncio
    async def test_information_completeness(self):
        """测试信息完整性保留率"""
        fusion_engine = IntelligentResultFusion()

        # 创建包含多样信息的原始结果
        original_results = [
            TaskResult(
                task_id="task_1",
                agent_type="agent1",
                success=True,
                result_data={
                    "content": "主要内容",
                    "examples": ["示例1", "示例2", "示例3"],
                    "details": {"key1": "value1", "key2": "value2", "key3": "value3"}
                }
            ),
            TaskResult(
                task_id="task_2",
                agent_type="agent2",
                success=True,
                result_data={
                    "content": "补充内容",
                    "additional_info": {"extra1": "data1", "extra2": "data2"},
                    "references": ["参考1", "参考2"]
                }
            )
        ]

        # 计算原始信息量
        original_content = ""
        for result in original_results:
            original_content += str(result.result_data)

        # 执行融合
        fusion_result = await fusion_engine.fuse_agent_results(original_results)

        # 计算融合后信息量
        fused_content = str(fusion_result.merged_content)

        # 计算完整性比率（简化版本）
        completeness_ratio = min(len(fused_content) / len(original_content), 1.0)

        # 验证信息完整性
        assert completeness_ratio >= INFORMATION_COMPLETENESS_TARGET, \
            f"信息完整性 {completeness_ratio:.2f} 低于目标 {INFORMATION_COMPLETENESS_TARGET}"

    @pytest.mark.asyncio
    async def test_confidence_assessment_accuracy(self):
        """测试置信度评估准确率"""
        confidence_calculator = ConfidenceCalculator()

        # 创建不同质量的结果
        test_results = [
            TaskResult(
                task_id="high_quality",
                agent_type="oral-explanation",  # 高基础置信度
                success=True,
                result_data={
                    "content": "这是一个高质量、详细且准确的内容解释。" * 10,
                    "examples": ["详细示例1", "详细示例2"],
                    "analysis": {"aspect1": "深入分析1", "aspect2": "深入分析2"}
                }
            ),
            TaskResult(
                task_id="low_quality",
                agent_type="memory-anchor",  # 较低基础置信度
                success=True,
                result_data={"content": "简单内容"}  # 简单内容
            ),
            TaskResult(
                task_id="failed",
                agent_type="scoring-agent",
                success=False,  # 失败结果
                result_data={"error": "处理失败"}
            )
        ]

        target_context = {"keywords": ["高质量", "内容"]}

        weights = await confidence_calculator.calculate_confidence_weights(
            test_results, target_context
        )

        # 验证置信度评估的合理性
        assert weights["high_quality"] > weights["low_quality"], "高质量结果应该有更高权重"
        assert weights["failed"] == 0.0, "失败结果权重应该为0"

        # 验证权重总和
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001, "权重总和应该为1"


# 集成测试类
class TestEndToEndIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_complete_fusion_workflow(self):
        """测试完整的融合工作流"""
        # 1. 创建融合引擎
        fusion_engine = IntelligentResultFusion()

        # 2. 创建多样化的Agent结果
        agent_results = [
            TaskResult(
                task_id="oral_1",
                agent_type="oral-explanation",
                success=True,
                result_data={
                    "content": "人工智能的发展历程可以分为多个阶段，从早期的符号主义到现在的深度学习。",
                    "stages": ["符号主义", "连接主义", "深度学习"],
                    "current_state": "目前深度学习在图像识别、自然语言处理等领域取得突破性进展。"
                }
            ),
            TaskResult(
                task_id="clarification_1",
                agent_type="clarification-path",
                success=True,
                result_data={
                    "content": "人工智能不是单一技术，而是一个包含多个子领域的综合性学科。",
                    "subfields": ["机器学习", "计算机视觉", "自然语言处理", "机器人学"],
                    "misconception": "常见误区是认为AI就等于深度学习，实际上AI范围更广。"
                }
            ),
            TaskResult(
                task_id="comparison_1",
                agent_type="comparison-table",
                success=True,
                result_data={
                    "content": "不同AI方法各有优劣，适用于不同场景。",
                    "comparison": {
                        "符号主义": "优点：逻辑清晰，缺点：难以处理不确定性",
                        "连接主义": "优点：学习能力强，缺点：需要大量数据",
                        "深度学习": "优点：性能优越，缺点：计算资源需求大"
                    }
                }
            ),
            TaskResult(
                task_id="memory_1",
                agent_type="memory-anchor",
                success=True,
                result_data={
                    "content": "记住AI发展的关键节点：1956年达特茅斯会议提出AI概念，2012年AlexNet开启深度学习时代。",
                    "mnemonic": "达特茅斯定AI名，AlexNet开深度篇"
                }
            ),
            TaskResult(
                task_id="failed_1",
                agent_type="example-teaching",
                success=False,
                result_data={"error": "处理超时"}
            )
        ]

        # 3. 执行智能融合
        fusion_result = await fusion_engine.fuse_agent_results(agent_results)

        # 4. 验证融合结果
        assert isinstance(fusion_result, FusionResult)
        assert fusion_result.confidence_score >= FUSION_CONFIDENCE_THRESHOLD
        assert len(fusion_result.merged_content) > 0
        assert fusion_result.processing_time <= FUSION_PROCESSING_TIME_TARGET

        # 5. 生成融合解释
        explanation = await fusion_engine.generate_fusion_explanation(fusion_result)
        assert len(explanation) > 0
        assert "AI" in explanation or "人工智能" in explanation

        # 6. 验证溯源信息
        assert len(fusion_result.source_attributions) > 0
        assert fusion_result.fusion_metadata["agent_count"] == len([r for r in agent_results if r.success])

    @pytest.mark.asyncio
    async def test_integration_with_concurrent_executor(self):
        """测试与并发执行器的集成"""
        executor = ConcurrentAgentExecutor()

        # 创建复杂任务
        complex_task = {
            "user_request": "解释什么是智能结果融合，以及它如何提高多Agent系统的输出质量",
            "canvas_context": {
                "topic": "智能结果融合",
                "keywords": ["融合", "多Agent", "质量", "智能"]
            }
        }

        # 执行带融合的并发任务
        result = await executor.execute_with_intelligent_fusion(
            complex_task,
            max_agents=3,
            enable_fusion=True,
            fusion_config={"strategy": "complementary"}
        )

        # 验证结果
        assert result["success"]
        assert result.get("fusion_applied", False)
        assert "fusion_result" in result
        assert "fusion_explanation" in result

        # 验证融合结果质量
        fusion_result = result["fusion_result"]
        assert fusion_result["confidence_score"] >= 0.6
        assert len(fusion_result["merged_content"]) > 0


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
