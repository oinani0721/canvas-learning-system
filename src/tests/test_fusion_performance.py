"""
智能结果融合性能测试 - Story 7.2

性能专项测试，验证融合引擎满足性能要求：
- 冲突检测准确率≥90%
- 融合处理时间≤2秒（5个Agent结果）
- 置信度评估准确率≥85%
- 信息完整性保留率≥95%

Author: Canvas Learning System Team
Version: 1.0
Created: 2025-01-19
"""

import pytest
import asyncio
import time
import statistics
from typing import List, Dict, Any

from canvas_utils import (
    IntelligentResultFusion, ConflictDetector, ConfidenceCalculator,
    TaskResult, ConflictDetection,
    CONFLICT_DETECTION_ACCURACY_TARGET, FUSION_PROCESSING_TIME_TARGET,
    CONFIDENCE_ASSESSMENT_ACCURACY_TARGET, INFORMATION_COMPLETENESS_TARGET,
    AGENT_BASE_CONFIDENCE
)


class TestFusionPerformance:
    """测试智能融合性能"""

    @pytest.fixture
    def fusion_engine(self):
        """创建融合引擎实例"""
        return IntelligentResultFusion()

    @pytest.fixture
    def conflict_detector(self):
        """创建冲突检测器实例"""
        return ConflictDetector()

    @pytest.fixture
    def confidence_calculator(self):
        """创建置信度计算器实例"""
        return ConfidenceCalculator()

    @pytest.fixture
    def performance_test_results(self):
        """创建性能测试用的结果集"""
        results = []
        for i in range(5):  # 5个Agent结果
            results.append(TaskResult(
                task_id=f"task_{i}",
                agent_type=f"agent_{i}",
                success=True,
                result_data={
                    "content": f"这是第{i}个Agent的详细结果内容，包含足够的信息进行性能测试。内容长度适中，质量较高。",
                    "data": f"数据_{i}",
                    "metadata": {
                        "source": f"agent_{i}",
                        "quality": "high",
                        "timestamp": time.time()
                    },
                    "examples": [f"示例{i}_1", f"示例{i}_2"],
                    "analysis": f"分析内容_{i}"
                }
            ))
        return results

    @pytest.mark.asyncio
    async def test_fusion_processing_time_performance(self, fusion_engine, performance_test_results):
        """测试融合处理时间性能 - AC: 融合处理时间≤2秒"""
        # 多次测试取平均值
        processing_times = []
        num_runs = 5

        for _ in range(num_runs):
            start_time = time.time()
            fusion_result = await fusion_engine.fuse_agent_results(performance_test_results)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)

        avg_processing_time = statistics.mean(processing_times)
        max_processing_time = max(processing_times)

        print(f"平均处理时间: {avg_processing_time:.3f}s")
        print(f"最大处理时间: {max_processing_time:.3f}s")

        # 验证性能目标
        assert avg_processing_time <= FUSION_PROCESSING_TIME_TARGET, \
            f"平均处理时间 {avg_processing_time:.3f}s 超过目标 {FUSION_PROCESSING_TIME_TARGET}s"
        assert max_processing_time <= FUSION_PROCESSING_TIME_TARGET * 1.5, \
            f"最大处理时间 {max_processing_time:.3f}s 超过目标容限"

    @pytest.mark.asyncio
    async def test_conflict_detection_accuracy(self, conflict_detector):
        """测试冲突检测准确率 - AC: 冲突检测准确率≥90%"""
        # 创建包含已知冲突的测试数据
        test_cases = [
            # 测试用例1: 明显的语义冲突
            {
                "results": [
                    TaskResult("task1", "agent1", True, {"content": "这个说法是完全正确的"}),
                    TaskResult("task2", "agent2", True, {"content": "这个说法是完全错误的"})
                ],
                "expected_conflicts": 1,
                "conflict_type": "semantic"
            },
            # 测试用例2: 事实冲突
            {
                "results": [
                    TaskResult("task1", "agent1", True, {"number": 100, "fact": "事实A"}),
                    TaskResult("task2", "agent2", True, {"number": 200, "fact": "事实B"})  # 数字冲突
                ],
                "expected_conflicts": 1,
                "conflict_type": "factual"
            },
            # 测试用例3: 无冲突
            {
                "results": [
                    TaskResult("task1", "agent1", True, {"content": "一致的内容"}),
                    TaskResult("task2", "agent2", True, {"content": "相似的表述"})
                ],
                "expected_conflicts": 0,
                "conflict_type": "none"
            }
        ]

        total_tests = 0
        correct_detections = 0

        for test_case in test_cases:
            detected_conflicts = await conflict_detector.detect_conflicts(test_case["results"])
            total_tests += 1

            # 判断检测是否正确
            expected_count = test_case["expected_conflicts"]
            actual_count = len(detected_conflicts)

            # 简化的准确性判断：如果期望有冲突且检测到冲突，或者期望无冲突且未检测到冲突，则认为正确
            is_correct = (expected_count > 0 and actual_count > 0) or (expected_count == 0 and actual_count == 0)

            if is_correct:
                correct_detections += 1

            print(f"测试用例: 期望{expected_count}个冲突，检测到{actual_count}个冲突 - {'正确' if is_correct else '错误'}")

        accuracy = correct_detections / total_tests if total_tests > 0 else 0.0
        print(f"冲突检测准确率: {accuracy:.2%}")

        # 验证准确率目标
        assert accuracy >= CONFLICT_DETECTION_ACCURACY_TARGET, \
            f"冲突检测准确率 {accuracy:.2%} 低于目标 {CONFLICT_DETECTION_ACCURACY_TARGET:.2%}"

    @pytest.mark.asyncio
    async def test_confidence_assessment_accuracy(self, confidence_calculator):
        """测试置信度评估准确率 - AC: 置信度评估准确率≥85%"""
        # 创建已知质量的测试结果
        test_cases = [
            # 高质量结果
            {
                "result": TaskResult(
                    "high_quality", "oral-explanation", True,
                    {
                        "content": "这是一个非常详细和准确的内容解释，包含丰富的信息、深入的分析和多个实例。",
                        "examples": ["示例1", "示例2", "示例3"],
                        "analysis": {"aspect1": "深入分析", "aspect2": "详细说明"},
                        "references": ["参考1", "参考2"]
                    }
                ),
                "expected_weight_range": (0.7, 1.0),
                "description": "高质量结果"
            },
            # 中等质量结果
            {
                "result": TaskResult(
                    "medium_quality", "clarification-path", True,
                    {
                        "content": "这是一个中等质量的内容，有一定的信息但不够详细。",
                        "examples": ["示例1"]
                    }
                ),
                "expected_weight_range": (0.4, 0.7),
                "description": "中等质量结果"
            },
            # 低质量结果
            {
                "result": TaskResult(
                    "low_quality", "memory-anchor", True,
                    {
                        "content": "简单内容"
                    }
                ),
                "expected_weight_range": (0.1, 0.4),
                "description": "低质量结果"
            },
            # 失败结果
            {
                "result": TaskResult(
                    "failed", "scoring-agent", False,
                    {"error": "处理失败"}
                ),
                "expected_weight_range": (0.0, 0.0),
                "description": "失败结果"
            }
        ]

        target_context = {"keywords": ["内容", "质量", "测试"]}

        correct_assessments = 0
        total_assessments = len(test_cases)

        for test_case in test_cases:
            weights = await confidence_calculator.calculate_confidence_weights(
                [test_case["result"]], target_context
            )

            weight = weights.get(test_case["result"].agent_type, 0.0)
            min_expected, max_expected = test_case["expected_weight_range"]

            is_correct = min_expected <= weight <= max_expected

            if is_correct:
                correct_assessments += 1

            print(f"{test_case['description']}: 权重{weight:.3f}, 期望范围{min_expected}-{max_expected} - {'正确' if is_correct else '错误'}")

        accuracy = correct_assessments / total_assessments if total_assessments > 0 else 0.0
        print(f"置信度评估准确率: {accuracy:.2%}")

        # 验证准确率目标
        assert accuracy >= CONFIDENCE_ASSESSMENT_ACCURACY_TARGET, \
            f"置信度评估准确率 {accuracy:.2%} 低于目标 {CONFIDENCE_ASSESSMENT_ACCURACY_TARGET:.2%}"

    @pytest.mark.asyncio
    async def test_information_completeness(self, fusion_engine):
        """测试信息完整性保留率 - AC: 信息完整性保留率≥95%"""
        # 创建包含丰富信息的原始结果
        original_results = [
            TaskResult(
                "task1", "agent1", True,
                {
                    "content": "主要内容1" * 10,  # 较长的内容
                    "examples": ["示例1_1", "示例1_2", "示例1_3"],
                    "details": {
                        "key1": "value1",
                        "key2": "value2",
                        "key3": "value3"
                    },
                    "metadata": {"source": "agent1", "quality": "high"}
                }
            ),
            TaskResult(
                "task2", "agent2", True,
                {
                    "content": "主要内容2" * 8,
                    "additional_info": {
                        "extra1": "data1",
                        "extra2": "data2",
                        "extra3": "data3"
                    },
                    "references": ["参考1", "参考2"]
                }
            ),
            TaskResult(
                "task3", "agent3", True,
                {
                    "content": "主要内容3" * 5,
                    "summary": "摘要内容",
                    "conclusion": "结论内容"
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

        # 计算完整性比率
        completeness_ratio = min(len(fused_content) / len(original_content), 1.0)

        print(f"原始内容长度: {len(original_content)}")
        print(f"融合后内容长度: {len(fused_content)}")
        print(f"信息完整性比率: {completeness_ratio:.2%}")

        # 验证信息完整性目标
        assert completeness_ratio >= INFORMATION_COMPLETENESS_TARGET, \
            f"信息完整性比率 {completeness_ratio:.2%} 低于目标 {INFORMATION_COMPLETENESS_TARGET:.2%}"

    @pytest.mark.asyncio
    async def test_scalability_performance(self, fusion_engine):
        """测试融合引擎的扩展性能"""
        # 测试不同规模的结果集
        test_sizes = [3, 5, 10, 15]
        performance_results = {}

        for size in test_sizes:
            # 创建指定大小的结果集
            results = []
            for i in range(size):
                results.append(TaskResult(
                    f"task_{i}", f"agent_{i}", True,
                    {
                        "content": f"Agent {i} 的结果内容，用于测试扩展性能。" * 5,
                        "data": f"data_{i}",
                        "metadata": {"index": i}
                    }
                ))

            # 测试性能
            start_time = time.time()
            fusion_result = await fusion_engine.fuse_agent_results(results)
            processing_time = time.time() - start_time

            performance_results[size] = {
                "processing_time": processing_time,
                "confidence": fusion_result.confidence_score,
                "throughput": size / processing_time  # 每秒处理的结果数
            }

            print(f"规模 {size}: 时间 {processing_time:.3f}s, 置信度 {fusion_result.confidence_score:.3f}, 吞吐量 {performance_results[size]['throughput']:.1f} 结果/秒")

        # 验证扩展性：处理时间增长应该是合理的
        time_3 = performance_results[3]["processing_time"]
        time_10 = performance_results[10]["processing_time"]

        # 10个结果的处理时间不应该超过3个结果的4倍（线性扩展的合理范围）
        time_ratio = time_10 / time_3 if time_3 > 0 else 0
        print(f"扩展性比率 (10/3): {time_ratio:.2f}")

        assert time_ratio <= 4.0, f"扩展性比率 {time_ratio:.2f} 超过合理范围"

    @pytest.mark.asyncio
    async def test_memory_usage_performance(self, fusion_engine):
        """测试内存使用性能"""
        # 创建较大的结果集来测试内存使用
        large_results = []
        for i in range(20):
            large_results.append(TaskResult(
                f"task_{i}", f"agent_{i}", True,
                {
                    "content": "大容量内容测试 " * 100,  # 较大的内容
                    "large_data": ["data"] * 1000,  # 较大的列表
                    "nested_data": {
                        "level1": {
                            "level2": {
                                "level3": f"深度数据_{i}" * 10
                            } * 10
                        } * 10
                    }
                }
            ))

        # 测试内存使用情况
        import sys
        import tracemalloc

        tracemalloc.start()

        start_time = time.time()
        fusion_result = await fusion_engine.fuse_agent_results(large_results)
        processing_time = time.time() - start_time

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        memory_usage_mb = peak / (1024 * 1024)

        print(f"大规模测试 (20个结果):")
        print(f"  处理时间: {processing_time:.3f}s")
        print(f"  内存使用峰值: {memory_usage_mb:.2f} MB")
        print(f"  置信度: {fusion_result.confidence_score:.3f}")

        # 验证内存使用合理（应该不超过100MB）
        assert memory_usage_mb < 100, f"内存使用 {memory_usage_mb:.2f} MB 超过合理范围"
        assert processing_time < 10.0, f"处理时间 {processing_time:.3f}s 超过合理范围"

    @pytest.mark.asyncio
    async def test_concurrent_fusion_performance(self, fusion_engine):
        """测试并发融合性能"""
        # 创建多个独立的融合任务
        async def fusion_task(task_id):
            results = [
                TaskResult(f"task_{task_id}_1", f"agent_{task_id}_1", True, {"content": f"并发内容{task_id}_1"}),
                TaskResult(f"task_{task_id}_2", f"agent_{task_id}_2", True, {"content": f"并发内容{task_id}_2"}),
                TaskResult(f"task_{task_id}_3", f"agent_{task_id}_3", True, {"content": f"并发内容{task_id}_3"})
            ]
            return await fusion_engine.fuse_agent_results(results)

        # 并发执行多个融合任务
        num_tasks = 5
        start_time = time.time()

        tasks = [fusion_task(i) for i in range(num_tasks)]
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        avg_time_per_task = total_time / num_tasks

        print(f"并发测试 ({num_tasks}个任务):")
        print(f"  总时间: {total_time:.3f}s")
        print(f"  平均每任务时间: {avg_time_per_task:.3f}s")

        # 验证所有任务都成功完成
        assert len(results) == num_tasks
        for result in results:
            assert result.confidence_score >= 0.0
            assert result.task_id

    def test_performance_constants(self):
        """测试性能相关常量"""
        from canvas_utils import (
            CONFLICT_DETECTION_ACCURACY_TARGET,
            FUSION_PROCESSING_TIME_TARGET,
            CONFIDENCE_ASSESSMENT_ACCURACY_TARGET,
            INFORMATION_COMPLETENESS_TARGET
        )

        assert CONFLICT_DETECTION_ACCURACY_TARGET == 0.90
        assert FUSION_PROCESSING_TIME_TARGET == 2.0
        assert CONFIDENCE_ASSESSMENT_ACCURACY_TARGET == 0.85
        assert INFORMATION_COMPLETENESS_TARGET == 0.95

    def test_agent_base_confidence_weights(self):
        """测试Agent基础置信度权重"""
        # 验证所有Agent类型都有基础置信度
        expected_agents = [
            "basic-decomposition", "deep-decomposition", "oral-explanation",
            "clarification-path", "comparison-table", "memory-anchor",
            "four-level-explanation", "example-teaching", "scoring-agent"
        ]

        for agent_type in expected_agents:
            assert agent_type in AGENT_BASE_CONFIDENCE, f"Agent {agent_type} 缺少基础置信度配置"
            confidence = AGENT_BASE_CONFIDENCE[agent_type]
            assert 0.0 <= confidence <= 1.0, f"Agent {agent_type} 的置信度 {confidence} 不在有效范围内"

        # 验证置信度权重分布合理
        confidences = list(AGENT_BASE_CONFIDENCE.values())
        min_confidence = min(confidences)
        max_confidence = max(confidences)

        assert 0.5 <= min_confidence <= max_confidence <= 1.0, "置信度权重分布不合理"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])