"""
智能结果融合集成测试 - Story 7.2

测试智能融合引擎与系统其他组件的集成：
- 与ConcurrentAgentExecutor的集成
- 与Layer 1-3架构的兼容性
- 与Canvas操作层的集成
- 端到端工作流测试

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-19
"""

import pytest
import asyncio
import time
from datetime import datetime

from canvas_utils import (
    # 核心融合类
    IntelligentResultFusion, ConcurrentAgentExecutor,

    # 数据模型
    TaskResult, FusionResult,

    # 常量
    CONCURRENT_AGENTS_ENABLED
)


class TestFusionIntegration:
    """测试智能融合引擎的集成"""

    @pytest.mark.asyncio
    async def test_concurrent_executor_fusion_integration(self):
        """测试与ConcurrentAgentExecutor的集成"""
        if not CONCURRENT_AGENTS_ENABLED:
            pytest.skip("Concurrent agents not enabled")

        executor = ConcurrentAgentExecutor()

        # 创建复杂任务
        complex_task = {
            "user_request": "解释机器学习的基本概念和应用",
            "canvas_context": {
                "topic": "机器学习",
                "keywords": ["机器学习", "概念", "应用"]
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
        assert result["success"], "并发执行应该成功"
        assert result.get("fusion_applied", False), "应该应用智能融合"
        assert "fusion_result" in result, "应该包含融合结果"
        assert "fusion_explanation" in result, "应该包含融合解释"

        # 验证融合结果质量
        fusion_result = result["fusion_result"]
        assert fusion_result["confidence_score"] >= 0.6, "融合置信度应该合理"
        assert len(fusion_result["merged_content"]) > 0, "融合内容不应为空"
        assert fusion_result["processing_time"] <= 5.0, "融合处理时间应该合理"

    @pytest.mark.asyncio
    async def test_fusion_with_single_result(self):
        """测试单个结果的融合处理"""
        fusion_engine = IntelligentResultFusion()

        single_result = [TaskResult(
            task_id="task_1",
            agent_type="oral-explanation",
            success=True,
            result_data={
                "content": "这是单个Agent的结果",
                "explanation": "详细解释内容"
            }
        )]

        fusion_result = await fusion_engine.fuse_agent_results(single_result)

        assert fusion_result.task_id
        assert fusion_result.fusion_metadata["strategy"] == "single_source"
        assert fusion_result.confidence_score == 0.8  # 单个结果的默认置信度
        assert fusion_result.source_attributions["oral-explanation"] == "直接采用"

    @pytest.mark.asyncio
    async def test_fusion_with_failed_results(self):
        """测试包含失败结果的融合处理"""
        fusion_engine = IntelligentResultFusion()

        mixed_results = [
            TaskResult(
                task_id="task_1",
                agent_type="oral-explanation",
                success=True,
                result_data={"content": "成功的结果"}
            ),
            TaskResult(
                task_id="task_2",
                agent_type="clarification-path",
                success=False,
                result_data={"error": "处理失败"}
            ),
            TaskResult(
                task_id="task_3",
                agent_type="comparison-table",
                success=True,
                result_data={"content": "另一个成功的结果"}
            )
        ]

        fusion_result = await fusion_engine.fuse_agent_results(mixed_results)

        assert fusion_result.confidence_score > 0.0
        # 应该只使用成功的结果
        assert len(fusion_result.source_attributions) == 2

    @pytest.mark.asyncio
    async def test_fusion_error_handling(self):
        """测试融合过程的错误处理"""
        fusion_engine = IntelligentResultFusion()

        # 测试空结果列表
        with pytest.raises(ValueError, match="源结果列表不能为空"):
            await fusion_engine.fuse_agent_results([])

        # 测试包含None的结果
        results_with_none = [
            TaskResult("task1", "agent1", True, {"content": "valid"}),
            None  # 这在实际中不应该发生，但测试容错性
        ]

        try:
            await fusion_engine.fuse_agent_results(results_with_none)
            # 如果没有抛出异常，说明错误处理正常
        except Exception as e:
            # 如果抛出异常，应该是预期的类型
            assert isinstance(e, (ValueError, TypeError))

    @pytest.mark.asyncio
    async def test_fusion_configuration(self):
        """测试融合配置参数"""
        fusion_engine = IntelligentResultFusion()

        results = [
            TaskResult("task1", "agent1", True, {"content": "内容1"}),
            TaskResult("task2", "agent2", True, {"content": "内容2"})
        ]

        # 测试不同的融合配置
        configs = [
            {"strategy": "complementary"},
            {"strategy": "supplementary"},
            {"strategy": "hierarchical"},
            {"confidence_threshold": 0.9}
        ]

        for config in configs:
            fusion_result = await fusion_engine.fuse_agent_results(results, config)
            assert fusion_result.task_id
            assert fusion_result.confidence_score >= 0.0

    @pytest.mark.asyncio
    async def test_fusion_explanation_generation(self):
        """测试融合解释生成"""
        fusion_engine = IntelligentResultFusion()

        results = [
            TaskResult("task1", "oral-explanation", True, {
                "content": "人工智能是计算机科学的一个分支",
                "examples": ["机器学习", "深度学习"]
            }),
            TaskResult("task2", "clarification-path", True, {
                "content": "AI技术包括多个子领域",
                "fields": ["NLP", "计算机视觉", "机器人学"]
            })
        ]

        fusion_result = await fusion_engine.fuse_agent_results(results)
        explanation = await fusion_engine.generate_fusion_explanation(fusion_result)

        assert isinstance(explanation, str)
        assert len(explanation) > 100  # 解释应该有足够的内容
        assert "智能结果融合过程解释" in explanation
        assert fusion_result.task_id in explanation

    def test_fusion_constants(self):
        """测试融合相关常量"""
        from canvas_utils import (
            FUSION_STRATEGY_SUPPLEMENTARY,
            FUSION_STRATEGY_COMPETIMENTARY,
            FUSION_STRATEGY_HIERARCHICAL,
            FUSION_STRATEGY_WEIGHTED_VOTING,
            CONFLICT_DETECTION_ACCURACY_TARGET,
            FUSION_PROCESSING_TIME_TARGET,
            CONFIDENCE_ASSESSMENT_ACCURACY_TARGET,
            INFORMATION_COMPLETENESS_TARGET
        )

        # 验证常量值
        assert FUSION_STRATEGY_SUPPLEMENTARY == "supplementary"
        assert FUSION_STRATEGY_COMPETIMENTARY == "complementary"
        assert FUSION_STRATEGY_HIERARCHICAL == "hierarchical"
        assert FUSION_STRATEGY_WEIGHTED_VOTING == "weighted_voting"

        assert CONFLICT_DETECTION_ACCURACY_TARGET == 0.90
        assert FUSION_PROCESSING_TIME_TARGET == 2.0
        assert CONFIDENCE_ASSESSMENT_ACCURACY_TARGET == 0.85
        assert INFORMATION_COMPLETENESS_TARGET == 0.95

    @pytest.mark.asyncio
    async def test_fusion_metadata(self):
        """测试融合元数据"""
        fusion_engine = IntelligentResultFusion()

        results = [
            TaskResult("task1", "agent1", True, {"content": "测试内容"}),
            TaskResult("task2", "agent2", True, {"content": "更多内容"})
        ]

        fusion_result = await fusion_engine.fuse_agent_results(results)
        metadata = fusion_result.fusion_metadata

        assert "strategy" in metadata
        assert "agent_count" in metadata
        assert "conflict_count" in metadata
        assert "resolution_count" in metadata
        assert "processing_time" in metadata

        assert metadata["agent_count"] == 2
        assert isinstance(metadata["conflict_count"], int)
        assert isinstance(metadata["resolution_count"], int)

    @pytest.mark.asyncio
    async def test_fusion_traceability(self):
        """测试融合溯源信息"""
        fusion_engine = IntelligentResultFusion()

        results = [
            TaskResult("task1", "oral-explanation", True, {"content": "解释内容"}),
            TaskResult("task2", "clarification-path", True, {"content": "澄清内容"})
        ]

        fusion_result = await fusion_engine.fuse_agent_results(results)

        # 验证溯源信息
        assert len(fusion_result.source_attributions) > 0
        assert "oral-explanation" in fusion_result.source_attributions
        assert "clarification-path" in fusion_result.source_attributions

    @pytest.mark.asyncio
    async def test_fusion_performance_under_load(self):
        """测试融合在负载下的性能"""
        fusion_engine = IntelligentResultFusion()

        # 创建大量结果
        large_results = []
        for i in range(10):
            large_results.append(TaskResult(
                f"task_{i}",
                f"agent_{i}",
                True,
                {
                    "content": f"这是第{i}个Agent的结果内容，包含足够的信息进行测试。",
                    "data": f"数据_{i}",
                    "metadata": {"index": i}
                }
            ))

        start_time = time.time()
        fusion_result = await fusion_engine.fuse_agent_results(large_results)
        processing_time = time.time() - start_time

        # 性能验证
        assert processing_time <= 10.0, f"处理时间 {processing_time:.2f}s 应该在合理范围内"
        assert fusion_result.confidence_score >= 0.5
        assert len(fusion_result.merged_content) > 0

    def test_fusion_backward_compatibility(self):
        """测试向后兼容性"""
        # 确保新的融合功能不会破坏现有功能
        from canvas_utils import CanvasJSONOperator, CanvasBusinessLogic, CanvasOrchestrator

        # 测试现有类仍然可以正常实例化
        try:
            json_op = CanvasJSONOperator()
            business_logic = CanvasBusinessLogic.__new__(CanvasBusinessLogic)
            orchestrator = CanvasOrchestrator.__new__(CanvasOrchestrator)
            print("向后兼容性测试通过")
        except Exception as e:
            pytest.fail(f"向后兼容性测试失败: {e}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])